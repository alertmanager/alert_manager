
import urllib
import httplib2
import time
import re
from time import localtime,strftime
from xml.dom import minidom
import json
import pprint
baseurl = 'https://localhost:8089'
username = 'admin'
password = 'changeme'
myhttp = httplib2.Http(disable_ssl_certificate_validation=True)

# http://blogs.splunk.com/2011/08/02/splunk-rest-api-is-easy-to-use/
#Step 1: Get a session key
servercontent = myhttp.request(baseurl + '/services/auth/login', 'POST',
                            headers={}, body=urllib.urlencode({'username':username, 'password':password}))[1]
sessionkey = minidom.parseString(servercontent).getElementsByTagName('sessionKey')[0].childNodes[0].nodeValue
print "====>sessionkey:  %s  <====" % sessionkey

from EventHandler import *
incident = {}
incident["owner"] = "demo1"

eh = EventHandler(sessionKey=sessionkey, alert="demo_alert2_splunk_warnings")
eh.handleEvent(event="incident_created", incident=incident, context=incident)

#pp = pprint.PrettyPrinter(depth=6)
#pp.pprint(notif.getNotifications("incident_created"))
