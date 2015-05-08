#!/bin/sh

read -p "Splunk username: " uname
stty -echo
read -p "Password: " passw; echo
stty echo

SPLUNK_HOME=/opt/splunk
SPLUNK_HOST=https://127.0.0.1:8089
SPLUNK_USER=$uname
SPLUNK_PASS=$passw

# TODO: check if data exists

# Purge notification schemes
#curl -k -u ${SPLUNK_USER}:${SPLUNK_PASS} -X DELETE ${SPLUNK_HOST}/servicesNS/nobody/alert_manager/storage/collections/data/notification_schemes

# Load default notification schemes
#curl -k -u ${SPLUNK_USER}:${SPLUNK_PASS} ${SPLUNK_HOST}/servicesNS/nobody/alert_manager/storage/collections/data/notification_schemes/batch_save -H 'Content-Type: application/json' -d @${SPLUNK_HOME}/etc/apps/alert_manager/appserver/src/default_notification_scheme.json
#curl -k -u ${SPLUNK_USER}:${SPLUNK_PASS} ${SPLUNK_HOST}/servicesNS/nobody/alert_manager/storage/collections/data/notification_schemes/batch_save -H 'Content-Type: application/json' -d @${SPLUNK_HOME}/etc/apps/alert_manager/appserver/src/custom_notification_scheme.json

# Purge email templates
#curl -k -u ${SPLUNK_USER}:${SPLUNK_PASS} -X DELETE ${SPLUNK_HOST}/servicesNS/nobody/alert_manager/storage/collections/data/email_templates

# Load default email templates
#curl -k -u ${SPLUNK_USER}:${SPLUNK_PASS} ${SPLUNK_HOST}/servicesNS/nobody/alert_manager/storage/collections/data/email_templates/batch_save -H 'Content-Type: application/json' -d @${SPLUNK_HOME}/etc/apps/alert_manager/appserver/src/default_email_templates.json

# Purge suppression rules
curl -k -u ${SPLUNK_USER}:${SPLUNK_PASS} -X DELETE ${SPLUNK_HOST}/servicesNS/nobody/alert_manager/storage/collections/data/suppression_rules
curl -k -u ${SPLUNK_USER}:${SPLUNK_PASS} ${SPLUNK_HOST}/servicesNS/nobody/alert_manager/storage/collections/data/suppression_rules/batch_save -H 'Content-Type: application/json' -d @${SPLUNK_HOME}/etc/apps/alert_manager/appserver/src/custom_suppression_rules.json