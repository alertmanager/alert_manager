import sys
import os
import subprocess
from subprocess import Popen, PIPE, STDOUT
import splunk
import splunk.auth as auth
import splunk.entity as entity
import splunk.Intersplunk as intersplunk
import splunk.rest as rest
import splunk.search as search
import splunk.input as input
import splunk.util as sutil
import urllib.parse
import json
import socket
import time
import hashlib
import re
import uuid
import tempfile
import traceback

import splunk.appserver.mrsparkle.lib.util as util
dir = os.path.join(util.get_apps_dir(), 'alert_manager', 'bin', 'lib')
if not dir in sys.path:
    sys.path.append(dir)

from EventHandler import EventHandler
from IncidentContext import IncidentContext
from AlertManagerUsers import AlertManagerUsers
from CsvLookup import CsvLookup
from CsvResultParser import CsvResultParser
from SuppressionHelper import SuppressionHelper

from AlertManagerLogger import setupLogger

def deleteIncidentEvent(incident_id, sessionKey):
    query = '{ "incident_id": "'+ incident_id +'" }'
    uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_results?query={}'.format(urllib.parse.quote(query))
    incidents = getRestData(uri, sessionKey, output_mode = 'default')

    for incident in incidents:
        incident_key = incident['_key']
        log.debug('Deleting old incident results key={}'.format(incident_key))
        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_results/{}'.format(incident_key)
        rest.simpleRequest(uri, sessionKey=sessionKey, method='DELETE', getargs={'output_mode': 'json'})

def getIncidentIdByTitle(title, sessionKey):
    if not title:
        return None, None
    else:
        log.debug("Using title '{}' to search for unresolved incidents with same title".format(title))
        # Fetch all incidents with the same title
        query = '{  "title": "'+ title +'"}'
        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents?sort=alert_time&query={}'.format(urllib.parse.quote(query))
        incidents = getRestData(uri, sessionKey, output_mode = 'default')

    # Return only the latest incident_id
    if len(incidents) > 0:
        incident = incidents[len(incidents)-1]
        # Skip any incident that contains the regex defined in 'append_ignore_status' in the status, assuming all incidents to be ignored match
        regex = settings.get('append_ignore_status')
        if bool(re.search(regex, incident['status'])):
            return None, None
        else:
            return incident['_key'], incident['incident_id']
    else:
        return None, None

def setIncidentsAutoPreviousResolved(context, index, sessionKey):
    if not context.get('title'):
        query = '{  "alert": "'+ context.get('name') +'", "$or": [ { "status": "auto_assigned" } , { "status": "new" } ], "job_id": { "$ne": "'+ context.get('job_id') +'"} }'
    else:
        log.debug("Using title '{}' to search for incidents to auto previous resolve.".format(context.get('title')))
        query = '{  "title": "'+ context.get('title') +'", "$or": [ { "status": "auto_assigned" } , { "status": "new" } ], "job_id": { "$ne": "'+ context.get('job_id') +'"} }'

    uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents?query={}'.format(urllib.parse.quote(query))
    incidents = getRestData(uri, sessionKey, output_mode = 'default')
    if len(incidents) > 0:
        log.info("Got {} incidents to auto-resolve".format(len(incidents)))
        for incident in incidents:
            log.info("Auto-resolving incident with key={}".format(incident['_key']))

            previous_status = incident["status"]
            previous_job_id = incident["job_id"]
            previous_incident_id = incident["incident_id"]
            previous_owner = incident["owner"]

            incident['status'] = 'auto_previous_resolved'
            uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents/{}'.format(incident['_key'])
            getRestData(uri, sessionKey, json.dumps(incident))

            event = 'severity=INFO origin="alert_handler" user="splunk-system-user" action="auto_previous_resolve" previous_status="{}" status="auto_previous_resolved" incident_id="{}" job_id="{}" resolving_incident="{}"'.format(previous_status, previous_incident_id, previous_job_id, context.get('incident_id'))
            createIncidentChangeEvent(event, previous_job_id, index)

            ic = IncidentContext(sessionKey, previous_incident_id)
            eh.handleEvent(alert=context.get('name'), event="incident_auto_previous_resolved", incident={"owner": previous_owner}, context=ic.getContext())
    else:
        log.info("No incidents with matching criteria for auto_previous_resolve found.")

