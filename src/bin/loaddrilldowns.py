import csv
import sys
import splunk.Intersplunk as intersplunk
import splunk.rest as rest
import urllib
import json
import re
import collections
from string import Template as StringTemplate

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

# Get incident results
query = {}
query['incident_id'] = incident_id
uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_results?query={}'.format(urllib.quote(json.dumps(query)))
serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)

incident_results = json.loads(serverContent)

# Create dict for results
incident_data = {}

if incident_results:
    fields = incident_results[0].get("fields")
    results = {}
    for key in fields[0]:
        value = fields[0]['comments'][0].encode('utf-8')
        key = key.encode('utf-8')
        results[key] = value

    # Append results to incident data
    incident_data.update(results)

# Get Incident
query = {}
query['incident_id'] = incident_id
uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents?query={}'.format(urllib.quote(json.dumps(query)))
serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)

incidents = json.loads(serverContent)

alert = incidents[0].get('alert')

# Get Incident Settings
query = {}
query['alert'] = alert
uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_settings?query={}'.format(urllib.quote(json.dumps(query)))
serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)

incident_settings = json.loads(serverContent)

drilldown_references = incident_settings[0].get('drilldowns')

if len(drilldown_references)>0:

    drilldown_references = drilldown_references.split()

    #sys.stderr.write("drilldown_references: {}".format(drilldown_references))

    query_prefix='{ "$or": [ ' 

    for drilldown_reference in drilldown_references:
        query_prefix += '{ "name": "' + drilldown_reference + '" } '

    query_prefix = query_prefix + '] }'

    query = json.loads(query_prefix.replace("} {", "}, {"))


    # Get Drilldown Actions for incident
    uri = '/servicesNS/nobody/alert_manager/storage/collections/data/drilldown_actions?query={}'.format(urllib.quote(json.dumps(query)))
    serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)

    drilldown_actions = json.loads(serverContent)

    drilldowns = []

    for drilldown_action in drilldown_actions:
        #sys.stderr.write("drilldown_action: {}".format(drilldown_action) )
        url = drilldown_action.get("url")
        label = drilldown_action.get("label")

        url = re.sub(r'(?<=\w)\$', '', url)

        class FieldTemplate(StringTemplate):
            idpattern = r'[a-zA-Z][_a-zA-Z0-9.]*'

        url_template = FieldTemplate(url)

        url = url_template.safe_substitute(incident_data)       
        drilldown = '{{ "label": "{}", "url": "{}" }}'.format(label, url)
        drilldown = drilldown.replace("\\", "\\\\")
        
        drilldown = json.loads(drilldown)
        drilldowns.append(drilldown)


intersplunk.outputResults(drilldowns)