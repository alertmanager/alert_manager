import sys, time
from splunklib.searchcommands import \
    dispatch, StreamingCommand, Configuration, Option, validators
import json
import urllib
import datetime
import time
import splunk.rest as rest
import splunk.input as input    
import hashlib
import socket
import splunk
import splunk.entity as entity

@Configuration()
class ModifyIncidentsCommand(StreamingCommand):
    """ %(synopsis)
    ##Syntax
    %(syntax)
    ##Description
    %(description)
    """

    config  = {}
    status  = Option(require=False)
    owner   = Option(require=False)
    urgency = Option(require=False)
    comment = Option(require=False)

    def stream(self, records):
        #self.logger.debug('ModifyIncidentsCommand: %s', self)  # logs command line
        user = self._input_header.get('owner')
        sessionKey = self._input_header.get('sessionKey')
        splunk.setDefault('sessionKey', sessionKey)

        #
        # Get global settings
        #
        sessionKey = self._input_header.get('sessionKey')
        self.config['index'] = 'alerts'

        restconfig = entity.getEntities('configs/alert_manager', count=-1, sessionKey=sessionKey)
        if len(restconfig) > 0:
            if 'index' in restconfig['settings']:
                self.config['index'] = restconfig['settings']['index']

        self.logger.debug("Global settings: %s" % self.config)

        self.logger.debug("Started")
        for record in records:
            
            if 'incident_id' in record:
                
                attrs = {}
                if self.status:
                    attrs.update({"status": self.status})
                if self.owner:
                    attrs.update({"owner": self.owner})
                if self.urgency:
                    attrs.update({"urgency": self.urgency})

                self.logger.debug("Attrs: %s" % attrs)
                if len(attrs) > 0 or self.comment:
                    # Get incident
                    query = {}
                    query['incident_id'] = record['incident_id']

                    uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents?query=%s' % urllib.quote(json.dumps(query))
                    serverResponse, incident = rest.simpleRequest(uri, sessionKey=sessionKey)
                    incident = json.loads(incident)
                    self.logger.debug("Read incident from collection: %s" % json.dumps(incident[0]))

                    now = time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())

                    changed_keys = []

                    for key in incident[0].keys():
                        if (key in attrs) and (incident[0][key] != attrs[key]):
                            changed_keys.append(key)

                            event_id = hashlib.md5(incident[0]['incident_id'] + now).hexdigest()
                            event = 'time="%s" severity=INFO origin="ModifyIncidentsCommand" event_id="%s" user="%s" action="change" incident_id="%s" %s="%s" previous_%s="%s"' % (now, event_id, user, incident[0]['incident_id'], key, attrs[key], key, incident[0][key])
                            
                            input.submit(event, hostname = socket.gethostname(), sourcetype = 'incident_change', source = 'modifyincidents.py', index = self.config['index'])

                            incident[0][key] = attrs[key]

                    if len(changed_keys) > 0:
                        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents/' + incident[0]['_key']
                        del incident[0]['_key']
                        contentsStr = json.dumps(incident[0])
                        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=contentsStr)

                    if self.comment:
                        self.comment = self.comment.replace('\n', '<br />').replace('\r', '')
                        event_id = hashlib.md5(incident[0]['incident_id'] + now).hexdigest()
                        event = 'time="%s" severity=INFO origin="ModifyIncidentsCommand" event_id="%s" user="%s" action="comment" incident_id="%s" comment="%s"' % (now, event_id, user, incident[0]['incident_id'], self.comment)
                        event = event.encode('utf8')
                        input.submit(event, hostname = socket.gethostname(), sourcetype = 'incident_change', source = 'modifyincidents.py', index = self.config['index'])

                else:                        
                    self.logger.warn("No attributes to modify found, aborting.")

            else:
                self.logger.warn("No incident_id field found in event, aborting.")  

            yield record
       

dispatch(ModifyIncidentsCommand, sys.argv, sys.stdin, sys.stdout, __name__)