def setIncidentAutoSubsequentResolved(context, index, sessionKey):
    if not context.get('title'):
        query = '{  "alert": "'+ context.get('name') +'", "$or": [ { "status": "auto_assigned" } , { "status": "new" }, { "status": "assigned" }, { "status": "work_in_progress" }, { "status": "on_hold" } ], "job_id": { "$ne": "'+ context.get('job_id') +'"} }'
    else:
        log.debug("Using title '{}' to search for incidents to auto subsequent resolve.".format(context.get('title')))
        query = '{  "title": "'+ context.get('title') +'", "$or": [ { "status": "auto_assigned" } , { "status": "new" }, { "status": "assigned" }, { "status": "work_in_progress" }, { "status": "on_hold" } ], "job_id": { "$ne": "'+ context.get('job_id') +'"} }'

    uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents?query={}'.format(urllib.parse.quote(query))
    prev_incidents = getRestData(uri, sessionKey, output_mode = 'default')
    if len(prev_incidents) > 0:
        prev_incident = prev_incidents[0]
        log.info("Found '{}' as pre-existing incident".format(prev_incident['incident_id']))

        # Set status of current incident and fire event
        setStatus(context.get('_key'), context.get('incident_id'), 'auto_subsequent_resolved', sessionKey)
        event = 'severity=INFO origin="alert_handler" user="splunk-system-user" action="auto_subsequent_resolve" previous_status="{}" status="auto_previous_resolved" incident_id="{}" job_id="{}"'.format(context.get('status'), context.get('incident_id'), context.get('job_id'))
        createIncidentChangeEvent(event, context.get('job_id'), index)

        ic = IncidentContext(sessionKey, incident_id)
        eh.handleEvent(alert=context.get('name'), event="incident_auto_subsequent_resolved", incident={"owner": context.get("owner")}, context=ic.getContext())

        # Update history of pre-existing incident and fire event
        event = 'severity=INFO origin="alert_handler" user="splunk-system-user" action="new_subsequent_incident" incident_id="{}" new_incident_id="{}"'.format(prev_incident['incident_id'], context.get('incident_id'))
        createIncidentChangeEvent(context.get('event'), context.get('job_id'), index)

        ic = IncidentContext(sessionKey, prev_incident['incident_id'])
        eh.handleEvent(alert=context.get('name'), event="incident_new_subsequent_incident", incident=prev_incident, context=ic.getContext())
        return True
    else:
        log.info("No pre-existing incidents with matching criteria for auto_subsequent_resolve found, keep this one open.")
        return False

def setIncidentAutoInfoResolved(context, index, sessionKey, statusval):
    log.info('Resolving incident {} per settings.'.format(context.get('incident_id')))

    # set the status of the incident to the configured resolution status
    setStatus(context.get('_key'), context.get('incident_id'), statusval, sessionKey)

    # create and index a change event
    event = 'severity=INFO origin="alert_handler" user="splunk-system-user" action="auto_informational_resolve" previous_status="{}" status="{}" incident_id="{}" job_id="{}"'.format(context.get('status'), statusval, context.get('incident_id'), context.get('job_id'))
    createIncidentChangeEvent(event, context.get('job_id'), index)

    # create a context run the event handler
    ic = IncidentContext(sessionKey, incident_id)
    eh.handleEvent(alert=context.get('name'), event="auto_informational_resolve", incident={"owner": context.get("owner")}, context=ic.getContext())


def setStatus(incident_key, incident_id, status, sessionKey):
    uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents/{}'.format(incident_key)
    incident = getRestData(uri, sessionKey)
    incident["status"] = status
    if "_user" in incident:
        del(incident["_user"])
    if "_key" in incident:
        del(incident["_key"])
    getRestData(uri, sessionKey, json.dumps(incident))

    log.info("Set status of incident {} to {}".format(incident_id, status))

def setOwner(incident_key, incident_id, owner, sessionKey):
    uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents/{}'.format(incident_key)
    incident = getRestData(uri, sessionKey)
    incident["owner"] = owner
    if "_user" in incident:
        del(incident["_user"])
    if "_key" in incident:
        del(incident["_key"])
    getRestData(uri, sessionKey, json.dumps(incident))

    log.info("Incident {} assigned to {}".format(incident_id, owner))

def createIncident(metadata, config, incident_status, sessionKey):
    alert_time = int(float(sutil.dt2epoch(sutil.parseISO(metadata['alert_time'], True))))
    entry = {}
    entry['title'] = metadata['title']
    entry['category'] = metadata["category"]
    entry['subcategory'] = metadata["subcategory"]
    entry['tags'] = metadata["tags"]
    entry['display_fields'] = metadata['display_fields']
    entry['incident_id'] = metadata['incident_id']
    entry['alert_time'] = alert_time
    entry['job_id'] = metadata['job_id']
    entry['result_id'] = metadata['result_id']
    entry['alert'] = metadata['alert']
    entry['app'] = metadata['app']
    entry['status'] = incident_status
    entry['ttl'] = metadata['ttl']
    entry['impact'] = metadata['impact']
    entry['urgency'] = metadata['urgency']
    entry['priority'] = metadata['priority']
    if metadata.get('owner') is not None:
        entry['owner'] = metadata['owner']
    else:
        entry['owner'] = 'unassigned'
    entry['search'] = metadata['entry'][0]['name']
    entry['external_reference_id'] = metadata['external_reference_id']

    entry = json.dumps(entry, sort_keys=True)
    log.debug("createIncident(): Entry: {}".format(entry))

    uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents'
    response = getRestData(uri, sessionKey, entry)
    return response["_key"]

