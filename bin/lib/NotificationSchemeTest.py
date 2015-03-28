import urllib
import httplib2
import time
import re
from time import localtime,strftime
from xml.dom import minidom
import json
baseurl = 'https://localhost:8089'
username = 'admin'
password = 'admin123'
myhttp = httplib2.Http(disable_ssl_certificate_validation=True)

# http://blogs.splunk.com/2011/08/02/splunk-rest-api-is-easy-to-use/
#Step 1: Get a session key
servercontent = myhttp.request(baseurl + '/services/auth/login', 'POST',
                            headers={}, body=urllib.urlencode({'username':username, 'password':password}))[1]
sessionkey = minidom.parseString(servercontent).getElementsByTagName('sessionKey')[0].childNodes[0].nodeValue
print "====>sessionkey:  %s  <====" % sessionkey

from NotificationScheme import *

notif = NotificationScheme(sessionKey=sessionkey, schemeName="default_notification_scheme")



print notif.notifications