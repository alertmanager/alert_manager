import json
import splunk.entity as entity
import splunk.rest as rest

class AlertManagerUsers:
    sessionKey = None

    def __init__(self, sessionKey):
        self.sessionKey = sessionKey

    def getUserList(self):
        
        # Get alert manager config
        config = {}
        config['user_directories'] = 'both'

        restconfig = entity.getEntities('configs/alert_manager', count=-1, sessionKey=self.sessionKey)
        if len(restconfig) > 0:
            for cfg in config.keys():
                if cfg in restconfig['settings']:
                    config[cfg] = restconfig['settings'][cfg]


        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/alert_users?output_mode=json'
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=self.sessionKey)
        entries = json.loads(serverContent)

        user_list = []
        if config['user_directories'] == "builtin" or config['user_directories'] == "both":
            if len(entries) > 0:
                for entry in entries:
                    if 'type' in entry and entry['type'] == "builtin":
                        if 'user' in entry:
                            del(entry['user'])
                        if '_user' in entry:
                            del(entry['_user'])                        
                        if '_key' in entry:
                            del(entry['_key'])
                        user_list.append(entry)

        if config['user_directories'] == "alert_manager" or config['user_directories'] == "both":
            if len(entries) > 0:
                for entry in entries:
                    if 'type' not in entry or entry['type'] == "alert_manager":
                        if 'user' in entry:
                            del(entry['user'])
                        if '_user' in entry:
                            del(entry['_user'])                        
                        if '_key' in entry:
                            del(entry['_key'])
                        user_list.append(entry)          

        return user_list

    def getUser(self, name):
        user_list = self.getUserList()
        retval = {}
        for user in user_list:
            if user['name'] == name:
                retval = user

        return retval