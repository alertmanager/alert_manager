import logging
import os
import sys
import json
import shutil
import cherrypy
import re
import time
import datetime

#from splunk import AuthorizationFailed as AuthorizationFailed
import splunk.appserver.mrsparkle.controllers as controllers
import splunk.appserver.mrsparkle.lib.util as util
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


sys.stdout = open('/tmp/stdout', 'w')
sys.stderr = open('/tmp/stderr', 'w')    


def setup_logger(level):
    """
    Setup a logger for the REST handler.
    """

    logger = logging.getLogger('splunk.appserver.alert_manager.controllers.AlertSettings')
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



class AlertSettings(controllers.BaseController):

    @expose_page(must_login=True, methods=['GET']) 
    def easter_egg(self, **kwargs):
        return 'Hellow World'

    @expose_page(must_login=True, methods=['POST']) 
    def save(self, contents, **kwargs):
        """
        Save the contents of a lookup file
        """

        logger.info("Saving alert settings contents...")

        user = cherrypy.session['user']['name']
        sessionKey = cherrypy.session.get('sessionKey')
        
        
        # Parse the JSON
        parsed_contents = json.loads(contents)

        logger.debug("Contents: %s" % contents)

        for entry in parsed_contents:
            if '_key' in entry:
                uri = '/servicesNS/nobody/alert_manager/storage/collections/data/alert_settings/' + entry['_key']
                logging.debug("uri is %s" % uri)

                del entry['_key']
                entry = json.dumps(entry)

                serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=entry)
                logging.debug("Updated entry. serverResponse was %s" % serverResponse)
            else:
                uri = '/servicesNS/nobody/alert_manager/storage/collections/data/alert_settings/'
                logging.debug("uri is %s" % uri)

                entry = json.dumps(entry)

                serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=entry)
                logging.debug("Added entry. serverResponse was %s" % serverResponse)

        return 'Data has been saved'

