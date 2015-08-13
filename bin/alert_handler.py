import sys
import os
import subprocess
from subprocess import Popen, PIPE, STDOUT
import splunk
import splunk.auth as auth
import splunk.entity as entity
import splunk.Intersplunk as intersplunk
import splunk.rest as rest
import splunk.search as search
import splunk.input as input
import splunk.util as util
import urllib
import json
import socket
import logging
import time
import datetime
import hashlib
import re
import uuid
import tempfile

sys.stdout = open(os.path.join(tempfile.gettempdir(), 'stdout'), 'a')
sys.stderr = open(os.path.join(tempfile.gettempdir(), 'stderr'), 'a')

dir = os.path.join(os.path.join(os.environ.get('SPLUNK_HOME')), 'etc', 'apps', 'alert_manager', 'bin', 'lib')
if not dir in sys.path:
    sys.path.append(dir)

from AlertManagerNotifications import *
from AlertManagerUsers import *
from CsvLookup import *
from CsvResultParser import *

# Write alert metadata to index
def writeAlertMetadataToIndex(job, incident_id, result_id):
    log.info("Attempting Alert metadata write to index=%s" % config['index'])
    job['result_id'] = result_id
    job['incident_id'] = incident_id
    input.submit(json.dumps(job), hostname = socket.gethostname(), sourcetype = 'alert_metadata', source = 'alert_handler.py', index = config['index'])
    log.info("Alert metadata written to index=%s" % config['index'])

# Get result_id depending of digest mode
def getResultId(digest_mode, job_path):
    if digest_mode == False:
            result_id = re.search("tmp_(\d+)\.csv\.gz", job_path).group(1)
            return result_id
    else:
            return 0

# Get alert results
def getResults(job_path, incident_id):
    parser = CsvResultParser(job_path)
    results = parser.getResults({ "incident_id": incident_id })
    return results

# Create New incident to collection
def createNewIncident(alert_time, incident_id, job_id, result_id, alert, status, ttl, impact, urgency, priority, owner, user_list, notifier, digest_mode, results):
    alert_time = int(float(util.dt2epoch(util.parseISO(alert_time, True))))
    entry = {}
    entry['incident_id'] = incident_id
    entry['alert_time'] = alert_time
    entry['job_id'] = job_id
    entry['result_id'] = result_id
    entry['alert'] = alert
    entry['status'] = status
    entry['ttl'] = ttl
    entry['impact'] = impact
    entry['urgency'] = urgency
    entry['priority'] = priority
    entry['owner'] = owner

    if incident_config['auto_assign'] and incident_config['auto_assign_owner'] != 'unassigned':
            entry['owner'] = incident_config['auto_assign_owner']
            owner = incident_config['auto_assign_owner']
            log.info("Assigning incident to %s" % incident_config['auto_assign_owner'])
            auto_assgined = True
            status = 'auto_assigned'
            entry['status'] = status
            notifyAutoAssign(user_list, notifier, digest_mode, results, job_id, result_id, ttl, impact, urgency, priority)

    entry = json.dumps(entry)

    writeIncidentToCollection(entry)

    logCreateEvent(alert, incident_id, job_id, result_id, owner, urgency, ttl, alert_time)
    logChangeEvent(incident_id, job_id, result_id, status, owner)

# Add Incident to collection
def writeIncidentToCollection(entry):
    uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents'
    serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=entry)

# Autoprevious resolve
def autoPreviousResolve(alert, job_id):
    # Auto Previous resolve

    log.info("auto_previous_resolve is active for alert %s, searching for incidents to resolve..." % alert)
    query = '{  "alert": "'+ alert +'", "$or": [ { "status": "auto_assigned" } , { "status": "new" } ], "job_id": { "$ne": "'+ job_id +'"} }'
    log.debug("Filter for auto_previous_resolve: %s" % query)
    uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents?query=%s' % urllib.quote(query)
    serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)
    incidents = json.loads(serverContent)
    if len(incidents):
        log.info("Got %s incidents to auto-resolve" % len(incidents))
        for incident in incidents:
            log.info("Auto-resolving incident with key=%s" % incident['_key'])

            previous_status = incident["status"]
            previous_job_id = incident["job_id"]
            previous_incident_id = incident["incident_id"]

            incident['status'] = 'auto_previous_resolved'
            uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incidents/%s' % incident['_key']
            incident = json.dumps(incident)
            serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=incident)

            now = datetime.datetime.now().isoformat()
            event_id = hashlib.md5(job_id + now).hexdigest()
            log.debug("event_id=%s now=%s incident=%s" % (event_id, now, incident))


            event = 'time=%s severity=INFO origin="alert_handler" event_id="%s" user="splunk-system-user" action="auto_previous_resolve" previous_status="%s" status="auto_previous_resolved" incident_id="%s" job_id="%s"' % (now, event_id, previous_status, previous_incident_id, previous_job_id)
            log.debug("Resolve event will be: %s" % event)
            input.submit(event, hostname = socket.gethostname(), sourcetype = 'incident_change', source = 'alert_handler.py', index = config['index'])
    else:
        log.info("No incidents with matching criteria for auto_previous_resolve found.")

