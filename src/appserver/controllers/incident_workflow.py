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
import hashlib

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

dir = os.path.join(util.get_apps_dir(), 'alert_manager', 'bin', 'lib')
if not dir in sys.path:
    sys.path.append(dir)  

from EventHandler import *
from IncidentContext import *
from AlertManagerLogger import *

logger = setupLogger('controllers')

from splunk.models.base import SplunkAppObjModel
from splunk.models.field import BoolField, Field

class IncidentWorkflow(controllers.BaseController):

    eh = None

    @expose_page(must_login=True, methods=['POST']) 
    def save(self, contents, **kwargs):


        logger.info("Saving incident settings contents...")

        user = cherrypy.session['user']['name']
        sessionKey = cherrypy.session.get('sessionKey')
        splunk.setDefault('sessionKey', sessionKey)

        eh = EventHandler(sessionKey = sessionKey)

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
        query['incident_id'] = contents['incident_id']
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
            if (key in contents) and (incident[0][key] != contents[key]):
                changed_keys.append(key)
                logger.info("%s for incident %s changed. Writing change event to index %s." % (key, incident[0]['incident_id'], config['index']))
                event_id = hashlib.md5(incident[0]['incident_id'] + now).hexdigest()
                event = 'time=%s severity=INFO origin="incident_posture" event_id="%s" user="%s" action="change" incident_id="%s" %s="%s" previous_%s="%s"' % (now, event_id, user, incident[0]['incident_id'], key, contents[key], key, incident[0][key])
                logger.debug("Change event will be: %s" % event)
                input.submit(event, hostname = socket.gethostname(), sourcetype = 'incident_change', source = 'incident_settings.py', index = config['index'])
                incident[0][key] = contents[key]

            else:
                logger.info("%s for incident %s didn't change." % (key, incident[0]['incident_id']))

        del incident[0]['_key']
        contentsStr = json.dumps(incident[0])
        logger.debug("content for update: %s" % contentsStr)
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=contentsStr)

        logger.debug("Response from update incident entry was %s " % serverResponse)
        logger.debug("Changed keys: %s" % changed_keys)

        if len(changed_keys) > 0:
            ic = IncidentContext(sessionKey, contents['incident_id'])
            if "owner" in changed_keys:
                eh.handleEvent(alert=incident[0]["alert"], event="incident_assigned", incident=incident[0], context=ic.getContext())
            elif "status" in changed_keys and contents["status"] == "resolved":
                eh.handleEvent(alert=incident[0]["alert"], event="incident_resolved", incident=incident[0], context=ic.getContext())
            else:
                eh.handleEvent(alert=incident[0]["alert"], event="incident_changed", incident=incident[0], context=ic.getContext())
        
        if contents['comment'] != "":
            contents['comment'] = contents['comment'].replace('\n', '<br />').replace('\r', '')
            event_id = hashlib.md5(incident[0]['incident_id'] + now).hexdigest()
            event = 'time=%s severity=INFO origin="incident_posture" event_id="%s" user="%s" action="comment" incident_id="%s" comment="%s"' % (now, event_id, user, incident[0]['incident_id'], contents['comment'])
            logger.debug("Comment event will be: %s" % event)
            event = event.encode('utf8')
            input.submit(event, hostname = socket.gethostname(), sourcetype = 'incident_change', source = 'incident_settings.py', index = config['index'])
        
        
        return 'Done'

