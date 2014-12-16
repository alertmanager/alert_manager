# Alert Manager
- **Authors**:		Simon Balz <simon@balz.me>, Mika Borner <mika.borner@gmail.com>
- **Description**:	Extended Splunk Alert Manager with advanced reporting on alerts, workflows (modify assignee, status, severity) and auto-resolve features
- **Version**: 		0.4

## Changelog
- **2014-12-16** simon@balz.me 			- Updated event when adding or changing incidents to provide origin, event_id and comment. Added comment form to modal dialog.
- **2014-12-15** simon@balz.me 			- Added ability to change incidents from posture dashboard (very rough version)
						- Changed nav and icon color to not use the same as the maps app by ziegfried uses ;)
						- Updated license
						- Improved edit incidents modal dialog
						- Added user field to incident change event
						- Fixed a bug in alert_handler.py to use correct filter when auto_previous_resolve
						- Removed status closed for now since we just don't need it.
						- Changed alert_handler.py to write an event when incident is created
- **2014-12-14** simon@balz.me 			- Added support to run alert shell scripts
						- Changed ttl to take from alert.expires
						- Released v0.4
- **2014-12-14** mika.borner@gmail.com  - Field renaming to make them more CIM compliant
						- current_assignee => owner, auto_assign_user => auto_assign_owner
						- current_state => status, status_name => status_description
						- search_name => alert
- **2014-12-14** mika.borner@gmail.com  - Added Alert Tagging to Settings and Posture
					- Fixed Singlevalue text for conformity (Info -> Informational)
					- Renamed lookup table alert_urgency.csv -> alert_urgencies.csv
- **2014-12-13** simon@balz.me          - Prepared alert settings for alert script run
						- Fixed minor UI issues
- **2014-12-13** mika.borner@gmail.com  - Added category and subcategory to alert settings and dashboards
- **2014-12-13** mika.borner@gmail.com  - Added Pivot to navigation
- **2014-12-13** mika.borner@gmail.com  - Created macro for `all_alerts`
						-Using tstats as there is a bug in timecharting pivotsj
						-pivot version saved as `all_alerts_pivot`
						-Using macro in incident posture and reporting
- **2014-12-12** mika.borner@gmail.com  - Added priority and urgency to Incident Posture
- **2014-12-12** mika.borner@gmail.com  - Added priority field to alert settings
- **2014-12-11** mika.borner@gmail.com  - Added Datamodel and fixed field consistency
- **2014-12-11** simon@balz.me          - Validation for alert settings
- **2014-12-10** simon@balz.me          - Release v0.3
- **2014-12-10** simon@balz.me          - Finally made alert settings page working (you can activate auto-assing and auto-resolve options for alerts now)
- **2014-12-09** simon@balz.me          - Improved preparations for alert settings view (button now fetches data from the table and reloads the search)
- **2014-12-08** simon@balz.me          - Renamed incident_overview to incident_posture
						   - Splitted reporting into dedicated dashboard (incident_reporting)
						   - Prepared alert settings view
						   - Improved logging in alert handler script
						   - Added alert scneario "auto assign to user" and "auto resolve previous incidents"
						   - Added scheduler with auto_ttl_resolve scenario
						   - Added auto_ttl_resolved and auto_previous_resolved as incident state
- **2014-12-07** simon@balz.me          - Released v0.2						   
- **2014-12-07** simon@balz.me          - Several enhancements (Added app config with app setup page, REST handler and config files; lots of UI improvements... )
- **2014-12-06** simon@balz.me          - Initial revision  

## Release Notes
- **v0.4** Again a lot of updates and improvements: CIM compliancy; ability to run classical alert scripts; incident categorization and tagging; ES-like urgency calculation; many UI improvements
- **v0.3** Release with major improvements (better see changelog :-) )
- **v0.2** Added config parsing (alert_manager.conf)
- **v0.1** First working version

## Credits
- Visualization snippets from Splunk 6.x Dashboard Examples app (https://apps.splunk.com/app/1603/)
- Single value design from Splunk App from AWS (https://apps.splunk.com/app/1274/)
- Handsontable (http://handsontable.com/)

## Prerequisites
- Splunk v6.2+ (we use the App Key Value Store)
- Alerts (Saved searches with alert action)

## Usage
### Installation
- Unpack app to $SPLUNK_HOME/etc/apps
- Link $SPLUNK_HOME/etc/apps/alert_manager/bin/alert_handler.py to $SPLUNK_HOME/bin/scripts/ (cd $SPLUNK_HOME/bin/script && ln -s ../../etc/apps/alert_manager/bin/alert_handler.py alert_handler.py)
- Copy $SPLUNK_HOME/etc/apps/alert_manager/default/alert_manager.conf $SPLUNK_HOME/etc/apps/alert_manager/local and edit settings (see README/alert_manager.conf.spec)

### Configure Alerts
1. Set alert_handler.py as alert action script filename
2. Configure the alert to be listet in Triggered Alerts (necessary to view the alert results without indexing them)
3. Configure alert permissions to be visible globally (necessary to configure settings with "Alert Settings" view)

### Settings
1. Configure global settings in the App setup page (Manage Apps -> Alert Manager -> Set up)
- Index: Where the alert manager will store the alert metadata
- Default Assignee: Username of the assignee a newly created incident will be assigned to
- Disable saving Alert results to index: Wheter to index alert results again in the index specified above, so it's possible to see them after they expired
2. Configure per-alert settings in the "Alert Settings" page
- Auto Assign: tbd
- Auto Resolve Previous: tbd
- Auto Resolve after TTL: tbd

## Roadmap
- Make incidents editable (Severity, Assigne, Status)
- E-mail notifications on incident assignement
- Incident Categorization
- Data model
- Extension hooks during alert metadata save (call to External systems)

## Known Issues
- Alert Manager Scheduler currently only works on windows (auto-ttl-resolve scenario)

## License
**This work is licensed under a Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.**
http://creativecommons.org/licenses/by-nc-sa/4.0/
