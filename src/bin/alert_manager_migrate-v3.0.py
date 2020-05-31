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
import datetime
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

if __name__ == "__main__":
    start = time.time()

    # Setup logger
    log = setupLogger('migration')

    sessionKey     = sys.stdin.readline().strip()
    splunk.setDefault('sessionKey', sessionKey)

    # Setup ApiManager
    am = ApiManager(sessionKey = sessionKey)

    log.debug("Alert Manager migration started.")

    # By default, don't disable myself
    disableInput = False

    # Check KV Store availability
    while not am.checkKvStore():
        log.warn("KV Store is not yet available, sleeping for 1s.")
        time.sleep(1)

    # Remove old application icons if they exist
    
    app_logo = os.path.join(util.get_apps_dir(), 'alert_manager', 'static', 'appLogo.png')
    app_logo2x = os.path.join(util.get_apps_dir(), 'alert_manager', 'static', 'appLogo_2x.png')

    if os.path.exists(app_logo):
        os.remove(app_logo)
        log.debug("appLogo.png removed")

    else:
        log.debug("appLogo.png not found")


    if os.path.exists(app_logo2x):
        os.remove(app_logo2x)
        log.debug("appLogo_2x.png removed")

    else:
        log.debug("appLogo_2x.png not found")

    # Clean up all alert states, Check if default status exist
    #

    # Get current default states
    uri = '/servicesNS/nobody/alert_manager/storage/collections/data/alert_status'
    serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)

    try:
        alert_status = json.loads(serverContent)
    except Exception as e:
        alert_status = []

    if len(alert_status) > 0:
        log.info("Some default alert status exist. Checking....")
        log.debug("alert_status: {}".format(alert_status))
        
        query = { "$or": [{"status":"new"},{"status":"auto_assigned"},{"status":"assigned"},{"status":"work_in_progress"},{"status":"on_hold"},{"status":"escalated_for_analysis"},{"status":"resolved"},{"status":"suppressed"},{"status":"auto_ttl_resolved"},{"status":"auto_previous_resolved"},{"status":"auto_suppress_resolved"},{"status":"auto_subsequent_resolved"},{"status":"false_positive_resolved"},{"status":"auto_info_resolved"},{"status":"closed"}] }
        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/alert_status?query={}'.format(urllib.parse.quote(json.dumps(query)))
        
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='DELETE')
        try:
            alert_status = json.loads(serverContent)

        except Exception as e:
            alert_status = []

        log.debug("serverContent: {}".format(serverContent))
        log.debug("serverResponse: {}".format(serverResponse))

        # Check for custom alert status
        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/alert_status'
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)
        custom_alert_statuses = json.loads(serverContent)
        log.debug("custom_alert_statuses: {}".format(custom_alert_statuses))

        log.info("Creating default alert status")
        defaultStatusFile = os.path.join(util.get_apps_dir(), 'alert_manager', 'appserver', 'src', 'default_status.json')

        if os.path.isfile(defaultStatusFile):

            with open (defaultStatusFile, "r") as defaultStatusFileHandle:
                defaultAlertStatus = defaultStatusFileHandle.read().replace('\n', ' ')
                log.debug("defaultAlertStatus: {}".format(defaultAlertStatus))

                uri = '/servicesNS/nobody/alert_manager/storage/collections/data/alert_status/batch_save'
                serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=defaultAlertStatus)
                log.info("Created new default alert status.")

                # Re-adding custom alert statuses
                for custom_alert_status in custom_alert_statuses:
                    status = custom_alert_status.get("status")
                    status_description = custom_alert_status.get("status_description")
                    status_hidden = custom_alert_status.get("hidden", 0)
                    status_key = custom_alert_status.get("_key")

                    log.debug("Removing custom_alert_status: {}".format(status))

                    uri = '/servicesNS/nobody/alert_manager/storage/collections/data/alert_status/{}'.format(status_key)
                    serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='DELETE')

                    custom_alert_status = '''[{{"status": "{}", "status_description": "{}", "internal_only": 0, "builtin": 0, "hidden": "{}"}}]'''.format(status, status_description, status_hidden)

                    log.info("Recreate custom_alert_status: {}".format(custom_alert_status))

                    uri = '/servicesNS/nobody/alert_manager/storage/collections/data/alert_status/batch_save'
                    serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=custom_alert_status)
                    log.debug("serverContent: {}".format(serverContent))
                    log.debug("serverResponse: {}".format(serverResponse))
                    log.info("Recreated custom alert statuses.")

                disableInput = True
        else:
            log.error("Default alert status seed file ({}) doesn't exist, have to stop here.".format(defaultStatusFile))
            disableInput = False
            sys.exit()   


    disableInput = True

    #
    # Disable myself if migration is done
    #
    if disableInput:
        log.info("Disabling current migration scripted inputs....")
        uri = '/servicesNS/nobody/alert_manager/data/inputs/script/.%252Fbin%252Falert_manager_migrate-v3.0.sh/disable'
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='POST')

        uri = '/servicesNS/nobody/alert_manager/data/inputs/script/.%5Cbin%5Calert_manager_migrate-v3.0.path/disable'
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='POST')

        log.info("Done.")


    end = time.time()
    duration = round((end-start), 3)
    log.info("Alert Manager migration finished. duration={}s".format(duration))