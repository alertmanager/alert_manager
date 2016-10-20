import json
import urllib
import splunk.rest as rest
import sys
import traceback

from AlertManagerLogger import *

class IncidentContext():

	log = setupLogger('incidentcontext')

	sessionKey = None
	context = { }

	incident = {}

	def __init__(self, sessionKey, incident_id):
		self.sessionKey = sessionKey

		query = {}
		query['incident_id'] = incident_id

		uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents?query=%s' % urllib.quote(json.dumps(query))
		serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)
		incident = json.loads(serverContent)
		incident = incident[0]

		query_incident_settings = {}
		query_incident_settings['alert'] = incident["alert"]
		uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_settings?query=%s' % urllib.quote(json.dumps(query_incident_settings))
		serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)
		incident_settings = json.loads(serverContent)
		if len(incident_settings) > 0:
			incident_settings = incident_settings[0]

		uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_results?query=%s' % urllib.quote(json.dumps(query))
		serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)
		results = json.loads(serverContent)
		if len(results) > 0:
			results = results[0]

		uri = '/services/server/settings?output_mode=json'
		serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)
		server_settings = json.loads(serverContent)
		if len(server_settings) > 0:
			server_settings = server_settings["entry"][0]["content"]

		uri = '/services/server/info?output_mode=json'
		serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)
		server_info = json.loads(serverContent)
		if len(server_info) > 0:
			server_info = server_info["entry"][0]["content"]

		self.setContext(incident, incident_settings, results, server_info, server_settings)

	def setContext(self, incident, incident_settings, results, server_info, server_settings):
		context = self.context
		try:
			http_port = "8000"
			if 'httpport' in server_settings:
				http_port = str(server_settings['httpport'])

			protocol = 'http'			
			if 'enableSplunkWebSSL' in server_settings and self.normalize_bool(str(server_settings['enableSplunkWebSSL'])):
				protocol = 'https'

			context.update({ "_key": incident['_key']})
			context.update({ "incident_id": incident['incident_id']})
			context.update({ "job_id": incident['job_id']})
			context.update({ "title": incident['title']})
			context.update({ "alert_time" : incident["alert_time"] })
			context.update({ "owner" : incident["owner"] })
			context.update({ "name" : incident["alert"] })
			context.update({ "alert" : { "impact": incident["impact"], "urgency": incident["urgency"], "priority": incident["priority"], "expires": incident["ttl"] } })
			context.update({ "app" : incident["app"] })
			context.update({ "category" : incident_settings['category'] })
			context.update({ "subcategory" : incident_settings['subcategory'] })
			context.update({ "tags" : incident_settings['tags'] })
			context.update({ "results_link" : protocol + "://"+server_info["host_fqdn"] + ":"+ http_port +"/app/" + incident["app"] + "/@go?sid=" + incident["job_id"] })
			context.update({ "view_link" : protocol + "://"+server_info["host_fqdn"] + ":" + http_port + "/app/" + incident["app"] + "/alert?s=" + urllib.quote("/servicesNS/nobody/"+incident["app"]+"/saved/searches/" + incident["alert"] ) })
			context.update({ "server" : { "version": server_info["version"], "build": server_info["build"], "serverName": server_info["serverName"] } })

			if 'status' in incident:
				context.update({ "status" : incident["status"] })

			if "fields" in results:
				result_context = { "result" : results["fields"][0] }
				context.update(result_context)  
				results_context = { "results" : results["fields"] }
				context.update(results_context)

		except Exception as e:
			#exc_type, exc_obj, exc_tb = sys.exc_info()
			self.log.error("Error occured during event handling. Error: %s" % (traceback.format_exc()))
			return "Error occured during event handling. Error: %s" % (traceback.format_exc())

		self.context = context

	def update(self, key, value):
		self.context.update({ key : value })
		return True

	def get(self, key):
		return self.context.get(key, False)

	def getContext(self):
		return self.context

	def normalize_bool(self, value):
		return True if value.lower() in ('1', 'true') else False

