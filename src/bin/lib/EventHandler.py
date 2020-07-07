import sys
import os
import logging
import json
import urllib
import splunk.rest as rest
import traceback

# TODO: Custom event handlers
from NotificationHandler import NotificationHandler
from AlertManagerLogger import setupLogger

class EventHandler(object):

	# Setup logger
	log = setupLogger('eventhandler')

	sessionKey	= None
	nh 			= None

	def __init__(self, sessionKey):
		self.sessionKey	= sessionKey

		self.nh = NotificationHandler(self.sessionKey)

	def handleEvent(self, alert, event, incident, context):
		self.log.info("event={} from alert={} incident_id={} has been fired. Calling custom event handlers.".format(event, alert, context.get('incident_id')))
		context.update({ "event" : event })
		try:
			# TODO: Custom event handlers
			self.nh.handleEvent(event, alert, incident, context)

		except Exception as e:
			self.log.error("Error occured during event handling. Error: {}".format(traceback.format_exc()))

		return True

	def setSessionKey(self, sessionKey):
		self.sessionKey = sessionKey
		if self.nh != None:
			self.nh.setSessionKey(sessionKey)
