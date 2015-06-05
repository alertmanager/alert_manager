import sys
import os
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
import logging
import time
import datetime
import hashlib
import re
import fnmatch

class SuppressionHelper:

    # Setup logger
    log = logging.getLogger('alert_manager_suppression_helper')
    log.propagate = False
    lf = os.path.join(os.environ.get('SPLUNK_HOME'), "var", "log", "splunk", "alert_manager_suppression_helper.log")
    fh     = logging.handlers.RotatingFileHandler(lf, maxBytes=25000000, backupCount=5)
    formatter = logging.Formatter("%(asctime)-15s %(levelname)-5s %(message)s")
    fh.setFormatter(formatter)
    log.addHandler(fh)
    log.setLevel(logging.DEBUG)

    sessionKey  = None

    def __init__(self, sessionKey):
        self.sessionKey = sessionKey

    def compareValue(self, test_value, comparator, pattern_value):
        self.log.debug("compareValue(testvalue=\"%s\", comparator=\"%s\", pattern_value=\"%s\")" % (test_value, comparator, pattern_value))

        if type(test_value) is list:
            test_value = test_value[0]

        if type(pattern_value) is list:
            pattern_value = pattern_value[0]

        if comparator == ">":
            return float(test_value) > float(pattern_value)
        elif comparator == "<":
            return float(test_value) < float(pattern_value)
        elif comparator == "=" or comparator == "==" or comparator == "is":
            return test_value == pattern_value
        elif comparator == "!=" or comparator == "is not":
            return test_value != pattern_value        
        elif comparator == "<=":
            return float(test_value) <= float(pattern_value)
        elif comparator == ">=":
            return float(test_value) >= float(pattern_value)
        elif comparator == "contains":
            return bool(re.match(test_value, pattern_value))
        elif comparator == "does not contain":
            return not bool(re.match(test_value, pattern_value))
        elif comparator == "starts with":
            return bool(re.match("^" + pattern_value + ".*", test_value))
        elif comparator == "ends with":
            return bool(re.match(".*" + pattern_value + "$", test_value))
        else:
            return False

    def checkSuppression(self, alert, context):
        self.log.info("Checking for matching suppression rules for alert=%s" % alert)
        #query = '{  "disabled": false, "$or": [ { "scope": "*" } , { "scope": "'+ alert +'" } ] }'
        query = '{ "disabled": false, "$or": [{ "scope" : "'+ alert +'"}, { "scope": { "$regex": "\\\*"}  } ]}'
        uri = '/servicesNS/nobody/alert_manager/storage/collections/data/suppression_rules?query=%s' % urllib.quote(query)
        serverResponse, serverContent = rest.simpleRequest(uri, sessionKey=self.sessionKey)    
        
        if serverResponse['status'] == "200" and len(serverContent) > 0:
            suppression_rules = json.loads(serverContent)
            self.log.debug("Got %s suppression rule(s) matching the scope ('*' or '%s')." % (len(suppression_rules), alert))
            matches = []
            unmatching_rules = []
            rule_names = []
            for suppression_rule in suppression_rules:

                # check if scope matches alert <-> suppression_rule['scope']
                if fnmatch.fnmatch(alert, suppression_rule['scope']):

                    rule_names.append(suppression_rule['suppression_title'])

                    if "rules" in suppression_rule:
                        for rule in suppression_rule["rules"]:
                            self.log.debug("Rule: suppression_title=\"%s\" field=\"%s\" condition=\"%s\" value=\"%s\"" % (suppression_rule['suppression_title'], rule["field"], rule["condition"], rule["value"]))

                            value_match = re.match("^\$(.*)\$$", rule["value"])
                            if bool(value_match):
                                value_field_name = value_match.group(1)
                                if len(context["result"]) > 0 and value_field_name in context["result"][0]:
                                    rule["value"] =  context["result"][0][value_field_name]   
                                else:
                                    self.log.warn("Invalid suppression rule: value field %s not found in results." % value_field_name)


                            if rule["field"] == "_time" or rule["field"] == "time":
                                # FIXME: Change timestamp to real timestamp from incident
                                match = self.compareValue(int(time.time()), rule["condition"], rule["value"])
                                matches.append(match)
                                if not match:
                                    unmatching_rules.append(rule)
                                    self.log.debug("Rule %s didn't match." % json.dumps(rule))
                            else:
                                field_match = re.match("^\$(.*)\$$", rule["field"])
                                if bool(field_match):
                                    field_name = field_match.group(1)
                                    if field_name in context:
                                        match = self.compareValue(context[field_name], rule["condition"], rule["value"])
                                        matches.append(match)
                                        if not match:
                                            unmatching_rules.append(rule)
                                            self.log.debug("Rule %s didn't match." % json.dumps(rule))
                                    elif len(context["result"]) > 0 and field_name in context["result"][0]:
                                        match = self.compareValue(context["result"][0][field_name], rule["condition"], rule["value"])
                                        matches.append(match)
                                        if not match:
                                            unmatching_rules.append(rule)
                                            self.log.debug("Rule %s didn't match." % json.dumps(rule))
                                    else:
                                        self.log.warn("Invalid suppression rule: field %s not found in results." % field_name)
                                else:
                                    self.log.warn("Suppression rule has an invalid field content format.")
                else:
                    self.log.info("Scope from rule (%s) didn't match to alert name (%s), skipping..." % (suppression_rule['scope'], alert))

            if len(matches) < 1:
                self.log.info("Suppression failed: No matches found.")
                return False, []

            elif False in matches:
                self.log.info("Suppression failed: Not all rules are matching. Umatching rules: %s" % json.dumps(unmatching_rules))
                return False, []
            else:
                self.log.info("Suppression successful: All supression rule(s) are matching: %s" % ' '.join(rule_names))
                return True, rule_names
        else:
            self.log.debug("Failed to get suppression rules with query=%s. Maybe no matching rules found? (status=%s)" % (query, serverResponse['status']))
            return False, []