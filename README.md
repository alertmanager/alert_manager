# Alert Manager
- **Authors**:		Simon Balz <simon@balz.me>, Mika Borner <mika.borner@gmail.com>
- **Description**:	Extended Splunk Alert Manager with advanced reporting on alerts, workflows (modify assignee, status, severity) and auto-resolve features
- **Version**: 		1.0

## Introduction
The Alert Manager adds simple incident workflows to Splunk. The general purpose is to provide a common app with dashboards in order to investigate fired alerts or notable events. It can be used with every Splunk alert and works as an extension on top of Splunk's built-in alerting mechanism.

- Awareness of your current operational situation with the incident posture dashboard
- Analyze root cause of incidents with only a few clicks
- Review and adjust the urgency of incidents to improve operations scheduling
- Dispatch incidents to the person in charge
- Track and report incident workflow KPIs
- Tag and categorize incidents

## Features
- Works as scripted alert action to catch enriched metadata of fired alerts and stores them in a configurable separate index
- Each fired alert creates an incident
- Configured incidents to run well-known scripted alert scripts
- Reassign incidents manually or auto-assign them to specific users
- Change incidents to another priority and status
- Incidents can be configured to get auto-resolved when a new incident is created from the same alert
- Incidents can be configured to get auto-resolved when the alert's ttl is reached

## Additional Notes for Apptitude App Contest
- The app utilizes the Common Information Model
- Demo data is provided with a separate app. Due to the nature of the app, we couldn't use Eventgen.
- The app uses only portable code and is tested thoroughly on *nix and Windows systems.
- The app will be used within customer projects, and improved according to customer and community needs. Development of the app will happen in public. Bugs/Issues and improvement requests can be opened on the project's Github page (<https://github.com/simcen/alert_manager/issues>).

## Release Notes
- **v1.0**	/ 	2015-01-19
	- Major release with e-mail notifications and templates
	- Lots of bugfixes and enhancements
	- Final release for Splunk Apptitude submission
- **v0.10**	/	2015-01-04
	- Bugfix & optimization release
- **v0.9**	/	2014-12-28
	- Lots of bugfixes
	- New KPI dashboard with sankey visualization
	- Full support to add/remove alert manager users
	- Improved app setup (check for index existence) and configuration (configure which user directories should be used)
	- Removed hardcoded index from searches
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
- **2015-02-10** simon@balz.me
	- Fixed trend timerange to depend on timepicker in incident posture
- **2015-02-04** simon@balz.me
	- Improved inicdent list when tags are empty
- **2015-02-04** mika.borner@gmail.com
	- Fixed issue #60
- **2015-02-03** simon@balz.me
	- Added support to display selected fields in incident row expansion on incident_posture
- **2015-02-01** simon@balz.me
	- Prepared CsvResultParser for per-result fixing
	- Code optimizations
	- Improved email notifications to support multi value fields
	- Added alert description to incident details
	- Added support for sorted field list in incident results
- **2015-02-01** mika.borner@gmail.com
	- Fixed per-result incident creation for all alerting types

Please find the full changelog here: <https://github.com/simcen/alert_manager/wiki/Changelog>.

