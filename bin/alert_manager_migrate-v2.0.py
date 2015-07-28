import os
import sys
import urllib
import json
import splunk
import splunk.rest as rest
import splunk.input as input
import splunk.entity as entity
import time
import logging
import logging.handlers
import hashlib
import datetime
import socket

import os.path

dir = os.path.join(os.path.join(os.environ.get('SPLUNK_HOME')), 'etc', 'apps', 'alert_manager', 'bin', 'lib')
if not dir in sys.path:
    sys.path.append(dir)

#from EventHandler import *
#from IncidentContext import *
#from SuppressionHelper import *

#sys.stdout = open('/tmp/stdout', 'w')
#sys.stderr = open('/tmp/stderr', 'w')

start = time.time()

# Setup logger
log = logging.getLogger('alert_manager_migration')
fh     = logging.handlers.RotatingFileHandler(os.environ.get('SPLUNK_HOME') + "/var/log/splunk/alert_manager_migration.log", maxBytes=25000000, backupCount=5)
formatter = logging.Formatter("%(asctime)-15s %(levelname)-5s %(message)s")
fh.setFormatter(formatter)
log.addHandler(fh)
log.setLevel(logging.DEBUG)

sessionKey     = sys.stdin.readline().strip()
splunk.setDefault('sessionKey', sessionKey)

#eh = EventHandler(sessionKey=sessionKey)
#sh = SuppressionHelper(sessionKey=sessionKey)
#sessionKey     = urllib.unquote(sessionKey[11:]).decode('utf8')

log.debug("Alert Manager migration started. sessionKey=%s" % sessionKey)

#
# Get global settings
#
config = {}
config['index'] = 'alerts'

restconfig = entity.getEntities('configs/alert_manager', count=-1, sessionKey=sessionKey)
if len(restconfig) > 0:
    if 'index' in restconfig['settings']:
        config['index'] = restconfig['settings']['index']

log.debug("Global settings: %s" % config)

disableInput = False

#
# Check if default email templates exist
#

defaultEmailTemplatesFile = os.path.join(os.path.join(os.environ.get('SPLUNK_HOME')), 'etc', 'apps', 'alert_manager', 'appserver', 'src', 'default_email_templates.json')

# Get current default templates
query = { "$or": [ { "template_name": "default_incident_created" } , { "template_name": "default_incident_assigned" }, { "template_name": "default_incident_suppressed" } ] }
uri = '/servicesNS/nobody/alert_manager/storage/collections/data/email_templates?query=%s' % urllib.quote(json.dumps(query))
serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)
email_templates = json.loads(serverContent)


if len(email_templates) > 0:
    log.info("Some default templates already exist. Nothing to do.")
    disableInput = True
else:
    log.info("No default email templates exist. Will create them...")

    if os.path.isfile(defaultEmailTemplatesFile):

        with open (defaultEmailTemplatesFile, "r") as defaultEmailTemplatesFileHandle:
            defaultEmailTemplates = defaultEmailTemplatesFileHandle.read().replace('\n', ' ')
        
            #defaultEmailTemplates = json.loads(defaultEmailTemplates)

            log.debug("defaultEmailTemplates: %s" % defaultEmailTemplates)

            uri = '/servicesNS/nobody/alert_manager/storage/collections/data/email_templates/batch_save'
            serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=defaultEmailTemplates)
            log.info("Created %s new default email templates." % len(json.loads(defaultEmailTemplates)))
            disableInput = True
    else:
        log.error("Default email templates seed file (%s) doesn't exist, have to stop here." % defaultEmailTemplatesFile)
        disableInput = False


#
# Check if default notification scheme exists
#

defaultNotificationSchemeFile = os.path.join(os.path.join(os.environ.get('SPLUNK_HOME')), 'etc', 'apps', 'alert_manager', 'appserver', 'src', 'default_notification_scheme.json')

# Get current default notification scheme
query = { "$or": [ { "schemeName": "default_notification_scheme" } ] }
uri = '/servicesNS/nobody/alert_manager/storage/collections/data/notification_schemes?query=%s' % urllib.quote(json.dumps(query))
serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)
notification_schemes = json.loads(serverContent)


if len(notification_schemes) > 0:
    log.info("Some default notification schemes exist. Nothing to do.")
    disableInput = True
else:
    log.info("No default notification schemes exist. Will create them...")

    if os.path.isfile(defaultNotificationSchemeFile):

        with open (defaultNotificationSchemeFile, "r") as defaultNotificationSchemeFileHandle:
            defaultNotificationSchemes = defaultNotificationSchemeFileHandle.read().replace('\n', ' ')
        
            log.debug("defaultNotificationSchemes: %s" % defaultNotificationSchemes)

            uri = '/servicesNS/nobody/alert_manager/storage/collections/data/notification_schemes/batch_save'
            serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=defaultNotificationSchemes)
            log.info("Created %s new default notification schemes." % len(json.loads(defaultNotificationSchemes)))
            disableInput = True
    else:
        log.error("Default notification scheme seed file (%s) doesn't exist, have to stop here." % defaultNotificationSchemeFile)
        disableInput = False


# Disable myself if migration is done
if disableInput:
    log.info("Disabling current migration scripted inputs....")
    uri = '/servicesNS/nobody/alert_manager/data/inputs/script/.%252Fbin%252Falert_manager_migrate-v2.0.sh/disable'
    serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='POST')

    uri = '/servicesNS/nobody/alert_manager/data/inputs/script/.%5Cbin%5Calert_manager_migrate-v2.0.path/disable'
    serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='POST')

    log.info("Done.")


end = time.time()
duration = round((end-start), 3)
log.info("Alert Manager migration finished. duration=%ss" % duration)
