import csv
import sys
import splunk.Intersplunk as intersplunk
import splunk.rest as rest
import splunk.entity
import splunklib.results as results
import splunklib.client as client
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
index_data_results = settings.get("index_data_results")
index = settings.get("index")

incident_results = []

# Fetch KV Store Data 
if collect_data_results == '1':

    field_list = None

    query = {}
    query['incident_id'] = incident_id
    uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_results?query={}'.format(urllib.parse.quote(json.dumps(query)))
    serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)

    data = json.loads(serverContent.decode('utf-8'))
    #sys.stderr.write("data: {}".format(data))
    
    
    for result in data:
        if "field_list" in result:
            field_list = result["field_list"]

        for line in result["fields"]:
            if type(field_list) is list:
                ordered_line = collections.OrderedDict()
                for field in field_list:
                    ordered_line[field] = line[field]
                incident_results.append(ordered_line)
            else:
                incident_results.append(line)

# If KV Store Data is not enabled, get indexed data
elif index_data_results == '1' and collect_data_results == '0':
    events = []
    try:
        service = client.connect(host='localhost', port=8089, user="admin", token=sessionKey)

    except Exception as e:
        sys.stderr.write("e: {}".format(e))

    query = {}
    query['incident_id'] = incident_id
    uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents?query={}'.format(urllib.parse.quote(json.dumps(query)))
    serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)

    data = json.loads(serverContent.decode('utf-8'))
    earliest_time = data[0].get("alert_time")

    kwargs_oneshot = json.loads('{{"earliest_time": "{}", "latest_time": "{}"}}'.format(earliest_time, "now"))

    searchquery_oneshot = "search index={} sourcetype=alert_data_results incident_id={} |dedup incident_id".format(index, incident_id)
    oneshotsearch_results = service.jobs.oneshot(searchquery_oneshot, **kwargs_oneshot)
    reader = results.ResultsReader(oneshotsearch_results)

    for result in reader:  
            for k, v in result.items():
                if k=='_raw':
                    events.append(json.loads(v))

    for event in events:
        event_fields = event.get("fields")
        
        for fields in event_fields:
            incident_results.append(fields)

# If nothing is enabled, return an error
else:
    incident_results.append({"Error": "Indexing/KV Store Collection of Results is not enabled. Please enable under Global Settings."})             

intersplunk.outputResults(incident_results)
