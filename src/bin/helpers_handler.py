import os
import sys
import urllib
import json

import splunk.appserver.mrsparkle.lib.util as util
import splunk.rest as rest

dir = os.path.join(util.get_apps_dir(), 'alert_manager', 'bin', 'lib')
if not dir in sys.path:
    sys.path.append(dir)

from AlertManagerUsers import *
from AlertManagerLogger import *
from CsvLookup import *

logger = setupLogger('helpers')

if sys.platform == "win32":
    import msvcrt
    # Binary mode is required for persistent mode on Windows.
    msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    msvcrt.setmode(sys.stderr.fileno(), os.O_BINARY)

from splunk.persistconn.application import PersistentServerConnectionApplication

def flatten_query_params(params):
    # Query parameters are provided as a list of pairs and can be repeated, e.g.:
    #
    #   "query": [ ["arg1","val1"], ["arg2", "val2"], ["arg1", val2"] ]
    #
    # This function simply accepts only the first parameter and discards duplicates and is not intended to provide an
    # example of advanced argument handling.
    flattened = {}
    for i, j in params:
        flattened[i] = flattened.get(i) or j
    return flattened


class HelpersHandler(PersistentServerConnectionApplication):
    def __init__(self, command_line, command_arg):
        PersistentServerConnectionApplication.__init__(self)

    def handle(self, in_string):
        request = json.loads(in_string)
        query_params = flatten_query_params(request['query'])

        action = query_params.get('action')
        sessionKey = request.get('session').get('authtoken')

        logger.debug('SESSIONKEY: %s', str(sessionKey))
        #logger.debug('QUERY_PARAMS: %s', str(query_params))

        payload = None
        err_payload = json.dumps({ 'payload': None })

        if not in_string or not action:
            return err_payload


        if action == 'list_users':
            users = self._get_users(sessionKey=sessionKey)
            payload = { 'payload': users, 'status': 200 }

        if action == 'list_status':
            status = self._get_status(sessionKey=sessionKey)
            payload = { 'payload': status, 'status': 200 }

        if action == 'get_savedsearch_description':
            savedsearch = query_params.get('savedsearch')
            app = query_params.get('app')
            if not savedsearch or not app:
                return err_payload

            description = self._get_savedsearch_description(sessionKey=sessionKey, savedsearch=savedsearch, app=app)
            payload = { 'payload': description, 'status': 200 }


        elif action == 'another_action':
            payload = { 'payload': [ 'hello world2' ], 'status': 200 }

        else:
            return err_payload

        logger.debug('PAYLOAD: %s', str(payload))

        return json.dumps(payload)

    def _get_users(self, sessionKey):

        users = AlertManagerUsers(sessionKey=sessionKey)
        user_list = users.getUserList()

        logger.debug("user_list: %s " % json.dumps(user_list))

        return user_list

    def _get_status(self, sessionKey):

        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/alert_status?output_mode=json'
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)

        logger.info("server_response: %s" % json.dumps(serverResponse))
        entries = json.loads(serverContent)

        status_list = []
        if len(entries) > 0:
            for entry in entries:
                if int(entry['internal_only']) == 0:
                    se = {'status_description': entry['status_description'], 'status': entry['status']}
                    status_list.append(se)

        logger.info("status_list: %s " % json.dumps(status_list))

        return status_list

    def _get_savedsearch_description(self, sessionKey, savedsearch, app):
        uri = '/servicesNS/nobody/%s/admin/savedsearch/%s?output_mode=json' % \
              (app, urllib.quote(savedsearch.encode('utf8')))
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='GET')

        savedSearchContent = json.loads(serverContent)

        if savedSearchContent["entry"][0]["content"]["description"]:
            return savedSearchContent["entry"][0]["content"]["description"]
        else:
            return ""
