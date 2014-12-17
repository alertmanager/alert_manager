# Alert Manager
- **Authors**:		Simon Balz <simon@balz.me>, Mika Borner <mika.borner@gmail.com>
- **Description**:	Extended Splunk Alert Manager with advanced reporting on alerts, workflows (modify assignee, status, severity) and auto-resolve features
- **Version**: 		0.5

## Changelog
- **2014-12-17** mika.borner@gmail.com
        - Added KPI Report - Incident Status (first rough version)
        - Improved KPI Report - Resolved Incidents with Dropdown Chaining.
- **2014-12-16** mika.borner@gmail.com
	- Added KPI Report - Resolved Incidents (first rough version)
	- Updated Datamodel for Incident Changes
	- Fixed small bug with non-existent priority informational
	- Changed logging format for incident changes to make reporting easier
- **2014-12-16** simon@balz.me
	- Updated event when adding or changing incidents to provide origin, event_id and comment. Added comment form to modal dialog.
	- Added owner filter to incident posture
	- Added incident change history to table row expansion in incident posture (first rough version)
	- Released v0.5 with better README
	- Updated alert_handler and alert_manager_scheduler to write change events on auto resolve (ttl and previous)
- **2014-12-15** simon@balz.me
	- Added ability to change incidents from posture dashboard (very rough version)
	- Changed nav and icon color to not use the same as the maps app by ziegfried uses ;)
	- Updated license
	- Improved edit incidents modal dialog
	- Added user field to incident change event
	- Fixed a bug in alert_handler.py to use correct filter when auto_previous_resolve
	- Removed status closed for now since we just don't need it.
	- Changed alert_handler.py to write an event when incident is created
- **2014-12-14** simon@balz.me
	- Added support to run alert shell scripts
	- Changed ttl to take from alert.expires
	- Released v0.4
- **2014-12-14** mika.borner@gmail.com 
	- Field renaming to make them more CIM compliant
		- current_assignee => owner, auto_assign_user => auto_assign_owner
		- current_state => status, status_name => status_description
		- search_name => alert
	- Added Alert Tagging to Settings and Posture
	- Fixed Singlevalue text for conformity (Info -> Informational)
	- Renamed lookup table alert_urgency.csv -> alert_urgencies.csv
- **2014-12-13** simon@balz.me
	- Prepared alert settings for alert script run
	- Fixed minor UI issues
- **2014-12-13** mika.borner@gmail.com
	- Added category and subcategory to alert settings and dashboards
	- Added Pivot to navigation
	- Created macro for all_alerts
	- Using tstats as there is a bug in timecharting pivots
	- pivot version saved as all_alerts_pivot
	- Using macro in incident posture and reporting
- **2014-12-12** mika.borner@gmail.com
	- Added priority and urgency to Incident Posture
	- Added priority field to alert settings
	- Added Datamodel and fixed field consistency
- **2014-12-11** simon@balz.me
	- Validation for alert settings
- **2014-12-10** simon@balz.me
	- Released v0.3
	- Finally made alert settings page working (you can activate auto-assing and auto-resolve options for alerts now)
- **2014-12-09** simon@balz.me
	- Improved preparations for alert settings view (button now fetches data from the table and reloads the search)
- **2014-12-08** simon@balz.me
	- Renamed incident_overview to incident_posture
	- Splitted reporting into dedicated dashboard (incident_reporting)
	- Prepared alert settings view
	- Improved logging in alert handler script
	- Added alert scneario "auto assign to user" and "auto resolve previous incidents"
	- Added scheduler with auto_ttl_resolve scenario
	- Added auto_ttl_resolved and auto_previous_resolved as incident state
- **2014-12-07** simon@balz.me
	- Released v0.2						   
- **2014-12-07** simon@balz.me
	- Several enhancements (Added app config with app setup page, REST handler and config files; lots of UI improvements... )
- **2014-12-06** simon@balz.me
 	- Initial revision  

## Release Notes
- **v0.5** New features: Change incidents (workflow, priority); new event on incident creation or update; bugfixing
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
1. Unpack app to $SPLUNK_HOME/etc/apps
2. Link $SPLUNK_HOME/etc/apps/alert_manager/bin/alert_handler.py to $SPLUNK_HOME/bin/scripts/:
 
`cd $SPLUNK_HOME/bin/script && ln -s ../../etc/apps/alert_manager/bin/alert_handler.py alert_handler.py`

3. Copy $SPLUNK_HOME/etc/apps/alert_manager/default/alert_manager.conf $SPLUNK_HOME/etc/apps/alert_manager/local and edit settings (see README/alert_manager.conf.spec)

#### Note for distributed environments
- The alert manager runs mostly on the search head (since we use the App Key Value Store)
- Due the usage of the App Key Value Store, there's no compatibility with the Search Head Clustering introduced in Splunk v6.2
- If you have separated instances for Search heads and indexers and you're forwarding events from the Search head to the indexers, only configure indexes.conf with the alerts index (or your own...) on the indexer. A separate add-on for indexer only will follow
- The alert manager runs a script each 30 seconds (in form of a scripted input) to look for incidents to be resolved after ttl is reached

### Alert Manager Settings
1. Configure global settings in the App setup page (Manage Apps -> Alert Manager -> Set up)
	- **Index:** Where the alert manager will store the alert metadata, alert results and change events
	- **Default Assignee:** Username of the assignee a newly created incident will be assigned to
	- **Default Priority:** Priority to be used for new incidents fired by the alert
	- **Disable saving Alert results to index:** Wheter to index alert results again in the index specified above, so it's possible to see them after they expired. Currently, there's no related feature in the alert manager.
2. Configure per-alert settings in the "Alert Settings" page

### Configure Alerts
1. Set "alert_handler.py" (without quotes) as alert action script filename
2. Configure the alert to be listet in Triggered Alerts (necessary to view the alert results without indexing them)
3. Configure alert permissions to be visible globally (necessary only to configure settings with "Alert Settings" view. In case you don't wan't to set your alerts to be exported globally, you can also add the alerts manuall to the alert settings by right-click to the table -> Insert row below)


### Per Alert Settings
- **Run Alert Script:** You can run a classical alert script (<http://docs.splunk.com/Documentation/Splunk/latest/Alert/Configuringscriptedalerts>). Place your script in $SPLUNKH_HOME/bin/scripts, enable run_alert_script and add the file name (without path!) to the alert_script field. All arguments will be passed to the script as you would configure it directly as an alert action.
- **Auto Assign:** Assign newly created incidents related to the alert to a user. Enter the username to the auto_assign_user field and enable auto_assign
- **Auto Resolve Previous:** Automatically resolve already existing incidents with status=new related to the alert when creating a new one
- **Auto Resolve after TTL:** Aumatically resolve existing incidents with status=new when the alert.expires time is reached

## Roadmap
- E-mail notifications on incident assignement
- Extension hooks during alert metadata save (call to External systems)

## Known Issues
- Alert Manager Scheduler currently only works on windows (auto-ttl-resolve scenario)

## License
- **This work is licensed under a Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.**
- Details: <http://creativecommons.org/licenses/by-nc-sa/4.0/>