def updateIncident(incident_id, metadata, sessionKey):
    query = '{ "incident_id": "'+ incident_id +'" }'
    uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents?query={}'.format(urllib.parse.quote(query))
    incidents = getRestData(uri, sessionKey, output_mode = 'default')

    entry = {}
    entry['title'] = incidents[0]['title']
    entry['category'] = metadata["category"]
    entry['subcategory'] = metadata["subcategory"]
    entry['tags'] = metadata["tags"]
    entry['display_fields'] = metadata['display_fields']
    entry['incident_id'] = incidents[0]['incident_id']
    entry['alert_time'] = incidents[0]['alert_time']
    entry['job_id'] = incidents[0]['job_id']
    entry['result_id'] = incidents[0]['result_id']
    entry['alert'] = incidents[0]['alert']
    entry['app'] = incidents[0]['app']
    entry['status'] = incidents[0]['status']
    entry['ttl'] = incidents[0]['ttl']
    entry['priority'] = metadata['priority']
    entry['impact'] = metadata['impact']
    # Only set group_id if it already exists
    if incidents[0].get('group_id') is not None:
        entry['group_id'] = incidents[0]['group_id']
    # Preserve urgency and owner, if overriden by user
    if incidents[0].get('preserve_urgency') == True:
        entry['urgency'] = incidents[0]['urgency']
    else:
        entry['urgency'] = metadata['urgency']
    if incidents[0].get('preserve_owner') == True:
        entry['owner'] = incidents[0]['owner']
    else:
        entry['owner'] = metadata['owner']

    entry['search'] = metadata['entry'][0]['name']
    entry['external_reference_id'] = metadata['external_reference_id']
    entry['duplicate_count'] = incidents[0]['duplicate_count']
    entry['preserve_owner'] = incidents[0].get('preserve_owner')
    entry['preserve_urgency'] = incidents[0].get('preserve_urgency')

    entry = json.dumps(entry, sort_keys=True)

    log.debug("updateIncident(): Entry: {}".format(entry))

    uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents/{}'.format(incidents[0]['_key'])
    getRestData(uri, sessionKey, entry)

def createMetadataEvent(metadata, index, sessionKey):
    input.submit(json.dumps(metadata, sort_keys=True), hostname = socket.gethostname(), sourcetype = 'alert_metadata', source = 'alert_handler.py', index = index)
    log.info("Alert metadata written to index={}".format(index))

def createIncidentChangeEvent(event, job_id, index):
    now = time.strftime("%Y-%m-%dT%H:%M:%S+0000", time.gmtime())
    event_id = hashlib.md5(job_id.encode('utf-8') + now.encode('utf-8')).hexdigest()
    event_prefix = 'time={} event_id="{}" '.format(now, event_id)
    event = event_prefix + event
    input.submit(event, hostname = socket.gethostname(), sourcetype = 'incident_change', source = 'alert_handler.py', index=index)

'''
Method added to allow for indexing of the results in addition to or in place of relying
on the KV store only.
'''
def createIncidentEvent(results, index, sessionKey, incident_id, alerttime, alert_title):
    alert_results = {}
    alert_results['incident_id'] = incident_id
    # Switching back to iso formatted timestamp to avoid misinterpreation
    # alert_results['alert_time'] = int(float(sutil.dt2epoch(sutil.parseISO(alerttime, True))))
    # alert_results['timestamp'] = str(time.strftime('%Y-%m-%d %T %Z', time.gmtime(alert_results['alert_time'])))
    alert_results['alert_time'] = alerttime
    alert_results['title'] = alert_title
    alert_results.update(results)
    input.submit(json.dumps(alert_results, sort_keys=True), hostname = socket.gethostname(), sourcetype = 'alert_data_results', source = 'alert_manager.py', index = index)

def getServerInfo(sessionKey):
    server_info = getRestData('/services/server/info', sessionKey)
    #log.debug("getServerInfo(): server Info: {}".format(json.dumps(server_info)))
    return server_info["entry"][0]["content"]

def createContext(metadata, incident_settings, results, sessionKey, payload):
    server_info = getServerInfo(sessionKey)

    context = { }
    context.update({ "job_id" : metadata["job_id"] })
    context.update({ "alert_time" : metadata["alert_time"] })
    if metadata.get('owner') is None:
        context.update({ "owner" : 'unassigned' })
    else:
        context.update({ "owner" : metadata["owner"] })
    context.update({ "name" : metadata["alert"] })
    context.update({ "title" : metadata["title"] })
    context.update({ "alert" : { "impact": metadata["impact"], "urgency": metadata["urgency"], "priority": metadata["priority"], "expires": metadata["ttl"] } })
    context.update({ "app" : metadata["app"] })
    context.update({ "category" : metadata["category"] })
    context.update({ "subcategory" : metadata["subcategory"] })
    context.update({ "tags" : metadata["tags"] })
    context.update({ "results_link" : payload['results_link'] })

    split_results_path = urllib.parse.splitquery(payload['results_link'])[0].split('/')
    view_path = '/'.join(split_results_path[:-1]) + '/'
    view_link = view_path + 'alert?' + urllib.parse.urlencode({'s': metadata['entry'][0]['links'].get('alternate') })
    context.update({ "view_link" : view_link })

    context.update({ "server" : { "version": server_info["version"], "build": server_info["build"], "serverName": server_info["serverName"] } })

    if "fields" in results:
        result_context = { "result" : results["fields"][0] }
        context.update(result_context)
        results_context = { "results" : results["fields"] }
        context.update(results_context)

    return context