## Credits
- Visualization snippets from Splunk 6.x Dashboard Examples app (https://apps.splunk.com/app/1603/)
- Single value design from Splunk App from AWS (https://apps.splunk.com/app/1274/)
- Trend indicator design from Splunk App for Microsoft Exchange (https://apps.splunk.com/app/1660/)
- Handsontable (http://handsontable.com/)
- ziegfried (https://github.com/ziegfried/) for support
- atremar (https://github.com/atremar) for documentation reviews

## Prerequisites
- Splunk v6.2+ (we use the App Key Value Store)
- Alerts (Saved searches with alert actions)
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

**Note:** If you forward events from the search head through heavy forwarders to the indexer, install the Add-on on the heavy forwarder and disable the index there.

### Installation
1. Unpack and install the App and Add-on according to the deployment matrix
	- The Add-on is located at alert_manager/appserver/src/TA-alert_manager.tar.gz
2. Link $SPLUNK_HOME/etc/apps/alert_manager/bin/alert_handler.py to $SPLUNK_HOME/bin/scripts/:
	- Linux:

	`cd $SPLUNK_HOME/bin/scripts && ln -s ../../etc/apps/alert_manager/bin/alert_handler.py alert_handler.py`

	- Windows (run with administrative privileges):

	`cd %SPLUNK_HOME && mklink alert_handler.py ..\..\etc\apps\alert_manager\bin\alert_handler.py`

3. Restart Splunk
4. Configure the Alert Manager global settings in the app setup

#### Demo Data
For testing purposes, we ship a separate App containing static demo data and demo alerts.
- Static demo data adds pre-generated incidents with some workflow examples in order to see the KPI dashboards working
- Demo alerts are configured to see some different live alert examples, like auto assign/resolve scenarios and support for realtime alerts

To add demo data, follow these instructions:

1. Unpack and install the "Supporting Add-on for Alert Manager Demo Data" (app folder name SA-alert_manager_demo) to $SPLUNK_HOME/etc/apps
2. Restart Splunk
3. Open Splunk and switch to the "Alert Manager Demo Data" App
4. Follow the instructions in the "Demo Data Setup" view

#### Note for distributed environments
- The alert manager runs mostly on the search head (since we use the App Key Value Store)
- Due to the usage of the App Key Value Store, there's no compatibility with Search Head Clustering (SHC) introduced in Splunk v6.2
- The Alert Manager runs a script every 30 seconds (as a scripted input) to search for incidents that should be resolved after their ttl is reached

### Alert Manager Settings
1. Configure global settings in the App's setup page (Manage Apps -> Alert Manager -> Set up)
	- **Index:** Where the Alert Manager will store the alert's metadata, alert results and change events
	- **Default Assignee:** Username of the assignee a newly created incident will be assigned to
	- **Default Priority:** Priority to be used for new incidents created by the alert
	- **Disable saving alert results to index:** Whether to index alert results again in the index specified above. Then they are still visible after they expired. Currently, there's no related feature in the Alert Manager.
2. Configure per-alert settings in the "Alert Settings" page

### Configure Alerts
1. Set "alert_handler.py" (without quotes) as the script's file name of an alert action
2. Configure the alert to be visible in Splunk's Triggered Alert view (necessary to view the alert results without indexing them)
3. Configure incident settings (Alert Manager App -> Settings -> Incident Settings)
	- Note: By default, only alerts configured as globally visible are shown in the list. In case you're missing an alert, try to select the correct App scope within the pulldown.

### Per Alert Settings
- **Run Alert Script:** You can run a classical alert script (<http://docs.splunk.com/Documentation/Splunk/latest/Alert/Configuringscriptedalerts>). Place your script in $SPLUNKH_HOME/bin/scripts, enable run_alert_script and add the file name (without path!) to the alert_script field. All arguments will be passed to the script as you would configure it directly as an alert action.
- **Auto Assign:** Assign newly created incidents related to this alert to a special user. Enter the username to the auto_assign_user field and enable auto_assign
- **Auto Resolve Previous:** Automatically resolve already existing incidents with status=new related to this alert when creating a new one
- **Auto Resolve after TTL:** Automatically resolve existing incidents with status=new when alert.expires time is reached

## Roadmap
- Custom incident handlers to extend the alert manager’s functionality

## Known Issues
- Default e-mail templates are not saved correctly in the KV store
	- **Workaround**: Go to E-Mail Settings and click "Save Templates" once. This step will copy the default template configuration to the KV store.
- Trend indicators in the Incident Posture dashboard are fixed to the timerange earliest=-48h latest-24h

## License
- **This work is licensed under a Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.** [1]
- **Commercial Use, Excerpt from CC BY-NC-SA 4.0:**
  - "A commercial use is one primarily intended for commercial advantage or monetary compensation."
- **In case of Alert Manager this translates to:**
  - You may use Alert Manager in commercial environments for handling in-house Splunk alerts
  - You may use Alert Manager as part of your consulting or integration work, if you're considered to be working on behalf of your customer. The customer will be the licensee of Alert Manager and must comply according to the license terms
  - You are not allowed to sell Alert Manager as a standalone product or within an application bundle
  - If you want to use Alert Manager outside of these license terms, please contact us and we will find a solution

## References
[1] http://creativecommons.org/licenses/by-nc-sa/4.0/
[2] "The Socio-Economic Effects of Splunk" by Carasso, Roger (1987, M.I.T. Press).
