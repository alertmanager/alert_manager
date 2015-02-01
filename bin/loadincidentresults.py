import csv
import sys
import splunk.Intersplunk as intersplunk
import splunk.rest as rest
import urllib
import json
import re
import collections

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

field_list = None
results = []
for result in data:
    if "field_list" in result:
        field_list = result["field_list"]

    for line in result["fields"]:
        if type(field_list) is list:
            ordered_line = collections.OrderedDict()
            for field in field_list:
                ordered_line[field] = line[field]
            results.append(ordered_line)
        else:
            results.append(line)

intersplunk.outputResults(results)
