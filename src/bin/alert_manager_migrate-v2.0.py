import os
import sys
import urllib
import urllib.parse
import json
import splunk
import splunk.rest as rest
import splunk.input as input
import splunk.entity as entity
import splunk
import time
import logging
import logging.handlers
import hashlib
import socket
import re
import os.path

import splunk.appserver.mrsparkle.lib.util as util
dir = os.path.join(util.get_apps_dir(), 'alert_manager', 'bin', 'lib')
if not dir in sys.path:
    sys.path.append(dir)

from CsvLookup import CsvLookup
from ApiManager import ApiManager

from AlertManagerLogger import setupLogger

# Helpers
def normalize_bool(value):
    if value == True:
        return True
    elif value == False:
        return False
    else:
        return True if value.lower() in ('1', 'true') else False

def getLookupFile(lookup_name, sessionKey):
    try:
        uri = '/servicesNS/nobody/alert_manager/data/transforms/lookups/{}?output_mode=json'.format(lookup_name)
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)
        lookup = json.loads(serverContent)
        log.debug("Got lookup content for lookup={}. filename={} app={}".format(lookup_name, lookup["entry"][0]["content"]["filename"], lookup["entry"][0]["acl"]["app"]))
        return os.path.join(util.get_apps_dir(), lookup["entry"][0]["acl"]["app"], 'lookups', lookup["entry"][0]["content"]["filename"])
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        log.warn("Unable to get lookup {}. Reason: {}. Line: {}".format(lookup_name, exc_type, exc_tb.tb_lineno))
        return ""

def getImpact(severity, sessionKey):
    try:
        csv_path = getLookupFile('alert_impact', sessionKey)

        if os.path.exists(csv_path):
            log.debug("Lookup file {} found. Proceeding...".format(csv_path))
            lookup = CsvLookup(csv_path)
            query = { "severity_id": str(severity) }
            log.debug("Querying lookup with filter={}".format(query))
            matches = lookup.lookup(query, { "impact" })
            if len(matches) > 0:
                log.debug("Matched impact in lookup, returning value={}".format(matches["impact"]))
                return matches["impact"]
            else:
                log.debug("No matching impact found in lookup, falling back to default_impact={}".format(config['default_impact']))
        else:
            log.warn("Lookup file {} not found. Falling back to default_impact={}".format(csv_path, config['default_impact']))

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        log.warn("Unable to get impact. Falling back to default_impact={}. Error: {}. Line: {}".format(config['default_impact'], exc_type, exc_tb.tb_lineno))
        return config['default_impact']

