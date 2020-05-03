#!/bin/sh
$SPLUNK_HOME/bin/splunk cmd python3.7 $SPLUNK_HOME/etc/apps/alert_manager/bin/alert_manager_migrate-v3.0.py
