import os
import sys
import urllib.parse
import json
import re
import datetime
import time
import hashlib
import socket
import http.client
import operator
import uuid
from string import Template as StringTemplate

import splunk
import splunk.appserver.mrsparkle.lib.util as util
import splunk.rest as rest
import splunk.entity as entity
import splunk.input as input

dir = os.path.join(util.get_apps_dir(), 'alert_manager', 'bin', 'lib')
if not dir in sys.path:
    sys.path.append(dir)

from AlertManagerUsers import AlertManagerUsers
from CsvLookup import CsvLookup
from EventHandler import EventHandler
from IncidentContext import IncidentContext

from AlertManagerLogger import setupLogger

logger = setupLogger('rest_handler')

if sys.platform == "win32":
    import msvcrt # pylint: disable=import-error
    # Binary mode is required for persistent mode on Windows.
    msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY) # pylint: disable=maybe-no-member
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY) # pylint: disable=maybe-no-member
    msvcrt.setmode(sys.stderr.fileno(), os.O_BINARY) # pylint: disable=maybe-no-member

from splunk.persistconn.application import PersistentServerConnectionApplication

class HelpersHandler(PersistentServerConnectionApplication):
    def __init__(self, command_line, command_arg):
        PersistentServerConnectionApplication.__init__(self)

    def handle(self, args):
        logger.debug("START handle()")
        logger.debug('ARGS: {}'.format(args))

        args = json.loads(args)

        try:
            logger.info('Handling {} request.'.format(args['method']))
            method = 'handle_' + args['method'].lower()
            if callable(getattr(self, method, None)):
                return operator.methodcaller(method, args)(self)
            else:
                return self.response('Invalid method for this endpoint', http.client.METHOD_NOT_ALLOWED)
        except ValueError as e:
            msg = 'ValueError: {}'.format(e.message)
            return self.response(msg, http.client.BAD_REQUEST)
        except splunk.RESTException as e:
            return self.response('RESTexception: {}'.format(e), http.client.INTERNAL_SERVER_ERROR)
        except Exception as e:
            msg = 'Unknown exception: {}'.format(e)
            logger.exception(msg)
            return self.response(msg, http.client.INTERNAL_SERVER_ERROR)

    def handle_get(self, args):
        logger.debug('GET ARGS {}'.format(json.dumps(args)))

        query_params = dict(args.get('query', []))

        try:
            sessionKey = args["session"]["authtoken"]
            user = args["session"]["user"]
        except KeyError:
            return self.response("Failed to obtain auth token", http.client.UNAUTHORIZED)


        required = ['action']
        missing = [r for r in required if r not in query_params]
        if missing:
            return self.response("Missing required arguments: {}".format(missing), http.client.BAD_REQUEST)

        action = '_' + query_params.pop('action').lower()
        if callable(getattr(self, action, None)):
            return operator.methodcaller(action, sessionKey, query_params)(self)
        else:
            msg = 'Invalid action: action="{}"'.format(action)
            logger.exception(msg)
            return self.response(msg, http.client.BAD_REQUEST)

    def handle_post(self, args):
        logger.debug('POST ARGS {}'.format(json.dumps(args)))

        post_data = dict(args.get('form', []))

        try:
            sessionKey = args["session"]["authtoken"]
            user = args["session"]["user"]
        except KeyError:
            return self.response("Failed to obtain auth token", http.client.UNAUTHORIZED)


        required = ['action']
        missing = [r for r in required if r not in post_data]
        if missing:
            return self.response("Missing required arguments: {}".format(missing), http.client.BAD_REQUEST)

        action = '_' + post_data.pop('action').lower()
        if callable(getattr(self, action, None)):
            return operator.methodcaller(action, sessionKey, user, post_data)(self)
        else:
            msg = 'Invalid action: action="{}"'.format(action)
            logger.exception(msg)
            return self.response(msg, http.client.BAD_REQUEST)

    @staticmethod
    def response(msg, status):
        if status < 400:
            payload = msg
        else:
            # replicate controller's jsonresponse format
            payload = {
                "success": False,
                "messages": [{'type': 'ERROR', 'message': msg}],
                "responses": [],
            }
        return {'status': status, 'payload': payload}

    def _get_users(self, sessionKey, query_params):
        logger.debug("START _get_users()")

        users = AlertManagerUsers(sessionKey=sessionKey)
        user_list = users.getUserList()

        logger.debug("user_list: {} ".format(json.dumps(user_list)))

        return self.response(user_list, http.client.OK)

    def _get_savedsearch_description(self, sessionKey, query_params):
        logger.debug("START _get_savedsearch_description()")

        required = ['savedsearch_name', 'app']
        missing = [r for r in required if r not in query_params]
        if missing:
            return self.response("Missing required arguments: {}".format(missing), http.client.BAD_REQUEST)

        savedsearch_name = query_params.pop('savedsearch_name')
        app = query_params.pop('app')

        uri = '/servicesNS/nobody/{}/admin/savedsearch/{}?output_mode=json'.format(app, urllib.parse.quote(savedsearch_name))
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='GET')

        savedSearchContent = json.loads(serverContent.decode('utf-8'))

        if savedSearchContent["entry"][0]["content"]["description"]:
            return self.response(savedSearchContent["entry"][0]["content"]["description"], http.client.OK)
        else:
            msg = 'Get saved search description failed'
            logger.exception(msg)
            return self.response(msg, http.client.INTERNAL_SERVER_ERROR)

    def _get_notification_schemes(self, sessionKey, query_params):
        logger.debug("START _get_notification_schemes()")

        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/notification_schemes?q=output_mode=json'
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='GET')
        logger.debug("notification_schemes: {}".format(serverContent.decode('utf-8')))
        entries = json.loads(serverContent.decode('utf-8'))

        scheme_list = [ ]
        if len(entries) > 0:
            for entry in entries:
                scheme_list.append(entry['schemeName'])


        return self.response(scheme_list, http.client.OK)


    def _get_notification_scheme_events(self, sessionKey, query_params, post_data):
        logger.debug("START _get_notification_scheme_events")
        logger.debug("query_params: {}".format(query_params))

        required = ['incident_id']
        missing = [r for r in required if r not in query_params]

	    # Get alert first
        query = {}
        
        query['incident_id'] = post_data.get('incident_id')
        logger.debug("Filter: {}".format(json.dumps(query)))

        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents?query={}'.format(urllib.parse.quote(json.dumps(query)))
        serverResponse, incident = rest.simpleRequest(uri, sessionKey=sessionKey)
        
        logger.info("Settings for incident: {}".format(incident))
        
        incidents = json.loads(incident)
        alert = incidents[0].get("alert")

	    # Get scheme for alert
        query = {}
        query['alert'] = alert
        logger.debug("Query for incident settings: {}".format(urllib.parse.quote(json.dumps(query))))
        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_settings?query={}'.format(urllib.parse.quote(json.dumps(query)))

        serverResponse, incident = rest.simpleRequest(uri, sessionKey=sessionKey)
        
        logger.info("Settings for incident: {}".format(incident))
        
        incidents = json.loads(incident)
        notification_scheme = incidents[0].get("notification_scheme")

        # Get events
        query = {}
        query['schemeName'] = notification_scheme
        logger.debug("Query for notification schemes: {}".format(urllib.parse.quote(json.dumps(query))))

        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/notification_schemes?query={}'.format(urllib.parse.quote(json).dumps(query))
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='GET')
        logger.debug("notification schemes: {}".format(serverContent.decode('utf-8')))
        notification_scheme = json.loads(serverContent.decode('utf-8'))[0]
        events = notification_scheme.get("notifications")

        logger.debug("Events: {}".format(json.dumps(events)))

        return self.response(events, http.client.OK)


    def _get_search_string(self, sessionKey, query_params):
        logger.debug("START _get_search_string()")

        required = ['incident_id']
        missing = [r for r in required if r not in query_params]
        if missing:
            return self.response("Missing required arguments: {}".format(missing), http.client.BAD_REQUEST)

        incident_id = query_params.pop('incident_id')

        incident_id_query = '{"incident_id": "' + incident_id + '"}'
        incident_uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents?q=output_mode=json&query=' + urllib.parse.quote_plus(incident_id_query)

        # Get incident json
        serverResponse, serverContent = rest.simpleRequest(incident_uri, sessionKey=sessionKey, method='GET')
        logger.debug("incident: {}".format(serverContent.decode('utf-8')))
        incident = json.loads(serverContent.decode('utf-8'))

        if incident[0]["search"]:
            return self.response(incident[0]["search"], http.client.OK)
        else:
            msg = 'Get search string failed'
            logger.exception(msg)
            return self.response(msg, http.client.INTERNAL_SERVER_ERROR)

    def _write_log_entry(self, sessionKey, user, post_data):
        logger.debug("START _write_log_entry()")

        required = ['incident_id', 'log_action', 'origin']
        missing = [r for r in required if r not in post_data]
        if missing:
            return self.response("Missing required arguments: {}".format(missing), http.client.BAD_REQUEST)

        incident_id = post_data.pop('incident_id')
        log_action = post_data.pop('log_action')
        comment = post_data.get('comment', '')
        origin = post_data.get('origin', '')
        severity = post_data.get('severity', 'INFO')
        owner = post_data.get('owner', '')
        previous_owner = post_data.get('previous_owner', '')
        status = post_data.get('status', '')
        previous_status = post_data.get('previous_status', '')
        job_id = post_data.get('job_id', '')
        result_id = post_data.get('result_id', '')

        now = datetime.datetime.now().isoformat()

        # Get Index
        config = {}
        config['index'] = 'main'

        restconfig = entity.getEntities('configs/alert_manager', count=-1, sessionKey=sessionKey)
        if len(restconfig) > 0:
            if 'index' in restconfig['settings']:
                config['index'] = restconfig['settings']['index']


        comment = comment.replace('\n', '<br />').replace('\r', '')
        event_id = hashlib.md5(incident_id.encode('utf-8') + now.encode('utf-8')).hexdigest()

        event = ''
        if (log_action == "comment"):
            event = 'time={} severity="{}" origin="{}" event_id="{}" user="{}" action="comment" incident_id="{}" comment="{}"'.format(now, severity, origin, event_id, user, incident_id, comment)
        elif (log_action == "change"):
            event = 'time={} severity="{}" origin="{}" event_id="{}" user="{}" action="change" incident_id="{}" job_id="{}" result_id="{}" status="{}" previous_status="{}"'.format(now, severity, origin, event_id, user, incident_id, job_id, result_id, status, previous_status)

        logger.debug("Event will be: {}".format(event))
        event = event.encode('utf8')

        try:
            splunk.setDefault('sessionKey', sessionKey)
            input.submit(event, hostname = socket.gethostname(), sourcetype = 'incident_change', source = 'helper.py', index = config['index'])
            return self.response('Action logged', http.client.OK)

        except Exception as e:
            msg = 'Unhandled Exception: {}'.format(str(e))
            logger.exception(msg)
            return self.response(msg, http.client.INTERNAL_SERVER_ERROR)

    def _update_incident(self, sessionKey, user, post_data):
        logger.debug("START _update_incident()")

        required = ['incident_data']
        missing = [r for r in required if r not in post_data]
        if missing:
            return self.response("Missing required arguments: {}".format(missing), http.client.BAD_REQUEST)

        incident_data = post_data.pop('incident_data')

        splunk.setDefault('sessionKey', sessionKey)

        eh = EventHandler(sessionKey = sessionKey)

        config = {}
        config['index'] = 'main'

        restconfig = entity.getEntities('configs/alert_manager', count=-1, sessionKey=sessionKey)
        if len(restconfig) > 0:
            if 'index' in restconfig['settings']:
                config['index'] = restconfig['settings']['index']

        logger.debug("Global settings: {}".format(config))

        # Parse the JSON
        incident_data = json.loads(incident_data)

        # Select between updating multiple incidents (replace full document) and updating single incidents (attribute update)
        if 'incident_ids' in incident_data and len(incident_data['incident_ids']) > 1:
            logger.info("do_update_incidents")
            self._do_update_incidents(sessionKey, config, eh, incident_data, user)
        elif 'incident_ids' in incident_data and len(incident_data['incident_ids']) == 1:
            logger.info("do_update_incident")
            self._do_update_incident(sessionKey, config, eh, incident_data['incident_ids'][0], incident_data, user)
        else:
            logger.info("do_update_incident")
            self._do_update_incident(sessionKey, config, eh, incident_data['incident_id'], incident_data, user)

        return self.response('Successfully updated incident(s).', http.client.OK)

    def _do_update_incident(self, sessionKey, config, eh, incident_id, incident_data, user):
        # Get key
        query = {}
        query['incident_id'] = incident_id
        logger.debug("Filter: {}".format(json.dumps(query)))

        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents?query={}'.format(urllib.parse.quote(json.dumps(query)))
        serverResponse, incident = rest.simpleRequest(uri, sessionKey=sessionKey)
        logger.debug("Settings for incident: {}".format(incident.decode('utf-8')))
        incident = json.loads(incident)

        # Update incident
        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents/' + incident[0]['_key']
        logger.debug("URI for incident update: {}".format(uri))

        # Prepared new entry
        now = datetime.datetime.now().isoformat()
        changed_keys = []

        # Add synthetic group_id if attribute is still null in incident[0] dict
        if 'group_id' not in incident[0] and 'group_id' in incident_data:
            incident[0]['group_id'] = ''

        for key in list(incident[0].keys()):
            if (key in incident_data) and (incident[0][key] != incident_data[key]):
                changed_keys.append(key)
                logger.info("{} for incident {} changed. Writing change event to index {}.".format(key, incident[0]['incident_id'], config['index']))
                event_id = hashlib.md5(incident[0]['incident_id'].encode('utf-8') + now.encode('utf-8')).hexdigest()
                event = 'time={} severity=INFO origin="incident_posture" event_id="{}" user="{}" action="change" incident_id="{}" {}="{}" previous_{}="{}"'.format(now, event_id, user, incident[0]['incident_id'], key, incident_data[key], key, incident[0][key])
                logger.debug("Change event will be: {}".format(event))
                input.submit(event, hostname = socket.gethostname(), sourcetype = 'incident_change', source = 'incident_settings.py', index = config['index'])
                incident[0][key] = incident_data[key]

                # Set flag to prevent manual owner/urgency override to be overwritten by subsequent alerts
                if key == "owner":
                    incident[0]['preserve_owner'] = True
                    logger.info('preserve_owner')
                elif key == "urgency":
                    incident[0]['preserve_urgency'] = True
                    logger.info('preserve_urgency')
            else:
                logger.info("{} for incident {} didn't change.".format(key, incident[0]['incident_id']))

        del incident[0]['_key']
        contentsStr = json.dumps(incident[0])
        logger.debug("content for update: {}".format(contentsStr))
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=contentsStr)

        logger.debug("Response from update incident entry was {} ".format(serverResponse))
        logger.debug("Changed keys: {}".format(changed_keys))

        if len(changed_keys) > 0:
            ic = IncidentContext(sessionKey, incident_id)
            if "owner" in changed_keys:
                eh.handleEvent(alert=incident[0]["alert"], event="incident_assigned", incident=incident[0], context=ic.getContext())
            elif "status" in changed_keys and incident_data["status"] == "resolved":
                eh.handleEvent(alert=incident[0]["alert"], event="incident_resolved", incident=incident[0], context=ic.getContext())
            else:
                eh.handleEvent(alert=incident[0]["alert"], event="incident_changed", incident=incident[0], context=ic.getContext())

        if incident_data['comment'] != "":
            incident_data['comment'] = incident_data['comment'].replace('\n', '<br />').replace('\r', '')
            event_id = hashlib.md5(incident[0]['incident_id'].encode('utf-8') + now.encode('utf-8')).hexdigest()
            event = 'time={} severity=INFO origin="incident_posture" event_id="{}" user="{}" action="comment" incident_id="{}" comment="{}"'.format(now, event_id, user, incident[0]['incident_id'], incident_data['comment'])
            logger.debug("Comment event will be: {}".format(event))
            event = event.encode('utf8')
            input.submit(event, hostname = socket.gethostname(), sourcetype = 'incident_change', source = 'incident_settings.py', index = config['index'])
            ic = IncidentContext(sessionKey, incident_id)
            eh.handleEvent(alert=incident[0]["alert"], event="incident_commented", incident=incident[0], context=ic.getContext())

    def _do_update_incidents(self, sessionKey, config, eh, incident_data, user):
         # Get key
        query = {}
        logger.debug("Filter: {}".format(json.dumps(query)))

        logger.info("_do_update_incidents")
        logger.debug("incident_data: {}".format(incident_data))

        incident_ids = incident_data.pop('incident_ids')

        # Prepared new entry
        now = datetime.datetime.now().isoformat()

        # Setting a filter batch size of max. 100 incidents
        filter_batchsize = 100
        incidents = []

        for i in range(0, len(incident_ids), filter_batchsize):
            filter_batch = incident_ids[i:i+filter_batchsize]
            filter=''
            
            for incident_id in filter_batch:
                filter += ' {{"incident_id": "{}"}},'.format(incident_id)

            # Remove last commma for valid json
            filter = filter[:-1]
            logger.debug("filter: {}".format(filter))

            query = '{"$or": [' + filter + ']}'

            logger.info("Incident filter query starting:")
            uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents?query={}'.format(urllib.parse.quote(query))
            serverResponse, incident_batch = rest.simpleRequest(uri, sessionKey=sessionKey)
            
            if serverResponse['status'] == "200":
                logger.info("Incident filter query finished successfully:")
            else:
                logger.info("Incident filter query failed: {}".format(serverResponse)    )

            incidents += (json.loads(incident_batch))
            
        logger.info("Number of all incidents: {}".format(len(incidents)))

        events=''

        # List of notification
        notification = {}
        notifications = []

        # Loop through all incidents and replace changed keys
        for attribute_key, attribute_value in incident_data.items():

            logger.debug("Update attribute key: {}".format(attribute_key))

            if attribute_key != "comment":
                for incident in incidents:
                    
                    event_id = hashlib.md5(incident['incident_id'].encode('utf-8') + now.encode('utf-8')).hexdigest()
                    event=''
                    
                    if (attribute_value != incident.get(attribute_key)):
                            event = 'time={} severity=INFO origin="incident_posture" event_id="{}" user="{}" action="change" incident_id="{}" {}="{}" previous_{}="{}"'.format(now, event_id, user, incident['incident_id'], attribute_key, attribute_value, attribute_key, incident.get(attribute_key))

                            # Event handling cases for owner and status changes
                            if attribute_key == "owner":
                                notification['incident'] = incident['incident_id']
                                notification['alert'] = incident["alert"]
                                notification['event'] = "incident_assigned"
                                notifications.append(notification.copy())
                                
                            elif attribute_key == "status" and attribute_value == "resolved":
                                notification['incident'] = incident['incident_id']
                                notification['alert'] = incident["alert"]
                                notification['event'] = "incident_resolved"
                                notifications.append(notification.copy())

                            else:
                                notification['incident'] = incident['incident_id']
                                notification['alert'] = incident["alert"]
                                notification['event'] = "incident_changed"
                                notifications.append(notification.copy())
                                
                            # Replace old value
                            incident[attribute_key] = attribute_value

                            # Send log event to index
                            if (event!=''):
                                events  += event + "\n"

                        # Reset event
                    else:
                        event=''

                notification = {}       

            # Logging and event handling cases for comments
            elif attribute_key == "comment" and attribute_value != "":
                for incident in incidents:
                    event_id = hashlib.md5(incident['incident_id'].encode('utf-8') + now.encode('utf-8')).hexdigest()
                    event = ''          
                    event = 'time={} severity=INFO origin="incident_posture" event_id="{}" user="{}" action="comment" incident_id="{}" comment="{}"'.format(now, event_id, user, incident['incident_id'], attribute_value)
                    notification['incident'] = incident['incident_id']
                    notification['alert'] = incident["alert"]
                    notification['event'] = "incident_commented"
                    notifications.append(notification.copy())

                    logger.debug("Comment event will be: {}".format(event))

                    # Send log event to index
                    if (event!=''):
                        if type(event) == 'byte':
                            event = event.decode("utf-8")
                        events += event + "\n"

                    notification = {}

        logger.debug("Events: {}".format(events))
        
        if events!='':
            input.submit(events, hostname = socket.gethostname(), sourcetype = 'incident_change', source = 'incident_settings.py', index = config['index'])

        logger.debug("Notifications: {}".format(notifications))


        self._send_notifications(sessionKey, eh, notifications)

        # Setting a batch size of max. 1000 incidents
        batchsize = 1000
        incident_batch_counter = 0

        for i in range(0, len(incidents), batchsize):
            incident_batch = incidents[i:i+batchsize]

            # Finally batch save updated incidents
            uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents/batch_save'
            logger.info("Batchsave starting")
            serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey,  method='POST', jsonargs=json.dumps(incident_batch))
            logger.debug("Batchsave serverResponse: {}".format(serverResponse))
            logger.debug("Batchsave serverResponse Status: {}".format(serverResponse['status']))
            logger.debug("Batchsave serverContent: {}".format(serverContent.decode('utf-8')))
            logger.info("Batchsave serverContent incident count: {}".format(len(json.loads(serverContent.decode('utf-8')))))
            if serverResponse['status'] == "200":
                logger.info("Batchsave finished successfully")
            else:
                logger.info("Batchsave finished failed: {}".format(serverResponse))

            incident_batch_counter+=  len(incident_batch)
            logger.info("Bulk update total of {} incidents finished".format(incident_batch_counter))

        logger.debug("Updated incidents: {}".format(incidents))
        logger.info("Bulk update finished")

    def _send_notifications(self, sessionKey, eh, notifications):
        logger.info("_send_notifications started")
        
        for notification in notifications:
            ic = IncidentContext(sessionKey, notification['incident'])
            logger.info("nofication['incident': {}".format(notification['incident']))

            eh.handleEvent(alert=notification['alert'], event=notification['event'], incident=notification['incident'], context=ic.getContext())
        
        logger.info("_send_notifications finished")

    def _send_manual_notification(self, sessionKey, user, post_data):
        logger.info("_send_manual_notification started",)

        logger.debug("user: {}".format(user))
        logger.debug("post_data: {}".format(post_data))
    
        notification = {}
        notifications = []

        query = {}
        query['incident_id'] = post_data.get('incident_id')        
        logger.debug("Filter: {}".format(json.dumps(query)))

        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents?query={}'.format(urllib.parse.quote(json.dumps(query)))
        serverResponse, incident = rest.simpleRequest(uri, sessionKey=sessionKey)
        
        logger.debug("Settings for incident: {}".format(incident))
        
        incidents = json.loads(incident)

        notification['alert'] = incidents[0].get("alert")
        notification['incident'] = post_data.get('incident_id')
        notification['event'] = post_data.get('event')
        notification_message = post_data.get('notification_message')
        
        recipients = post_data.get('recipients')
        recipients_overwrite = post_data.get('recipients_overwrite')

        logger.debug("recipients_overwrite: {}".format(recipients_overwrite))

        notifications.append(notification.copy())
   
        ic = IncidentContext(sessionKey, notification['incident'])

        context = ic.getContext()

        context.update({'notification_message' : notification_message})
        context.update({'recipients' : recipients})
        context.update({'recipients_overwrite': recipients_overwrite})

        logger.debug("Notification context: {}".format(json.dumps(context)))

        eh = EventHandler(sessionKey = sessionKey)

        eh.handleEvent(alert=notification['alert'], event=notification['event'], incident=incidents[0], context=ic.getContext())
      
        logger.info("_send_manual_notification stopped") 

        return self.response('Manual notification executed', http.client.OK)

    def _create_new_incident(self, sessionKey, user, post_data):
        logger.debug("START _create_new_incident()")
        logger.debug("post_data: {}".format(post_data))
        config = {}
        config['index'] = 'main'
        config['collect_data_results'] = False
        config['index_data_results'] = False

        # Get config data
        restconfig = entity.getEntities('configs/alert_manager', count=-1, sessionKey=sessionKey)
        if len(restconfig) > 0:
            # Get index
            if 'index' in restconfig['settings']:
                config['index'] = restconfig['settings']['index']

            # Check if results have be written to collection
            if 'collect_data_results' in restconfig['settings']:
                if restconfig['settings']['collect_data_results'].lower() in ('1', 'true'):
                    config['collect_data_results'] = True
                else:
                    config['collect_data_results'] = False

            # Check if results have be indexed
            if 'index_data_results' in restconfig['settings']:
                if restconfig['settings']['index_data_results'].lower() in ('1', 'true'):
                    config['index_data_results'] = True
                else:
                    config['index_data_results'] = False

        logger.info("Global settings: {}".format(config))

        # Create timestamp for event
        gmtime = time.gmtime()
        now = time.strftime("%Y-%m-%dT%H:%M:%S.000%z", gmtime)
        now_epoch = time.strftime("%s", gmtime)

        required = ['title', 'urgency', 'impact', 'owner']
        missing = [r for r in required if r not in post_data]
        if missing:
            return self.response("Missing required arguments: {}".format(missing), http.client.BAD_REQUEST)

        title         = post_data.get('title')
        category      = post_data.get('category')
        subcategory   = post_data.get('subcategory')
        tags          = post_data.get('tags')
        urgency       = post_data.get('urgency')
        impact        = post_data.get('impact')
        owner         = post_data.get('owner')
        origin        = post_data.get('origin')
        group_id      = post_data.get('group_id')
        fields        = post_data.get('fields')
        earliest_time = post_data.get('earliest_time')
        latest_time   = post_data.get('latest_time')
        event_search  = post_data.get('event_search')

        if not category:
            category='unknown'
        if not subcategory :
            subcategory = 'unknown'
        if not tags:
            tags = '[Untagged]'
        if not event_search:
            event_search = '|noop'
        if not earliest_time:
            earliest_time = int(now_epoch)-1
        if not latest_time:
            latest_time = now

        # Field validation and formatting
        if fields:
            fields=fields.rstrip()
            try:
                fields=(dict(item.split("=") for item in fields.split("\n")))
                # Remove double-quotes
                for key, value in fields.items():
                     fields[key] = value.replace('"', '')

            except Exception as e:
                msg = 'Unhandled Exception: {}'.format(str(e))
                logger.exception(msg)
                return self.response(msg, http.client.INTERNAL_SERVER_ERROR)

        # Create unique id
        incident_id = str(uuid.uuid4())

        # Create event_id
        event_id = hashlib.md5(incident_id.encode('utf-8') + now.encode('utf-8')).hexdigest()

        # Defaults
        ttl                   = 3600
        alert_time            = now
        search_name           = 'Manual Alert'
        result_id             = 0
        job_id                = event_id
        alert                 = title
        display_fields        = ''
        external_reference_id = ''
        priority              = ''
        status                = 'new'
        app                   = 'alert_manager'

        logger.debug("title: {}".format(title))

        # Create metadata event
        metadata = '{{"alert":"{}", "alert_time": "{}", "origin": "{}", "app": "{}", "category": "{}", "display_fields":  "{}", "entry":[{{"content": "earliestTime": "{}", "eventSearch": "{}","latestTime": "{}"}}], "external_reference_id": "{}", "impact": "{}", "incident_id": "{}", "job_id": "{}", "owner": "{}", "priority": "{}", "result_id": "{}", "subcategory": "{}", "tags": "{}", "title": "{}", "ttl": "{}", "urgency": "{}"}}'.format(alert, now, origin, app, category, display_fields, earliest_time, event_search, latest_time, external_reference_id, impact, incident_id, job_id, owner, priority, result_id, subcategory, tags, title, ttl, urgency)
        logger.debug("Metadata {}".format(metadata))

        try:
            splunk.setDefault('sessionKey', sessionKey)
            input.submit(metadata, hostname = socket.gethostname(), sourcetype = 'alert_metadata', source = 'helper.py', index = config['index'])

        except Exception as e:
            msg = 'Unhandled Exception: {}'.format(str(e))
            logger.exception(msg)
            return self.response(msg, http.client.INTERNAL_SERVER_ERROR)

        # Create incident
        entry = {}
        entry['title'] = title
        entry['category'] = category
        entry['subcategory'] = subcategory
        entry['tags'] = tags
        entry['display_fields'] = display_fields
        entry['incident_id'] = incident_id
        entry['alert_time'] = now_epoch
        entry['job_id'] = job_id
        entry['result_id'] = result_id
        entry['alert'] = alert
        entry['app'] = app
        entry['status'] = status
        entry['ttl'] = ttl
        entry['impact'] = impact
        entry['urgency'] = urgency
        entry['priority'] = priority
        entry['owner'] = owner
        entry['search'] = event_search
        entry['external_reference_id'] = external_reference_id
        entry['group_id'] = group_id

        entry = json.dumps(entry, sort_keys=True)
        logger.debug("createIncident(): Entry: {}".format(entry))

        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents'
        rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=entry)

        # Create incident results
        if fields:

            field_array = []
            field_array.append(fields)

            field_list=[]

            for key in fields:
                field_list.append(key)

            logger.debug("fields: {}".format(fields))

            results = {}
            results['incident_id'] = incident_id
            results['fields'] = field_array
            results['field_list'] = field_list

            logger.debug("Entry: {}".format(results))

            # Write results to incident_results collection
            if config['collect_data_results'] == True:
                try:
                    # Add job_id and result_id to collection
                    results['job_id'] = job_id
                    results['result_id'] = result_id
                    results = json.dumps(results, sort_keys=True)

                    uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_results'
                    rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=results)
                    logger.info("Results for incident_id={} written to collection.".format(incident_id))

                except:
                    msg = 'Unhandled Exception: {}'.format(str(e))
                    logger.exception(msg)
                    return self.response(msg, http.client.INTERNAL_SERVER_ERROR)

            # Write results to index
            if config['index_data_results'] == True:
                try:
                    results = json.dumps(results, sort_keys=True)

                    input.submit(results, hostname = socket.gethostname(), sourcetype = 'alert_data_results', source = 'helper.py', index = config['index'])
                    logger.info("Results for incident_id={} written to index.".format(incident_id))

                except:
                    msg = 'Unhandled Exception: {}'.format(str(e))
                    logger.exception(msg)
                    return self.response(msg, http.client.INTERNAL_SERVER_ERROR)

        # Create incident_change events
        event = 'time={} event_id={} severity=INFO origin="alert_handler" user="{}" action="create" alert="{}" incident_id="{}" job_id="{}" result_id="{}" owner="{}" status="new" urgency="{}" ttl="{}" alert_time="{}"'.format(now, event_id, user, search_name, incident_id, job_id, result_id, owner, urgency, ttl, alert_time)

        logger.debug("Event will be: {}".format(event))
        event = event.encode('utf8')

        try:
            splunk.setDefault('sessionKey', sessionKey)
            input.submit(event, hostname = socket.gethostname(), sourcetype = 'incident_change', source = 'helper.py', index = config['index'])
            return self.response('Action logged', http.client.OK)

        except Exception as e:
            msg = 'Unhandled Exception: {}'.format(str(e))
            logger.exception(msg)
            return self.response(msg, http.client.INTERNAL_SERVER_ERROR)

        return self.response('Action logged', http.client.OK)

    def _get_incident_groups(self, sessionKey, query_params):
            logger.debug("START _get_incident_groups()")

            uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_groups?q=output_mode=json'
            serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='GET')
            logger.debug("incident_groups: {}".format(serverContent.decode('utf-8')))
            entries = json.loads(serverContent.decode('utf-8'))

            return self.response(entries, http.client.OK)

    def _create_incident_group(self, sessionKey, user, post_data):
            logger.debug("START _create_incident_group()")
            uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_groups'

            required = ['group']
            missing = [r for r in required if r not in post_data]
            if missing:
                return self.response("Missing required arguments: {}".format(missing), http.client.BAD_REQUEST)

            group = post_data.get('group')

            # Check for duplicate group names
            uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_groups?q=output_mode=json'
            serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='GET')
            incident_groups = json.loads(serverContent.decode('utf-8'))
            for item in incident_groups:
                if group == item.get('group'):
                    entry = {}
                    entry['group'] = item.get('group')
                    entry['group_id'] = item.get('_key')           
                    entry = json.dumps(entry, sort_keys=True)
                    return self.response("{}".format(entry), http.client.BAD_REQUEST)

            entry = {}
            entry['group'] = group

            # Create incident group
            uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_groups'
            serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=json.dumps(entry, sort_keys=True))
            serverContent = json.loads(serverContent.decode('utf-8'))

            entry['group_id'] = serverContent['_key']
            entry = json.dumps(entry, sort_keys=True)

            return self.response(entry, http.client.OK)
