# Alert Manager
- **Authors**:		Simon Balz <simon@balz.me>, Mika Borner <mika.borner@gmail.com>
- **Description**:	Extended Splunk Alert Manager with advanced reporting on alerts, workflows (modify assignee, status, severity) and auto-resolve features
- **Version**: 		0.8

## Introduction
The Alert Manager adds simple incident workflows to Splunk. The general purpose is to provide a common app with dashboards in order to investigate fired alerts or notable events. It can be used with every Splunk alert and works as an extension on top of the Splunk built-in alerting mechanism. 

- Awareness of your current operational situation with the incident posture dashboard
- Analyze root cause of incidents with only a few clicks
- Review and adjust the urgency of incidents to improve operations scheduling
- Dispatch incidents to the person in charge
- Track and report incident workflow KPIs
- Tag and categorize incidents

## Features
- Works as scripted alert action to catch enriched metadata of fired alerts and write them to a configurable index
- Each fired alert will create an incident
- Incidents can be configured to run well-know Splunk scripted alert scripts
- Incidents may be reassigned manually or auto-assigned to specific users
- Incidents may be changed to another priority and status
- Incidents can be configured to get auto-resolved when a new incident is created from the same alert
- Incidents can be configured to get auto-resolved when the alert's ttl is reached

## Release Notes
- **v0.8**	/	2014-12-26
	- Minor bugfixes & enhancements
	- Documentation improvements
	- App for demo data
- **v0.7**	/	2014-12-21
	- Trend indicators for single values in incident posture dashboard
	- Full Windows support
	- Bugfixes
- **v0.6**	/	2014-12-18
	- New TA for distributed Splunk environment support
	- Improved incident settings (former alert settings) to work with non-global visible alerts
	- Added incident change events and KPI reporting based on them; 
- **v0.5**	/	2014-12-16
	- Added change incidents (workflow, priority) feature
	- Indexed events on incident creation or update
	- Bugfixes
- **v0.4**	/	2014-12-14
	- Again a lot of updates and improvements
	- CIM compliancy
	- Ability to run classical alert scripts; incident categorization and tagging
	- ES-like urgency calculation; many UI improvements
- **v0.3**	/	2014-12-10
	- Release with major improvements (better see changelog :-) )
- **v0.2**	/	2014-12-07	
	- Added config parsing (alert_manager.conf)
- **v0.1**	/	2014-12-07
	- First working version

## Changelog
- **2014-12-28** simon@balz.me
	- Added class and endpoint to get list of users
- **2014-12-28** mika.borner@gmail.com
	- Calculating duration differently when current status in new or incident resolved. Using info_max_time as comparison 
- **2014-12-27** simon@balz.me
	- Improved app setup to check for index existance
	- Added placeholders for app documentation in the navigation
- **2014-12-26** simon@balz.me
	- Better legibility for trend indicators
	- Fixed missing fatal severity consideration
	- Documentation update
	- Released v0.8
	- Fixed hardcoded index filtering
- **2014-12-24** simon@balz.me
	- Added auto_assigned status to several dashboards
	- Minor enhancements for kpi_report_resolved_incidents dashboard
- **2014-12-23** simon@balz.me
	- Documentation improvements
	- Improved incident auto assignment
		- Better tracking
		- Changed status to 'auto_assigned', adjusted MongoDB queries
- **2014-12-21** simon@balz.me
	- Added previous_status to event at auto_*_resolve scenarios
	- Added possibility to remove incident settings (right click to table -> remove row)
	- Renamed splunk web controllers
	- Fixed alert_handler.py to work on windows
	- Fixed alert manager scheduler to work on windows (added windows-style scripted input; fixes in alert_manager_scheduler.py)
	- Released v0.7
	- Renamed handsontableview to incidentsettingsview
	- Added user settings view and endpoint implementation (still not finished)
- **2014-12-19** simon@balz.me
	- Added single value trends, improved incident posture dashboard
- **2014-12-19** mika.borner@gmail.com
	- Minor bugfixes for KPI Reports
- **2014-12-18** mika.borner@gmail.com
	- Fixing KPI Report - Incident Status - Still some bugs
- **2014-12-18** simon@balz.me
	- Added app context selector for alert_settings. Renamed alert_settings to incident_settings.
	- Improved incident settings to show help as tooltip
	- Installation instructions update	
	- Fixed a bug in alert handler when running a Splunk alert script (wrong argument were passed)
	- Fixed and improved incident detail row expansion in incident posture dashboard
	- Released v0.6.2
- **2014-12-17** simon@balz.me
	- Added correct scope when trying to get savedsearch settings in alert_handler. Added error handling.
- **2014-12-17** mika.borner@gmail.com
	- Added KPI Report - Incident Status (first rough version)
	- Improved KPI Report - Resolved Incidents with Dropdown Chaining.
	- App split into alert_manager and TA-alert_manager
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

