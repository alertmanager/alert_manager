import csv
import splunk.rest as rest
import json
import collections
import os, re, sys, urllib
import splunk.Intersplunk, splunk.mining.dcutils as dcu

logger    = dcu.getLogger()

results,dummyresults,settings = splunk.Intersplunk.getOrganizedResults()

#(isgetinfo, sys.argv) = intersplunk.isGetInfo(sys.argv)

if len(sys.argv) < 2:
    splunk.Intersplunk.generateErrorResults("Please specify a valid incident_id field")

#if isgetinfo:
#    intersplunk.outputInfo(False, False, True, False, None, True)
#    # outputInfo automatically calls sys.exit()    

sessionKey = settings.get("sessionKey", None)

incident_id_field = sys.argv[1]

for row in results:
	if incident_id_field in row:

		query = { 'incident_id': row[incident_id_field] }

		uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_results?query=%s' % urllib.quote(json.dumps(query))
		serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)

		if serverResponse['status'] == "200":
			data = json.loads(serverContent)
			inc_results = data[0]
			for field in inc_results["field_list"]:
				# TODO: Support for multi-value fields
				if field in inc_results["fields"][0]:
					row[field] = inc_results["fields"][0][field]

splunk.Intersplunk.outputResults( results )