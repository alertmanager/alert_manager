#!/bin/sh

SPLUNK_HOME=/opt/splunk
SPLUNK_HOST=https://127.0.0.1:8089
SPLUNK_USER=admin
SPLUNK_PASS=changeme


# Purge notification schemes
curl -k -u ${SPLUNK_USER}:${SPLUNK_PASS} -X DELETE ${SPLUNK_HOST}/servicesNS/nobody/alert_manager/storage/collections/data/notification_schemes

# Load default notification scheme
curl -k -u ${SPLUNK_USER}:${SPLUNK_PASS} ${SPLUNK_HOST}/servicesNS/nobody/alert_manager/storage/collections/data/notification_schemes -H 'Content-Type: application/json' -d @${SPLUNK_HOME}/etc/apps/alert_manager/appserver/src/default_notification_scheme.json