def getResultId(digest_mode, results_file):
    if digest_mode == False:
        result_id = re.search("tmp_(\d+)\.csv\.gz", results_file).group(1)
        return result_id
    else:
        return 0

def getResults(results_file, incident_id):
    parser = CsvResultParser(results_file)
    results = parser.getResults({ "incident_id": incident_id })
    return results

def getUrgencyFromResults(results, default_urgency, incident_id):
    valid_urgencies = { "low", "medium", "high" }
    if len(results["fields"]) > 0 and "urgency" in results["fields"][0] and results["fields"][0]["urgency"] in valid_urgencies:
        log.debug("Found valid urgency field in results, will use urgency={} for incident_id={}".format(results["fields"][0]["urgency"], incident_id))
        return results["fields"][0]["urgency"]
    else:
        log.debug("No valid urgency field found in results. Falling back to default_urgency={} for incident_id={}".format(default_urgency, incident_id))
        return default_urgency

def getImpactFromResults(results, default_impact, incident_id):
    valid_impacts = { "low", "medium", "high" }
    if len(results["fields"]) > 0 and "impact" in results["fields"][0] and results["fields"][0]["impact"] in valid_impacts:
        log.debug("Found valid impact field in results, will use impact={} for incident_id={}".format(results["fields"][0]["impact"], incident_id))
        return results["fields"][0]["impact"]
    else:
        log.debug("No valid impact field found in results. Falling back to default_impact={} for incident_id={}".format(default_impact, incident_id))
        return default_impact

def getOwnerFromResults(results, default_owner, incident_id):
    if len(results["fields"]) > 0 and "owner" in results["fields"][0]:
        log.debug("Found valid owner field in results, will use owner={} for incident_id={}".format(results["fields"][0]["owner"], incident_id))	
        return results["fields"][0]["owner"]
    else:
        log.debug("No valid owner field found in results. Falling back to default_owner={} for incident_id={}".format(default_owner, incident_id))
        return default_owner

def getCategoryFromResults(results, default_category, incident_id):
    if len(results["fields"]) > 0 and "category" in results["fields"][0]:
        log.debug("Found category field in results, will use category={} for incident_id={}".format(results["fields"][0]["category"], incident_id))
        return results["fields"][0]["category"]
    else:
        log.debug("No category field found in results. Falling back to default_category={} for incident_id={}".format(default_category, incident_id))
        return default_category

def getSubcategoryFromResults(results, default_subcategory, incident_id):
    if len(results["fields"]) > 0 and "subcategory" in results["fields"][0]:
        log.debug("Found subcategory field in results, will use subcategory={} for incident_id={}".format(results["fields"][0]["subcategory"], incident_id))
        return results["fields"][0]["subcategory"]
    else:
        log.debug("No subcategory field found in results. Falling back to default_subcategory={} for incident_id={}".format(default_subcategory, incident_id))
        return default_subcategory

def getTagsFromResults(results, default_tags, incident_id):
    if len(results["fields"]) > 0 and "tags" in results["fields"][0]:
        log.debug("Found tags field in results, will use tags={} for incident_id={}".format(results["fields"][0]["tags"], incident_id))
        return results["fields"][0]["tags"]
    else:
        log.debug("No tags field found in results. Falling back to default_tags={} for incident_id={}".format(default_tags, incident_id))
        return default_tags

def getDisplayfieldsFromResults(results, default_displayfields, incident_id):
    if len(results["fields"]) > 0 and "display_fields" in results["fields"][0]:
        log.debug("Found display_fields field in results, will use tags={} for incident_id={}".format(results["fields"][0]["display_fields"], incident_id))
        return results["fields"][0]["display_fields"]
    else:
        log.debug("No display_fields field found in results. Falling back to default_displayfields={} for incident_id={}".format(default_displayfields, incident_id))
        return default_displayfields

def getExternalreferenceidFromResults(results, default_externalreferenceid, incident_id):
    if len(results["fields"]) > 0 and "external_reference_id" in results["fields"][0]:
        log.debug("Found external_reference_id field in results, will use external_reference_id={} for incident_id={}".format(results["fields"][0]["external_reference_id"], incident_id))
        return results["fields"][0]["external_reference_id"]
    else:
        log.debug("No external_reference_id field found in results. Falling back to default_external_reference_id={} for incident_id={}".format(default_externalreferenceid, incident_id))
        return default_externalreferenceid

