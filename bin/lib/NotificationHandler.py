import sys
import os
from os.path import basename
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
from AlertManagerLogger import *

from jinja2 import Environment, Template
from jinja2 import FileSystemLoader

import smtplib
import mimetypes
from email import encoders
from email.message import Message
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate

def get_type(value):
    return type(value).__name__

class NotificationHandler:

    # Setup logger
    log = setupLogger('notifications')

    sessionKey = None
    env = None
    default_sender = None
    settings = {}

    def __init__(self, sessionKey):
        self.sessionKey = sessionKey

        # Setup template paths
        local_dir = os.path.join(os.environ.get('SPLUNK_HOME'), "etc", "apps", "alert_manager", "default", "templates")
        default_dir = os.path.join(os.environ.get('SPLUNK_HOME'), "etc", "apps", "alert_manager", "local", "templates")
        loader = FileSystemLoader([default_dir, local_dir])
        self.env = Environment(loader=loader, variable_start_string='$', variable_end_string='$')

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
        if server_settings['use_ssl']:
            use_ssl = True

        use_tls = False
        if server_settings['use_tls']:
            use_tls = True

        # Configure django settings
        clear_pass = ''
        if 'clear_password' in server_settings:
            clear_pass = server_settings['clear_password']

        auth_username = ""
        if 'auth_username' in server_settings:
            auth_username = server_settings['auth_username']

        mail_server = "localhost"
        if 'mailserver' in server_settings:
            mail_server = server_settings['mailserver']

        self.settings = {    
                            "MAIL_SERVER": mail_server,
                            "EMAIL_HOST_USER": auth_username,
                            "EMAIL_HOST_PASSWORD": clear_pass,
                            "EMAIL_USE_TLS": use_tls,
                            "EMAIL_USE_SSL": use_ssl
                        }


    def handleEvent(self, event, alert, incident, context):
        notificationSchemeName = self.getNotificationSchemeName(alert)
        notificationScheme = NotificationScheme(self.sessionKey, notificationSchemeName)
        notifications = notificationScheme.getNotifications(event)      

        if len(notifications) > 0:
            for notification in notifications:

                # Parse template
                template_match = re.search("^\$(.+)\.(.+)\$$", notification["template"])
                if template_match != None:
                    result_type = template_match.group(1)
                    field_name = template_match.group(2)
                    self.log.debug("Template (%s) references to a field name, starting to parse" % notification["template"] )
                    if result_type == 'result' and "result" in context and field_name in context["result"]:
                        notification["template"] = context["result"][field_name]
                        self.log.debug("%s found in result. Parsed value %s as template name." % (field_name, notification["template"]))
                    else:
                        self.log.warn("Field %s not found in '%s'. Won't send a notification." % (field_name, result_type))

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
                        if incident["owner"] != "unassigned":
                            recipient = user["email"]
                        else:
                            self.log.info("Can't send a notification to 'unassigned' or a user who is configured to not receive notifications. alert=%s owner=%s event=%s" % (alert, incident["owner"], event))
                            recipient_ok = False

                    else:
                        # Check if recipient is a crosslink to a result field and parse
                        field_recipient = re.search("\$(.+)\.(.+)\$", recipient)
                        if field_recipient != None:
                            result_type = field_recipient.group(1)
                            field_name = field_recipient.group(2)
                            self.log.debug("Should use a recipient from array '%s'. field: %s." % (result_type, field_name))
                            if result_type == 'result' and "result" in context and field_name in context["result"]:
                                recipient = context["result"][field_name].split(",")
                                self.log.debug("%s found in result. Parsed value %s." % (field_name, recipient))
                            else:
                                self.log.warn("Field %s not found in '%s'. Won't send a notification." % (field_name, result_type))
                                recipient_ok = False

                    if recipient_ok:
                        if mode == "mailto":
                            if isinstance(recipient, list):
                                recipients = recipients + recipient
                            else:
                                recipients.append(recipient)
                        elif mode == "mailcc":
                            if isinstance(recipient, list):
                                recipients_cc = recipients_cc + recipient
                            else:
                                recipients_cc.append(recipient)
                        elif mode == "mailbcc":
                            if isinstance(recipient, list):
                                recipients_bcc = recipients_bcc + recipient
                            else:
                                recipients_bcc.append(recipient)
                
                if len(recipients) > 0 or len(recipients_cc) > 0 or len(recipients_bcc) > 0:
                    self.log.info("Prepared notification. event=%s, alert=%s, template=%s, sender=%s, recipients=%s, recipients_cc=%s, recipients_bcc=%s" % (event, alert, notification["template"], notification["sender"], recipients, recipients_cc, recipients_bcc))
                    self.send_notification(event, alert, notification["template"], notification["sender"], recipients, recipients_cc, recipients_bcc, context)
                else:
                    self.log.info("Done parsing notifications but will stop here since no recipients are present.")


        return True

    def send_notification(self, event, alert, template_name, sender, recipients, recipients_cc=[], recipients_bcc=[], context = {}):
        all_recipients = recipients + recipients_cc + recipients_bcc
        self.log.info("Start trying to send notification to %s with event=%s of alert %s" % (str(all_recipients), event, alert))       

        mail_template = self.get_email_template(template_name)        
        if mail_template != False:
            self.log.debug("Found template file (%s). Ready to send notification." % json.dumps(mail_template))

            
            # Parse html template with django 
            try: 
                # Parse body as django template
                template = self.env.get_template(mail_template['template_file'])
                content = template.render(context)
                #self.log.debug("Parsed message body. Context was: %s" % (json.dumps(context)))

                text_content = strip_tags(content)

                # Parse subject as django template
                subject_template = Template(source=mail_template['subject'], variable_start_string='$', variable_end_string='$')
                subject = subject_template.render(context)
                self.log.debug("Parsed message subject: %s" % subject)

                # Prepare message
                self.log.debug("Preparing SMTP message...")
                msgRoot = MIMEMultipart('related')
                msgRoot['Subject']  = subject
                msgRoot['From']     = sender
                msgRoot['Date']     = formatdate(localtime = True)

                smtpRecipients = []
                msg = MIMEMultipart('alternative')
                msgRoot.attach(msg)

                #msg.preamble    = text_content

                if len(recipients) > 0:
                    smtpRecipients = smtpRecipients + recipients
                    msgRoot['To']       = COMMASPACE.join(recipients)
                if len(recipients_cc) > 0:
                    smtpRecipients = smtpRecipients + recipients_cc
                    msgRoot['CC'] = COMMASPACE.join(recipients_cc)

                if len(recipients_bcc) > 0:
                    smtpRecipients = smtpRecipients + recipients_bcc
                    msgRoot['BCC'] = COMMASPACE.join(recipients_bcc)


                # Add message body
                if mail_template['content_type'] == "html":
                    msg.attach(MIMEText(content, 'html'))
                else:
                    msg.attach(MIMEText(text_content, 'plain'))

                # Add attachments
                if 'attachments' in mail_template and mail_template['attachments'] != None and mail_template['attachments'] != "":
                    attachment_list = mail_template['attachments'].split(" ")
                    self.log.debug("Have to add attachments to this notification. Attachment list: %s" % json.dumps(attachment_list))

                    for attachment in attachment_list or []:
                        local_file = os.path.join(os.environ.get('SPLUNK_HOME'), "etc", "apps", "alert_manager", "local", "templates", "attachments", attachment)
                        default_file = os.path.join(os.environ.get('SPLUNK_HOME'), "etc", "apps", "alert_manager", "default", "templates", "attachments", attachment)

                        attachment_file = None
                        if os.path.isfile(local_file):
                            attachment_file = local_file
                            self.log.debug("%s exists in local, using this one..." % attachment)
                        else:
                            self.log.debug("%s not found in local folder, checking if there's one in default..." % attachment)
                            if os.path.isfile(default_file):
                                attachment_file = default_file
                                self.log.debug("%s exists in default, using this one..." % attachment)
                            else:
                                self.log.warn("%s doesn't exist, won't add it to the message." % attachment)

                        if attachment_file != None:
                            ctype, encoding = mimetypes.guess_type(attachment_file)
                            if ctype is None or encoding is not None:
                                ctype = "application/octet-stream"
                            maintype, subtype = ctype.split("/", 1)

                            msgAttachment = None
                            if maintype == "text":
                                try:
                                    fp = open(attachment_file)
                                    # Note: we should handle calculating the charset
                                    msgAttachment = MIMEText(fp.read(), _subtype=subtype)
                                finally:
                                    fp.close()
                            elif maintype == "image":
                                try:
                                    fp = open(attachment_file, "rb")
                                    msgAttachment = MIMEImage(fp.read(), _subtype=subtype)
                                finally:
                                    fp.close()
                            elif maintype == "audio":
                                try:
                                    fp = open(attachment_file, "rb")
                                    msgAttachment = MIMEAudio(fp.read(), _subtype=subtype)
                                finally:
                                    fp.close()
                            else:
                                try:
                                    fp = open(attachment_file, "rb")
                                    msgAttachment = MIMEBase(maintype, subtype)
                                    msgAttachment.set_payload(fp.read())
                                    encoders.encode_base64(msgAttachment)
                                finally:
                                    fp.close()
                                
                            if msgAttachment != None:
                                msgAttachment.add_header("Content-ID", "<" + basename(attachment_file) + "@splunk>")
                                msgAttachment.add_header("Content-Disposition", "attachment", filename=basename(attachment_file))
                                msgRoot.attach(msgAttachment)

                #self.log.debug("Mail message: %s" % msg.as_string())
                #self.log.debug("Settings: %s " % json.dumps(self.settings))
                self.log.debug("smtpRecipients: %s type: %s" % (smtpRecipients, type(smtpRecipients)))
                self.log.info("Connecting to mailserver=%s ssl=%s tls=%s" % (self.settings["MAIL_SERVER"], self.settings["EMAIL_USE_SSL"], self.settings["EMAIL_USE_TLS"]))
                if not self.settings["EMAIL_USE_SSL"]:
                     s = smtplib.SMTP(self.settings["MAIL_SERVER"])
                else:
                     s = smtplib.SMTP_SSL(self.settings["MAIL_SERVER"])

                if self.settings["EMAIL_USE_TLS"]:
                     s.starttls()

                if len(self.settings["EMAIL_HOST_USER"]) > 0:
                    s.login(str(self.settings["EMAIL_HOST_USER"]), str(self.settings["EMAIL_HOST_PASSWORD"]))

                self.log.info("Sending emails....")
                s.sendmail(sender, smtpRecipients, msgRoot.as_string().encode('utf-8'))
                s.quit()
                
                self.log.info("Notifications sent successfully")

            #except TemplateSyntaxError, e:
            #    self.log.error("Unable to parse template %s. Error: %s. Continuing without sending notification..." % (mail_template['template_file'], e))
            #except smtplib.SMTPServerDisconnected, e:
            #    self.log.error("SMTP server disconnected the connection. Error: %s" % e)    
            except socket.error, e:
                self.log.error("Wasn't able to connect to mailserver. Reason: %s" % e)
            #except TemplateDoesNotExist, e:
            #    self.log.error("Template %s not found in %s nor %s. Continuing without sending notification..." % (mail_template['template_file'], local_dir, default_dir))
            except Exception as e:
                self.log.error("Unable to send notification. Continuing without sending notification. Unexpected Error: %s" % (traceback.format_exc()))
        else:
            self.log.warn("Unable to find template file (%s)." % json.dumps(mail_template))


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
        query["template_name"] = template_name
        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/email_templates?output_mode=json&query=%s' % urllib.quote(json.dumps(query))
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=self.sessionKey)
        self.log.debug("Response for template listing: %s" %  serverContent)
        entries = json.loads(serverContent)    

        if len(entries) > 0:
            return entries[0]
        else:
            self.log.error("Template %s not found in email_templates! Aborting..." % template_name)
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
