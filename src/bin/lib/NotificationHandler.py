import sys
import os
from os.path import basename
import json
import splunk.entity as entity
import splunk.rest as rest
import logging
import urllib
import urllib.parse
import smtplib
import re
import socket
import traceback
from MLStripper import strip_tags
from html.parser import HTMLParser

from NotificationScheme import NotificationScheme
from AlertManagerUsers import AlertManagerUsers
from AlertManagerLogger import setupLogger

from jinja2 import Environment, Template
from jinja2 import FileSystemLoader

import smtplib
import mimetypes
from email import encoders
#from email.message import Message
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.utils import COMMASPACE, formatdate

import splunk.appserver.mrsparkle.lib.util as util

def get_type(value):
    return type(value).__name__

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

class NotificationHandler(object):

    # Setup logger
    log = setupLogger('notifications')

    sessionKey = None
    env = None
    default_sender = None
    settings = {}

    def __init__(self, sessionKey):
        self.sessionKey = sessionKey

        # Setup template paths
        local_dir = os.path.join(util.get_apps_dir(), "alert_manager", "default", "templates")
        default_dir = os.path.join(util.get_apps_dir(), "alert_manager", "local", "templates")
        loader = FileSystemLoader([default_dir, local_dir])
        self.env = Environment(loader=loader, variable_start_string='$', variable_end_string='$')

        # TODO: Add support for custom filters
        self.env.filters['get_type'] = get_type

        # Get mailserver settings from splunk
        uri = '/servicesNS/nobody/system/configs/conf-alert_actions/email?output_mode=json'
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=self.sessionKey)
        server_settings = json.loads(serverContent.decode('utf-8'))
        server_settings = server_settings["entry"][0]["content"]
        #self.log.debug("server settings from splunk: {}".format(json.dumps(server_settings)))

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
        self.log.debug("Start handleEvent")
        self.log.debug("Incident: {}".format(incident))
        self.log.debug("Context: {}".format(context))

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
                    self.log.debug("Template ({}) references to a field name, starting to parse".format(notification["template"]))
                    if result_type == 'result' and "result" in context and field_name in context["result"]:
                        notification["template"] = context["result"][field_name]
                        self.log.debug("{} found in result. Parsed value {} as template name.".format(field_name, notification["template"]))
                    else:
                        self.log.warn("Field {} not found in '{}'. Won't send a notification.".format(field_name, result_type))

                # Parse sender
                if notification["sender"] == "default_sender":
                    notification["sender"] = self.default_sender

                # Parse recipients
                recipients = []
                recipients_cc = []
                recipients_bcc = []

                notification_recipients = notification["recipients"]

                # Test if manual notification overwrites recipients
                if context.get("recipients_overwrite") == "true":
                    self.log.debug("Overwriting recipients: true") 
                    notification_recipients= context.get("recipients").split(",")

                self.log.debug("notification_recipients: {}".format(notification_recipients))

                for recipient in notification_recipients:
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
                            self.log.info("Can't send a notification to 'unassigned' or a user who is configured to not receive notifications. alert={} owner={} event={}".format(alert, incident["owner"], event))
                            recipient_ok = False

                    else:
                        # Check if recipient is a crosslink to a result field and parse
                        field_recipient = re.search("\$(.+)\.(.+)\$", recipient)
                        if field_recipient != None:
                            result_type = field_recipient.group(1)
                            field_name = field_recipient.group(2)
                            self.log.debug("Should use a recipient from array '{}'. field: {}.".format(result_type, field_name))
                            if result_type == 'result' and "result" in context and field_name in context["result"]:
                                recipient = context["result"][field_name].split(",")
                                self.log.debug("{} found in result. Parsed value {}.".format(field_name, recipient))
                            else:
                                self.log.warn("Field {} not found in '{}'. Won't send a notification.".format(field_name, result_type))
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
                    self.log.info("Prepared notification. event={}, alert={}, template={}, sender={}, recipients={}, recipients_cc={}, recipients_bcc={}".format(event, alert, notification["template"], notification["sender"], recipients, recipients_cc, recipients_bcc))
                    self.send_notification(event, alert, notification["template"], notification["sender"], recipients, recipients_cc, recipients_bcc, context)
                else:
                    self.log.info("Done parsing notifications but will stop here since no recipients are present.")


        return True

    def send_notification(self, event, alert, template_name, sender, recipients, recipients_cc=[], recipients_bcc=[], context = {}):
        all_recipients = recipients + recipients_cc + recipients_bcc
        self.log.info("Start trying to send notification to {} with event={} of alert {}".format(str(all_recipients), event, alert))

        mail_template = self.get_email_template(template_name)
        if mail_template != False:
            self.log.debug("Found template file ({}). Ready to send notification.".format(json.dumps(mail_template)))


            # Parse html template with django
            try:
                # Parse body as django template
                template = self.env.get_template(mail_template['template_file'])
                content = template.render(context)

                #self.log.debug("Parsed message body. Context was: {}".format(json.dumps(context)))
                text_content = strip_tags(content)
               
                # Parse subject as django template
                subject_template = Template(source=mail_template['subject'], variable_start_string='$', variable_end_string='$')
                subject = subject_template.render(context)
                self.log.debug("Parsed message subject: {}".format(subject))

                # Prepare message
                self.log.debug("Preparing SMTP message...")
                message = MIMEMultipart('mixed')
                message['Subject']  = subject
                message['From']     = sender
                message['Date']     = formatdate(localtime = True)

                smtpRecipients = []

                if len(recipients) > 0:
                    smtpRecipients = smtpRecipients + recipients
                    message['To']       = COMMASPACE.join(recipients)
                if len(recipients_cc) > 0:
                    smtpRecipients = smtpRecipients + recipients_cc
                    message['CC'] = COMMASPACE.join(recipients_cc)

                if len(recipients_bcc) > 0:
                    smtpRecipients = smtpRecipients + recipients_bcc
                    message['BCC'] = COMMASPACE.join(recipients_bcc)

                message_alternative = MIMEMultipart('alternative')
                message_related = MIMEMultipart('related')

                # Add message body
                if mail_template['content_type'] == "html":
                    message_alternative.attach(MIMEText(text_content, 'plain'))
                    message_related.attach(MIMEText(content, 'html', 'utf-8'))
                else:
                    message_alternative.attach(MIMEText(text_content, 'plain'))

                message_alternative.attach(message_related)
                message.attach(message_alternative)    

                # Add attachments
                if 'attachments' in mail_template and mail_template['attachments'] != None and mail_template['attachments'] != "":
                    attachment_list = mail_template['attachments'].split(" ")
                    self.log.debug("Have to add attachments to this notification. Attachment list: {}".format(json.dumps(attachment_list)))

                    for attachment in attachment_list or []:
                        local_file = os.path.join(util.get_apps_dir(), "alert_manager", "local", "templates", "attachments", attachment)
                        default_file = os.path.join(util.get_apps_dir(), "alert_manager", "default", "templates", "attachments", attachment)

                        attachment_file = None
                        if os.path.isfile(local_file):
                            attachment_file = local_file
                            self.log.debug("{} exists in local, using this one...".format(attachment))
                        else:
                            self.log.debug("{} not found in local folder, checking if there's one in default...".format(attachment))
                            if os.path.isfile(default_file):
                                attachment_file = default_file
                                self.log.debug("{} exists in default, using this one...".format(attachment))
                            else:
                                self.log.warn("{} doesn't exist, won't add it to the message.".format(attachment))

                        if attachment_file != None:
                            ctype, encoding = mimetypes.guess_type(attachment_file)
                            if ctype is None or encoding is not None:
                                ctype = "application/octet-stream"
                            maintype, subtype = ctype.split("/", 1)

                            message_attachment = None
                            if maintype == "text":
                                try:
                                    fp = open(attachment_file)
                                    # Note: we should handle calculating the charset
                                    message_attachment = MIMEText(fp.read(), _subtype=subtype)
                                finally:
                                    fp.close()
                            elif maintype == "image":
                                try:
                                    fp = open(attachment_file, "rb")
                                    message_attachment = MIMEImage(fp.read(), _subtype=subtype)
                                finally:
                                    fp.close()
                            elif maintype == "audio":
                                try:
                                    fp = open(attachment_file, "rb")
                                    message_attachment = MIMEAudio(fp.read(), _subtype=subtype)
                                finally:
                                    fp.close()
                            else:
                                try:
                                    fp = open(attachment_file, "rb")
                                    message_attachment = MIMEBase(maintype, subtype)
                                    message_attachment.set_payload(fp.read())
                                    encoders.encode_base64(message_attachment)
                                finally:
                                    fp.close()

                            if message_attachment != None:
                                message_attachment.add_header("Content-ID", "<" + basename(attachment_file) + "@splunk>")
                                message_attachment.add_header("Content-Disposition", "attachment", filename=basename(attachment_file))
                                message_related.attach(message_attachment)

                #self.log.debug("Mail message: {}".format(msg.as_string()))
                #self.log.debug("Settings: {}".format(json.dumps(self.settings)))
                self.log.debug("smtpRecipients: {} type: {}".format(smtpRecipients, type(smtpRecipients)))
                self.log.info("Connecting to mailserver={} ssl={} tls={}".format(self.settings["MAIL_SERVER"], self.settings["EMAIL_USE_SSL"], self.settings["EMAIL_USE_TLS"]))
                if not self.settings["EMAIL_USE_SSL"]:
                     s = smtplib.SMTP(self.settings["MAIL_SERVER"])
                else:
                     s = smtplib.SMTP_SSL(self.settings["MAIL_SERVER"])

                if self.settings["EMAIL_USE_TLS"]:
                     s.starttls()

                if len(self.settings["EMAIL_HOST_USER"]) > 0:
                    s.login(str(self.settings["EMAIL_HOST_USER"]), str(self.settings["EMAIL_HOST_PASSWORD"]))

                self.log.info("Sending emails....")
                s.sendmail(sender, smtpRecipients, message.as_string())
                s.quit()

                self.log.info("Notifications sent successfully")

            #except TemplateSyntaxError, e:
            #    self.log.error("Unable to parse template {}. Error: {}. Continuing without sending notification...".format(mail_template['template_file'], e)))
            #except smtplib.SMTPServerDisconnected, e:
            #    self.log.error("SMTP server disconnected the connection. Error: {}".format(e))
            except socket.error as e:
                self.log.error("Wasn't able to connect to mailserver. Reason: {}".format(e))
            #except TemplateDoesNotExist, e:
            #    self.log.error("Template {} not found in {} nor {}. Continuing without sending notification...".format(mail_template['template_file'], local_dir, default_dir)))
            except Exception as e:
                self.log.error("Unable to send notification. Continuing without sending notification. Unexpected Error: {}".format(traceback.format_exc()))
        else:
            self.log.warn("Unable to find template file ({}).".format(json.dumps(mail_template)))


    def getNotificationSchemeName(self, alert):
        # Retrieve notification scheme from KV store
        query_filter = {}
        query_filter["alert"] = alert
        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_settings/?query={}'.format(urllib.parse.quote(json.dumps(query_filter)))
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=self.sessionKey)

        entries = json.loads(serverContent.decode('utf-8'))

        try:
            return entries[0]["notification_scheme"]

        except Exception as e:
            # TODO: Check response, fall back to default notification scheme
            return None

    def get_email_template(self, template_name):
        query = {}
        query["template_name"] = template_name
        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/email_templates?output_mode=json&query={}'.format(urllib.parse.quote(json.dumps(query)))
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=self.sessionKey)
        self.log.debug("Response for template listing: {}".format(serverContent.decode('utf-8')))
        entries = json.loads(serverContent.decode('utf-8'))

        if len(entries) > 0:
            return entries[0]
        else:
            self.log.error("Template {} not found in email_templates! Aborting...".format(template_name))
            return False

    def get_template_file(self, template_file_name):

        self.log.debug("Parsed template file from settings: {}".format(template_file_name))

        local_file = os.path.join(util.get_apps_dir(), "alert_manager", "local", "templates", template_file_name)
        default_file = os.path.join(util.get_apps_dir(), "alert_manager", "default", "templates", template_file_name)

        if os.path.isfile(local_file):
            self.log.debug("{} exists in local, using this one...".format(template_file_name))
            return  local_file
        else:
            self.log.debug("{} not found in local folder, checking if there's one in default...".format(template_file_name))
            if os.path.isfile(default_file):
                self.log.debug("{} exists in default, using this one...".format(template_file_name))
                return default_file
            else:
                self.log.debug("{} doesn't exist at all, stopping here.".format(template_file_name))
                return False


    def setSessionKey(self, sessionKey):
        self.sessionKey = sessionKey