def getLookupFile(lookup_name, sessionKey):
    uri = '/servicesNS/nobody/alert_manager/data/transforms/lookups/{}'.format(lookup_name)
    lookup = getRestData(uri, sessionKey)
    #log.debug("getLookupFile(): lookup: {}".format(json.dumps(lookup)))
    log.debug("Got lookup content for lookup={}. filename={} app={}".format(lookup_name, lookup["entry"][0]["content"]["filename"], lookup["entry"][0]["acl"]["app"]))
    return os.path.join(util.get_apps_dir(), lookup["entry"][0]["acl"]["app"], 'lookups', lookup["entry"][0]["content"]["filename"])

def getPriority(impact, urgency, default_priority, sessionKey):
    log.debug("getPriority(): Try to calculate priority for impact={} urgency={}".format(impact, urgency))
    try:
        csv_path = getLookupFile('alert_priority', sessionKey)

        if os.path.exists(csv_path):
            log.debug("Lookup file {} found. Proceeding...".format(csv_path))
            lookup = CsvLookup(csv_path)
            query = { "impact": impact, "urgency": urgency }
            log.debug("Querying lookup with filter={}".format(query))
            matches = lookup.lookup(query, { "priority" })
            if len(matches) > 0:
                log.debug("Matched priority in lookup, returning value={}".format(matches["priority"]))
                return matches["priority"]
            else:
                log.debug("No matching priority found in lookup, falling back to default_priority={}".format(config['default_priority']))
        else:
            log.warning("Lookup file {} not found. Falling back to default_priority={}".format(csv_path, config['default_priority']))

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        log.warning("Unable to get priority. Falling back to default_priority={}. Error: {}. Line: {}".format(default_priority, exc_type, exc_tb.tb_lineno))
        return default_priority

def getRestData(uri, sessionKey, data = None, output_mode = 'json'):
    try:
        if data == None:
            if output_mode == 'default':
                serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)
            else:
                serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, getargs={'output_mode': 'json'})
        else:
            if output_mode == 'default':
                serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=data)
            else:
                serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=data, getargs={'output_mode': 'json'})
    except:
        log.info("An error occurred or no data was returned from the server query on uri={}.".format(uri))
        log.info("Exception details: {}".format(traceback.format_exc()))
        serverContent = None

    log.debug("serverResponse: {}".format(serverResponse))
    log.debug("serverContent: {}".format(serverContent.decode('utf-8')))
    try:
        returnData = json.loads(serverContent.decode('utf-8'))
    except:
        log.info("An error occurred or no data was returned from the server query.")
        returnData = []

    return returnData

def getJob(job_id, sessionKey):
    job = getRestData('/services/search/jobs/{}'.format(job_id),sessionKey)
    #log.debug("getJob(): Got job details: {}".format(json.dumps(job))
    return job['entry'][0]

def getSavedSearch(app, search_name, sessionKey):
    if search_name != 'adhoc':
        uri = '/servicesNS/-/{}/admin/savedsearch/{}'.format(app, urllib.parse.quote(search_name, safe=''))
        savedSearch = getRestData(uri, sessionKey)
        #log.debug("getSavedSearch(): Got saved search details: {}".format(json.dumps(savedSearch)))
        return savedSearch['entry'][0]
    else:
        return {}

def getAppSettings(sessionKey):
    cfg = splunk.entity.getEntity('/admin/conf-alert_manager','settings', namespace='alert_manager', sessionKey=sessionKey, owner='nobody')
    #log.debug("getAppSettings(): app settings: {}".format(cfg))
    return cfg

def getIncidentSettings(payload, app_settings, search_name, sessionKey):
    cfg = payload.get('configuration')
    result = payload.get('result')
    
    settings = {}
    settings['title']                    = search_name if ('title' not in cfg or cfg['title'] == '') else cfg['title']
    settings['auto_assign_owner']        = 'unassigned' if ('auto_assign_owner' not in cfg or cfg['auto_assign_owner'] == '') else cfg['auto_assign_owner']
    settings['append_incident']          = False if ('append_incident' not in cfg or cfg['append_incident'] == '') else normalize_bool(cfg['append_incident'])
    settings['auto_ttl_resolve']         = False if ('auto_ttl_resolve' not in cfg or cfg['auto_ttl_resolve'] == '') else normalize_bool(cfg['auto_ttl_resolve'])
    settings['auto_previous_resolve']    = False if ('auto_previous_resolve' not in cfg or cfg['auto_previous_resolve'] == '') else normalize_bool(cfg['auto_previous_resolve'])
    settings['auto_subsequent_resolve']  = False if ('auto_subsequent_resolve' not in cfg or cfg['auto_subsequent_resolve'] == '') else normalize_bool(cfg['auto_subsequent_resolve'])
    
    if ('impact' in result and result['impact'] != ''):
        settings['impact'] = result['impact']
    elif ('impact' not in cfg and cfg['impact'] == ''):
        settings['impact'] = ''
    else:
        settings['impact'] = cfg['impact']

    if ('urgency' in result and result['urgency'] != ''):
        settings['urgency'] = result['urgency']
    elif ('urgency' not in cfg and cfg['urgency'] == ''):
        settings['urgency'] = ''
    else:
        settings['urgency'] = cfg['urgency']

    # Fetch additional settings from incident_settings collection
    query = '{{ "alert": "{}" }}'.format(search_name)
    uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_settings?query={}'.format(urllib.parse.quote(query))
    incident_settings = getRestData(uri, sessionKey, output_mode = 'default')
    if len(incident_settings) > 0:
        incident_setting = incident_settings[0]
    else:
        incident_setting = {}

    settings['category']                 = incident_setting.get('category', '')
    settings['subcategory']              = incident_setting.get('subcategory', '')
    settings['tags']                     = incident_setting.get('tags', '')
    settings['display_fields']           = incident_setting.get('display_fields', '')
    #log.debug("getIncidentSettings: parsed incident settings: {}".format(json.dumps(settings)))
    return settings

