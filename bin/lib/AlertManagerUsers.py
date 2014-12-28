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


        user_list = []
        # Get splunk users
        if config['user_directories'] == "builtin" or config['user_directories'] == "both":
            uri = '/services/admin/users?output_mode=json'
            serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=self.sessionKey, method='GET')
            entries = json.loads(serverContent)
            
            if len(entries['entry']) > 0:
                for entry in entries['entry']:
                    user = { "name": entry['name'], "email": entry['content']['email'], "type": "builtin" }
                    user_list.append(user)

        if config['user_directories'] == "alert_manager" or config['user_directories'] == "both":
            uri = '/servicesNS/nobody/alert_manager/storage/collections/data/alert_users?output_mode=json'
            serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=self.sessionKey)
            entries = json.loads(serverContent)

            if len(entries) > 0:
                for entry in entries:
                    if "email" not in entry:
                        entry['email'] = ''

                    user = { "name": entry['user'], "email": entry['email'], "type": "alert_manager" }
                    user_list.append(user)            

        return user_list