import json
import urllib
import splunk.rest as rest

class NotificationScheme:

	sessionKey	= None

	schemeName	= None
	displayName	= None
	notifications = None

	def __init__(self, sessionKey, schemeName, currentAssignee=None):
		self.sessionKey = sessionKey

		# Retrieve notification scheme from KV store
		schemeFilter = {}
		schemeFilter["schemeName"] = schemeName 
		uri = '/servicesNS/nobody/alert_manager/storage/collections/data/notification_schemes/?query=%s' % urllib.quote(json.dumps(schemeFilter))
		schemeFilter = json.dumps(schemeFilter)
		serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)
		# TODO: Check response, fall back to default notification scheme
		entries = json.loads(serverContent)
		scheme = entries[0]

		self.schemeName = scheme["schemeName"]
		self.displayName = scheme["displayName"]
		self.notifications = self.parseNotifications(scheme["notifications"])


	def parseNotifications(self, notifications):
		return notifications
