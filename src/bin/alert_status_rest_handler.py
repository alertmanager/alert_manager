import os
import sys
import urllib
import json
import re
import datetime
import urllib
import hashlib
import socket
import httplib
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

from AlertManagerUsers import *
from AlertManagerLogger import *
from CsvLookup import *

logger = setupLogger('rest_handler')

if sys.platform == "win32":
    import msvcrt
    # Binary mode is required for persistent mode on Windows.
    msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    msvcrt.setmode(sys.stderr.fileno(), os.O_BINARY)

from splunk.persistconn.application import PersistentServerConnectionApplication

class AlertStatusHandler(PersistentServerConnectionApplication):
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


    def _delete_alert_status(self, sessionKey, user, post_data):
        logger.debug("START _delete_alert_status()")

        required = ['key']
        missing = [r for r in required if r not in post_data]
        if missing:
            return self.response("Missing required arguments: %s" % missing, httplib.BAD_REQUEST)

        key = post_data.pop('key')

        query = {}
        query['_key'] = key
        logger.debug("Query for alert status: %s" % urllib.quote(json.dumps(query)))
        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/alert_status?query=%s' % urllib.quote(json.dumps(query))
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='DELETE')

        logger.debug("Alert Status removed. serverResponse was %s" % serverResponse)

        return self.response('Alert Status with key {} successfully removed'.format(key), httplib.OK)

    def _update_alert_status(self, sessionKey, user, post_data):
        logger.debug("START _update_alert_status()")

        required = ['alert_status_data']
        missing = [r for r in required if r not in post_data]
        if missing:
            return self.response("Missing required arguments: %s" % missing, httplib.BAD_REQUEST)

        alert_status_data = post_data.pop('alert_status_data')

        # Parse the JSON
        parsed_alert_status_data = json.loads(alert_status_data)

        for entry in parsed_alert_status_data:
            if '_key' in entry and entry['_key'] != None and entry['_key'] != 'n/a':
                uri = '/servicesNS/nobody/alert_manager/storage/collections/data/alert_status/' + entry['_key']
                logger.debug("uri is %s" % uri)

                entry = json.dumps(entry)

                serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=entry)
                logger.debug("Updated entry. serverResponse was %s" % serverResponse)
            else:
                if '_key' in entry:
                    del entry['_key']

                if 'builtin' not in entry or entry['builtin'] is None or entry['builtin'] == '':
                    entry['builtin'] = 0

                if 'internal_only' not in entry or entry['internal_only'] is None or entry['internal_only'] == '':
                    entry['internal_only'] = 0

                if 'hidden' not in entry or entry['hidden'] is None or entry['hidden'] == '':
                    entry['hidden'] = 0

                ['' if val is None else val for val in entry]

                uri = '/servicesNS/nobody/alert_manager/storage/collections/data/alert_status/'
                logger.debug("uri is %s" % uri)

                entry = json.dumps(entry)
                logger.debug("entry is %s" % entry)

                serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=entry)
                logger.debug("Added entry. serverResponse was %s" % serverResponse)

        return self.response('Alert Status successfully updated', httplib.OK)

    def _get_alert_status(self, sessionKey, query_params):
        logger.debug("START _get_alert_status()")

        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/alert_status?output_mode=json'
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)

        logger.debug("alert_status: %s" % json.dumps(serverResponse))
        logger.debug("Entries: %s" % json.dumps(serverContent))
        entries = json.loads(serverContent)

        status_list = []
        if len(entries) > 0:
            for entry in entries:
                if int(entry['internal_only']) == 0 and int(entry['hidden']) == 0:
                    se = {'status_description': entry['status_description'], 'status': entry['status']}
                    status_list.append(se)

        logger.debug("status_list: %s " % json.dumps(status_list))

        return self.response(status_list, httplib.OK)
