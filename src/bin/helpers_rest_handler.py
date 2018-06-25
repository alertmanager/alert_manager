import os
import sys
import urllib
import json
import re
import datetime
import time
import urllib
import hashlib
import socket
import httplib
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

from AlertManagerUsers import *
from AlertManagerLogger import *
from CsvLookup import *
from EventHandler import *
from IncidentContext import *

logger = setupLogger('rest_handler')

if sys.platform == "win32":
    import msvcrt
    # Binary mode is required for persistent mode on Windows.
    msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    msvcrt.setmode(sys.stderr.fileno(), os.O_BINARY)

from splunk.persistconn.application import PersistentServerConnectionApplication

class HelpersHandler(PersistentServerConnectionApplication):
    def __init__(self, command_line, command_arg):
        PersistentServerConnectionApplication.__init__(self)

    def handle(self, args):
        logger.debug("START handle()")
        logger.debug('ARGS: %s', args)

        args = json.loads(args)

        try:
            logger.info('Handling %s request.' % args['method'])
            method = 'handle_' + args['method'].lower()
            if callable(getattr(self, method, None)):
                return operator.methodcaller(method, args)(self)
            else:
                return self.response('Invalid method for this endpoint', httplib.METHOD_NOT_ALLOWED)
        except ValueError as e:
            msg = 'ValueError: %s' % e.message
            return self.response(msg, httplib.BAD_REQUEST)
        except splunk.RESTException as e:
            return self.response('RESTexception: %s' % e, httplib.INTERNAL_SERVER_ERROR)
        except Exception as e:
            msg = 'Unknown exception: %s' % e
            logger.exception(msg)
            return self.response(msg, httplib.INTERNAL_SERVER_ERROR)


    def handle_get(self, args):
        logger.debug('GET ARGS %s', json.dumps(args))

        query_params = dict(args.get('query', []))

        try:
            sessionKey = args["session"]["authtoken"]
            user = args["session"]["user"]
        except KeyError:
            return self.response("Failed to obtain auth token", httplib.UNAUTHORIZED)


        required = ['action']
        missing = [r for r in required if r not in query_params]
        if missing:
            return self.response("Missing required arguments: %s" % missing, httplib.BAD_REQUEST)

        action = '_' + query_params.pop('action').lower()
        if callable(getattr(self, action, None)):
            return operator.methodcaller(action, sessionKey, query_params)(self)
        else:
            msg = 'Invalid action: action="{}"'.format(action)
            logger.exception(msg)
            return self.response(msg, httplib.BAD_REQUEST)

    def handle_post(self, args):
        logger.debug('POST ARGS %s', json.dumps(args))

        post_data = dict(args.get('form', []))

        try:
            sessionKey = args["session"]["authtoken"]
            user = args["session"]["user"]
        except KeyError:
            return self.response("Failed to obtain auth token", httplib.UNAUTHORIZED)


        required = ['action']
        missing = [r for r in required if r not in post_data]
        if missing:
            return self.response("Missing required arguments: %s" % missing, httplib.BAD_REQUEST)

        action = '_' + post_data.pop('action').lower()
        if callable(getattr(self, action, None)):
            return operator.methodcaller(action, sessionKey, user, post_data)(self)
        else:
            msg = 'Invalid action: action="{}"'.format(action)
            logger.exception(msg)
            return self.response(msg, httplib.BAD_REQUEST)


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

        logger.debug("user_list: %s " % json.dumps(user_list))

        return self.response(user_list, httplib.OK)

    def _get_savedsearch_description(self, sessionKey, query_params):
        logger.debug("START _get_savedsearch_description()")

        required = ['savedsearch_name', 'app']
        missing = [r for r in required if r not in query_params]
        if missing:
            return self.response("Missing required arguments: %s" % missing, httplib.BAD_REQUEST)

        savedsearch_name = query_params.pop('savedsearch_name')
        app = query_params.pop('app')

        uri = '/servicesNS/nobody/%s/admin/savedsearch/%s?output_mode=json' % \
              (app, urllib.quote(savedsearch_name.encode('utf8')))
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='GET')

        savedSearchContent = json.loads(serverContent)

        if savedSearchContent["entry"][0]["content"]["description"]:
            return self.response(savedSearchContent["entry"][0]["content"]["description"], httplib.OK)
        else:
            msg = 'Get saved search description failed'
            logger.exception(msg)
            return self.response(msg, httplib.INTERNAL_SERVER_ERROR)


    def _get_notification_schemes(self, sessionKey, query_params):
        logger.debug("START _get_notification_schemes()")

        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/notification_schemes?q=output_mode=json'
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='GET')
        logger.debug("notification_schemes: %s" % serverContent)
        entries = json.loads(serverContent)

        scheme_list = [ ]
        if len(entries) > 0:
            for entry in entries:
                scheme_list.append(entry['schemeName'])


        return self.response(scheme_list, httplib.OK)

    def _get_search_string(self, sessionKey, query_params):
        logger.debug("START _get_search_string()")

        required = ['incident_id']
        missing = [r for r in required if r not in query_params]
        if missing:
            return self.response("Missing required arguments: %s" % missing, httplib.BAD_REQUEST)

        incident_id = query_params.pop('incident_id')

        incident_id_query = '{"incident_id": "' + incident_id + '"}'
        incident_uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents?q=output_mode=json&query=' + urllib.quote_plus(incident_id_query)

        # Get incident json
        serverResponse, serverContent = rest.simpleRequest(incident_uri, sessionKey=sessionKey, method='GET')
        logger.debug("incident: %s" % serverContent)
        incident = json.loads(serverContent)

        if incident[0]["search"]:
            return self.response(incident[0]["search"], httplib.OK)
        else:
            msg = 'Get search string failed'
            logger.exception(msg)
            return self.response(msg, httplib.INTERNAL_SERVER_ERROR)

    def _write_log_entry(self, sessionKey, user, post_data):
        logger.debug("START _write_log_entry()")

        required = ['incident_id', 'log_action', 'origin']
        missing = [r for r in required if r not in post_data]
        if missing:
            return self.response("Missing required arguments: %s" % missing, httplib.BAD_REQUEST)

        incident_id = post_data.pop('incident_id')
        log_action  = post_data.pop('log_action')

    	comment         = post_data.get('comment', '')
    	origin          = post_data.get('origin', '')
    	severity        = post_data.get('severity', 'INFO')
    	owner           = post_data.get('owner', '')
    	previous_owner  = post_data.get('previous_owner', '')
    	status          = post_data.get('status', '')
    	previous_status = post_data.get('status', '')
    	job_id          = post_data.get('job_id', '')
    	result_id       = post_data.get('result_id', '')

        now = datetime.datetime.now().isoformat()

        # Get Index
    	config = {}
        config['index'] = 'main'

        restconfig = entity.getEntities('configs/alert_manager', count=-1, sessionKey=sessionKey)
        if len(restconfig) > 0:
            if 'index' in restconfig['settings']:
                config['index'] = restconfig['settings']['index']


        comment = comment.replace('\n', '<br />').replace('\r', '')
        event_id = hashlib.md5(incident_id + now).hexdigest()

        event = ''
        if (log_action == "comment"):
            event = 'time=%s severity="%s" origin="%s" event_id="%s" user="%s" action="comment" incident_id="%s" comment="%s"' % (now, severity, origin, event_id, user, incident_id, comment)
        elif (log_action == "change"):
            event = 'time=%s severity="%s" origin="%s" event_id="%s" user="%s" action="comment" incident_id="%s" job_id="%s" result_id="%s" status="%s" previous_status="%s"' % (now, severity, origin, event_id, user, incident_id, job_id, result_id, status, previous_status)

        logger.debug("Event will be: %s" % event)
        event = event.encode('utf8')

        try:
            splunk.setDefault('sessionKey', sessionKey)
            input.submit(event, hostname = socket.gethostname(), sourcetype = 'incident_change', source = 'helper.py', index = config['index'])
            return self.response('Action logged', httplib.OK)

        except Exception as e:
            msg = 'Unhandled Exception: {}'.format(str(e))
            logger.exception(msg)
            return self.response(msg, httplib.INTERNAL_SERVER_ERROR)

    def _update_incident(self, sessionKey, user, post_data):
        logger.debug("START _update_incident()")

        required = ['incident_data']
        missing = [r for r in required if r not in post_data]
        if missing:
            return self.response("Missing required arguments: %s" % missing, httplib.BAD_REQUEST)

        incident_data = post_data.pop('incident_data')

        splunk.setDefault('sessionKey', sessionKey)

        eh = EventHandler(sessionKey = sessionKey)

        config = {}
        config['index'] = 'main'

        restconfig = entity.getEntities('configs/alert_manager', count=-1, sessionKey=sessionKey)
        if len(restconfig) > 0:
            if 'index' in restconfig['settings']:
                config['index'] = restconfig['settings']['index']

        logger.debug("Global settings: %s" % config)

        # Parse the JSON
        incident_data = json.loads(incident_data)

        if 'incident_ids' in incident_data:
            for incident_id in incident_data['incident_ids']:
                self._do_update_incident(sessionKey, config, eh, incident_id, incident_data, user)

        if 'incident_id' in incident_data:
            self._do_update_incident(sessionKey, config, eh, incident_data['incident_id'], incident_data, user)


        return self.response('Successfully updated incident(s).', httplib.OK)

    def _do_update_incident(self, sessionKey, config, eh, incident_id, incident_data, user):
        # Get key
        query = {}
        query['incident_id'] = incident_id
        logger.debug("Filter: %s" % json.dumps(query))

        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents?query=%s' % urllib.quote(json.dumps(query))
        serverResponse, incident = rest.simpleRequest(uri, sessionKey=sessionKey)
        logger.debug("Settings for incident: %s" % incident)
        incident = json.loads(incident)

        # Update incident
        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents/' + incident[0]['_key']
        logger.debug("URI for incident update: %s" % uri )

        # Prepared new entry
        now = datetime.datetime.now().isoformat()
        changed_keys = []
        for key in incident[0].keys():
            if (key in incident_data) and (incident[0][key] != incident_data[key]):
                changed_keys.append(key)
                logger.info("%s for incident %s changed. Writing change event to index %s." % (key, incident[0]['incident_id'], config['index']))
                event_id = hashlib.md5(incident[0]['incident_id'] + now).hexdigest()
                event = 'time=%s severity=INFO origin="incident_posture" event_id="%s" user="%s" action="change" incident_id="%s" %s="%s" previous_%s="%s"' % (now, event_id, user, incident[0]['incident_id'], key, incident_data[key], key, incident[0][key])
                logger.debug("Change event will be: %s" % event)
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
                logger.info("%s for incident %s didn't change." % (key, incident[0]['incident_id']))

        del incident[0]['_key']
        contentsStr = json.dumps(incident[0])
        logger.debug("content for update: %s" % contentsStr)
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=contentsStr)

        logger.debug("Response from update incident entry was %s " % serverResponse)
        logger.debug("Changed keys: %s" % changed_keys)

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
            event_id = hashlib.md5(incident[0]['incident_id'] + now).hexdigest()
            event = 'time=%s severity=INFO origin="incident_posture" event_id="%s" user="%s" action="comment" incident_id="%s" comment="%s"' % (now, event_id, user, incident[0]['incident_id'], incident_data['comment'])
            logger.debug("Comment event will be: %s" % event)
            event = event.encode('utf8')
            input.submit(event, hostname = socket.gethostname(), sourcetype = 'incident_change', source = 'incident_settings.py', index = config['index'])
            ic = IncidentContext(sessionKey, incident_id)
            eh.handleEvent(alert=incident[0]["alert"], event="incident_commented", incident=incident[0], context=ic.getContext())

    def _create_new_incident(self, sessionKey, user, post_data):
        logger.debug("START _create_new_incident()")

        gmtime = time.gmtime()
        now = time.strftime("%Y-%m-%dT%H:%M:%S.000%z", gmtime)
        now_epoch = time.strftime("%s", gmtime)
        
        required = ['title', 'urgency', 'impact', 'owner']
        missing = [r for r in required if r not in post_data]
        if missing:
            return self.response("Missing required arguments: %s" % missing, httplib.BAD_REQUEST)

    	title         = post_data.get('title')
    	category      = post_data.get('category')
    	subcategory   = post_data.get('subcategory')
        tags          = post_data.get('tags')
        urgency       = post_data.get('urgency')
        impact        = post_data.get('impact')
        owner         = post_data.get('owner')
        origin        = post_data.get('origin')
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
            earliest_time = now
        if not latest_time:
            latest_time = now    

        # Field validation and formatting
        if fields:
            fields=fields.rstrip()
            try:
                fields=(dict(item.split("=") for item in fields.split("\n")))
                # Remove double-quotes
                for key, value in fields.iteritems():
                     fields[key] = value.replace('"', '')

            except:
                msg = 'Unhandled Exception: {}'.format(str(e))
                logger.exception(msg)
                return self.response(msg, httplib.INTERNAL_SERVER_ERROR)


        # Defaults
        ttl                   = 3600        
        alert_time            = now
        search_name           = 'Manual Alert'
        result_id             = 0
        job_id                = ''
        alert                 = title
        display_fields        = ''
        external_reference_id = ''
        priority              = ''
        status                = 'new'
        app                   = 'alert_manager'

        # Create unique id
        incident_id = str(uuid.uuid4())

        # Get Index
    	config = {}
        config['index'] = 'main'

        restconfig = entity.getEntities('configs/alert_manager', count=-1, sessionKey=sessionKey)
        if len(restconfig) > 0:
            if 'index' in restconfig['settings']:
                config['index'] = restconfig['settings']['index']

        event_id = hashlib.md5(incident_id + now).hexdigest()

        # Create metadata event
        metadata = '{"alert":"%s", "alert_time": "%s", "origin": "%s", "app": "%s", "category": "%s", "display_fields":  "%s", "entry":[{"content": {"earliestTime": "%s", "eventSearch": "%s","latestTime": "%s"}}], "external_reference_id": "%s", "impact": "%s", "incident_id": "%s", "job_id": "%s", "owner": "%s", "priority": "%s", "result_id": "%s", "subcategory": "%s", "tags": "%s", "title": "%s", "ttl": "%s", "urgency": "%s"}' % (alert, now, origin, app, category, display_fields, earliest_time, event_search, latest_time, external_reference_id, impact, incident_id, job_id, owner, priority, result_id, subcategory, tags, title, ttl, urgency)

        logger.info("Metadata %s" % metadata)

        try:
            splunk.setDefault('sessionKey', sessionKey)
            input.submit(metadata, hostname = socket.gethostname(), sourcetype = 'alert_metadata', source = 'helper.py', index = config['index'])

        except Exception as e:
            msg = 'Unhandled Exception: {}'.format(str(e))
            logger.exception(msg)
            return self.response(msg, httplib.INTERNAL_SERVER_ERROR)

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

        entry = json.dumps(entry, sort_keys=True)
        logger.info("createIncident(): Entry: %s" % entry)
        
        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents'
        rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=entry)

        # Create incident results
        if fields:

            field_array = []
            field_array.append(fields)

            field_list=[]

            for key in fields:
                field_list.append(key)

            logger.info("fields: %s" % fields)    

            results = {}
            results['incident_id'] = incident_id
            results['job_id'] = job_id
            results['result_id'] = result_id
            results['fields'] = field_array
            results['field_list'] = field_list

            results = json.dumps(results, sort_keys=True)

            logger.info("Entry: %s" % results)

            try:
                uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_results'
                serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=results)
                logger.info("Results for incident_id=%s written to collection." % (incident_id))

            except:
                msg = 'Unhandled Exception: {}'.format(str(e))
                logger.exception(msg)
                return self.response(msg, httplib.INTERNAL_SERVER_ERROR)

        # Create incident_change events
        event = 'time=%s event_id=%s severity=INFO origin="alert_handler" user="%s" action="create" alert="%s" incident_id="%s" job_id="%s" result_id="%s" owner="%s" status="new" urgency="%s" ttl="%s" alert_time="%s"' % (now, event_id, user, search_name, incident_id, job_id, result_id, owner, urgency, ttl, alert_time)

        logger.debug("Event will be: %s" % event)
        event = event.encode('utf8')

        try:
            splunk.setDefault('sessionKey', sessionKey)
            input.submit(event, hostname = socket.gethostname(), sourcetype = 'incident_change', source = 'helper.py', index = config['index'])
            return self.response('Action logged', httplib.OK)

        except Exception as e:
            msg = 'Unhandled Exception: {}'.format(str(e))
            logger.exception(msg)
            return self.response(msg, httplib.INTERNAL_SERVER_ERROR)

        return self.response('Action logged', httplib.OK)