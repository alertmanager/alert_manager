import os
import sys
import json
import re
import urllib.parse
import hashlib
import socket
import http.client
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

class ExternalWorkflowActionsHandler(PersistentServerConnectionApplication):
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


    def _delete_externalworkflow_action(self, sessionKey, user, post_data):
        logger.debug("START _delete_externalworkflow_action()")

        required = ['key']
        missing = [r for r in required if r not in post_data]
        if missing:
            return self.response("Missing required arguments: {}".format(missing), http.client.BAD_REQUEST)

        key = post_data.pop('key')

        query = {}
        query['_key'] = key
        logger.debug("Query for external workflow actions: {}".format(urllib.parse.quote(json.dumps(query))))
        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/externalworkflow_actions?query={}'.format(urllib.parse.quote(json.dumps(query)))
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='DELETE')

        logger.debug("External Workflow Action removed. serverResponse was {}".format(serverResponse))

        return self.response('External Workflow Action with key {} successfully removed'.format(key), http.client.OK)

    def _update_externalworkflow_actions(self, sessionKey, user, post_data):
        logger.debug("START _update_externalworkflow_actions()")

        required = ['externalworkflowaction_data']
        missing = [r for r in required if r not in post_data]
        if missing:
            return self.response("Missing required arguments: {}".format(missing), http.client.BAD_REQUEST)

        externalworkflowaction_data = post_data.pop('externalworkflowaction_data')

        # Parse the JSON
        parsed_externalworkflowaction_data = json.loads(externalworkflowaction_data)

        for entry in parsed_externalworkflowaction_data:
            if '_key' in entry and entry['_key'] != None:
                uri = '/servicesNS/nobody/alert_manager/storage/collections/data/externalworkflow_actions/' + entry['_key']
                logger.debug("uri is {}".format(uri))

                del entry['_key']
                entry = json.dumps(entry)

                serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=entry)
                logger.debug("Updated entry. serverResponse was {}".format(serverResponse))
            else:
                if '_key' in entry:
                    del entry['_key']
                ['' if val is None else val for val in entry]

                uri = '/servicesNS/nobody/alert_manager/storage/collections/data/externalworkflow_actions/'
                logger.debug("uri is {}".format(uri))

                entry = json.dumps(entry)
                logger.debug("entry is {}".format(entry))

                serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=entry)
                logger.debug("Added entry. serverResponse was {}".format(serverResponse))

        return self.response('External Workflow Actions successfully updated', http.client.OK)


    def _get_externalworkflow_actions(self, sessionKey, query_params):
        logger.debug("START _get_externalworkflow_actions()")

        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/externalworkflow_actions?q=output_mode=json'
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='GET')
        logger.debug("externalworkflow_actions: %s" % serverContent.decode('utf-8'))
        entries = json.loads(serverContent.decode('utf-8'))

        externalworkflow_actions = [ ]

        if len(entries) > 0:
            for entry in entries:        
                status = False if ( entry['disabled'] == 0 or entry['disabled'] == "0" or entry['disabled'] == False) else True

                if status == False:
                	ewa = {'_key': entry['_key'], 'label': entry['label'], 'alert_action': entry['alert_action'] }
                	externalworkflow_actions.append(ewa)
        return self.response(externalworkflow_actions, http.client.OK)

    def _get_externalworkflowaction_command(self, sessionKey, query_params):
        """
        Gives back sendalert string based on template
        Takes incident_id and external workflow action as a parameter
        e.g. https://<hostname>/en-US/custom/alert_manager/helpers/get_externalworkflowaction_command?incident_id=<incident_id>&externalworkflowaction=<externalworkflowaction>
        """
        logger.debug("START _get_externalworkflowaction_command()")

        required = ['incident_id', '_key']
        missing = [r for r in required if r not in query_params]
        if missing:
            return self.response("Missing required arguments: {}".format(missing), http.client.BAD_REQUEST)

        incident_id = query_params.get('incident_id')
        _key = query_params.get('_key')
        comment = query_params.get('comment', '')

        # Get incident json
        incident_id_query = '{"incident_id": "' + incident_id + '"}'
        incident_uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents?q=output_mode=json&query=' + urllib.parse.quote_plus(incident_id_query)
        serverResponse, serverContent = rest.simpleRequest(incident_uri, sessionKey=sessionKey, method='GET')
        logger.debug("incident: {}".format(serverContent.decode('utf-8')))
        incident = json.loads(serverContent.decode('utf-8'))

        # Get incident_results
        incident_results_uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_results?q=output_mode=json&query=' + urllib.parse.quote_plus(incident_id_query)
        serverResponse, serverContent = rest.simpleRequest(incident_results_uri, sessionKey=sessionKey, method='GET')
        logger.debug("incident_results: {}".format(serverContent.decode('utf-8')))
        incident_results = json.loads(serverContent.decode('utf-8'))

        # Get externalworkflowaction settings json
        externalworkflowaction_query = '{"_key": "' + _key + '"}'
        externalworkflowaction_uri = '/servicesNS/nobody/alert_manager/storage/collections/data/externalworkflow_actions?q=output_mode=json&query=' + urllib.parse.quote_plus(externalworkflowaction_query)
        serverResponse, serverContent = rest.simpleRequest(externalworkflowaction_uri, sessionKey=sessionKey, method='GET')
        logger.debug("externalworkflow_action: {}".format(serverContent.decode('utf-8')))
        externalworkflow_action = json.loads(serverContent.decode('utf-8'))

        if len(externalworkflow_action) == 1:
            logger.debug("Found correct number of External Workflow Actions. Proceeding...")
            # Extract alert_action from ewf settings
            alert_action = externalworkflow_action[0]['alert_action']
            logger.debug("alert_action: {}".format(alert_action))
            # Create dict for template replacement key/values
            incident_data = {}
            for key in incident[0]:
        	       incident_data[key] = incident[0][key]

            # Append comment to incident_data dict
            incident_data['comment'] = comment  

            # Create dict for results
            if incident_results:
                incident_results=incident_results[0]['fields']
                results = {}
                for key in incident_results[0]:
                    results['result.' + key] = incident_results[0][key]

                # Append results to incident data
                incident_data.update(results)

            logger.debug("incident_data: {}".format(json.dumps(incident_data)))

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
                        idpattern = '[a-zA-Z][_a-zA-Z0-9.]*'

                    # Create template from parameters
                    parameters_template = FieldTemplate(parameters)
                    parameters_substitute = parameters_template.safe_substitute(incident_data)

                    # Empty values for non existing fields
                    parameters_substitute=re.sub('\$[a-zA-Z][_a-zA-Z0-9.]*','', parameters_substitute)
                    logger.debug("Cleaned empty parameters : {}".format(parameters_substitute))

                    # Build command string
                    command = '| sendalert ' + alert_action + ' ' + parameters_substitute
                else:
                    logger.info("No params found in external workflow action, returning 'empty' command...")
                    command = '| sendalert ' + alert_action
            except Exception as e:
                msg = "Unexpected Error: {}".format(traceback.format_exc())
                logger.exception(msg)
                return self.response(msg, http.client.INTERNAL_SERVER_ERROR)

            # Return command
            logger.debug("Returning command '{}'".format(command))
            return {
            'payload': command,
            'status': 200,
            'headers': {
                'Content-Type': 'text/plain'
            }
        }
        else:
            msg = 'Number of return external workflow actions is incorrect. Expected: 1. Given: {}'.format(len(externalworkflow_action))
            logger.exception(msg)
            return self.response(msg, http.client.INTERNAL_SERVER_ERROR)
