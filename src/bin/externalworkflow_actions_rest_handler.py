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
import traceback
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

logger = setupLogger('rest_handler')

if sys.platform == "win32":
    import msvcrt
    # Binary mode is required for persistent mode on Windows.
    msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    msvcrt.setmode(sys.stderr.fileno(), os.O_BINARY)

from splunk.persistconn.application import PersistentServerConnectionApplication

class ExternalWorkflowActionsHandler(PersistentServerConnectionApplication):
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


    def _delete_externalworkflow_action(self, sessionKey, user, post_data):
        logger.debug("START _delete_externalworkflow_action()")

        required = ['key']
        missing = [r for r in required if r not in post_data]
        if missing:
            return self.response("Missing required arguments: %s" % missing, httplib.BAD_REQUEST)

        key = post_data.pop('key')

        query = {}
        query['_key'] = key
        logger.debug("Query for external workflow actions: %s" % urllib.quote(json.dumps(query)))
        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/externalworkflow_actions?query=%s' % urllib.quote(json.dumps(query))
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='DELETE')

        logger.debug("External Workflow Action removed. serverResponse was %s" % serverResponse)

        return self.response('External Workflow Action with key {} successfully removed'.format(key), httplib.OK)

    def _update_externalworkflow_actions(self, sessionKey, user, post_data):
        logger.debug("START _update_externalworkflow_actions()")

        required = ['externalworkflowaction_data']
        missing = [r for r in required if r not in post_data]
        if missing:
            return self.response("Missing required arguments: %s" % missing, httplib.BAD_REQUEST)

        externalworkflowaction_data = post_data.pop('externalworkflowaction_data')

        # Parse the JSON
        parsed_externalworkflowaction_data = json.loads(externalworkflowaction_data)

        for entry in parsed_externalworkflowaction_data:
            if '_key' in entry and entry['_key'] != None:
                uri = '/servicesNS/nobody/alert_manager/storage/collections/data/externalworkflow_actions/' + entry['_key']
                logger.debug("uri is %s" % uri)

                del entry['_key']
                entry = json.dumps(entry)

                serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=entry)
                logger.debug("Updated entry. serverResponse was %s" % serverResponse)
            else:
                if '_key' in entry:
                    del entry['_key']
                ['' if val is None else val for val in entry]

                uri = '/servicesNS/nobody/alert_manager/storage/collections/data/externalworkflow_actions/'
                logger.debug("uri is %s" % uri)

                entry = json.dumps(entry)
                logger.debug("entry is %s" % entry)

                serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=entry)
                logger.debug("Added entry. serverResponse was %s" % serverResponse)

        return self.response('External Workflow Actions successfully updated', httplib.OK)


    def _get_externalworkflow_actions(self, sessionKey, query_params):
        logger.debug("START _get_externalworkflow_actions()")

        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/externalworkflow_actions?q=output_mode=json'
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='GET')
        logger.debug("externalworkflow_actions: %s" % serverContent)
        entries = json.loads(serverContent)

        externalworkflow_actions = [ ]

        if len(entries) > 0:
            for entry in entries:
                if int(entry['disabled']) == 0:
                	ewa = {'label': entry['label'], 'title': entry['title'] }
                	externalworkflow_actions.append(ewa)

        return self.response(externalworkflow_actions, httplib.OK)

    def _get_externalworkflowaction_command(self, sessionKey, query_params):
        """
        Gives back sendalert string based on template
        Takes incident_id and external workflow action as a parameter
        e.g. https://<hostname>/en-US/custom/alert_manager/helpers/get_externalworkflowaction_command?incident_id=<incident_id>&externalworkflowaction=<externalworkflowaction>
        """
        logger.debug("START _get_externalworkflowaction_command()")

        required = ['incident_id', 'externalworkflowaction']
        missing = [r for r in required if r not in query_params]
        if missing:
            return self.response("Missing required arguments: %s" % missing, httplib.BAD_REQUEST)

        incident_id = query_params.pop('incident_id')
        externalworkflowaction = query_params.pop('externalworkflowaction')

        # Get incident json
        incident_id_query = '{"incident_id": "' + incident_id + '"}'
        incident_uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents?q=output_mode=json&query=' + urllib.quote_plus(incident_id_query)
        serverResponse, serverContent = rest.simpleRequest(incident_uri, sessionKey=sessionKey, method='GET')
        logger.debug("incident: %s" % serverContent)
        incident = json.loads(serverContent)

        # Get incident_results
        incident_results_uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_results?q=output_mode=json&query=' + urllib.quote_plus(incident_id_query)
        serverResponse, serverContent = rest.simpleRequest(incident_results_uri, sessionKey=sessionKey, method='GET')
        logger.debug("incident_results: %s" % serverContent)
        incident_results = json.loads(serverContent)

        # Get externalworkflowaction settings json
        externalworkflowaction_query = '{"title": "' + externalworkflowaction + '"}'
        externalworkflowaction_uri = '/servicesNS/nobody/alert_manager/storage/collections/data/externalworkflow_actions?q=output_mode=json&query=' + urllib.quote_plus(externalworkflowaction_query)
        serverResponse, serverContent = rest.simpleRequest(externalworkflowaction_uri, sessionKey=sessionKey, method='GET')
        logger.debug("externalworkflow_action: %s" % serverContent)
        externalworkflow_action = json.loads(serverContent)

        if len(externalworkflow_action) == 1:
            logger.debug("Found correct number of External Workflow Actions. Proceeding...")
            # Extract title from ewf settings
            title = externalworkflow_action[0]['title']

            # Create dict for template replacement key/values
            incident_data = {}
            for key in incident[0]:
        	       incident_data[key] = incident[0][key]

            # Create dict for results
            if incident_results:
                incident_results=incident_results[0]['fields']
                results = {}
                for key in incident_results[0]:
                    results['result.' + key] = incident_results[0][key]

                # Append results to incident data
                incident_data.update(results)

            logger.debug("incident_data: %s" % json.dumps(incident_data))

            # Get parameters
            command = ''
            try:
                if 'parameters' in externalworkflow_action[0]:
                    logger.info("Params found in external worflow action, parsing them...")
                    parameters = externalworkflow_action[0]['parameters']

                    # Change parameters from Splunk variables to Python variables ( remove appended $)
                    parameters=re.sub('(?<=\w)\$', '', parameters)

                    # Allow dot in pattern for template
                    class FieldTemplate(StringTemplate):
                        idpattern = r'[a-zA-Z][_a-zA-Z0-9.]*'

                    # Create template from parameters
                    parameters_template = FieldTemplate(parameters)

                    # Build command string
                    command = '| sendalert ' + title + ' ' + parameters_template.safe_substitute(incident_data)
                else:
                    logger.info("No params found in external workflow action, returning 'empty' command...")
                    command = '| sendalert ' + title
            except Exception as e:
                msg = "Unexpected Error: %s" % (traceback.format_exc())
                logger.exception(msg)
                return self.response(msg, httplib.INTERNAL_SERVER_ERROR)

            # Return command
            logger.debug("Returning command '%s'" % command)
            return self.response(command, httplib.OK)
        else:
            msg = 'Number of return external workflow actions is incorrect. Expected: 1. Given: {}'.format(len(externalworkflow_action))
            logger.exception(msg)
            return self.response(msg, httplib.INTERNAL_SERVER_ERROR)
