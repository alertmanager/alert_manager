import sys
import os
import splunk
import splunk.auth as auth
import splunk.entity as entity
import splunk.Intersplunk as intersplunk
import splunk.rest as rest
import splunk.search as search
import splunk.input as input
#from xml.dom import minidom
#import urllib2
import urllib
import json
import socket
#import logging as logger

sys.stdout = open('/tmp/stdout', 'w')
sys.stderr = open('/tmp/stderr', 'w')

# Parse arguments
job_id		= os.path.split(sys.argv[8])[0].split('/')
job_id_seg	= len(job_id)-1
job_id		= job_id[job_id_seg]
sessionKey 	= sys.stdin.readline().strip()
sessionKey 	= urllib.unquote(sessionKey[11:]).decode('utf8')
search_name = sys.argv[4]

#logger.basicConfig(format='%(asctime)s %(levelname)s %(message)s', filename=outputFileLog, filemode='a+', level=logger.INFO, datefmt='%Y-%m-%d %H:%M:%S %z')
#logger.Formatter.converter = time.gmtime

# Need to set the sessionKey (input.submit() doesn't allow passing the sessionKey)
splunk.setDefault('sessionKey', sessionKey)

# Get settings
config = {}
config['index']				= 'alerts'
config['default_assignee'] 	= 'unassigned'
config['save_results']		= '1'

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

print("settings: %s" % config)

# Get alert metadata
uri = '/services/search/jobs/%s' % job_id
serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, getargs={'output_mode': 'json'})

# Get alert severity
uri = '/servicesNS/nobody/search/admin/savedsearch/%s' % search_name
savedsearchResponse, savedsearchContent = rest.simpleRequest(uri, sessionKey=sessionKey, getargs={'output_mode': 'json'})
savedsearchContent = json.loads(savedsearchContent)
print("severity: %s" % savedsearchContent['entry'][0]['content']['alert.severity'])

# Add attributes id to alert metadata
job = json.loads(serverContent)
job['job_id'] = job_id
job['severity'] = savedsearchContent['entry'][0]['content']['alert.severity']
alert_time = job['updated']

# Write alert metadata to index
input.submit(json.dumps(job), hostname = socket.gethostname(), sourcetype = 'alert_metadata', source = 'alert_handler.py', index = config['index'])
print("alert saved")

if config['save_results'] == True:
	# Get alert results
	job = search.getJob(job_id, sessionKey=sessionKey, message_level='warn')
	feed = job.getFeed(mode='results', outputMode='json')
	feed = json.loads(feed)
	feed['job_id'] = job_id
	feed['updated'] = alert_time

	# Write results to index
	input.submit(json.dumps(feed), hostname = socket.gethostname(), sourcetype = 'alert_results', source = 'alert_handler.py', index = config['index'])
	print("results saved")

#Write to alert state collection
uri = '/servicesNS/nobody/alert_manager/storage/collections/data/alert_state'
entry = {}
entry['job_id'] = job_id
entry['search_name'] = search_name
entry['current_assignee'] = config['default_assignee']
entry['current_state'] = 'new'
entry['severity'] = savedsearchContent['entry'][0]['content']['alert.severity']
entry = json.dumps(entry)

serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=entry)
print("state saved")