# Notify Auto assign
def notifyAutoAssign(user_list, notifier, digest_mode, results, job_id, result_id, ttl, impact, urgency, priority):
    # Send notification
    log.debug("User list: %s" % user_list)

    user = {}
    user_found = False
    for item in user_list:
        if item["name"] == incident_config['auto_assign_owner']:
            user = item
            user_found = True

    if user_found:
        log.debug("Got user settings for user %s. notify_user is set to %s" % (incident_config['auto_assign_owner'], user['notify_user']))
        if user['notify_user'] != False and user['email'] != "":
            log.info("Auto-assign user %s (email=%s) configured correctly to receive notification. Proceeding..." % (incident_config['auto_assign_owner'], user['email']))

            # Prepare context
            context = {}
            context.update({ "alert_time" : alert_time })
            context.update({ "owner" : incident_config['auto_assign_owner'] })
            context.update({ "name" : alert })
            context.update({ "alert" : { "impact": impact, "urgency": urgency, "priority": priority, "expires": ttl, "digest_mode": digest_mode } })
            context.update({ "app" : alert_app })
            context.update({ "category" : incident_config['category'] })
            context.update({ "subcategory" : incident_config['subcategory'] })
            context.update({ "tags" : incident_config['tags'] })
            context.update({ "results_link" : "http://"+socket.gethostname() + ":8000/app/" + alert_app + "/@go?sid=" + job_id })
            context.update({ "view_link" : "http://"+socket.gethostname() + ":8000/app/" + alert_app + "/alert?s=" + urllib.quote("/servicesNS/nobody/"+alert_app+"/saved/searches/" + alert) })
            context.update({ "server" : { "version": job["generator"]["version"], "build": job["generator"]["build"], "serverName": socket.gethostname() } })

            result_context = { "result" : results["fields"] }
            context.update(result_context)

            notifier.send_notification(alert, user['email'], "notify_user", context)

        else:
            log.info("Auto-assign user %s is configured either to not receive a notification or is missing the email address. Won't send any notification." % incident_config['auto_assign_owner'])

# Write create event to index
def logCreateEvent(alert, incident_id, job_id, result_id, owner, urgency, ttl, alert_time):
    now = datetime.datetime.now().isoformat()
    event_id = hashlib.md5(job_id + now).hexdigest()
    user = 'splunk-system-user'
    event = 'time=%s severity=INFO origin="alert_handler" event_id="%s" user="%s" action="create" alert="%s" incident_id="%s" job_id="%s" result_id="%s" owner="%s" status="new" urgency="%s" ttl="%s" alert_time="%s"' % (now, event_id, user, alert, incident_id, job_id, result_id, owner, urgency, ttl, alert_time)
    log.debug("Create event will be: %s" % event)
    input.submit(event, hostname = socket.gethostname(), sourcetype = 'incident_change', source = 'alert_handler.py', index = config['index'])

# Write change event to index
def logChangeEvent(incident_id, job_id, result_id, status, owner):
    if status=='auto_assigned':
        now = datetime.datetime.now().isoformat()
        event_id = hashlib.md5(job_id + now).hexdigest()

        event = 'time=%s severity=INFO origin="alert_handler" event_id="%s" user="splunk-system-user" action="change" incident_id="%s" job_id="%s" result_id="%s" owner="%s" previous_owner="unassigned"' % (now, event_id, incident_id, job_id, result_id, owner)
        log.debug("Auto assign (owner change) event will be: %s" % event)
        input.submit(event, hostname = socket.gethostname(), sourcetype = 'incident_change', source = 'alert_handler.py', index = config['index'])

        event = 'time=%s severity=INFO origin="alert_handler" event_id="%s" user="splunk-system-user" action="change" incident_id="%s" job_id="%s" result_id="%s" status="auto_assigned" previous_status="new"' % (now, event_id, incident_id, job_id, result_id)
        log.debug("Auto assign (status change) event will be: %s" % event)
        input.submit(event, hostname = socket.gethostname(), sourcetype = 'incident_change', source = 'alert_handler.py', index = config['index'])

