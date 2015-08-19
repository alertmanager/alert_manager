import sys
import json
import urllib
import splunk.rest as rest

class NotificationScheme:

	sessionKey	= None

	schemeName	= None
	displayName	= None
	notifications	= []

	def __init__(self, sessionKey, schemeName):
		self.sessionKey = sessionKey

		# Retrieve notification scheme from KV store
		query_filter = {}
		query_filter["schemeName"] = schemeName 
		uri = '/servicesNS/nobody/alert_manager/storage/collections/data/notification_schemes/?query=%s' % urllib.quote(json.dumps(query_filter))
		serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)
		
		entries = json.loads(serverContent)

		try:
			scheme = entries[0]

			self.schemeName = scheme["schemeName"]
			self.displayName = scheme["displayName"]
			self.notifications = self.parseNotifications(scheme["notifications"])

		except Exception as e:
			# TODO: Check response, fall back to default notification scheme
			self.notifications = []

	def parseNotifications(self, notifications):
		return notifications


	def getNotifications(self, event):
		notifs = []
		for notification in self.notifications:
			if notification['event'] == event:
				del(notification['event'])
				notifs.append(notification)
		return notifs
