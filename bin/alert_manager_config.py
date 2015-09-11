
import splunk.admin as admin
import splunk.entity as entity
    

class AlertHandlerApp(admin.MConfigHandler):
    '''
    Set up supported arguments
    '''
    
    def setup(self):
        if self.requestedAction == admin.ACTION_EDIT:
            for arg in ['index', 'incident_list_length', 'default_owner', 'default_impact', 'default_urgency', 'default_priority', 'user_directories']:
                self.supportedArgs.addOptArg(arg)
        pass

    def handleList(self, confInfo):
        confDict = self.readConf("alert_manager")
        if None != confDict:
            for stanza, settings in confDict.items():
                for key, val in settings.items():
                    #if key in ['save_results']:
                    #    if int(val) == 1:
                    #        val = '1'
                    #    else:
                    #        val = '0'
                    if key in ['index'] and val in [None, '']:
                        val = ''    
                    if key in ['incident_list_length'] and val in [None, '']:
                        val = ''
                    if key in ['default_owner'] and val in [None, '']:
                        val = ''
                    if key in ['default_impact'] and val in [None, '']:
                        val = ''                        
                    if key in ['default_urgency'] and val in [None, '']:
                        val = ''
                    if key in ['default_priority'] and val in [None, '']:
                        val = ''                            
                    if key in ['user_directories'] and val in [None, '']:
                        val = ''

                    confInfo[stanza].append(key, val)

    def handleEdit(self, confInfo):
        name = self.callerArgs.id
        args = self.callerArgs
        
        if self.callerArgs.data['index'][0] in [None, '']:
            self.callerArgs.data['index'][0] = ''
        
        if self.callerArgs.data['incident_list_length'][0] in [None, '']:
            self.callerArgs.data['incident_list_length'][0] = ''   

        if self.callerArgs.data['default_owner'][0] in [None, '']:
            self.callerArgs.data['default_owner'][0] = ''   

        if self.callerArgs.data['default_impact'][0] in [None, '']:
            self.callerArgs.data['default_impact'][0] = ''    

        if self.callerArgs.data['default_urgency'][0] in [None, '']:
            self.callerArgs.data['default_urgency'][0] = ''    

        if self.callerArgs.data['default_priority'][0] in [None, '']:
            self.callerArgs.data['default_priority'][0] = ''

        if self.callerArgs.data['user_directories'][0] in [None, '']:
            self.callerArgs.data['user_directories'][0] = ''

        #if int(self.callerArgs.data['save_results'][0]) == 1:
        #    self.callerArgs.data['save_results'][0] = '1'
        #else:
        #    self.callerArgs.data['save_results'][0] = '0'             
                
        self.writeConf('alert_manager', 'settings', self.callerArgs.data)                        
                    
# initialize the handler
admin.init(AlertHandlerApp, admin.CONTEXT_APP_AND_USER)