# Write incident_result to collection
def writeResultToCollection(results):
    incident_result = json.dumps(results)
    uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_results'
    serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, jsonargs=incident_result)
    log.debug("results for incident_id=%s written to collection." % (incident_id))

# Read urgency from results
def readUrgencyFromResults(results, default_urgency, incident_id):
    if len(results["fields"]) > 0 and "urgency" in results["fields"][0] and results["fields"][0]["urgency"] in valid_urgencies:
        log.debug("Found valid urgency field in results, will use urgency=%s for incident_id=%s" % (results["fields"][0]["urgency"], incident_id))
        return results["fields"][0]["urgency"]
    else:
        log.debug("No valid urgency field found in results. Falling back to default_urgency=%s for incident_id=%s" % (default_urgency, incident_id))
        return default_urgency


def getLookupFile(lookup_name):
    try:
        uri = '/servicesNS/nobody/alert_manager/data/transforms/lookups/%s?output_mode=json' % lookup_name
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)
        lookup = json.loads(serverContent)
        log.debug("Got lookup content for lookup=%s. filename=%s app=%s" % (lookup_name, lookup["entry"][0]["content"]["filename"], lookup["entry"][0]["acl"]["app"]))
        return os.path.join(os.path.join(os.environ.get('SPLUNK_HOME')), 'etc', 'apps', lookup["entry"][0]["acl"]["app"], 'lookups', lookup["entry"][0]["content"]["filename"])
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        log.warn("Unable to get lookup %s. Reason: %s. Line: %s" % (lookup_name, config['default_priority'], exc_type, exc_tb.tb_lineno))
        return ""

def getImpact(severity):
    try:
        csv_path = getLookupFile('alert_impact')

        if os.path.exists(csv_path):
            log.debug("Lookup file %s found. Proceeding..." % csv_path)
            lookup = CsvLookup(csv_path)
            query = { "severity_id": str(severity) }
            log.debug("Querying lookup with filter=%s" % query)
            matches = lookup.lookup(query, { "impact" })
            if len(matches) > 0:
                log.debug("Matched impact in lookup, returning value=%s" % matches["impact"])
                return matches["impact"]
            else:
                log.debug("No matching impact found in lookup, falling back to default_impact=%s" % (config['default_impact']))
        else:
            log.warn("Lookup file %s not found. Falling back to default_impact=%s" % (csv_path, config['default_impact']))

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        log.warn("Unable to get impact. Falling back to default_impact=%s. Error: %s. Line: %s" % (config['default_impact'], exc_type, exc_tb.tb_lineno))
        return config['default_impact']

def getPriority(impact, urgency):
    #/servicesNS/nobody/alert_manager/data/transforms/lookups/alert_priority
    try:
        csv_path = getLookupFile('alert_priority')

        if os.path.exists(csv_path):
            log.debug("Lookup file %s found. Proceeding..." % csv_path)
            lookup = CsvLookup(csv_path)
            query = { "impact": impact, "urgency": urgency }
            log.debug("Querying lookup with filter=%s" % query)
            matches = lookup.lookup(query, { "priority" })
            if len(matches) > 0:
                log.debug("Matched priority in lookup, returning value=%s" % matches["priority"])
                return matches["priority"]
            else:
                log.debug("No matching priority found in lookup, falling back to default_priority=%s" % (config['default_priority']))
        else:
            log.warn("Lookup file %s not found. Falling back to default_priority=%s" % (csv_path, config['default_priority']))

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        log.warn("Unable to get priority. Falling back to default_priority=%s. Error: %s. Line: %s" % (config['default_priority'], exc_type, exc_tb.tb_lineno))
        return config['default_priority']

#
# Init
#
start = time.time()

if len(sys.argv) < 9:
    print "Wrong number of arguments provided, aborting."
    sys.exit(1)

# Setup logger
log = logging.getLogger('alert_manager')
lf = os.path.join(os.environ.get('SPLUNK_HOME'), "var", "log", "splunk", "alert_manager.log")
fh     = logging.handlers.RotatingFileHandler(lf, maxBytes=25000000, backupCount=5)
formatter = logging.Formatter("%(asctime)-15s %(levelname)-5s %(message)s")
fh.setFormatter(formatter)
log.addHandler(fh)
log.setLevel(logging.DEBUG)

