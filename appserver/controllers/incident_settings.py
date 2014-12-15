import logging
import os
import sys
import json
import shutil
import cherrypy
import re
import time
import datetime
import urllib
import socket

#from splunk import AuthorizationFailed as AuthorizationFailed
import splunk
import splunk.appserver.mrsparkle.controllers as controllers
import splunk.appserver.mrsparkle.lib.util as util
import splunk.input as input
import splunk.bundle as bundle
import splunk.entity as entity
from splunk.appserver.mrsparkle.lib import jsonresponse
from splunk.appserver.mrsparkle.lib.util import make_splunkhome_path
import splunk.clilib.bundle_paths as bundle_paths
from splunk.util import normalizeBoolean as normBool
from splunk.appserver.mrsparkle.lib.decorators import expose_page
from splunk.appserver.mrsparkle.lib.routes import route
import splunk.rest as rest

dir = os.path.join(util.get_apps_dir(), __file__.split('.')[-2], 'bin')

if not dir in sys.path:
    sys.path.append(dir)


#sys.stdout = open('/tmp/stdout', 'w')
#sys.stderr = open('/tmp/stderr', 'w')    


def setup_logger(level):
    """
    Setup a logger for the REST handler.
    """

    logger = logging.getLogger('splunk.appserver.alert_manager.controllers.IncidentSettings')
    logger.propagate = False # Prevent the log messages from being duplicated in the python.log file
    logger.setLevel(level)

    file_handler = logging.handlers.RotatingFileHandler(make_splunkhome_path(['var', 'log', 'splunk', 'alert_manager_settings_controller.log']), maxBytes=25000000, backupCount=5)

    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

logger = setup_logger(logging.DEBUG)

from splunk.models.base import SplunkAppObjModel
from splunk.models.field import BoolField, Field



class IncidentSettings(controllers.BaseController):

    @expose_page(must_login=True, methods=['POST']) 
    def save(self, contents, **kwargs):
        """
        Save the contents of a lookup file
        """

        logger.info("Saving incident settings contents...")

        user = cherrypy.session['user']['name']
        sessionKey = cherrypy.session.get('sessionKey')
        splunk.setDefault('sessionKey', sessionKey)
        
        #
        # Get global settings
        #
        config = {}
        config['index'] = 'alerts'
        
        restconfig = entity.getEntities('configs/alert_manager', count=-1, sessionKey=sessionKey)
        if len(restconfig) > 0:
            if 'index' in restconfig['settings']:
                config['index'] = restconfig['settings']['index']

        logger.debug("Global settings: %s" % config)

        # Parse the JSON
        contents = json.loads(contents)

        logger.debug("Contents: %s" % json.dumps(contents))

        # Get key
        query = {}
        query['job_id'] = contents['job_id']
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
        for key in incident[0].keys():
            if (key in contents) and (incident[0][key] != contents[key]):
                logger.info("%s for incident %s changed. Writing change event to index %s." % (key, incident[0]['job_id'], config['index']))
                event = 'time=%s severity=INFO user="%s" action="change" job_id="%s" attribute="%s" old_value="%s" new_value="%s"' % (now, user, incident[0]['job_id'], key, incident[0][key], contents[key])
                logger.debug("Event will be: %s" % event)
                input.submit(event, hostname = socket.gethostname(), sourcetype = 'incident_change', source = 'incident_settings.py', index = config['index'])
                incident[0][key] = contents[key]
            else:
                logger.info("%s for incident %s didn't change." % (key, incident[0]['job_id']))

        del incident[0]['_key']
        contentsStr = json.dumps(incident[0])
        logger.debug("content for update: %s" % contentsStr)
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=contentsStr)
        logger.debug("Response from update incident entry was %s " % serverResponse)


        return 'Data has been saved'

