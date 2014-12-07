
import splunk.admin as admin
import splunk.entity as entity
    

class AlertHandlerApp(admin.MConfigHandler):
    '''
    Set up supported arguments
    '''
    
    def setup(self):
        #if self.requestedAction == admin.ACTION_EDIT:
        #    for arg in ['field_1', 'field_2_boolean', 'field_3']:
        #        self.supportedArgs.addOptArg(arg)
        pass

    def handleList(self, confInfo):
        confDict = self.readConfCtx('alert_manager')
        if confDict != None:
            for stanza, settings in confDict.items():
                for key, value in settings.items():
                    if key != 'eai:acl':
                        confInfo[stanza].append(key, str(value))
                    else:
                        confInfo[stanza].setMetadata(key, value)
                    
# initialize the handler
admin.init(AlertHandlerApp, admin.CONTEXT_APP_AND_USER)