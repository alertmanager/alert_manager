import os
import sys
import urllib
import json
import splunk.rest as rest
import time
import logging
import logging.handlers

sys.stdout = open('/tmp/stdout', 'w')
sys.stderr = open('/tmp/stderr', 'w')

start = time.time()

# Setup logger
log = logging.getLogger('alert_manager_scheduler')
fh 	= logging.handlers.RotatingFileHandler(os.environ.get('SPLUNK_HOME') + "/var/log/splunk/alert_manager_scheduler.log", maxBytes=25000000, backupCount=5)
formatter = logging.Formatter("%(asctime)-15s %(levelname)-5s %(message)s")
fh.setFormatter(formatter)
log.addHandler(fh)
log.setLevel(logging.DEBUG)

sessionKey 	= sys.stdin.readline().strip()
#sessionKey 	= urllib.unquote(sessionKey[11:]).decode('utf8')

log.debug("Scheduler started. sessionKey=%s" % sessionKey)

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
		query_incidents = {}
		query_incidents['search_name'] = alert['search_name']
		query_incidents['current_state'] = 'new'
		uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents?query=%s' % urllib.quote(json.dumps(query_incidents))
		serverResponseIncidents, serverContentIncidents = rest.simpleRequest(uri, sessionKey=sessionKey)
		
		incidents = json.loads(serverContentIncidents)
		if len(incidents) > 0:
			for incident in incidents:
				log.debug("Incident: %s" % incident)
				if (incident['alert_time'] + incident['ttl']) <= time.time():
					log.debug("Resolving incident %s (%s) since ttl is reached" % (incident['job_id'], incident['_key']))
					incident['current_state'] = 'auto_ttl_resolved'
					uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents/%s' % incident['_key']
					incident = json.dumps(incident)
					serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=incident)

# TODO: Addtl. scheudler scenarios


end = time.time()
duration = round((end-start), 3)
log.info("Alert manager scheduler finished. duration=%ss" % duration)
