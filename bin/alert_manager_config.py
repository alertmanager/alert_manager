
import splunk.admin as admin
import splunk.entity as entity
    

class AlertHandlerApp(admin.MConfigHandler):
    '''
    Set up supported arguments
    '''
    
    def setup(self):
        if self.requestedAction == admin.ACTION_EDIT:
            for arg in ['index', 'default_owner', 'default_priority', 'disable_save_results', 'user_directiories']:
                self.supportedArgs.addOptArg(arg)
        pass

    def handleList(self, confInfo):
        confDict = self.readConf("alert_manager")
        if None != confDict:
            for stanza, settings in confDict.items():
                for key, val in settings.items():
                    if key in ['disable_save_results']:
                        if int(val) == 1:
                            val = '0'
                        else:
                            val = '1'
                    if key in ['index'] and val in [None, '']:
                        val = ''                            
                    if key in ['default_owner'] and val in [None, '']:
                        val = ''
                    if key in ['default_priority'] and val in [None, '']:
                        val = ''    
                    if key in ['user_directiories'] and val in [None, '']:
                        val = ''

                    confInfo[stanza].append(key, val)

    def handleEdit(self, confInfo):
        name = self.callerArgs.id
        args = self.callerArgs
        
        if self.callerArgs.data['index'][0] in [None, '']:
            self.callerArgs.data['index'][0] = ''
        
        if self.callerArgs.data['default_owner'][0] in [None, '']:
            self.callerArgs.data['default_owner'][0] = ''   

        if self.callerArgs.data['default_priority'][0] in [None, '']:
            self.callerArgs.data['default_priority'][0] = ''    

        if self.callerArgs.data['user_directiories'][0] in [None, '']:
            self.callerArgs.data['user_directiories'][0] = ''

        if int(self.callerArgs.data['disable_save_results'][0]) == 1:
            self.callerArgs.data['disable_save_results'][0] = '0'
        else:
            self.callerArgs.data['disable_save_results'][0] = '1'             
                
        self.writeConf('alert_manager', 'settings', self.callerArgs.data)                        
                    
# initialize the handler
admin.init(AlertHandlerApp, admin.CONTEXT_APP_AND_USER)