if __name__ == "__main__":
    start = time.time()

    # Setup logger
    log = setupLogger('migration')

    sessionKey     = sys.stdin.readline().strip()
    splunk.setDefault('sessionKey', sessionKey)

    # Setup ApiManager
    am = ApiManager(sessionKey = sessionKey)

    #eh = EventHandler(sessionKey=sessionKey)
    #sh = SuppressionHelper(sessionKey=sessionKey)
    #sessionKey     = urllib.unquote(sessionKey[11:]).decode('utf8')

    log.debug("Alert Manager migration started.")

    #
    # Get global settings
    #
    config = {}
    config['index'] = 'main'
    config['default_impact'] = 'low'

    restconfig = entity.getEntities('configs/alert_manager', count=-1, sessionKey=sessionKey)
    if len(restconfig) > 0:
        if 'index' in restconfig['settings']:
            config['index'] = restconfig['settings']['index']

    log.debug("Global settings: {}".format(config))

    # By default, don't disable myself
    disableInput = False

    # Check KV Store availability
    while not am.checkKvStore():
        log.warn("KV Store is not yet available, sleeping for 1s.")
        time.sleep(1)

    #
    # Migrate Incident Settings to Custom Alert Action
    #
    uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_settings'
    serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)
    try:
        incident_settings = json.loads(serverContent)
    except Exception as e:
        incident_settings = []

    if len(incident_settings) > 0:
        log.info("Found {} alerts to migrate. Starting...".format(len(incident_settings)))

        for incSet in incident_settings:
            uri = '/servicesNS/-/-/saved/searches/{}?output_mode=json'.format(urllib.parse.quote(incSet['alert'].encode('utf8')))
            serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)
            alert = json.loads(serverContent)

            if 'entry' in alert and len(alert['entry']) > 0:
                for entry in alert['entry']:
                    if 'content' in entry and 'alert.severity' in entry['content']:
                        sharing = entry['acl']['sharing']
                        app = entry['acl']['app']
                        owner = entry['acl']['owner']
                        severity = entry['content']['alert.severity']

                        if sharing != 'user':
                            log.info("Savedsearch '{}' in scope '{}' and app '{}' of owner '{}' is valid for alert manager, migrating...".format(incSet['alert'], sharing, app, owner))
                            log.debug("Parsed settings from existing savedsearch: app={} owner={} severity={}".format(app, owner, severity))
                            log.debug("Incident setting: {}".format(json.dumps(incSet)))

                            # enable alert action
                            content = {}
                            content.update({ 'action.alert_manager': 1})

                            #fields_list = _key, alert, title, category, subcategory, tags, urgency, display_fields, run_alert_script, alert_script, auto_assign_owner, auto_assign, auto_ttl_resolve, auto_previous_resolve, auto_suppress_resolve, notification_scheme

                            # title
                            if 'title' in incSet and incSet['title'] != "":
                                title = re.sub('{{\s?','$', incSet['title'])
                                title = re.sub('\s?}}','$', title)
                                title = re.sub('result\.0\.','result.', title)

                                content.update({ 'action.alert_manager.param.title': title })

                            # urgency
                            if 'urgency' in incSet and incSet['urgency'] != "":
                                content.update({ 'action.alert_manager.param.urgency': incSet['urgency'] })

                            # impact (to be read from saved searches)
                            content.update({ 'action.alert_manager.param.impact': getImpact(severity, sessionKey) })

                            # auto_assign_owner
                            if 'auto_assign_owner' in incSet and 'auto_assign' in incSet and incSet['auto_assign_owner'] != "" and normalize_bool(incSet['auto_assign']):
                                content.update({ 'action.alert_manager.param.auto_assign_owner': incSet['auto_assign_owner'] })

                            # auto_previous_resolve
                            if 'auto_previous_resolve' in incSet and incSet['auto_previous_resolve'] != "" and normalize_bool(incSet['auto_previous_resolve']):
                                content.update({ 'action.alert_manager.param.auto_previous_resolve': incSet['auto_previous_resolve'] })

                            # auto_ttl_resolve
                            if 'auto_ttl_resolve' in incSet and incSet['auto_ttl_resolve'] != "" and normalize_bool(incSet['auto_ttl_resolve']):
                                content.update({ 'action.alert_manager.param.auto_ttl_resolve': incSet['auto_ttl_resolve'] })

                            # auto_suppress_resolve
                            if 'auto_suppress_resolve' in incSet and incSet['auto_suppress_resolve'] != "" and normalize_bool(incSet['auto_suppress_resolve']):
                                content.update({ 'action.alert_manager.param.auto_suppress_resolve': incSet['auto_suppress_resolve'] })

                            # remove legacy script action
                            content.update({ 'action.script': 0 })
                            content.update({ 'action.script.filename': '' })

                            log.debug("Settings to update saved search with: {}".format(json.dumps(content)))

                            try:
                                uri = '/servicesNS/nobody/{}/configs/conf-savedsearches/{}'.format(app, urllib.parse.quote(incSet['alert'].encode('utf8')))
                                serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, postargs=content, method='POST')

                                log.debug("Update response status: {}".format(serverResponse['status']))
                                #log.debug("Update content: {}".format(serverContent))
                                log.info("Updated saved search '{}', proceeding...".format(incSet['alert']))

                            except splunk.ResourceNotFound:
                                log.warn("Didn't find savedsearch '{}' in system. May be this is an old alert?! Shall be removed from incident settings...".format(incSet['alert']))

                            except:
                                log.error("Unexpected error")
                                raise
                        else:
                            log.warn("Savedsearch '{}' in scope '{}' and app '{}' of owner '{}' isn't valid for alert manager, ignoring...".format(incSet['alert'], sharing, app, owner))
            else:
                log.error("Something wen't wrong fetching settings from savedsearch '{}'. Reponse: {}".format(incSet['alert'], serverResponse))


    else:
        log.warn("No incident settings found . Seems that the Alert Manager wasn't in use... Whaaat?!?")

    #
    # Check if default email templates exist
    #
    defaultEmailTemplatesFile = os.path.join(util.get_apps_dir(), 'alert_manager', 'appserver', 'src', 'default_email_templates.json')

    # Get current default templates
    query = { "$or": [ { "template_name": "default_incident_created" } , { "template_name": "default_incident_assigned" }, { "template_name": "default_incident_suppressed" } ] }
    uri = '/servicesNS/nobody/alert_manager/storage/collections/data/email_templates?query={}'.format(urllib.parse.quote(json.dumps(query)))
    serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)
    try:
        email_templates = json.loads(serverContent)
    except Exception as e:
        email_templates = []

    if len(email_templates) > 0:
        log.info("Found some default email templates, will re-create them...")

        for template in email_templates:
            uri = '/servicesNS/nobody/alert_manager/storage/collections/data/email_templates/{}'.format(template['_key'])
            serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='DELETE')

        log.debug("Done removing pre-existing default templates.")


    log.info("Creating new default email templates...")
    if os.path.isfile(defaultEmailTemplatesFile):

        with open (defaultEmailTemplatesFile, "r") as defaultEmailTemplatesFileHandle:
            defaultEmailTemplates = defaultEmailTemplatesFileHandle.read().replace('\n', ' ')

            #defaultEmailTemplates = json.loads(defaultEmailTemplates)

            log.debug("defaultEmailTemplates: {}".format(defaultEmailTemplates))

            uri = '/servicesNS/nobody/alert_manager/storage/collections/data/email_templates/batch_save'
            serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=defaultEmailTemplates)
            log.debug("serverResponse: {}".format(serverResponse))
            log.debug("serverContent: {}".format(serverContent))
            log.info("Created {} new default email templates.".format(len(json.loads(defaultEmailTemplates))))
            disableInput = True
    else:
        log.error("Default email templates seed file ({}) doesn't exist, have to stop here.".format(defaultEmailTemplatesFile))
        disableInput = False


    #
    # Check if default notification scheme exists
    #
    defaultNotificationSchemeFile = os.path.join(util.get_apps_dir(), 'alert_manager', 'appserver', 'src', 'default_notification_scheme.json')

    # Get current default notification scheme
    query = { "$or": [ { "schemeName": "default_notification_scheme" } ] }
    uri = '/servicesNS/nobody/alert_manager/storage/collections/data/notification_schemes?query={}'.format(urllib.parse.quote(json.dumps(query)))
    serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)
    try:
        notification_schemes = json.loads(serverContent)
    except Exception as e:
        notification_schemes = []

    if len(notification_schemes) > 0:
        log.info("Some default notification schemes exist. Nothing to do.")
        disableInput = True
    else:
        log.info("No default notification schemes exist. Will create them...")

        if os.path.isfile(defaultNotificationSchemeFile):

            with open (defaultNotificationSchemeFile, "r") as defaultNotificationSchemeFileHandle:
                defaultNotificationSchemes = defaultNotificationSchemeFileHandle.read().replace('\n', ' ')

                log.debug("defaultNotificationSchemes: {}".format(defaultNotificationSchemes))

                uri = '/servicesNS/nobody/alert_manager/storage/collections/data/notification_schemes/batch_save'
                serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=defaultNotificationSchemes)
                log.info("Created new default notification schemes.")
                disableInput = True
        else:
            log.error("Default notification scheme seed file ({}) doesn't exist, have to stop here.".format(defaultNotificationSchemeFile))
            disableInput = False

    #
    # Disable myself if migration is done
    #
    if disableInput:
        log.info("Disabling current migration scripted inputs....")
        uri = '/servicesNS/nobody/alert_manager/data/inputs/script/.%252Fbin%252Falert_manager_migrate-v2.0.sh/disable'
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='POST')

        uri = '/servicesNS/nobody/alert_manager/data/inputs/script/.%5Cbin%5Calert_manager_migrate-v2.0.path/disable'
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='POST')

        log.info("Done.")


    end = time.time()
    duration = round((end-start), 3)
    log.info("Alert Manager migration finished. duration={}s".format(duration))
