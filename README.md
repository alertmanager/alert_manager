# Alert Manager
- **Authors**:		Simon Balz <simon@balz.me>, Mika Borner <mika.borner@gmail.com>
- **Description**:	Extended Splunk Alert Manager with advanced reporting on alerts and simple alert workflow possibilites (Reassign alerts, edit categories, change severity, change status)
- **Version**: 		0.2

## Changelog
- **2014-12-08** simon@balz.me - Renamed incident_overview to incident_posture
						   - Splitted reporting into dedicated dashboard (incident_reporting)
						   - Prepared alert settings view
						   - Improved logging in alert handler script
						   - Added alert scneario "auto assign to user" and "auto resolve previous incidents"
						   - Added scheduler with auto_ttl_resolve scenario
						   - Added auto_ttl_resolved and auto_previous_resolved as incident state
- **2014-12-07** simon@balz.me - Several enhancements (Added app config with app setup page, REST handler and config files; lots of UI improvements... )
- **2014-12-06** simon@balz.me - Initial revision  

## Release Notes
- **v0.2** Added config parsing (alert_manager.conf)
- **v0.1** First working version

## Credits
- Visualization snippets from Splunk 6.x Dashboard Examples app (https://apps.splunk.com/app/1603/)
- Single value design from Splunk App from AWS (https://apps.splunk.com/app/1274/)

## Usage
### Installation
- Unpack app to $SPLUNK_HOME/etc/apps
- Link $SPLUNK_HOME/etc/apps/alert_manager/bin/alert_handler.py to $SPLUNK_HOME/bin/scripts/
- Copy $SPLUNK_HOME/etc/apps/alert_manager/default/alert_manager.conf $SPLUNK_HOME/etc/apps/alert_manager/local and edit settings (see README/alert_manager.conf.spec)

## Configure Alerts
1. Set alert_handler.py as alert action script filename
2. Configure alert permissions to be visible globally (necessary to configure settings with "Alert Settings" view)

### Settings
1. Configure global settings in the App setup page (Manage Apps -> Alert Manager -> Set up)
- Default Assignee: tbd
2. Configure per-alert settings in the "Alert Settings" page
- Auto Assign: tbd
- Auto Resolve Previous: tbd
- Auto Resolve after TTL: tbd

## Roadmap
- Make alert editable (Severity, Assigne, Status)
- Use Case implementation (auto assignement, auto resolve, ... scenarios)
- Categorization
- Data model
- Extension hooks during alert metadata save (call to External systems)
- Application setup (setup.xml, e.g. default email recipient on new alert)

## Issues
- n/a
