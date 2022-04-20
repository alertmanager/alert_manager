import os
import sys
import urllib.parse
import json
import splunk
import splunk.rest as rest
import splunk.input as input
import splunk.entity as entity
import time
import hashlib
import socket
from operator import itemgetter

import splunk.appserver.mrsparkle.lib.util as util
dir = os.path.join(util.get_apps_dir(), 'alert_manager', 'bin', 'lib')
if not dir in sys.path:
    sys.path.append(dir)

from EventHandler import EventHandler
from IncidentContext import IncidentContext
from SuppressionHelper import SuppressionHelper
from ApiManager import ApiManager

from AlertManagerLogger import setupLogger

def resolve_roles(role, roles):
    if role in roles:
        inherited_roles = roles[role]
    else:
        inherited_roles = []

    inherited_roles.append(role)

    for inherited_role in inherited_roles:
        if inherited_role != role:
            new_roles = resolve_roles(inherited_role, roles)
            if len(new_roles) > 0:
                inherited_roles = inherited_roles + list(set(new_roles) - set(inherited_roles))

    return inherited_roles

if __name__ == "__main__":
    start = time.time()

    # Setup logger
    log = setupLogger('scheduler')

    sessionKey     = sys.stdin.readline().strip()
    splunk.setDefault('sessionKey', sessionKey)

    # Setup Helpers
    am = ApiManager(sessionKey = sessionKey)
    eh = EventHandler(sessionKey=sessionKey)
    sh = SuppressionHelper(sessionKey=sessionKey)
    #sessionKey     = urllib.unquote(sessionKey[11:]).decode('utf8')

    log.debug("Scheduler started.")

    # Check KV Store availability
    while not am.checkKvStore():
        log.warn("KV Store is not yet available, sleeping for 1s.")
        time.sleep(1)

    #
    # Get global settings
    #
    config = {}
    config['index'] = 'main'

    restconfig = entity.getEntities('configs/alert_manager', count=-1, sessionKey=sessionKey)
    if len(restconfig) > 0:
        if 'index' in restconfig['settings']:
            config['index'] = restconfig['settings']['index']

    log.debug("Global settings: {}".format(config))

    #
    # Look for auto_ttl_resolve incidents
    #
    uri = '/services/saved/searches?output_mode=json&count=0'
    serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)
    try:
        alerts = json.loads(urllib.parse.unquote(serverContent.decode('utf-8')))
    except:
        log.info('No saved searches found in system, skipping...')
        alerts = []

    if len(alerts) > 0 and 'entry' in alerts:
        for alert in alerts['entry']:
            if 'content' in alert and 'action.alert_manager' in alert['content'] and alert['content']['action.alert_manager'] == "1" and 'action.alert_manager.param.auto_ttl_resove' in alert['content'] and alert['content']['action.alert_manager.param.auto_ttl_resove'] == "1":
                query_incidents = '{  "alert": "'+alert['name']+'", "$or": [ { "status": "auto_assigned" } , { "status": "new" } ] }'
                uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents?query={}'.format(urllib.parse.quote(query_incidents))
                serverResponseIncidents, serverContentIncidents = rest.simpleRequest(uri, sessionKey=sessionKey)

                try:
                    incidents = json.loads(serverContentIncidents.decode('utf-8'))
                except:
                    log.info("Error loading results or no results returned from server for alert='{}'. Skipping...".format((str(alert['name'].encode('utf8').replace('/','%2F')))))
                    incidents = []

                if len(incidents) > 0:
                    log.info("Found {} incidents of alert {} to check for reached ttl...".format(len(incidents), alert['name']))
                    for incident in incidents:
                        log.info("Checking incident: {}".format(incident['incident_id']))
                        if (incident['alert_time'] + incident['ttl']) <= time.time():
                            log.info("Incident {} ({}) should be resolved. alert_time={} ttl={} now={}" .format(incident['incident_id'], incident['_key'], incident['alert_time'], incident['ttl'], time.time()))
                            old_status = incident['status']
                            incident['status'] = 'auto_ttl_resolved'
                            uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents/{}'.format(incident['_key'])
                            incidentStr = json.dumps(incident)
                            serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=incidentStr)

                            now = time.strftime("%Y-%m-%dT%H:%M:%S+0000", time.gmtime())
                            event_id = hashlib.md5(incident['incident_id'].encode('utf-8') + now.encode('utf-8')).hexdigest()
                            log.debug("event_id={} now={}".format(event_id, now))

                            event = 'time={} severity=INFO origin="alert_manager_scheduler" event_id="{}" user="splunk-system-user" action="auto_ttl_resolve" previous_status="{}" status="auto_ttl_resolved" incident_id="{}"'.format(now, event_id, old_status, incident['incident_id'])
                            log.debug("Event will be: {}".format(event))
                            input.submit(event, hostname = socket.gethostname(), sourcetype = 'incident_change', source = 'alert_manager_scheduler.py', index = config['index'])
                            ic = IncidentContext(sessionKey, incident["incident_id"])
                            eh.handleEvent(alert=alert["name"], event="incident_auto_ttl_resolved", incident={"owner": incident["owner"]}, context=ic.getContext())
                        else:
                            log.info("Incident {} has not ttl reached yet.".format(incident['incident_id']))
                else:
                    log.info("No incidents of alert {} to check for reached ttl.".format(alert['name']))
            log.debug('Alert "{}" is not configured for auto_ttl_resolve, skipping...'.format(alert['name']))

    #
    # Look for auto_suppress_resolve incidents
    #
    query = {}
    query['auto_suppress_resolve'] = True
    log.debug("Filter: {}".format(json.dumps(query)))
    uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_settings?query={}'.format(urllib.parse.quote(json.dumps(query)))
    serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)
    try:
        alerts = json.loads(serverContent.decode('utf-8'))
    except:
        log.info('An error happened or no incidents were found with auto_suppress_resolve set to True.')
        alerts = []

    if len(alerts) >0:
        for alert in alerts:
            query_incidents = '{ "alert": "'+ alert['name'].encode('utf8').replace('/','%2F')+ '", "$or": [ { "status": "auto_assigned" } , { "status": "new" } ] }'
            uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents?query={}'.format(urllib.parse.quote(query_incidents))
            serverResponseIncidents, serverContentIncidents = rest.simpleRequest(uri, sessionKey=sessionKey)

            try:
                incidents = json.loads(serverContentIncidents.decode('utf-8'))
            except:
                log.info("An error happened or no incidents were found for alert='{}'. Continuing.".format(str(alert['name'].encode('utf8').replace('/','%2F'))))
                incidents = []

            if len(incidents) > 0:
                log.info("Found {} incidents of alert {} to check for suppression...".format(len(incidents), alert['alert']))
                for incident in incidents:
                    log.info("Checking incident: {}".format(incident['incident_id']))
                    ic = IncidentContext(sessionKey, incident["incident_id"])
                    context = ic.getContext()
                    incident_suppressed, rule_names = sh.checkSuppression(alert['alert'], context)
                    if incident_suppressed == True:
                        log.info("Incident {} ({}) should be resolved. alert_time={} since suppression was successful.".format(incident['incident_id'], incident['_key'], incident['alert_time']))
                        old_status = incident['status']
                        incident['status'] = 'auto_suppress_resolved'
                        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents/{}'.format(incident['_key'])
                        incidentStr = json.dumps(incident)
                        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=incidentStr)

                        now = time.strftime("%Y-%m-%dT%H:%M:%S+0000", time.gmtime())
                        event_id = hashlib.md5(incident['incident_id'].encode('utf-8') + now.encode('utf-8')).hexdigest()
                        log.debug("event_id={} now={}".format(event_id, now))

                        rules = ' '.join(['suppression_rule="'+ rule_name +'"' for  rule_name in rule_names])
                        event = 'time={} severity=INFO origin="alert_manager_scheduler" event_id="{}" user="splunk-system-user" action="auto_suppress_resolve" previous_status="{}" status="auto_suppress_resolved" incident_id="{}" {}'.format(now, event_id, old_status, incident['incident_id'], rules)
                        input.submit(event, hostname = socket.gethostname(), sourcetype = 'incident_change', source = 'alert_manager_scheduler.py', index = config['index'])

                        eh.handleEvent(alert=alert['alert'], event="incident_auto_suppress_resolved", incident={"owner": incident['owner']}, context=context)


    else:
        log.info("No alert found where auto_suppress_resolve is active.")

    #
    # Sync Splunk users to KV store
    #
    log.info("Starting to sync splunk built-in users to kvstore...")

    # Get system roles
    uri = '/services/admin/roles?output_mode=json&count=-1'
    serverRespouse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='GET')
    roles_json = json.loads(serverContent.decode('utf-8'))
    system_roles = {}
    if len(roles_json['entry']) > 0:
        for roles_entry in roles_json['entry']:
            role_name = roles_entry["name"]
            system_roles[role_name] = roles_entry["content"]["imported_roles"]

    log.debug("Roles: {}".format(json.dumps(system_roles)))

    uri = '/services/admin/users?output_mode=json&count=-1'
    serverRespouse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='GET')
    entries = json.loads(serverContent.decode('utf-8'))
    splunk_builtin_users = []
    if len(entries['entry']) > 0:
        for entry in entries['entry']:
            # Only add users with role_alert_manager role
            user_primary_roles = []
            for user_primary_role in entry['content']['roles']:
                user_secondary_roles = resolve_roles(user_primary_role, system_roles)
                log.debug("Resolved user_primary_role {} to {}.".format(user_primary_role, user_secondary_roles))
                user_primary_roles = user_primary_roles + list(set(user_secondary_roles) - set(user_primary_roles))
            log.debug("Roles of user '{}': {}".format(entry['name'], json.dumps(user_primary_roles)))

            if 'alert_manager' in user_primary_roles or 'alert_manager_user' in user_primary_roles:
                user = { "name": entry['name'], "email": entry['content']['email'], "type": "builtin" }
                splunk_builtin_users.append(user)
    log.debug("Got list of splunk users: {}".format(json.dumps(splunk_builtin_users)))

    query = '{ "type": "builtin"}'
    uri = '/servicesNS/nobody/alert_manager/storage/collections/data/alert_users?query={}'.format(urllib.parse.quote(query))
    serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)
    try:
        entries = json.loads(serverContent.decode('utf-8'))
    except Exception as e:
        entries = []

    am_builtin_users = []
    if len(entries) > 0:
        for entry in entries:
            if "email" not in entry:
                entry['email'] = ''

            user = { "_key": entry['_key'], "name": entry['name'], "email": entry['email'], "type": "alert_manager" }
            am_builtin_users.append(user)
    log.debug("Got list of built-in users in the kvstore: {}".format(json.dumps(am_builtin_users)))

    # Search for builtin users to be added or updated in the kvstore
    for entry in splunk_builtin_users:
        el = [element for element in am_builtin_users if element['name'] == entry['name']]
        if not el:
            log.debug("{} needs to be added".format(entry['name']))
            data = json.dumps(entry)
            uri = '/servicesNS/nobody/alert_manager/storage/collections/data/alert_users'
            serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=data)
            log.info("Successfully added user '{}' to kvstore.".format(entry['name']))
        else:
            log.debug("{} found in kvstore.".format(entry['name']))
            if el[0]['email'] != entry['email']:
                log.debug("email of {} needs to be changed to '{}' (is '{}').".format(entry['name'], entry['email'], el[0]['email']))
                data = json.dumps(entry)
                uri = '/servicesNS/nobody/alert_manager/storage/collections/data/alert_users/{}'.format(el[0]['_key'])
                serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=data)
                log.info("Successfully updated user '{}' in the kvstore.".format(entry['name']))
            else:
                log.debug("No change for '{}' required, skipping..".format(entry['name']))

    # search for users to be removed from the kvstore
    for entry in am_builtin_users:
        log.debug("entry: {}".format(json.dumps(entry)))
        el = [element for element in splunk_builtin_users if element['name'] == entry['name']]
        if not el:
            log.debug("'{}' needs to be removed from the kvstore".format(entry['name']))
            uri = '/servicesNS/nobody/alert_manager/storage/collections/data/alert_users/{}'.format(entry['_key'])
            serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='DELETE')
            log.info("Successfully removed user '{}' from the kvstore.".format(entry['name']))

    end = time.time()
    duration = round((end-start), 3)
    log.info("Alert manager scheduler finished. duration={}s".format(duration))