# Parse arguments
job_path = sys.argv[8]

if os.name == "nt":
    match = re.search(r'dispatch\\([^\\]+)\\', job_path)
else:
    match = re.search(r'dispatch\/([^\/]+)\/', job_path)

job_id = match.group(1)

stdinArgs = sys.stdin.readline()
stdinLines = stdinArgs.strip()
sessionKeyOrig = stdinLines[11:]
sessionKey = urllib.unquote(sessionKeyOrig).decode('utf8')
alert = sys.argv[4]

log.debug("Parsed arguments: job_path=%s job_id=%s sessionKey=%s alert=%s" % (job_path, job_id, sessionKey, alert))

# Need to set the sessionKey (input.submit() doesn't allow passing the sessionKey)
splunk.setDefault('sessionKey', sessionKey)

# Finished initialization

log.info("alert_handler started because alert '%s' with id '%s' has been fired." % (alert, job_id))

#
# Get/set global settings
#
valid_urgencies = { "low", "medium", "high"}

config = {}
config['index']                        = 'alerts'
config['default_owner']                 = 'unassigned'
config['default_impact']             = 'low'
config['default_urgency']             = 'low'
config['default_priority']             = 'low'

restconfig = splunk.entity.getEntities('configs/alert_manager', count=-1, sessionKey=sessionKey)
if len(restconfig) > 0:
    for cfg in config.keys():
        if cfg in restconfig['settings']:
            if restconfig['settings'][cfg] == '0':
                config[cfg] = False
            elif restconfig['settings'][cfg] == '1':
                config[cfg] = True
            else:
                config[cfg] = restconfig['settings'][cfg]

log.debug("Parsed global alert handler settings: %s" % json.dumps(config))

#
# Get per incident settings
#
incident_config = {}
incident_config['run_alert_script']        = False
incident_config['alert_script']            = ''
incident_config['auto_assign']            = False
incident_config['auto_assign_user']        = ''
incident_config['auto_ttl_resolve']        = False
incident_config['auto_previous_resolve']= False
incident_config['urgency']                = config['default_urgency']
incident_config['category']                = ''
incident_config['subcategory']            = ''
incident_config['tags']                    = ''
query = {}
query['alert'] = alert
log.debug("Query for alert settings: %s" % urllib.quote(json.dumps(query)))
uri = '/servicesNS/nobody/alert_manager/storage/collections/data/incident_settings?query=%s' % urllib.quote(json.dumps(query))
serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey)
log.debug("Incident settings: %s" % serverContent)
incident_settings = json.loads(serverContent)
if len(incident_settings) > 0:
    log.info("Found incident settings for %s" % alert)
    for key, val in incident_settings[0].iteritems():
        incident_config[key] = val
else:
    log.info("No incident settings found for %s, switching back to defaults." % alert)

log.debug("Incident config after getting settings: %s" % json.dumps(incident_config))

#
# Alert metadata
#
# Get alert metadata
uri = '/services/search/jobs/%s' % job_id
serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=sessionKey, getargs={'output_mode': 'json'})
job = json.loads(serverContent)
#log.debug("Job: %s" % json.dumps(job))
alert_app = job['entry'][0]['acl']['app']
result_count = job['entry'][0]['content']['resultCount']
log.info("Found job for alert %s. Context is '%s' with %s results." % (alert, alert_app, result_count))

# Get savedsearch settings
uri = '/servicesNS/nobody/%s/admin/savedsearch/%s' % (alert_app, urllib.quote(alert))
try:
    savedsearchResponse, savedsearchContent = rest.simpleRequest(uri, sessionKey=sessionKey, getargs={'output_mode': 'json'})
except splunk.ResourceNotFound, e:
    log.error("%s not found in saved searches, so we're not able to get alert.severity and alert.expires. Have to stop here. Exception: %s" % (alert, e))
    sys.exit(1)
except:
    log.error("Unable to get savedsearch. Unexpected error: %s" % sys.exc_info()[0])

savedsearchContent = json.loads(savedsearchContent)
log.debug("Parsed savedsearch settings: severity=%s expiry=%s digest_mode=%s" % (savedsearchContent['entry'][0]['content']['alert.severity'], savedsearchContent['entry'][0]['content']['alert.expires'], savedsearchContent['entry'][0]['content']['alert.digest_mode'] ))

