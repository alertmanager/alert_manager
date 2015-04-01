import os
import json
from jinja2 import Environment, Template
from jinja2 import FileSystemLoader
from MLStripper import strip_tags

import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def get_type(value):
    return type(value).__name__

context = json.loads('{"alert": {"impact": "high", "urgency": "high", "priority": "critical", "digest_mode": true, "expires": 3600}, "subcategory": "Warnings", "server": {"version": "6.2.1", "build": "245427", "serverName": "skyfall.local"}, "results_link": "http://skyfall.local:8000/app/SA-alert_manager_demo/@go?sid=scheduler__admin_U0EtYWxlcnRfbWFuYWdlcl9kZW1v__RMD5ad7b61a9b44b3088_at_1427887080_426", "view_link": "http://skyfall.local:8000/app/SA-alert_manager_demo/alert?s=/servicesNS/nobody/SA-alert_manager_demo/saved/searches/demo_alert2_splunk_warnings", "app": "SA-alert_manager_demo", "category": "Splunk", "name": "demo_alert2_splunk_warnings", "alert_time": 1427887081, "result": [{"count": "60", "sourcetype": "alert_manager-28", "values(component)": "", "urgency": "high", "recipient": "simon@balz.me"}, {"count": "4", "sourcetype": "alert_manager_eventhandler-2", "values(component)": "", "urgency": "high", "recipient": "simon@balz.me"}, {"count": "28", "sourcetype": "alert_manager_notifications-3", "values(component)": "", "urgency": "high", "recipient": "simon@balz.me"}, {"count": "60", "sourcetype": "alert_manager_scheduler-4", "values(component)": "", "urgency": "high", "recipient": "simon@balz.me"}, {"count": "12", "sourcetype": "eventgen", "values(component)": "", "urgency": "high", "recipient": "simon@balz.me"}, {"count": "9", "sourcetype": "mongod", "values(component)": "", "urgency": "high", "recipient": "simon@balz.me"}, {"count": "6", "sourcetype": "scheduler", "values(component)": "", "urgency": "high", "recipient": "simon@balz.me"}, {"count": "4", "sourcetype": "splunk_python", "values(component)": "", "urgency": "high", "recipient": "simon@balz.me"}, {"count": "1", "sourcetype": "splunk_web_access", "values(component)": "", "urgency": "high", "recipient": "simon@balz.me"}, {"count": "666", "sourcetype": "splunkd", "values(component)": ["HttpListener", "LicenseUsage", "Metrics", "StatsProcessor", "TransformsExtractionHandler"], "urgency": "high", "recipient": "simon@balz.me"}, {"count": "194", "sourcetype": "splunkd_access", "values(component)": "", "urgency": "high", "recipient": "simon@balz.me"}, {"count": "12", "sourcetype": "splunkd_stderr", "values(component)": "", "urgency": "high", "recipient": "simon@balz.me"}, {"count": "55", "sourcetype": "splunkd_ui_access", "values(component)": "", "urgency": "high", "recipient": "simon@balz.me"}], "tags": "warning splunk", "owner": "unassigned"}')

local_dir = os.path.join(os.environ.get('SPLUNK_HOME'), "etc", "apps", "alert_manager", "default", "templates")
default_dir = os.path.join(os.environ.get('SPLUNK_HOME'), "etc", "apps", "alert_manager", "local", "templates")
loader = FileSystemLoader([local_dir, default_dir])
env = Environment(loader=loader)
env.filters['get_type'] = get_type
template = env.get_template("default_incident_assigned.html")
content = template.render(context)

me = "my@email.com"
you = "your@email.com"

# Create message container - the correct MIME type is multipart/alternative.
msg = MIMEMultipart('alternative')
msg['Subject'] = "Link"
msg['From'] = me
msg['To'] = you

text = strip_tags(content)
html = content

part1 = MIMEText(text, 'plain')
part2 = MIMEText(html, 'html')


msg.attach(part1)
msg.attach(part2)

s = smtplib.SMTP('localhost:10025')

s.sendmail(me, you, msg.as_string())
s.quit()