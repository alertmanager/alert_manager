#!/usr/bin/env python
# coding=utf-8
import os,sys
import time
import splunklib.client as client
import splunklib.results as results
import json
import collections
import re
import urllib.parse
from string import Template as StringTemplate

splunkhome = os.environ['SPLUNK_HOME']
sys.path.append(os.path.join(splunkhome, 'etc', 'apps', 'alert_manager', 'bin', 'splunklib'))
from splunklib.searchcommands import dispatch, GeneratingCommand, Configuration, Option, validators

@Configuration(type='reporting')
class loaddrilldowns(GeneratingCommand):

    incident_id = Option(require=True)

    def generate(self):
        self.logger.debug("Generating %s events" % self.incident_id)

        service = client.Service(token=self.metadata.searchinfo.session_key)

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

            incident_data = {}
                    
            incident_data = data[0].get("fields")[0]

            for k,v in incident_data.items():
                incident_data[k] = urllib.parse.quote(v)

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
            incident_data = {}
        
            kwargs_oneshot = json.loads('{{"earliest_time": "{}", "latest_time": "{}"}}'.format(earliest_time, "now"))

            searchquery_oneshot = "search index={} sourcetype=alert_data_results incident_id={} |dedup incident_id".format(index, self.incident_id)
            oneshotsearch_results = service.jobs.oneshot(searchquery_oneshot, **kwargs_oneshot)
            reader = results.ResultsReader(oneshotsearch_results)

            for result in reader:  
                    for k, v in result.items():
                        if k=='_raw':
                            events.append(json.loads(v))

            for event in events:
                incident_data = event.get("fields")[0]
                
            for k,v in incident_data.items():
                incident_data[k] = urllib.parse.quote(v)
        
        # Get Incident
        query_dict = {}
        query_dict['incident_id'] = self.incident_id

        collection_name = "incidents"
        collection = service.kvstore[collection_name]
        query = json.dumps(query_dict)

        data = collection.data.query(query=query)

        alert = data[0].get('alert')

        # Get Incident Settings
        query_dict = {}
        query_dict['alert'] = alert

        collection_name = "incident_settings"
        collection = service.kvstore[collection_name]
        query = json.dumps(query_dict)
        
        data = collection.data.query(query=query)

        drilldown_references = data[0].get('drilldowns')

        # Get Drilldown Settings
        if len(drilldown_references)>0:
            query_dict =  {}

            drilldown_references = drilldown_references.split()

            query_prefix='{ "$or": [ ' 

            for drilldown_reference in drilldown_references:
                query_prefix += '{ "name": "' + drilldown_reference + '" } '

            query_prefix = query_prefix + '] }'

            collection_name = "drilldown_actions"
            collection = service.kvstore[collection_name]
            query = query_prefix.replace("} {", "}, {")
            
            data = collection.data.query(query=query)

            drilldowns = []

            # Substitute variables with field values
            for drilldown_action in data:
               
                url = drilldown_action.get("url")
                label = drilldown_action.get("label")

                url = re.sub(r'(?<=\w)\$', '', url)

                class FieldTemplate(StringTemplate):
                    idpattern = r'[a-zA-Z][_a-zA-Z0-9.]*'

                url_template = FieldTemplate(url)

                url = url_template.safe_substitute(incident_data)
                
                drilldown = r'''{{ "label": "{}", "url": "{}" }}'''.format(label, url)
               
                yield(json.loads(drilldown))


dispatch(loaddrilldowns, sys.argv, sys.stdin, sys.stdout, __name__)    