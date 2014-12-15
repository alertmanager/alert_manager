import sys
import subprocess
from subprocess import Popen, PIPE, STDOUT
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

#
# Init
#
start = time.time()

sys.stdout = open('/tmp/stdout', 'w')
sys.stderr = open('/tmp/stderr', 'w')

# Parse arguments
job_id		= os.path.split(sys.argv[8])[0].split('/')
job_id_seg	= len(job_id)-1
job_id		= job_id[job_id_seg]
stdinArgs 	= sys.stdin.readline()
stdinLines  = stdinArgs.strip()
sessionKeyOrig = stdinLines[11:]
sessionKey 	= urllib.unquote(sessionKeyOrig).decode('utf8')
alert = sys.argv[4]

# Setup logger
log = logging.getLogger('alert_manager')
lf = os.path.join(os.environ.get('SPLUNK_HOME'), "var", "log", "splunk", "alert_manager.log")
fh 	= logging.handlers.RotatingFileHandler(lf, maxBytes=25000000, backupCount=5)
formatter = logging.Formatter("%(asctime)-15s %(levelname)-5s %(message)s")
fh.setFormatter(formatter)
log.addHandler(fh)
log.setLevel(logging.DEBUG)

# Need to set the sessionKey (input.submit() doesn't allow passing the sessionKey)
log.debug("sessionKey=%s" % sessionKey)
splunk.setDefault('sessionKey', sessionKey)

#
# Get global settings
#
config = {}
config['index']						= 'alerts'
config['default_owner']		 		= 'unassigned'
config['default_priority']	 		= 'unknown'
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

#
# Get per alert settings
#
alert_config = {}
alert_config['run_alert_script']		= False
alert_config['alert_script']			= ''
alert_config['auto_assign']				= False
alert_config['auto_assign_user']		= ''
alert_config['auto_ttl_resolve']		= False
alert_config['auto_previous_resolve']	= False
alert_config['priority']				= config['default_priority']
query = {}
query['alert'] = alert
log.debug("Query for alert settings: %s" % urllib.quote(json.dumps(query)))
uri = '/servicesNS/nobody/alert_manager/storage/collections/data/alert_settings?query=%s' % urllib.quote(json.dumps(query))
serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)
log.debug("Alert settings: %s" % serverContent)
alert_settings = json.loads(serverContent)
if len(alert_settings) > 0:
	log.info("Found settings for %s" % alert)
	for key, val in alert_settings[0].iteritems():
		alert_config[key] = val

log.debug("Alert config after getting settings: %s" % json.dumps(alert_config))

#
# Alert metadata
#
# Get alert metadata
uri = '/services/search/jobs/%s' % job_id
serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, getargs={'output_mode': 'json'})

# Get savedsearch settings
uri = '/servicesNS/nobody/search/admin/savedsearch/%s' % alert
savedsearchResponse, savedsearchContent = rest.simpleRequest(uri, sessionKey=sessionKey, getargs={'output_mode': 'json'})
savedsearchContent = json.loads(savedsearchContent)
log.debug("severity_id: %s" % savedsearchContent['entry'][0]['content']['alert.severity'])
log.debug("expiry: %s" % savedsearchContent['entry'][0]['content']['alert.expires'])
#log.debug("savedsearchContent: %s" % json.dumps(savedsearchContent))

# Transform expiry to seconds
timeModifiers = { 's': 1, 'm': 60, 'h': 3600, 'd' : 86400, 'w': 604800 }
timeModifier = savedsearchContent['entry'][0]['content']['alert.expires'][-1]
timeRange    = int(savedsearchContent['entry'][0]['content']['alert.expires'][:-1])
ttl 		 = timeRange * timeModifiers[timeModifier]
log.debug("Transformed %s into %s seconds" % (savedsearchContent['entry'][0]['content']['alert.expires'], ttl))

# Add attributes id to alert metadata
job = json.loads(serverContent)
job['job_id'] = job_id
job['severity_id'] = savedsearchContent['entry'][0]['content']['alert.severity']
job['ttl'] = ttl
alert_time = job['entry'][0]['published']

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

#
# Alert scenarios
#
# Run alert script (runshellscript.py)
if alert_config['run_alert_script']:
	log.info("Will run alert script '%s' now." % alert_config['alert_script'])

	runshellscript = os.path.join(os.environ.get('SPLUNK_HOME'), 'etc', 'apps', 'search', 'bin', 'runshellscript.py')
	splunk_bin = os.path.join(os.environ.get('SPLUNK_HOME'), 'bin', 'splunk')

	#0	SPLUNK_ARG_0	Script name
	#1	SPLUNK_ARG_1	Number of events returned
	#2	SPLUNK_ARG_2	Search terms
	#3	SPLUNK_ARG_3	Fully qualified query string
	#4	SPLUNK_ARG_4	Name of report
	#5	SPLUNK_ARG_5	Trigger reason. For example, "The number of events was greater than 1."
	#6	SPLUNK_ARG_6	Browser URL to view the report.
	#7	SPLUNK_ARG_7	Not used for historical reasons.
	#8	SPLUNK_ARG_8	File in which the results for the search are stored. Contains raw results.
	args = [splunk_bin, 'cmd', 'python', runshellscript, alert_config['alert_script'], sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7], sys.argv[8] ]

	args_stdout = "sessionKey:%s" % sessionKeyOrig
	log.debug("args for %s: %s" % (alert_config['alert_script'], args))
	
	try:
		p = Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=False)
		p.communicate(input=args_stdout)
		log.debug("Alert script run finished.")
	except OSError, e:
		log.debug("Alert script failed. Error: %s" % str(e))

# Auto Previous resolve
if alert_config['auto_previous_resolve']:
	query = {}
	query['alert'] = alert
	query['status'] = "new"
	log.debug("Filter: %s" % json.dumps(query))
	uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents?query=%s' % urllib.quote(json.dumps(query))
	serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)
	incidents = json.loads(serverContent)
	if len(incidents):
		log.info("Got %s incidents to auto-resolve" % len(incidents))
		for incident in incidents:
			log.info("Auto-resolving incident with key=%s" % incident['_key'])
			incident['status'] = 'auto_previous_resolved'
			uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents/%s' % incident['_key']
			incident = json.dumps(incident)
			serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=incident)
			# TODO: Save event to index

# Auto assign
if alert_config['auto_assign'] and alert_config['auto_assign_owner'] != 'unassigned':
	entry['owner'] = alert_config['auto_assign_owner']
	log.info("Assigning incident to %s" % alert_config['auto_assign_owner'])
	# TODO: Notification
else:
	entry['owner'] = config['default_owner']	
	log.info("Assigning incident to default owner %s" % config['default_owner'])

log.debug("Alert time: %s" % util.dt2epoch(util.parseISO(alert_time, True)))

# Write to incident to collection
uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents'
entry['alert_time'] = int(float(util.dt2epoch(util.parseISO(alert_time, True))))
entry['job_id'] = job_id
entry['alert'] = alert
entry['status'] = 'new'
entry['ttl'] = ttl
entry['priority'] = alert_config['priority']
entry['severity_id'] = savedsearchContent['entry'][0]['content']['alert.severity']
entry = json.dumps(entry)

serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=entry)
log.info("Incident initial state added to collection")

#
# Finish
#
end = time.time()
duration = round((end-start), 3)
log.info("Alert handler finished. duration=%ss" % duration)
