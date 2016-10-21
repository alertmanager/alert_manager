import os
import sys
import urllib
import json
import splunk
import splunk.rest as rest
import splunk.input as input
import splunk.entity as entity
import time
import hashlib
import datetime
import socket
from operator import itemgetter

dir = os.path.join(os.path.join(os.environ.get('SPLUNK_HOME')), 'etc', 'apps', 'alert_manager', 'bin', 'lib')
if not dir in sys.path:
    sys.path.append(dir)

from EventHandler import *
from IncidentContext import *
from SuppressionHelper import *
from AlertManagerLogger import *
from ApiManager import *


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

    log.debug("Scheduler started. sessionKey=%s" % sessionKey)

    # Check KV Store availability
    while not am.checkKvStore():
        log.warn("KV Store is not yet available, sleeping for 1s.")
        time.sleep(1)
        
    #
    # Get global settings
    #
    config = {}
    config['index'] = 'alerts'

    restconfig = entity.getEntities('configs/alert_manager', count=-1, sessionKey=sessionKey)
    if len(restconfig) > 0:
        if 'index' in restconfig['settings']:
            config['index'] = restconfig['settings']['index']

    log.debug("Global settings: %s" % config)

    #
    # Look for auto_ttl_resolve incidents
    #
    uri = '/services/saved/searches?output_mode=json'
    serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)
    try:
        alerts = json.loads(urllib.unquote(serverContent))
    except:
        log.info('No saved searches found in system, skipping...')
        alerts = []

    if len(alerts) > 0 and 'entry' in alerts:
        for alert in alerts['entry']:
            if 'content' in alert and 'action.alert_manager' in alert['content'] and alert['content']['action.alert_manager'] == "1" and 'action.alert_manager.param.auto_ttl_resove' in alert['content'] and alert['content']['action.alert_manager.param.auto_ttl_resove'] == "1":
                query_incidents = '{  "alert": "'+alert['name'].encode('utf8')+'", "$or": [ { "status": "auto_assigned" } , { "status": "new" } ] }'
                uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents?query=%s' % urllib.quote(query_incidents)
                serverResponseIncidents, serverContentIncidents = rest.simpleRequest(uri, sessionKey=sessionKey)
                
                try:
                    incidents = json.loads(serverContentIncidents)
                except:                
                    log.info("Error loading results or no results returned from server for alert='%s'. Skipping..." % (str(alert['name'].encode('utf8').replace('/','%2F'))))
                    incidents = []

                if len(incidents) > 0:
                    log.info("Found %s incidents of alert %s to check for reached ttl..." % (len(incidents), alert['name']))
                    for incident in incidents:
                        log.info("Checking incident: %s" % incident['incident_id'])
                        if (incident['alert_time'] + incident['ttl']) <= time.time():
                            log.info("Incident %s (%s) should be resolved. alert_time=%s ttl=%s now=%s" % (incident['incident_id'], incident['_key'], incident['alert_time'], incident['ttl'], time.time()))
                            old_status = incident['status']
                            incident['status'] = 'auto_ttl_resolved'
                            uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents/%s' % incident['_key']
                            incidentStr = json.dumps(incident)
                            serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=incidentStr)
                            
                            now = datetime.datetime.now().isoformat()
                            event_id = hashlib.md5(incident['incident_id'] + now).hexdigest()
                            log.debug("event_id=%s now=%s" % (event_id, now))

                            event = 'time=%s severity=INFO origin="alert_manager_scheduler" event_id="%s" user="splunk-system-user" action="auto_ttl_resolve" previous_status="%s" status="auto_ttl_resolved" incident_id="%s"' % (now, event_id, old_status, incident['incident_id'])
                            log.debug("Event will be: %s" % event)
                            input.submit(event, hostname = socket.gethostname(), sourcetype = 'incident_change', source = 'alert_manager_scheduler.py', index = config['index'])
                            ic = IncidentContext(sessionKey, incident["incident_id"])
                            eh.handleEvent(alert=alert["name"], event="incident_auto_ttl_resolved", incident={"owner": incident["owner"]}, context=ic.getContext())
                        else:
                            log.info("Incident %s has not ttl reached yet." % incident['incident_id'])
                else:
                    log.info("No incidents of alert %s to check for reached ttl." % alert['name'])
            log.debug('Alert "%s" is not configured for auto_ttl_resolve, skipping...' % alert['name'])

    #
    # Look for auto_suppress_resolve incidents
    #
    query = {}
    query['auto_suppress_resolve'] = True
    log.debug("Filter: %s" % json.dumps(query))
    uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_settings?query=%s' % urllib.quote(json.dumps(query))
    serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)
    try:
        alerts = json.loads(serverContent)
    except:
        log.info('An error happened or no incidents were found with auto_suppress_resolve set to True.')
        alerts = []

    if len(alerts) >0:
        for alert in alerts:
            query_incidents = '{ "alert": "'+ alert['name'].encode('utf8').replace('/','%2F')+ '", "$or": [ { "status": "auto_assigned" } , { "status": "new" } ] }'
            uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents?query=%s' % urllib.quote(query_incidents)
            serverResponseIncidents, serverContentIncidents = rest.simpleRequest(uri, sessionKey=sessionKey)

            try:
                incidents = json.loads(serverContentIncidents)
            except:
                log.info("An error happened or no incidents were found for alert='%s'. Continuing." % (+ str(alert['name'].encode('utf8').replace('/','%2F'))))
                incidents = []

            if len(incidents) > 0:
                log.info("Found %s incidents of alert %s to check for suppression..." % (len(incidents), alert['alert']))
                for incident in incidents:
                    log.info("Checking incident: %s" % incident['incident_id'])
                    ic = IncidentContext(sessionKey, incident["incident_id"])
                    context = ic.getContext()
                    incident_suppressed, rule_names = sh.checkSuppression(alert['alert'], context)
                    if incident_suppressed == True:
                        log.info("Incident %s (%s) should be resolved. alert_time=%s since suppression was successful." % (incident['incident_id'], incident['_key'], incident['alert_time']))
                        old_status = incident['status']
                        incident['status'] = 'auto_suppress_resolved'
                        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents/%s' % incident['_key']
                        incidentStr = json.dumps(incident)
                        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=incidentStr)

                        now = datetime.datetime.now().isoformat()
                        event_id = hashlib.md5(incident['incident_id'] + now).hexdigest()
                        log.debug("event_id=%s now=%s" % (event_id, now))

                        rules = ' '.join(['suppression_rule="'+ rule_name +'"' for  rule_name in rule_names])
                        event = 'time=%s severity=INFO origin="alert_manager_scheduler" event_id="%s" user="splunk-system-user" action="auto_suppress_resolve" previous_status="%s" status="auto_suppress_resolved" incident_id="%s" %s' % (now, event_id, old_status, incident['incident_id'], rules)
                        input.submit(event, hostname = socket.gethostname(), sourcetype = 'incident_change', source = 'alert_manager_scheduler.py', index = config['index'])

                        eh.handleEvent(alert=alert['alert'], event="incident_auto_suppress_resolved", incident={"owner": incident['owner']}, context=context)
                        

    else:
        log.info("No alert found where auto_suppress_resolve is active.")

    #
    # Sync Splunk users to KV store
    #
    log.info("Starting to sync splunk built-in users to kvstore...")
    uri = '/services/admin/users?output_mode=json&count=-1'
    serverRespouse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='GET')
    entries = json.loads(serverContent)
    splunk_builtin_users = []
    if len(entries['entry']) > 0:
        for entry in entries['entry']:
            # Only add users with am_is_owner capability
            if 'am_is_owner' in entry['content']['capabilities']:
                user = { "name": entry['name'], "email": entry['content']['email'], "type": "builtin" }
                splunk_builtin_users.append(user)
    log.debug("Got list of splunk users: %s" % json.dumps(splunk_builtin_users))

    query = '{ "type": "builtin"}'
    uri = '/servicesNS/nobody/alert_manager/storage/collections/data/alert_users?query=%s' % urllib.quote(query)
    serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)
    try:
        entries = json.loads(serverContent)
    except Exception as e:
        entries = []

    am_builtin_users = []
    if len(entries) > 0:
        for entry in entries:
            if "email" not in entry:
                entry['email'] = ''

            user = { "_key": entry['_key'], "name": entry['name'], "email": entry['email'], "type": "alert_manager" }
            am_builtin_users.append(user)    
    log.debug("Got list of built-in users in the kvstore: %s" % json.dumps(am_builtin_users))

    # Search for builtin users to be added or updated in the kvstore
    for entry in splunk_builtin_users:
        el = [element for element in am_builtin_users if element['name'] == entry['name']]
        if not el:
            log.debug("%s needs to be added" % entry['name'])
            data = json.dumps(entry)
            uri = '/servicesNS/nobody/alert_manager/storage/collections/data/alert_users'
            serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=data)
            log.info("Successfully added user '%s' to kvstore." % entry['name'])
        else:
            log.debug("%s found in kvstore." % entry['name'])
            if el[0]['email'] != entry['email']:
                log.debug("email of %s needs to be changed to '%s' (is '%s')." % (entry['name'], entry['email'], el[0]['email']))
                data = json.dumps(entry)
                uri = '/servicesNS/nobody/alert_manager/storage/collections/data/alert_users/%s' % el[0]['_key']
                serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=data)
                log.info("Successfully updated user '%s' in the kvstore." % entry['name'])
            else:
                log.debug("No change for '%s' required, skipping.." % entry['name'])

    # search for users to be removed from the kvstore
    for entry in am_builtin_users:
        log.debug("entry: %s" % json.dumps(entry))
        el = [element for element in splunk_builtin_users if element['name'] == entry['name']]
        if not el:
            log.debug("'%s' needs to be removed from the kvstore" % entry['name'])
            uri = '/servicesNS/nobody/alert_manager/storage/collections/data/alert_users/%s' % entry['_key']
            serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='DELETE')
            log.info("Successfully removed user '%s' from the kvstore." % entry['name'])        

    end = time.time()
    duration = round((end-start), 3)
    log.info("Alert manager scheduler finished. duration=%ss" % duration)
