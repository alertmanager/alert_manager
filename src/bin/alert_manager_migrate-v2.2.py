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

    #eh = EventHandler(sessionKey=sessionKey)
    #sh = SuppressionHelper(sessionKey=sessionKey)
    #sessionKey     = urllib.unquote(sessionKey[11:]).decode('utf8')

    log.debug("Alert Manager migration started.")

    # By default, don't disable myself
    disableInput = False

    # Check KV Store availability
    while not am.checkKvStore():
        log.warn("KV Store is not yet available, sleeping for 1s.")
        time.sleep(1)

    #
    # Check if default status exist
    #
    defaultStatusFile = os.path.join(util.get_apps_dir(), 'alert_manager', 'appserver', 'src', 'default_status.json')

    # Get current default notification scheme
    query = { "$or": [{"status":"new"},{"status":"auto_assigned"},{"status":"assigned"},{"status":"work_in_progress"},{"status":"on_hold"},{"status":"escalated_for_analysis"},{"status":"resolved"},{"status":"suppressed"},{"status":"auto_ttl_resolved"},{"status":"auto_previous_resolved"},{"status":"auto_suppress_resolved"},{"status":"auto_subsequent_resolved"},{"status":"false_positive_resolved"}] }
    uri = '/servicesNS/nobody/alert_manager/storage/collections/data/alert_status?query={}'.format(urllib.parse.quote(json.dumps(query)))
    serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)
    try:
        alert_status = json.loads(serverContent)
    except Exception as e:
        alert_status = []

    if len(alert_status) > 0:
        log.info("Some default alert status exist. Nothing to do.")
        disableInput = True
    else:
        log.info("No default alert status exist. Will create them...")

        if os.path.isfile(defaultStatusFile):

            with open (defaultStatusFile, "r") as defaultStatusFileHandle:
                defaultAlertStatus = defaultStatusFileHandle.read().replace('\n', ' ')

                log.debug("defaultAlertStatus: {}".format(defaultAlertStatus))

                uri = '/servicesNS/nobody/alert_manager/storage/collections/data/alert_status/batch_save'
                serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=defaultAlertStatus)
                log.info("Created new default alert status.")
                disableInput = True
        else:
            log.error("Default alert status seed file ({}) doesn't exist, have to stop here.".format(defaultStatusFile))
            disableInput = False

    #
    # Disable myself if migration is done
    #
    if disableInput:
        log.info("Disabling current migration scripted inputs....")
        uri = '/servicesNS/nobody/alert_manager/data/inputs/script/.%252Fbin%252Falert_manager_migrate-v2.2.sh/disable'
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='POST')

        uri = '/servicesNS/nobody/alert_manager/data/inputs/script/.%5Cbin%5Calert_manager_migrate-v2.2.path/disable'
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='POST')

        log.info("Done.")


    end = time.time()
    duration = round((end-start), 3)
    log.info("Alert Manager migration finished. duration={}s".format(duration))