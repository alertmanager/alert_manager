import sys
import os
import logging
import json
import urllib
import splunk.rest as rest
import traceback

# TODO: Custom event handlers
from NotificationHandler import *

class EventHandler:

	# Setup logger
	log = logging.getLogger('alert_manager_eventhandler')
	log.propagate = False
	lf = os.path.join(os.environ.get('SPLUNK_HOME'), "var", "log", "splunk", "alert_manager_eventhandler.log")
	fh     = logging.handlers.RotatingFileHandler(lf, maxBytes=25000000, backupCount=5)
	formatter = logging.Formatter("%(asctime)-15s %(levelname)-5s %(message)s")
	fh.setFormatter(formatter)
	log.addHandler(fh)
	log.setLevel(logging.INFO)

	sessionKey	= None
	nh 			= None

	def __init__(self, sessionKey):
		self.sessionKey	= sessionKey

		self.nh = NotificationHandler(self.sessionKey)

	def handleEvent(self, alert, event, incident, context):
		self.log.info("event=%s from alert=%s incident_id=%s has been fired. Calling custom event handlers." % (event, alert, context.get('incident_id')))
		context.update({ "event" : event })
		try:
			# TODO: Custom event handlers
			self.nh.handleEvent(event, alert, incident, context)

		except Exception as e:
			self.log.error("Error occured during event handling. Error: %s" % (traceback.format_exc()))

		return True

	def setSessionKey(self, sessionKey):
		self.sessionKey = sessionKey
		if self.nh != None:
			self.nh.setSessionKey(sessionKey)

