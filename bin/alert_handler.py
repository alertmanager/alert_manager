import sys
import os
import splunk
import splunk.auth as auth
import splunk.entity as entity
import splunk.Intersplunk as intersplunk
import splunk.rest as rest
import splunk.search as search
import splunk.input as input
import splunk.util as util
#from xml.dom import minidom
#import urllib2
import urllib
import json
import socket
import logging
import time

start = time.time()

sys.stdout = open('/tmp/stdout', 'w')
sys.stderr = open('/tmp/stderr', 'w')

# Parse arguments
job_id		= os.path.split(sys.argv[8])[0].split('/')
job_id_seg	= len(job_id)-1
job_id		= job_id[job_id_seg]
sessionKey 	= sys.stdin.readline().strip()
sessionKey 	= urllib.unquote(sessionKey[11:]).decode('utf8')
search_name = sys.argv[4]

# Setup logger
log = logging.getLogger('alert_manager')
fh 	= logging.handlers.RotatingFileHandler(os.environ.get('SPLUNK_HOME') + "/var/log/splunk/alert_manager.log", maxBytes=25000000, backupCount=5)
formatter = logging.Formatter("%(asctime)-15s %(levelname)-5s %(message)s")
fh.setFormatter(formatter)
log.addHandler(fh)
log.setLevel(logging.DEBUG)

# Need to set the sessionKey (input.submit() doesn't allow passing the sessionKey)
splunk.setDefault('sessionKey', sessionKey)

# Get global settings
config = {}
config['index']						= 'alerts'
config['default_assignee'] 			= 'unassigned'
config['disable_save_results']		= 0

restconfig = splunk.entity.getEntities('configs/alert_manager', count=-1, sessionKey=sessionKey)
if len(restconfig) > 0:
	for cfg in config.keys():
		if cfg in restconfig['settings']:
			if restconfig['settings'][cfg] == '0':
				config[cfg] = False
			elif restconfig['settings'][cfg] == '1':
				config[cfg] = True
			else:
				config[cfg] = restconfig['settings'][cfg]

log.debug("Global settings: %s" % config)

# Get per alert settings
alert_config = {}
alert_config['auto_assign']				= False
alert_config['auto_assign_user']		= ''
alert_config['auto_ttl_resolve']		= False
alert_config['auto_previous_resolve']	= False
query = {}
query['search_name'] = search_name
log.debug("Query for alert settings: %s" % urllib.quote(json.dumps(query)))
uri = '/servicesNS/nobody/alert_manager/storage/collections/data/alert_settings?query=%s' % urllib.quote(json.dumps(query))
serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)
log.debug("Alert settings: %s" % serverContent)
alert_settings = json.loads(serverContent)
if len(alert_settings) > 0:
	log.info("Found settings for %s" % search_name)
	for key, val in alert_settings[0].iteritems():
		alert_config[key] = val

log.debug("Alert config after getting settings: %s" % json.dumps(alert_config))

# Get alert metadata
uri = '/services/search/jobs/%s' % job_id
serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, getargs={'output_mode': 'json'})

# Get alert severity
uri = '/servicesNS/nobody/search/admin/savedsearch/%s' % search_name
savedsearchResponse, savedsearchContent = rest.simpleRequest(uri, sessionKey=sessionKey, getargs={'output_mode': 'json'})
savedsearchContent = json.loads(savedsearchContent)
log.debug("severity: %s" % savedsearchContent['entry'][0]['content']['alert.severity'])

# Add attributes id to alert metadata
job = json.loads(serverContent)
job['job_id'] = job_id
job['severity'] = savedsearchContent['entry'][0]['content']['alert.severity']
#log.debug("Job: %s" % json.dumps(job))
alert_time = job['entry'][0]['published']

#job2 = splunk.search.getJob(job_id, sessionKey=sessionKey, message_level='warn')
#log.debug("job2: %s" % json.dumps(job2.toJsonable(timeFormat="unix")))

# Write alert metadata to index
input.submit(json.dumps(job), hostname = socket.gethostname(), sourcetype = 'alert_metadata', source = 'alert_handler.py', index = config['index'])
log.info("Alert metadata written to index=%s" % config['index'])

if config['disable_save_results'] == 0:
	# Get alert results
	job = search.getJob(job_id, sessionKey=sessionKey, message_level='warn')
	feed = job.getFeed(mode='results', outputMode='json')
	feed = json.loads(feed)
	feed['job_id'] = job_id
	feed['published'] = alert_time

	# Write results to index
	input.submit(json.dumps(feed), hostname = socket.gethostname(), sourcetype = 'alert_results', source = 'alert_handler.py', index = config['index'])
	log.info("Alert results written to index=%s" % config['index'])

entry = {}

# Check for alert scenarios
if alert_config['auto_previous_resolve']:
	query = {}
	query['search_name'] = search_name
	query['current_state'] = {"$ne": 'resolved'}
	log.debug("Filter: %s" % json.dumps(query))
	uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents?query=%s' % urllib.quote(json.dumps(query))
	serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)
	incidents = json.loads(serverContent)
	if len(incidents):
		log.info("Got %s incidents to auto-resolve" % len(incidents))
		for incident in incidents:
			log.info("Auto-resolving incident with key=%s" % incident['_key'])
			incident['current_state'] = 'resolved'
			uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents/%s' % incident['_key']
			incident = json.dumps(incident)
			serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=incident)
			# TODO: Save event to index

if alert_config['auto_assign'] and alert_config['auto_assign_user'] != 'unassigned':
	entry['current_assignee'] = alert_config['auto_assign_user']
	log.info("Assigning incident to %s" % alert_config['auto_assign_user'])
	# TODO: Notification
else:
	entry['current_assignee'] = config['default_assignee']	
	log.info("Assigning incident to default assignee %s" % config['default_assignee'])

log.debug("Alert time: %s" % util.dt2epoch(util.parseISO(alert_time, True)))
# Write to alert state collection
uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents'
entry['alert_time'] = int(float(util.dt2epoch(util.parseISO(alert_time, True))))
entry['job_id'] = job_id
entry['search_name'] = search_name
entry['current_state'] = 'new'
entry['severity'] = savedsearchContent['entry'][0]['content']['alert.severity']
entry['ttl'] = job['entry'][0]['content']['ttl']
entry = json.dumps(entry)

serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=entry)
log.info("Incident initial state added to collection")

end = time.time()
duration = round((end-start), 3)
log.info("Alert handler finished. duration=%ss" % duration)
