import os
import sys
import urllib
import json
import re
import urllib
import urllib.parse
import hashlib
import socket
import http.client
import operator
from string import Template

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

from AlertManagerLogger import setupLogger

logger = setupLogger('rest_handler')

if sys.platform == "win32":
    import msvcrt # pylint: disable=import-error
    # Binary mode is required for persistent mode on Windows.
    msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY) # pylint: disable=maybe-no-member
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY) # pylint: disable=maybe-no-member
    msvcrt.setmode(sys.stderr.fileno(), os.O_BINARY) # pylint: disable=maybe-no-member

from splunk.persistconn.application import PersistentServerConnectionApplication

class IncidentSettingsHandler(PersistentServerConnectionApplication):
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

    def _delete_incident_setting(self, sessionKey, user, post_data):
        logger.debug("START _delete_incident_setting()")

        required = ['key']
        missing = [r for r in required if r not in post_data]
        if missing:
            return self.response("Missing required arguments: {}".format(missing), http.client.BAD_REQUEST)

        key = post_data.pop('key')

        query = {}
        query['_key'] = key
        logger.debug("Query for incident settings: {}".format(urllib.parse.quote(json.dumps(query))))
        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_settings?query={}'.format(urllib.parse.quote(json.dumps(query)))
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='DELETE')

        logger.debug("Entry removed. serverResponse was {}".format(serverResponse))

        return self.response('Incident Setting with key {} successfully removed'.format(key), http.client.OK)


    def _update_incident_settings(self, sessionKey, user, post_data):
        logger.debug("START _update_incident_settings()")

        required = ['incident_settings']
        missing = [r for r in required if r not in post_data]
        if missing:
            return self.response("Missing required arguments: {}".format(missing), http.client.BAD_REQUEST)

        incident_settings = post_data.pop('incident_settings')

        # Parse the JSON
        incident_settings = json.loads(incident_settings)

        for entry in incident_settings:
            if '_key' in entry and entry['_key'] != None:
                uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_settings/' + entry['_key']
                logger.debug("uri is {}".format(uri))

                del entry['_key']
                entry = json.dumps(entry)

                serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=entry)
                logger.debug("Updated entry. serverResponse was {}".format(serverResponse))
            else:
                if '_key' in entry:
                    del entry['_key']
                ['' if val is None else val for val in entry]

                uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_settings/'
                logger.debug("uri is {}".format(uri))

                entry = json.dumps(entry)
                logger.debug("entry is {}".format(entry))

                serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=entry)
                logger.debug("Added entry. serverResponse was {}".format(serverResponse))

        return self.response('Incident Settings successfully updated', http.client.OK)
