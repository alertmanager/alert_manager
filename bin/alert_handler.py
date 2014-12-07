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


# Get alert metadata
uri = '/services/search/jobs/%s' % job_id
serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, getargs={'output_mode': 'json'})

# Add job id to alert metadata
job = json.loads(serverContent)
job['job_id'] = job_id
alert_time = job['updated']

# Write alert metadata to index
input.submit(json.dumps(job), hostname = 'localhost', sourcetype = 'alert_metadata', source = 'alert_handler.py', index = 'alerts')
print("alert saved")

# Get alert results
job = search.getJob(job_id, sessionKey=sessionKey, message_level='warn')
feed = job.getFeed(mode='results', outputMode='json')
feed = json.loads(feed)
feed['job_id'] = job_id
feed['updated'] = alert_time

# Write results to index
input.submit(json.dumps(feed), hostname = 'localhost', sourcetype = 'alert_results', source = 'alert_handler.py', index = 'alerts')
print("results saved")

#Write to alert state collection
uri = '/servicesNS/nobody/alert_manager/storage/collections/data/alert_state'
entry = {}
entry['job_id'] = job_id
entry['search_name'] = search_name
entry['current_assignee'] = 'unassigned'
entry['current_state'] = 'new'
entry['severity'] = 5
entry = json.dumps(entry)

serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=entry)
print("state saved")


