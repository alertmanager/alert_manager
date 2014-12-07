# Alert Manager
- Author:		Simon Balz <simon@balz.me>, Mika Borner <mika.borner@gmail.com>
- Description:	Extended Splunk Alert Manager with simple workflow possibilites (Reassign alerts, edit categories, change severity, change status)$
- Version: 		0.2

## Changelog
- 2014-12-07 simon@balz.me - Several enhancements
- 2014-12-06 simon@balz.me - Initial revision  

## Release Notes
- **v0.2** Added config parsing (alert_manager.conf)
- **v0.1** First working version

## Installation
### Alert Manager
- Unpack app to $SPLUNK_HOME/etc/apps
- Link $SPLUNK_HOME/etc/apps/alert_manager/bin/alert_handler.py to $SPLUNK_HOME/bin/scripts/
- Copy $SPLUNK_HOME/etc/apps/alert_manager/default/alert_manager.conf $SPLUNK_HOME/etc/apps/alert_manager/local and edit settings (see README/alert_manager.conf.spec)

## Roadmap
- Make alert editable (Severity, Assigne, Status)
- Categorization
- Data model
- Propper logging in alert_handler.py

## Issues
- n/a
