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

#sys.stdout = open('/tmp/stdout', 'w')
#sys.stderr = open('/tmp/stderr', 'w')

start = time.time()

# Setup logger
log = logging.getLogger('alert_manager_scheduler')
fh 	= logging.handlers.RotatingFileHandler(os.environ.get('SPLUNK_HOME') + "/var/log/splunk/alert_manager_scheduler.log", maxBytes=25000000, backupCount=5)
formatter = logging.Formatter("%(asctime)-15s %(levelname)-5s %(message)s")
fh.setFormatter(formatter)
log.addHandler(fh)
log.setLevel(logging.DEBUG)

sessionKey 	= sys.stdin.readline().strip()
splunk.setDefault('sessionKey', sessionKey)
#sessionKey 	= urllib.unquote(sessionKey[11:]).decode('utf8')

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

# Look for auto-resolve incidents
query = {}
query['auto_ttl_resolve'] = True
log.debug("Filter: %s" % json.dumps(query))
uri = '/servicesNS/nobody/alert_manager/storage/collections/data/alert_settings?query=%s' % urllib.quote(json.dumps(query))
serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)
alerts = json.loads(serverContent)
if len(alerts) >0:
	for alert in alerts:
		log.debug("Alert settings: %s" % alert)
		#query_incidents = {}
		#query_incidents['alert'] = alert['alert']
		#query_incidents['status'] = 'new'
		#query_incidents = json.dumps(query_incidents)
		query_incidents = '{  "alert": "'+alert['alert']+'", "$or": [ { "status": "auto_assigned" } , { "status": "new" } ] }'
		uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents?query=%s' % urllib.quote(query_incidents)
		serverResponseIncidents, serverContentIncidents = rest.simpleRequest(uri, sessionKey=sessionKey)
		
		incidents = json.loads(serverContentIncidents)
		if len(incidents) > 0:
			for incident in incidents:
				log.info("Checking incident: %s" % incident['job_id'])
				if (incident['alert_time'] + incident['ttl']) <= time.time():
					log.info("Incident %s (%s) should be resolved. alert_time=%s ttl=%s now=%s" % (incident['job_id'], incident['_key'], incident['alert_time'], incident['ttl'], time.time()))
					incident['status'] = 'auto_ttl_resolved'
					uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents/%s' % incident['_key']
					incidentStr = json.dumps(incident)
					serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=incidentStr)
					
					now = datetime.datetime.now().isoformat()
					event_id = hashlib.md5(incident['job_id'] + now).hexdigest()
					log.debug("event_id=%s now=%s" % (event_id, now))

					event = 'time=%s severity=INFO origin="alert_manager_scheduler" event_id="%s" user="splunk-system-user" action="auto_ttl_resolve" previous_status="%s" status="auto_ttl_resolved" job_id="%s"' % (now, event_id, incident['status'], incident['job_id'])
					log.debug("Event will be: %s" % event)
					input.submit(event, hostname = socket.gethostname(), sourcetype = 'incident_change', source = 'alert_manager_scheduler.py', index = config['index'])
				else:
					log.info("Incident %s has not ttl reached yet." % incident['job_id'])

# TODO: Addtl. scheduler scenarios


end = time.time()
duration = round((end-start), 3)
log.info("Alert manager scheduler finished. duration=%ss" % duration)
