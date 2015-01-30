import sys
import os
import json
import splunk.entity as entity
import splunk.rest as rest
import logging
import urllib
import smtplib
import re
import socket
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives 
from django.template.loader import get_template
from django.template import Template, Context
from django.conf import settings
from django.utils.html import strip_tags

#sys.stdout = open('/tmp/stdout', 'w')
#sys.stderr = open('/tmp/stderr', 'w')

class AlertManagerNotifications:

    # Setup logger
    log = logging.getLogger('alert_manager_notifications')
    lf = os.path.join(os.environ.get('SPLUNK_HOME'), "var", "log", "splunk", "alert_manager_notifications.log")
    fh     = logging.handlers.RotatingFileHandler(lf, maxBytes=25000000, backupCount=5)
    formatter = logging.Formatter("%(asctime)-15s %(levelname)-5s %(message)s")
    fh.setFormatter(formatter)
    log.addHandler(fh)
    log.setLevel(logging.DEBUG)

    sessionKey = None

    def __init__(self, sessionKey):
        self.sessionKey = sessionKey

        # Setup template paths
        local_dir = os.path.join(os.environ.get('SPLUNK_HOME'), "etc", "apps", "alert_manager", "default", "templates")
        default_dir = os.path.join(os.environ.get('SPLUNK_HOME'), "etc", "apps", "alert_manager", "local", "templates")

        # Get mailserver settings from splunk
        uri = '/servicesNS/nobody/system/configs/conf-alert_actions/email?output_mode=json'
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=self.sessionKey)
        server_settings = json.loads(serverContent)
        server_settings = server_settings["entry"][0]["content"]
        #self.log.debug("server settings from splunk: %s" % json.dumps(server_settings))

        # Parse mailserver
        if ":" in server_settings['mailserver']:
            match = re.search(r'([^\:]+)\:(\d+)', server_settings['mailserver'])
            mailserver = match.group(1)
            mailport   = int(match.group(2))
        else:
            mailserver = server_settings['mailserver']
            mailport   = 25
        self.log.debug("Parsed mailserver settings. Host: %s, Port: %s" % (mailserver, mailport))

        use_ssl = False
        if server_settings['use_ssl'] == "1":
            use_ssl = True

        use_tls = False
        if server_settings['use_tls'] == "1":
            use_tls = True

        # Configure django settings
        settings.configure(    TEMPLATE_DIRS=(default_dir, local_dir), 
                            EMAIL_HOST=mailserver,
                            EMAIL_PORT=mailport,
                            EMAIL_HOST_USER=server_settings['auth_username'],
                            EMAIL_HOST_PASSWORD=server_settings['auth_password'],
                            EMAIL_USE_TLS=use_tls,
                            EMAIL_USE_SSL=use_ssl
                        )

    def send_notification(self, alert, recipient, action, context = {}):
        self.log.info("Start trying to send notification to %s with action=%s of alert %s" % (recipient, action, alert))

        # Get the settings related to the alert
        settings = self.get_email_settings(alert)

        # Now get the email template related to the alert and action
        if settings == False:
            log.debug("No email template found for %s, falling back to defaults." % alert)
            # TODO: get alert manager settings for defaults. At the moment, there's only notify_user so static entry
            alert_email_template_name = 'notify_user'
        else:
            alert_email_template_name = settings[action + '_template']

        template = self.get_email_template(alert_email_template_name)
        
        self.log.debug("Found settings and template file. Ready to send notification.")

        
        # Parse html template with django 
        try: 
            # Parse body as django template
            context = Context(context)
            content = get_template(template['email_template_file']).render(context)
            self.log.debug("Parsed message body: \"%s\" (Context was %s)" % (content, context))

            text_content = strip_tags(content)

            # Parse subject as django template
            subject_template = Template(template['email_subject'])
            subject = subject_template.render(context)
            self.log.debug("Parsed message subject: %s" % subject)

            # Prepare message
            msg = EmailMultiAlternatives(subject, text_content, template['email_from'], [ recipient ])
            
            # Add content as HTML if necessary
            if template['email_content_type'] == "html":
                msg.attach_alternative(content, "text/html")

            msg.send()
            self.log.info("Notification sent successfully to %s" % recipient)

        except smtplib.SMTPServerDisconnected, e:
            self.log.error("SMTP server disconnected the connection. Error: %s" % e)    
        except socket.error, e:
            self.log.error("Wasn't able to connect to mailserver. Reason: %s" % e)
        except:
            self.log.error("Unable to send notification. Unexpected error: %s. Continuing..." % sys.exc_info()[0])    


    def get_email_settings(self, alert):
        query = {}
        query["alert"] = alert
        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/email_settings?output_mode=json&query=%s' % urllib.quote(json.dumps(query))
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=self.sessionKey)
        self.log.debug("Response for email settings: %s" %  serverContent)
        entries = json.loads(serverContent)    

        if len(entries) > 0:
            return entries[0]
        else:
            return False

    def get_email_template(self, template_name):
        query = {}
        query["email_template_name"] = template_name
        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/email_templates?output_mode=json&query=%s' % urllib.quote(json.dumps(query))
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=self.sessionKey)
        self.log.debug("Response for template listing: %s" %  serverContent)
        entries = json.loads(serverContent)    

        if len(entries) > 0:
            return entries[0]
        else:
            return False

    def get_template_file(self, template_file_name):
        
        self.log.debug("Parsed template file from settings: %s" % template_file_name)

        local_file = os.path.join(os.environ.get('SPLUNK_HOME'), "etc", "apps", "alert_manager", "default", "templates", template_file_name)
        default_file = os.path.join(os.environ.get('SPLUNK_HOME'), "etc", "apps", "alert_manager", "local", "templates", template_file_name)

        if os.path.isfile(local_file):
            self.log.debug("%s exists in local, using this one..." % template_file_name)
            return  local_file
        else:
            self.log.debug("%s not found in local folder, checking if there's one in default..." % template_file_name)
            if os.path.isfile(default_file):
                self.log.debug("%s exists in default, using this one..." % template_file_name)
                return default_file
            else:
                self.log.debug("%s doesn't exist at all, stopping here.")
                return False

        