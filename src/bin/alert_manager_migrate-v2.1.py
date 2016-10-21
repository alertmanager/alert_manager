import os
import sys
import urllib
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

dir = os.path.join(os.path.join(os.environ.get('SPLUNK_HOME')), 'etc', 'apps', 'alert_manager', 'bin', 'lib')
if not dir in sys.path:
    sys.path.append(dir)

from CsvLookup import *
from AlertManagerLogger import *
from ApiManager import *

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

    log.debug("Alert Manager migration started. sessionKey=%s" % sessionKey)

    # By default, don't disable myself
    disableInput = False

    # Check KV Store availability
    while not am.checkKvStore():
        log.warn("KV Store is not yet available, sleeping for 1s.")
        time.sleep(1)

    #
    # Migrate users
    #
    query = '{ "name": ""}'
    uri = '/servicesNS/nobody/alert_manager/storage/collections/data/alert_users?query=%s' % urllib.quote(query)
    serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)
    try:
        entries = json.loads(serverContent)
    except Exception as e:
        entries = []

    for entry in entries:
        if 'user' in entry and entry['user'] != "":
            log.info("Found user '%s' to migrate." % entry['user'])

            key = entry['_key']
            del(entry['_key'])

            entry['name'] = entry['user']
            del(entry['user'])

            if not 'type' in entry or entry['type'] == "":
                entry['type'] = "alert_manager"

            data = json.dumps(entry)
            uri = '/servicesNS/nobody/alert_manager/storage/collections/data/alert_users/%s' % key
            serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=data)
            log.info("Successfully migrate attributes of user '%s'." % entry['name'])
        else:
            log.warn("User with _key '%s' identified but no proper attributes found, skipping..." % entry['_key'])
    disableInput = True

    #
    # Disable myself if migration is done
    #
    if disableInput:
        log.info("Disabling current migration scripted inputs....")
        uri = '/servicesNS/nobody/alert_manager/data/inputs/script/.%252Fbin%252Falert_manager_migrate-v2.1.sh/disable'
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='POST')

        uri = '/servicesNS/nobody/alert_manager/data/inputs/script/.%5Cbin%5Calert_manager_migrate-v2.1.path/disable'
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, method='POST')

        log.info("Done.")


    end = time.time()
    duration = round((end-start), 3)
    log.info("Alert Manager migration finished. duration=%ss" % duration)
