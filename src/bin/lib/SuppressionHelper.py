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

from AlertManagerLogger import *

class SuppressionHelper:

    # Setup logger
    log = setupLogger('suppression_helper')

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

            matching_rules = []
            unmatching_rules = []

            for suppression_rule in suppression_rules:

                # check if scope matches alert <-> suppression_rule['scope']
                if fnmatch.fnmatch(alert, suppression_rule['scope']):

                    match_type = 'all'
                    if 'match_type' in suppression_rule and suppression_rule['match_type'] != '':
                        match_type = suppression_rule['match_type']

                    self.log.debug("Match type: %s" % match_type)

                    # iterate over rules of suppressions
                    ruleset_suppression_all = True
                    ruleset_suppression_any = False

                    if "rules" in suppression_rule:
                        for rule in suppression_rule["rules"]:
                            rule_suppression = False

                            self.log.debug("Rule: suppression_title=\"%s\" field=\"%s\" condition=\"%s\" value=\"%s\"" % (suppression_rule['suppression_title'], rule["field"], rule["condition"], rule["value"]))

                            # Parse value from results
                            value_match = re.match("^\$(.*)\$$", rule["value"])
                            if bool(value_match):
                                value_field_name = value_match.group(1)
                                if len(context["result"]) > 0 and value_field_name in context["result"][0]:
                                    rule["value"] =  context["result"][0][value_field_name]   
                                else:
                                    self.log.warn("Invalid suppression rule: value field %s not found in results." % value_field_name)

                            # Parse special case "time"
                            if rule["field"] == "_time" or rule["field"] == "time":
                                # FIXME: Change timestamp to real timestamp from incident
                                match = self.compareValue(int(time.time()), rule["condition"], rule["value"])
                                if not match:
                                    rule_suppression = False
                                    self.log.debug("Rule %s didn't match." % json.dumps(rule))
                                else:
                                    rule_suppression = True
                                    self.log.debug("Rule %s matched." % json.dumps(rule))

                            # Parse rules refering to fields
                            else:
                                field_match = re.match("^\$result.(.*)\$$", rule["field"])
                                field_match_result = re.match("^\$result\.(.*)\$$", rule["field"])
                                
                                if bool(field_match_result):
                                    field_name = field_match.group(1)
                                    if 'result' in context and field_name in context["result"]:
                                        match = self.compareValue(context["result"][field_name], rule["condition"], rule["value"])
                                        if not match:
                                            rule_suppression = False
                                            self.log.debug("Rule %s didn't match." % json.dumps(rule))
                                        else:
                                            rule_suppression = True
                                            self.log.debug("Rule %s matched." % json.dumps(rule))    
                                    else:
                                        self.log.warn("Invalid suppression rule: field %s not found in result." % field_name)                                    

                                elif bool(field_match):
                                    field_name = field_match.group(1)
                                    # Search for field in results
                                    if field_name in context:
                                        match = self.compareValue(context[field_name], rule["condition"], rule["value"])
                                        if not match:
                                            rule_suppression = False
                                            self.log.debug("Rule %s didn't match." % json.dumps(rule))
                                        else:
                                            rule_suppression = True
                                            self.log.debug("Rule %s matched." % json.dumps(rule))

                                    elif len(context["result"]) > 0 and field_name in context["result"][0]:
                                        match = self.compareValue(context["result"][0][field_name], rule["condition"], rule["value"])
                                        if not match:
                                            rule_suppression = False
                                            self.log.debug("Rule %s didn't match." % json.dumps(rule))
                                        else:
                                            rule_suppression = True
                                            self.log.debug("Rule %s matched." % json.dumps(rule))    

                                    else:
                                        self.log.warn("Invalid suppression rule: field %s not found in context." % field_name)

                                else:
                                    self.log.warn("Suppression rule has an invalid field content format.")

                            # Apply suppression state for this specific rule
                            if rule_suppression:
                                ruleset_suppression_any = True

                            if ruleset_suppression_all and rule_suppression:
                                ruleset_suppression_all = True
                            else:
                                ruleset_suppression_all = False


                        # Check if suppression for this ruleset was successful
                        if match_type == "all":
                            if ruleset_suppression_all:
                                matching_rules.append(suppression_rule['suppression_title'])
                                self.log.info("Suppression for rule with suppression_title='%s' was successful (match_type=%s)." % (suppression_rule['suppression_title'], match_type))
                            else:
                                unmatching_rules.append(suppression_rule['suppression_title'])
                                self.log.info("Suppression for rule with suppression_title='%s' was NOT successful (match_type=%s)." % (suppression_rule['suppression_title'], match_type))

                        if match_type == "any":
                            if ruleset_suppression_any:
                                matching_rules.append(suppression_rule['suppression_title'])
                                self.log.info("Suppression for rule with suppression_title='%s' was successful (match_type=%s)." % (suppression_rule['suppression_title'], match_type))


                else:
                    self.log.info("Scope from rule (%s) didn't match to alert name (%s), skipping..." % (suppression_rule['scope'], alert))

            # Check if suppression was successful
            if len(matching_rules) > 0:
                self.log.info("Suppression successful: At least one matching suppression rule(s) was found. Matching rules : %s. Unmatching rules: %s" % (', '.join(matching_rules), ', '.join(unmatching_rules)))
                return True, matching_rules
            else:
                self.log.info("Suppression failed: No matching rules found. Unmatching rules: %s" % ', '.join(unmatching_rules))
                return False, []

        else:
            self.log.debug("Failed to get suppression rules with query=%s. Maybe no matching rules found? (status=%s)" % (query, serverResponse['status']))
            return False, []