## Credits
- Visualization snippets from Splunk 6.x Dashboard Examples app (https://apps.splunk.com/app/1603/)
- Single value design from Splunk App from AWS (https://apps.splunk.com/app/1274/)
- Handsontable (http://handsontable.com/)

## Prerequisites
- Splunk v6.2+ (we use the App Key Value Store)
- Alerts (Saved searches with alert action)
- Technology Add-on for Alert Manager

## Installation and Usage
### Deployment Matrix

<table>
	<tr>
		<td></td>
		<td>Alert Manager</td>
		<td>Technology Add-on for Alert Manager</td>
		<td>Supporting Add-on for Alert Manager Demo Data</td>
	</tr>
    <tr>
        <td>Search Head</td>
        <td>x</td>
        <td>x</td>
        <td>x</td>
    </tr>
    <tr>
    	<td>Indexer</td>
    	<td></td>
    	<td>x</td>
    	<td></td>
    </tr>
</table>

**Note:** If you forward events from the search head trough heavy forwarder to the indexer, install the Add-on on the heavy forwarder and disable the index.

### Installation
1. Unpack and install the app and Add-on according to the deployment matrix
	- Download the latest Add-on here: <https://github.com/simcen/TA-alert_manager/archive/master.zip>
2. Link $SPLUNK_HOME/etc/apps/alert_manager/bin/alert_handler.py to $SPLUNK_HOME/bin/scripts/:
	- Linux:

	`cd $SPLUNK_HOME/bin/scripts && ln -s ../../etc/apps/alert_manager/bin/alert_handler.py alert_handler.py`
	
	- Windows (run with administrative privileges):


	`cd %SPLUNK_HOME && mklink alert_handler.py ..\..\etc\apps\alert_manager\bin\alert_handler.py`

3. Restart Splunk
4. Configure the alert manager global settings in the app setup

#### Demo Data
For testing purposes, we ship a separate app containing static demo data and demo alerts.
- Static demo data adds some pre-generated incidents with some workflow examples in order to see the KPI dashbaords working
- Demo alerts are configured to see different live alert examples, like auto assign/resolve scenarios and support for realtime alerts

To add demo data, follow these instructions:

1. Unpack and install the "Supporting Add-on for Alert Manager Demo Data" (app folder name SA-alert_manager_demo) to $SPLUNK_HOME/etc/apps
2. Restart Splunk
3. Open Splunk and switch to the "Alert Manager Demo Data" app
4. Follow the instructions in the "Demo Data Setup" view

#### Note for distributed environments
- The alert manager runs mostly on the search head (since we use the App Key Value Store)
- Due to the usage of the App Key Value Store, there's no compatibility with the Search Head Clustering introduced in Splunk v6.2
- The alert manager runs a script each 30 seconds (in form of a scripted input) to look for incidents to be resolved after ttl is reached

### Alert Manager Settings
1. Configure global settings in the App setup page (Manage Apps -> Alert Manager -> Set up)
	- **Index:** Where the alert manager will store the alert metadata, alert results and change events
	- **Default Assignee:** Username of the assignee a newly created incident will be assigned to
	- **Default Priority:** Priority to be used for new incidents fired by the alert
	- **Disable saving Alert results to index:** Whether to index alert results again in the index specified above, so it's possible to see them after they expired. Currently, there's no related feature in the alert manager.
2. Configure per-alert settings in the "Alert Settings" page

### Configure Alerts
1. Set "alert_handler.py" (without quotes) as alert action script filename
2. Configure the alert to be listet in Triggered Alerts (necessary to view the alert results without indexing them)
3. Configure incident settings (Go to the Alert Manager app -> Settings -> Incident Settings)
	- Note: By default, only alerts configured as globally visible are shown in the list. In case you're missing an alert, try to select the correct app scope with the pulldown.

### Per Alert Settings
- **Run Alert Script:** You can run a classical alert script (<http://docs.splunk.com/Documentation/Splunk/latest/Alert/Configuringscriptedalerts>). Place your script in $SPLUNKH_HOME/bin/scripts, enable run_alert_script and add the file name (without path!) to the alert_script field. All arguments will be passed to the script as you would configure it directly as an alert action.
- **Auto Assign:** Assign newly created incidents related to the alert to a user. Enter the username to the auto_assign_user field and enable auto_assign
- **Auto Resolve Previous:** Automatically resolve already existing incidents with status=new related to the alert when creating a new one
- **Auto Resolve after TTL:** Automatically resolve existing incidents with status=new when the alert.expires time is reached

## Roadmap
- Custom incident handlers to extend the alert manager’s functionality
- Custom e-mail notifications based on templates
- Incident enrichment with search data

## Known Issues
- n/a

## License
- **This work is licensed under a Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.**
- Details: <http://creativecommons.org/licenses/by-nc-sa/4.0/>
