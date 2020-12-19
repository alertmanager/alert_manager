#!/usr/bin/env python
# coding=utf-8

import os,sys
import time
import splunklib.client as client
import splunklib.results as results
import json
import collections

splunkhome = os.environ['SPLUNK_HOME']
sys.path.append(os.path.join(splunkhome, 'etc', 'apps', 'alert_manager', 'bin', 'splunklib'))
from splunklib.searchcommands import dispatch, GeneratingCommand, Configuration, Option, validators

@Configuration(type='reporting')
class loadincidentresults2(GeneratingCommand):

    incident_id = Option(require=True)

    def generate(self):
        self.logger.debug("Generating %s events" % self.incident_id)

        service = self.service

        # Check if configuration exists for collect_data_results
        try:
            collect_data_results = service.confs['alert_manager']['settings']['collect_data_results']
        except:
            raise RuntimeWarning('Specified setting ""collect_data_results" in "alert_manager.conf" does not exist.')

        # Check if configuration exists for index_data_results
        try:
            index_data_results = service.confs['alert_manager']['settings']['index_data_results']
        except:
            raise RuntimeWarning('Specified setting ""index_data_results" in "alert_manager.conf" does not exist.')

        # Fetch Results from KV Store by default if enabled
        if collect_data_results == '1':
            service.namespace['owner'] = "Nobody"

            collection_name = "incident_results"
            collection = service.kvstore[collection_name]

            query_dict = {}
            query_dict['incident_id'] = self.incident_id
            query = json.dumps(query_dict)

            data = collection.data.query(query=query)
                                        
            for fields in data[0].get("fields"):
                yield fields

        # If KV Store Data is not enabled, get indexed data
        elif index_data_results == '1' and collect_data_results == '0':
            # Get index location
            try:
                index = service.confs['alert_manager']['settings']['index']
            except:
                raise RuntimeWarning('Specified setting ""index_data_results" in "alert_manager.conf" does not exist.')

            # Get earliest time first for incident results
            service.namespace['owner'] = "Nobody"

            collection_name = "incidents"
            collection = service.kvstore[collection_name]

            query_dict = {}
            query_dict['incident_id'] = self.incident_id
            query = json.dumps(query_dict)

            data = collection.data.query(query=query)
            earliest_time = data[0].get("alert_time")

            # Fetch events
            events = []

            kwargs_oneshot = json.loads('{{"earliest_time": "{}", "latest_time": "{}"}}'.format(earliest_time, "now"))

            searchquery_oneshot = "search index={} sourcetype=alert_data_results incident_id={} |dedup incident_id".format(index, self.incident_id)
            oneshotsearch_results = service.jobs.oneshot(searchquery_oneshot, **kwargs_oneshot)
            reader = results.ResultsReader(oneshotsearch_results)

            for result in reader:  
                    for k, v in result.items():
                        if k=='_raw':
                            events.append(json.loads(v))

            for event in events:
                event_fields = event.get("fields")
                
                for fields in event_fields:
                    yield(fields)

        else:
            yield({'Error': 'Indexing/KV Store Collection of Results is not enabled. Please enable under Global Settings.'})

        self.finish()                
    
dispatch(loadincidentresults2, sys.argv, sys.stdin, sys.stdout, __name__)