def getTTL(expiry):
    timeModifiers = { 's': 1, 'm': 60, 'h': 3600, 'd' : 86400, 'w': 604800 }
    timeModifier = expiry[-1]
    timeRange    = int(expiry[:-1])
    ttl          = timeRange * timeModifiers[timeModifier]
    log.debug("getTTL(): Transformed expiriy {} into {} seconds".format(expiry, ttl))
    return ttl

def normalize_bool(value):
    return True if value.lower() in ('1', 'true') else False

def updateDuplicateCount(incident_key, sessionKey):
    uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents/{}'.format(incident_key)
    incident = getRestData(uri, sessionKey, output_mode = 'default')
    try:
        duplicate_count = incident['duplicate_count']
        duplicate_count = duplicate_count + 1
    except:
        duplicate_count = 1

    uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents/{}'.format(incident_key)
    incident = getRestData(uri, sessionKey)
    incident["duplicate_count"] = duplicate_count
    if "_user" in incident:
        del(incident["_user"])
    if "_key" in incident:
        del(incident["_key"])
    getRestData(uri, sessionKey, json.dumps(incident))

    log.info("Duplicate count: {}".format(duplicate_count))

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--execute":
        start = time.time()

        log = setupLogger('alert_manager')

        log.debug("Python Version: {}".format(sys.version))

        #
        # BEGING Setup
        #
        payload = json.loads(sys.stdin.read())
        #log.debug("Payload: {}".format(json.dumps(payload)))

        sessionKey = payload.get('session_key')
        job_id = payload.get('sid')
        search_name = payload.get('search_name')
        # Support for manually running the alert action using the 'sendalert' search command
        if search_name == '':
            search_name = 'adhoc'

        # Need to set the sessionKey (input.submit() doesn't allow passing the sessionKey)
        splunk.setDefault('sessionKey', sessionKey)

        # Get app settings
        settings = getAppSettings(sessionKey)
        log.debug("Parsed index from app settings: {}".format(settings.get('index')))

        # Get incident config
        config = getIncidentSettings(payload, settings, search_name, sessionKey)

        # Get job details
        job = getJob(job_id, sessionKey)
        result_count = job['content']['resultCount']
        log.info("Found job for alert '{}' with title '{}'. Context is '{}' with {} results.".format(search_name, config['title'], payload.get('app'), result_count))

        # Get saved search config
        savedSearch = getSavedSearch(payload.get('app'), search_name, sessionKey)
        log.debug("Parsed savedsearch settings: expiry={} digest_mode={}".format(savedSearch['content']['alert.expires'], savedSearch['content']['alert.digest_mode']))

        # Parse ttl
        ttl = getTTL(savedSearch['content']['alert.expires'])

        # Get helpers
        eh = EventHandler(sessionKey=sessionKey)
        sh = SuppressionHelper(sessionKey=sessionKey)

        incident_id = None
        incident_key = None

        # If append_incident is set, look for an existing incident_id
        log.debug("Append Incident: {}".format(config['append_incident']))

        if config['append_incident']:
            incident_key, incident_id = getIncidentIdByTitle(config['title'], sessionKey)

        # Create unique id
        if incident_id is None:
            incident_id = str(uuid.uuid4())

        # Get results and result id
        results = getResults(payload.get('results_file'), incident_id)
        result_id = getResultId(savedSearch['content']['alert.digest_mode'], payload.get('results_file'))

        # Prepare metadata
        metadata = {}
        metadata.update({ 'alert': search_name })
        metadata.update({ 'alert_time': job['updated'] })
        metadata.update({ 'app': payload.get('app') })
        # metadata.update({ 'entry': [ job ] })
        # The goal here is to reduce event size and limit the job data down to the fields we
        # absolutely want/care about making them easier to handle later.
        # For backwards compat purposes, I want to keep the data structure the same.

        try:
            job_data = {}
            job_data['content'] = {
                'searchEarliestTime': job['content']['searchEarliestTime'],
                'searchLatestTime': job['content']['searchLatestTime'],
                'earliestTime': job['content']['earliestTime'],
                'latestTime': job['content']['latestTime'],
                'eventCount': job['content']['eventCount'],
                'resultCount': job['content']['resultCount'],
                'eventSearch': job['content']['eventSearch']
            }
            job_data['links'] = { 'alternate': job['links']['alternate'] }
            job_data['name'] = job['name']

            # Not sure why this is stored as a list but later references expect it, so I will leave it this way
            metadata.update({ 'entry': [ job_data ] })

        except:
            # default to original functionality if any error happens above.
            metadata.update({ 'entry': [ job ] })
        ####

        metadata.update({ 'incident_id': incident_id })
        metadata.update({ 'job_id': job_id })
        metadata.update({ 'name': search_name })
        metadata.update({ 'result_id': result_id })
        metadata.update({ 'title': config['title'] })
        metadata.update({ 'ttl': ttl })

        # Get urgency from results and parse priority
        metadata.update({ 'urgency': getUrgencyFromResults(results, config['urgency'], incident_id)})
        metadata.update({ 'impact': getImpactFromResults(results, config['impact'], incident_id)})
        metadata.update({ 'owner': getOwnerFromResults(results, config.get('auto_assign_owner'), incident_id)})
        metadata.update({ 'category': getCategoryFromResults(results, config.get('category'), incident_id)})
        metadata.update({ 'subcategory': getSubcategoryFromResults(results, config.get('subcategory'), incident_id)})
        metadata.update({ 'tags': getTagsFromResults(results, config.get('tags'), incident_id)})
        metadata.update({ 'display_fields': getDisplayfieldsFromResults(results, config.get('display_fields'), incident_id)})
        metadata.update({ 'external_reference_id': getExternalreferenceidFromResults(results, None, incident_id)})
        metadata.update({ 'priority': getPriority(config['impact'], config['urgency'], settings.get('default_priority'), sessionKey)})

        #log.debug("metadata: {}".format(json.dumps(metadata)))

        # Prepare context
        context = createContext(metadata, config, results, sessionKey, payload)

        #
        # END Setup
        #

        #
        # Incident creation
        #

        # Check for incident suppression
        incident_suppressed = False
        incident_status = 'new'
        try:
            incident_suppressed, rule_names = sh.checkSuppression(search_name, context)
        except Exception as e:
            log.error("Suppression failed due nexpected Error: {}".format(traceback.format_exc()))

        if incident_suppressed == True:
            incident_status = 'suppressed'
        log.info("Incident status after suppresion check: {}".format(incident_status))

        # Write incident to collection
        log.debug("Metadata: {}".format(json.dumps(metadata)))
        # Check if there is already an incident to append to...
        if config['append_incident'] and incident_key is not None:
            append_incident = True
            event = 'severity=INFO origin="alert_handler" user="{}" action="comment" incident_id="{}" job_id="{}" alert_time="{}" comment="{}"'.format('splunk-system-user', incident_id, job_id, metadata['alert_time'], "Appending duplicate alert")
            createIncidentChangeEvent(event, metadata['job_id'], settings.get('index'))
            # Update the duplicate_count
            updateDuplicateCount(incident_key, sessionKey)
            # Update incident
            updateIncident(incident_id, metadata, sessionKey)

            log.info("Appending incident for job_id={} with incident_id={} key={}".format(job_id, incident_id, incident_key))

        else:
            append_incident = False
            incident_key = createIncident(metadata, config, incident_status, sessionKey)
            event = 'severity=INFO origin="alert_handler" user="{}" action="create" alert="{}" incident_id="{}" job_id="{}" result_id="{}" owner="{}" status="new" urgency="{}" ttl="{}" alert_time="{}"'.format('splunk-system-user', search_name, incident_id, job_id, result_id, metadata['owner'], metadata['urgency'], metadata['ttl'], metadata['alert_time'])
            createIncidentChangeEvent(event, metadata['job_id'], settings.get('index'))
            log.info("Incident initial state added to collection for job_id={} with incident_id={} key={}".format(job_id, incident_id, incident_key))

        # Log suppress event if necessary
        if incident_suppressed:
            user = 'splunk-system-user'
            rules = ' '.join(['suppression_rule="'+ rule_name +'"' for  rule_name in rule_names])
            event = 'severity=INFO origin="alert_handler" user="{}" action="suppress" alert="{}" incident_id="{}" job_id="{}" result_id="{}" {}'.format('splunk-system-user', search_name, incident_id, job_id, result_id, rules)
            createIncidentChangeEvent(event, metadata['job_id'], settings.get('index'))

        # Write results to collection
        try:
            if normalize_bool(settings.get('collect_data_results')):
                # Old incident results are removed from collection and replaced with new results
                if config['append_incident']:
                    log.debug("Deleting old incident results for incident={}".format(incident_id))
                    deleteIncidentEvent(incident_id, sessionKey)
                uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_results'
                response = getRestData(uri, sessionKey, json.dumps(results))
                log.info("Results for incident_id={} written to collection.".format(incident_id))
        except:
            log.error('Attempting to write results to kvstore for incident_id={} resulted in an exception. {}'.format(incident_id, traceback.format_exc()))

        # Write metadata to index
        try:
            createMetadataEvent(metadata, settings.get('index'), sessionKey)
        except:
            log.error('Attempting to write metadata event to index for incident_id={} resulted in an exception. {}'.format(incident_id, traceback.format_exc()))

        # Write alert results data to index
        try:
            if normalize_bool(settings.get('index_data_results')):
                createIncidentEvent(results, settings.get('index'), sessionKey, incident_id, metadata['alert_time'], metadata['alert'])
                log.debug('Data results indexed for incident_id={}.'.format(incident_id))
        except:
            log.error('Attempting to index results for incident_id={} resulted in an exception. {}'.format(incident_id, traceback.format_exc()))

        # set up incident context
        ic = IncidentContext(sessionKey, incident_id)

        is_subsequent_resolved = False
        # Auto Previous Resolve - run only once
        if config['auto_previous_resolve'] and incident_suppressed == False:
            log.debug("auto_previous_resolve is active for {}. Starting to handle it.".format(search_name))
            setIncidentsAutoPreviousResolved(ic, settings.get('index'), sessionKey)

        elif config['auto_subsequent_resolve'] and incident_suppressed == False:
            log.debug("auto_subsequent_resolve is active for {}. Starting to handle it.".format(search_name))
            is_subsequent_resolved = setIncidentAutoSubsequentResolved(ic, settings.get('index'), sessionKey)


        # Fire incident_created or incident_suppressed event
        # only if it was not deemed a duplicate
        if is_subsequent_resolved:
            log.info("Skipping firing of incident_created event for incident={} because it is a duplicate.".format(incident_id))

        else:
            if incident_suppressed == False and append_incident == False:
                log.info("Firing incident_created event for incident={}".format(incident_id))
                eh.handleEvent(alert=search_name, event="incident_created", incident={"owner": metadata['owner']}, context=ic.getContext())
            elif incident_suppressed == False and append_incident == True:
                log.info("Firing incident_changed event for incident={}".format(incident_id))
                eh.handleEvent(alert=search_name, event="incident_changed", incident={"owner": metadata['owner']}, context=ic.getContext())
            else:
                log.info("Firing incident_suppressed event for incident={}".format(incident_id))
                eh.handleEvent(alert=search_name, event="incident_suppressed", incident={"owner": metadata['owner']}, context=ic.getContext())

        # If the incident was not resolved already, auto resolved is enabled, and priority is informational - resolve it.
        auto_info_resolved = False
        if is_subsequent_resolved == False:
            # This automatic resolution is optional.
            try:
                if normalize_bool(settings.get('auto_close_info')) and metadata['priority'] == 'informational':
                    log.debug('Auto close informational is on')
                    setIncidentAutoInfoResolved(ic, settings.get('index'), sessionKey, settings.get('auto_close_info_status'))
                    auto_info_resolved = True

            except:
                log.error('Attempting to auto resolve for incident_id={} resulted in an exception. {}'.format(incident_id, traceback.format_exc()))


        # Handle auto-assign
        # Added a check to see if the event was resolved as a duplicate. We don't need to do this if it is...
        if config['auto_assign_owner'] != '' and config['auto_assign_owner'] != 'unassigned' and incident_suppressed == False and is_subsequent_resolved == False and auto_info_resolved == False and config['append_incident'] is None:
            log.debug("auto_assign is active for {}. Starting to handle it.".format(search_name))
            setOwner(incident_key, incident_id, config['auto_assign_owner'], sessionKey)
            setStatus(incident_key, incident_id, 'auto_assigned', sessionKey)
            ic.update("owner", config['auto_assign_owner'])

            event = 'severity=INFO origin="alert_handler" user="splunk-system-user" action="change" incident_id="{}" job_id="{}" result_id="{}" owner="{}" previous_owner="unassigned"'.format(incident_id, job_id, result_id, config['auto_assign_owner'])
            createIncidentChangeEvent(event, metadata['job_id'], settings.get('index'))

            event = 'severity=INFO origin="alert_handler" user="splunk-system-user" action="change" incident_id="{}" job_id="{}" result_id="{}" status="auto_assigned" previous_status="new"'.format(incident_id, job_id, result_id)
            createIncidentChangeEvent(event, metadata['job_id'], settings.get('index'))

            if config['auto_subsequent_resolve'] == False:
                eh.handleEvent(alert=search_name, event="incident_auto_assigned", incident={"owner": config["auto_assign_owner"]}, context=ic.getContext())

        #
        # END Incident creation
        #

        #
        # Finish
        #
        end = time.time()
        duration = round((end-start), 3)
        log.info("Alert handler finished. duration={}s".format(duration))

    else:
        print >> sys.stderr, "FATAL Unsupported execution mode (expected --execute flag)"
        sys.exit(1)
