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

dir = os.path.join(util.get_apps_dir(), 'alert_manager', 'bin', 'lib')
if not dir in sys.path:
    sys.path.append(dir)    

from AlertManagerLogger import *

logger = setupLogger('controllers')

from splunk.models.base import SplunkAppObjModel
from splunk.models.field import BoolField, Field



class IncidentSettings(controllers.BaseController):

    @expose_page(must_login=True, methods=['GET']) 
    def easter_egg(self, **kwargs):
        return 'Hellow World'

    @expose_page(must_login=True, methods=['POST']) 
    def delete(self, key, **kwargs):
        logger.info("Removing incident settings contents for %s..." % key)

        user = cherrypy.session['user']['name']
        sessionKey = cherrypy.session.get('sessionKey')

        query = {}
        query['_key'] = key
        logger.debug("Query for incident settings: %s" % urllib.quote(json.dumps(query)))
        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_settings?query=%s' % urllib.quote(json.dumps(query))
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='DELETE')

        logger.debug("Entry removed. serverResponse was %s" % serverResponse)        

        return 'Incident settings have been removed for entry with _key=%s' % key


    @expose_page(must_login=True, methods=['POST']) 
    def save(self, contents, **kwargs):

        logger.info("Saving incident settings contents...")

        user = cherrypy.session['user']['name']
        sessionKey = cherrypy.session.get('sessionKey')
        
        
        # Parse the JSON
        parsed_contents = json.loads(contents)

        logger.debug("Contents: %s" % contents)

        for entry in parsed_contents:
            if '_key' in entry and entry['_key'] != None:
                uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_settings/' + entry['_key']
                logger.debug("uri is %s" % uri)

                del entry['_key']
                entry = json.dumps(entry)

                serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=entry)
                logger.debug("Updated entry. serverResponse was %s" % serverResponse)
            else:
                if '_key' in entry:
                    del entry['_key']
                ['' if val is None else val for val in entry]

                uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_settings/'
                logger.debug("uri is %s" % uri)

                entry = json.dumps(entry)
                logger.debug("entry is %s" % entry)

                serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=entry)
                logger.debug("Added entry. serverResponse was %s" % serverResponse)

        return 'Data has been saved'

