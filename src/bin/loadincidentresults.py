import csv
import sys
import splunk.Intersplunk as intersplunk
import splunk.rest as rest
import splunk.entity
import urllib
import urllib.parse
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
stdinArgs = urllib.parse.unquote(stdinArgs)
match = re.search(r'<authToken>([^<]+)</authToken>', stdinArgs)
sessionKey = match.group(1)

incident_id = sys.argv[1]

settings = splunk.entity.getEntity('/admin/conf-alert_manager','settings', namespace='alert_manager', sessionKey=sessionKey, owner='nobody')

collect_data_results = settings.get("collect_data_results")

query = {}
query['incident_id'] = incident_id
uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_results?query={}'.format(urllib.parse.quote(json.dumps(query)))
serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)

data = json.loads(serverContent.decode('utf-8'))
#sys.stderr.write("data: {}".format(data))

field_list = None
results = []

if collect_data_results == False:
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

else:
    results.append({"Error": "KV Store Collection of Results not enabled. Please enable under Global Settings."})             

intersplunk.outputResults(results)
