import csv
import sys
import splunk.Intersplunk as intersplunk
import splunk.rest as rest
import urllib
import json
import re

#(isgetinfo, sys.argv) = intersplunk.isGetInfo(sys.argv)

if len(sys.argv) < 2:
    intersplunk.parseError("Please specify a valid incident_id")

#if isgetinfo:
#    intersplunk.outputInfo(False, False, True, False, None, True)
#    # outputInfo automatically calls sys.exit()    

stdinArgs = sys.stdin.readline()
stdinArgs = stdinArgs.strip()
stdinArgs = stdinArgs[11:]
stdinArgs = urllib.unquote(stdinArgs).decode('utf8')
match = re.search(r'<authToken>([^<]+)</authToken>', stdinArgs)
sessionKey = match.group(1)

incident_id = sys.argv[1]

query = {}
query['incident_id'] = incident_id
uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_results?query=%s' % urllib.quote(json.dumps(query))
serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)

data = json.loads(serverContent)
#sys.stderr.write("data: %s" % data)

results = []
for result in data:
	if type(result["fields"]) is dict:
		results.append(result["fields"])
	else:
		for field in result["fields"]:
			results.append(field)

intersplunk.outputResults(results)