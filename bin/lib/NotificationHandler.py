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
import traceback
from MLStripper import strip_tags

from NotificationScheme import *
from AlertManagerUsers import *

from jinja2 import Environment, Template
from jinja2 import FileSystemLoader

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def get_type(value):
    return type(value).__name__

class NotificationHandler:

    # Setup logger
    log = logging.getLogger('alert_manager_notifications')
    lf = os.path.join(os.environ.get('SPLUNK_HOME'), "var", "log", "splunk", "alert_manager_notifications.log")
    fh     = logging.handlers.RotatingFileHandler(lf, maxBytes=25000000, backupCount=5)
    formatter = logging.Formatter("%(asctime)-15s %(levelname)-5s %(message)s")
    fh.setFormatter(formatter)
    log.addHandler(fh)
    log.setLevel(logging.DEBUG)

    sessionKey = None
    env = None
    default_sender = None
    settings = {}

    def __init__(self, sessionKey):
        self.sessionKey = sessionKey

        # Setup template paths
        local_dir = os.path.join(os.environ.get('SPLUNK_HOME'), "etc", "apps", "alert_manager", "default", "templates")
        default_dir = os.path.join(os.environ.get('SPLUNK_HOME'), "etc", "apps", "alert_manager", "local", "templates")
        loader = FileSystemLoader([local_dir, default_dir])
        self.env = Environment(loader=loader)

        # TODO: Add support for custom filters
        self.env.filters['get_type'] = get_type

        # Get mailserver settings from splunk
        uri = '/servicesNS/nobody/system/configs/conf-alert_actions/email?output_mode=json'
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=self.sessionKey)
        server_settings = json.loads(serverContent)
        server_settings = server_settings["entry"][0]["content"]
        #self.log.debug("server settings from splunk: %s" % json.dumps(server_settings))

        self.default_sender = server_settings['from']

        use_ssl = False
        if server_settings['use_ssl'] == "1":
            use_ssl = True

        use_tls = False
        if server_settings['use_tls'] == "1":
            use_tls = True

        # Configure django settings
        self.settings = {    
                            "MAIL_SERVER": server_settings['mailserver'],
                            "EMAIL_HOST_USER": server_settings['auth_username'],
                            "EMAIL_HOST_PASSWORD": server_settings['auth_password'],
                            "EMAIL_USE_TLS": use_tls,
                            "EMAIL_USE_SSL": use_ssl
                        }


    def handleEvent(self, event, alert, incident, context):
        notificationSchemeName = self.getNotificationSchemeName(alert)
        notificationScheme = NotificationScheme(self.sessionKey, notificationSchemeName)
        notifications = notificationScheme.getNotifications(event)      

        for notification in notifications:

            # Parse sender
            if notification["sender"] == "default_sender":
                notification["sender"] = self.default_sender

            # Parse recipients
            recipients = []
            recipients_cc = []
            recipients_bcc = []

            for recipient in notification["recipients"]:
                recipient_ok = True

                # Parse recipient mode
                if ":" in recipient:
                    search = re.search("(mailto|mailcc|mailbcc)\:(.+)", recipient)
                    mode = search.group(1)
                    recipient = search.group(2)
                else:
                    mode = "mailto"
                
                # Parse recipient string
                if recipient == "current_owner":
                    users = AlertManagerUsers(sessionKey=self.sessionKey)
                    user = users.getUser(incident["owner"])
                    if incident["owner"] != "unassigned" and user["notify_user"]:
                        recipient = user["email"]
                    else:
                        self.log.warn("Can't send a notification to unassigned or a user who is configured to not receive notifications. owner=%s" % incident["owner"])
                        recipient_ok = False

                else:
                    # Check if recipient is a crosslink to a result field and parse
                    field_recipient = re.search("\$(.+)\$", recipient)
                    if field_recipient != None:
                        field_name = field_recipient.group(1)
                        self.log.debug("Should use a recipient from results. field: %s." % field_name)
                        if "result" in context and len(context["result"]) > 0 and field_name in context["result"][0]:
                            recipient = context["result"][0][field_name]
                            self.log.debug("%s found in result. Parsed value %s." % (field_name, recipient))
                        else:
                            self.log.warn("Field %s not found in results. Won't send a notification." % field_name)
                            recipient_ok = False

                if recipient_ok:
                    if mode == "mailto":
                        recipients.append(recipient)
                    elif mode == "mailcc":
                        recipients_cc.append(recipient)
                    elif mode == "mailbcc":
                        recipients_bcc.append(recipient)

            self.log.debug("Prepared notification. event=%s, alert=%s, template=%s, sender=%s, recipients=%s, recipients_cc=%s, recipients_bcc=%s" % (event, alert, notification["template"], notification["sender"], recipients, recipients_cc, recipients_bcc))
            
            if len(recipients) > 0 or len(recipients_cc) > 0 or len(recipients_bcc) > 0:
                self.send_notification(event, alert, notification["template"], notification["sender"], recipients, recipients_cc, recipients_bcc, context)

        return True

    def send_notification(self, event, alert, template_name, sender, recipients, recipients_cc=[], recipients_bcc=[], context = {}):
        all_recipients = recipients + recipients_cc + recipients_bcc
        self.log.info("Start trying to send notification to %s with event=%s of alert %s" % (str(all_recipients), event, alert))       

        mail_template = self.get_email_template(template_name)        
        self.log.debug("Found template file (%s). Ready to send notification." % json.dumps(mail_template))

        
        # Parse html template with django 
        try: 
            # Parse body as django template
            template = self.env.get_template(mail_template['email_template_file'])
            content = template.render(context)
            #self.log.debug("Parsed message body. Context was: %s" % (json.dumps(context)))

            text_content = strip_tags(content)

            # Parse subject as django template
            subject_template = Template(mail_template['email_subject'])
            subject = subject_template.render(context)
            self.log.debug("Parsed message subject: %s" % subject)

            # Prepare message
            smtpRecipients = []
            msg = MIMEMultipart('alternative')
            msg['Subject']  = subject
            msg['From']     = sender

            if len(recipients) > 0:
                smtpRecipients.append(recipients)
                msg['To']       = ", ".join(recipients)
            if len(recipients_cc) > 0:
                smtpRecipients.append(recipients_cc)
                msg['CC:'] = ", ".join(recipients_cc)

            if len(recipients_bcc) > 0:
                smtpRecipients.append(recipients_bcc)
                msg['BCC:'] = ", ".join(recipients_bcc)

            msg.attach(MIMEText(text_content, 'plain'))
            if mail_template['email_content_type'] == "html":
                msg.attach(MIMEText(content, 'html'))

            #self.log.debug("Settings: %s " % json.dumps(self.settings))
            if not self.settings["EMAIL_USE_SSL"]:
                 s = smtplib.SMTP(self.settings["MAIL_SERVER"])
            else:
                 s = smtplib.SMTP_SSL(self.settings["MAIL_SERVER"])

            if self.settings["EMAIL_USE_TLS"]:
                 s.starttls()

            if len(self.settings["EMAIL_HOST_USER"]) > 0:
                s.login(self.settings["EMAIL_HOST_USER"], self.settings["EMAIL_HOST_PASSWORD"])


            s.sendmail(sender, smtpRecipients, msg.as_string())
            s.quit()
            
            self.log.info("Notification sent successfully")

        #except TemplateSyntaxError, e:
        #    self.log.error("Unable to parse template %s. Error: %s. Continuing without sending notification..." % (mail_template['email_template_file'], e))
        #except smtplib.SMTPServerDisconnected, e:
        #    self.log.error("SMTP server disconnected the connection. Error: %s" % e)    
        except socket.error, e:
            self.log.error("Wasn't able to connect to mailserver. Reason: %s" % e)
        #except TemplateDoesNotExist, e:
        #    self.log.error("Template %s not found in %s nor %s. Continuing without sending notification..." % (mail_template['email_template_file'], local_dir, default_dir))
        except Exception as e:
            self.log.error("Unable to send notification. Continuing without sending notification. Unexpected Error: %s" % (traceback.format_exc()))


    def getNotificationSchemeName(self, alert):
        # Retrieve notification scheme from KV store
        query_filter = {}
        query_filter["alert"] = alert 
        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_settings/?query=%s' % urllib.quote(json.dumps(query_filter))
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=self.sessionKey)

        entries = json.loads(serverContent)

        try:
            return entries[0]["notification_scheme"]

        except Exception as e:
            # TODO: Check response, fall back to default notification scheme
            return None

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

        local_file = os.path.join(os.environ.get('SPLUNK_HOME'), "etc", "apps", "alert_manager", "local", "templates", template_file_name)
        default_file = os.path.join(os.environ.get('SPLUNK_HOME'), "etc", "apps", "alert_manager", "default", "templates", template_file_name)

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

    
    def setSessionKey(self, sessionKey):
        self.sessionKey = sessionKey
