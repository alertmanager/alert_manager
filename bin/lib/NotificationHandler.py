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
import django
from django import template
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives 
from django.template.loader import get_template
from django.template import Template, Context
from django.utils.html import strip_tags
from django.template.base import TemplateSyntaxError
from django.template.base import TemplateDoesNotExist

from NotificationScheme import *
from AlertManagerUsers import *

from django.conf import settings

django.template.base.add_to_builtins("NotificationHandlerFilter")

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

    default_sender = None

    def __init__(self, sessionKey):
        self.sessionKey = sessionKey

        if not settings.configured:
            self.log.debug("Django settings aren't configured yet. Continuing..")

            # Setup template paths
            local_dir = os.path.join(os.environ.get('SPLUNK_HOME'), "etc", "apps", "alert_manager", "default", "templates")
            default_dir = os.path.join(os.environ.get('SPLUNK_HOME'), "etc", "apps", "alert_manager", "local", "templates")

            # Get mailserver settings from splunk
            uri = '/servicesNS/nobody/system/configs/conf-alert_actions/email?output_mode=json'
            serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=self.sessionKey)
            server_settings = json.loads(serverContent)
            server_settings = server_settings["entry"][0]["content"]
            #self.log.debug("server settings from splunk: %s" % json.dumps(server_settings))

            self.default_sender = server_settings['from']

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
        else:
            self.log.debug("Django settings already configured. Current settings: TEMPLATE_DIRS=%s EMAIL_HOST=%s" % (settings.TEMPLATE_DIRS, settings.EMAIL_HOST))


    def handleEvent(self, event, alert, incident, context):
        notificationSchemeName = self.getNotificationSchemeName(alert)
        notificationScheme = NotificationScheme(self.sessionKey, notificationSchemeName)
        notifications = notificationScheme.getNotifications(event)      

        for notification in notifications:

            if notification["sender"] == "default_sender":
                notification["sender"] = self.default_sender

            recipients = []
            recipients_cc = []
            recipients_bcc = []
            for recipient in notification["recipients"]:

                # Parse recipient mode
                if ":" in recipient:
                    search = re.search("(mailto|mailcc|mailbcc)\:(.+)", recipient)
                    mode = search.group(1)
                    recipient = search.group(2)
                else:
                    mode = "mailto"
                
                if recipient == "current_owner":
                    users = AlertManagerUsers(sessionKey=self.sessionKey)
                    user = users.getUser(incident["owner"])
                    if incident["owner"] != "unassigned" and user["notify_user"]:
                        recipient = user["email"]
                    else:
                        break

                # Check if recipient is a crosslink to a result field and parse
                field_recipient = re.search("\$(.+)\$", recipient)
                if field_recipient != None:
                    field_name = field_recipient.group(1)
                    self.log.debug("Should use a recipient from results. field: %s." % field_name)
                    if "result" in context:and len(context["result"]) > 0 and field_name in context["result"][0]:
                        recipient = context["result"][0][field_name]
                        self.log.debug("%s found in result. Parsed value %s." % (field_name, recipient))
                    else:
                        self.log.warn("Field %s not found in results. Won't send a notification." % field_name)
                        break

                if mode == "mailto":
                    recipients.append(recipient)
                elif mode == "mailcc":
                    recipients_cc.append(recipient)
                elif mode == "mailbcc":
                    recipients_bcc.append(recipient)

            self.log.debug("Prepared notification. event=%s, alert=%s, template=%s, sender=%s, recipients=%s, recipients_cc=%s, recipients_bcc=%s" % (event, alert, notification["template"], notification["sender"], recipients, recipients_cc, recipients_bcc))
            self.send_notification(event, alert, notification["template"], notification["sender"], recipients, recipients_cc, recipients_bcc, context)

        return True

    def send_notification(self, event, alert, template_name, sender, recipients, recipients_cc=[], recipients_bcc=[], context = {}):
        if len(recipients) < 1 and len(recipients_cc) < 1 and len(recipients_bcc):
            return False

        self.log.info("Start trying to send notification to %s with event=%s of alert %s" % (str(recipients), event, alert))       

        mail_template = self.get_email_template(template_name)        
        self.log.debug("Found template file (%s). Ready to send notification." % json.dumps(mail_template))

        
        # Parse html template with django 
        try: 
            # Parse body as django template
            orig_context = context
            context = Context(orig_context)
            #tplFile = self.get_template_file(mail_template['email_template_file'])
            #content = get_template(tplFile).render(context)
            content = get_template(mail_template['email_template_file']).render(context)
            #self.log.debug("Parsed message body: \"%s\" (Context was %s)" % (content, context))
            self.log.debug("Parsed message body. Context was: %s" % json.dumps(orig_context))

            text_content = strip_tags(content)

            # Parse subject as django template
            subject_template = Template(mail_template['email_subject'])
            subject = subject_template.render(context)
            self.log.debug("Parsed message subject: %s" % subject)

            # Prepare message
            msg = EmailMultiAlternatives(subject, text_content, sender, recipients, cc = recipients_cc, bcc = recipients_bcc)
            
            # Add content as HTML if necessary
            if mail_template['email_content_type'] == "html":
                msg.attach_alternative(content, "text/html")

            msg.send()
            self.log.info("Notification sent successfully")

        except TemplateSyntaxError, e:
            self.log.error("Unable to parse template %s. Error: %s. Continuing without sending notification..." % (mail_template['email_template_file'], e))
        except smtplib.SMTPServerDisconnected, e:
            self.log.error("SMTP server disconnected the connection. Error: %s" % e)    
        except socket.error, e:
            self.log.error("Wasn't able to connect to mailserver. Reason: %s" % e)
        except TemplateDoesNotExist, e:
            self.log.error("Template %s not found in %s nor %s. Continuing without sending notification..." % (mail_template['email_template_file'], local_dir, default_dir))
        except:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            self.log.error("Unable to send notification. Continuing without sending notification. Unexpected error: %s" % (traceback.format_exc()))


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