# Transform expiry to seconds
timeModifiers = { 's': 1, 'm': 60, 'h': 3600, 'd' : 86400, 'w': 604800 }
timeModifier = savedsearchContent['entry'][0]['content']['alert.expires'][-1]
timeRange    = int(savedsearchContent['entry'][0]['content']['alert.expires'][:-1])
ttl          = timeRange * timeModifiers[timeModifier]
log.debug("Transformed %s into %s seconds" % (savedsearchContent['entry'][0]['content']['alert.expires'], ttl))

# Add attributes id to alert metadata
job['job_id']    = job_id
job['ttl']        = ttl

# Read severity from saved search, translate to impact, read urgency from results, translate impact and urgency to priority
# TODO: remove placeholders
job['severity']    = savedsearchContent['entry'][0]['content']['alert.severity']
job['impact']    = getImpact(job['severity'])

# Set globals
alert_time = job['entry'][0]['published']
digest_mode = savedsearchContent['entry'][0]['content']['alert.digest_mode']

#
# Main alert handler part
#

# Run pass-through shell scripts for each alert_handler call
if incident_config['run_alert_script']:
    log.info("Will run alert script '%s' for job_id=%s now." % (incident_config['alert_script'], job_id))

    runshellscript = os.path.join(os.environ.get('SPLUNK_HOME'), 'etc', 'apps', 'search', 'bin', 'runshellscript.py')
    splunk_bin = os.path.join(os.environ.get('SPLUNK_HOME'), 'bin', 'splunk')

    #0    SPLUNK_ARG_0    Script name
    #1    SPLUNK_ARG_1    Number of events returned
    #2    SPLUNK_ARG_2    Search terms
    #3    SPLUNK_ARG_3    Fully qualified query string
    #4    SPLUNK_ARG_4    Name of report
    #5    SPLUNK_ARG_5    Trigger reason. For example, "The number of events was greater than 1."
    #6    SPLUNK_ARG_6    Browser URL to view the report.
    #7    SPLUNK_ARG_7    Not used for historical reasons.
    #8    SPLUNK_ARG_8    File in which the results for the search are stored. Contains raw results.
    args = [splunk_bin, 'cmd', 'python', runshellscript, incident_config['alert_script'], sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7], job_id, sys.argv[8],  ]

    args_stdout = "sessionKey:%s" % sessionKeyOrig + "\n"
    args_stdout = args_stdout + "namespace:%s" % alert_app + "\n"
    log.debug("stdout args for %s: %s" % (incident_config['alert_script'], args_stdout))
    log.debug("args for %s: %s" % (incident_config['alert_script'], args))

    try:
        p = Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=False)
        output = p.communicate(input=args_stdout)
        log.debug("Alert script run finished. RC=%s. Output: %s" % (p.returncode, output[0]))
    except OSError, e:
        log.debug("Alert script failed. Error: %s" % str(e))


log.info("Creating incident for job_id=%s" % job_id)

users = AlertManagerUsers(sessionKey=sessionKey)
user_list = users.getUserList()
notifier = AlertManagerNotifications(sessionKey=sessionKey)

###############################
# Incident creation starts here

# Create unique id
incident_id = str(uuid.uuid4())

# Get results
results = getResults(job_path, incident_id)

# Get result_id
result_id = getResultId(digest_mode, job_path)

# Get urgency from results
job['urgency'] = readUrgencyFromResults(results, incident_config['urgency'], incident_id)

# Calculate priority
job['priority']    = getPriority(job['impact'], job['urgency'])

# Write incident to collection
entry = createNewIncident(alert_time, incident_id, job_id, result_id, alert, 'new', ttl, job['impact'], job['urgency'], job['priority'], config['default_owner'], user_list, notifier, digest_mode, results)
log.info("Incident initial state added to collection for job_id=%s with incident_id=%s" % (job_id, incident_id))

# Write results to collection
writeResultToCollection(results)
log.info("Alert results for job_id=%s incident_id=%s result_id=%s written to collection incident_results" % (job_id, incident_id, str(result_id)))

# Write metadata to index
writeAlertMetadataToIndex(job, incident_id, result_id)

# Done creating incidents

# Auto Previous Resolve - run only once
if incident_config['auto_previous_resolve']:
    autoPreviousResolve(alert, job_id)

#
# Finish
#
end = time.time()
duration = round((end-start), 3)
log.info("Alert handler finished. duration=%ss" % duration)
