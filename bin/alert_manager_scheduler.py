import os
import sys
import urllib
import json
import splunk
import splunk.rest as rest
import splunk.input as input
import splunk.entity as entity
import time
import logging
import logging.handlers
import hashlib
import datetime
import socket

dir = os.path.join(os.path.join(os.environ.get('SPLUNK_HOME')), 'etc', 'apps', 'alert_manager', 'bin', 'lib')
if not dir in sys.path:
    sys.path.append(dir)

from EventHandler import *
from IncidentContext import *
from SuppressionHelper import *

#sys.stdout = open('/tmp/stdout', 'w')
#sys.stderr = open('/tmp/stderr', 'w')

start = time.time()

# Setup logger
log = logging.getLogger('alert_manager_scheduler')
fh     = logging.handlers.RotatingFileHandler(os.environ.get('SPLUNK_HOME') + "/var/log/splunk/alert_manager_scheduler.log", maxBytes=25000000, backupCount=5)
formatter = logging.Formatter("%(asctime)-15s %(levelname)-5s %(message)s")
fh.setFormatter(formatter)
log.addHandler(fh)
log.setLevel(logging.INFO)

sessionKey     = sys.stdin.readline().strip()
splunk.setDefault('sessionKey', sessionKey)

eh = EventHandler(sessionKey=sessionKey)
sh = SuppressionHelper(sessionKey=sessionKey)
#sessionKey     = urllib.unquote(sessionKey[11:]).decode('utf8')

log.debug("Scheduler started. sessionKey=%s" % sessionKey)

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

# Look for auto_ttl_resolve incidents
uri = '/services/saved/searches?output_mode=json'
serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)
alerts = json.loads(urllib.unquote(serverContent))
if len(alerts) > 0 and 'entry' in alerts:
    for alert in alerts['entry']:
        if 'content' in alert and 'action.alert_manager' in alert['content'] and alert['content']['action.alert_manager'] == "1" and 'action.alert_manager.param.auto_ttl_resove' in alert['content'] and alert['content']['action.alert_manager.param.auto_ttl_resove'] == "1":
            query_incidents = '{  "alert": "'+alert['name'].encode('utf8')+'", "$or": [ { "status": "auto_assigned" } , { "status": "new" } ] }'
            uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents?query=%s' % urllib.quote(query_incidents)
            serverResponseIncidents, serverContentIncidents = rest.simpleRequest(uri, sessionKey=sessionKey)
            
            incidents = json.loads(serverContentIncidents)
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

# Look for auto_suppress_resolve incidents
query = {}
query['auto_suppress_resolve'] = True
log.debug("Filter: %s" % json.dumps(query))
uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_settings?query=%s' % urllib.quote(json.dumps(query))
serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)
alerts = json.loads(serverContent)
if len(alerts) >0:
    for alert in alerts:
        query_incidents = '{  "alert": "'+alert['alert']+'", "$or": [ { "status": "auto_assigned" } , { "status": "new" } ] }'
        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents?query=%s' % urllib.quote(query_incidents)
        serverResponseIncidents, serverContentIncidents = rest.simpleRequest(uri, sessionKey=sessionKey)

        incidents = json.loads(serverContentIncidents)
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


end = time.time()
duration = round((end-start), 3)
log.info("Alert manager scheduler finished. duration=%ss" % duration)
