import urllib.parse
import json
import os
import sys
import splunk.rest as rest

import splunk.appserver.mrsparkle.lib.util as util
dir = os.path.join(util.get_apps_dir(), 'alert_manager', 'bin', 'lib')
if not dir in sys.path:
    sys.path.append(dir)

from AlertManagerLogger import setupLogger

class ApiManager(object):

    log = None
    sessionKey = ''

    def __init__(self, sessionKey):
        self.sessionKey = sessionKey
        self.log = setupLogger('apimanager')

    def checkKvStore(self):
        try:
            query = { }
            uri = '/servicesNS/nobody/alert_manager/storage/collections/data/email_templates?query={}'.format(urllib.parse.quote(json.dumps(query)))
            serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=self.sessionKey)

            if serverResponse['status'] == '503':
                self.log.debug("KVStore unavailable. Response status: {}".format(serverResponse['status']))
                return False
            else:
                self.log.debug("KVStore is available. Response status: {}".format(serverResponse['status']))
                return True
        except Exception as e:
            self.log.debug("KVStore unavailable. Exception: {}".format(str(e)))
            return False
