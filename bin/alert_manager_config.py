
import splunk.admin as admin
import splunk.entity as entity
    

class AlertHandlerApp(admin.MConfigHandler):
    '''
    Set up supported arguments
    '''
    
    def setup(self):
        if self.requestedAction == admin.ACTION_EDIT:
            for arg in ['index', 'default_assignee', 'disable_save_results']:
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
                    if key in ['default_assignee'] and val in [None, '']:
                        val = ''
                    confInfo[stanza].append(key, val)

    def handleEdit(self, confInfo):
        name = self.callerArgs.id
        args = self.callerArgs
        
        if self.callerArgs.data['index'][0] in [None, '']:
            self.callerArgs.data['index'][0] = ''
        
        if self.callerArgs.data['default_assignee'][0] in [None, '']:
            self.callerArgs.data['default_assignee'][0] = ''   

        if int(self.callerArgs.data['disable_save_results'][0]) == 1:
            self.callerArgs.data['disable_save_results'][0] = '0'
        else:
            self.callerArgs.data['disable_save_results'][0] = '1'             
                
        self.writeConf('alert_manager', 'settings', self.callerArgs.data)                        
                    
# initialize the handler
admin.init(AlertHandlerApp, admin.CONTEXT_APP_AND_USER)