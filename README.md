# Alert Manager
- **Authors**:		Simon Balz <simon@balz.me>, Mika Borner <mika.borner@gmail.com>
- **Description**:	Extended Splunk Alert Manager with advanced reporting on alerts, workflows (modify assignee, status, severity) and auto-resolve features
- **Version**: 		2.0.1

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
- **v2.0.1**/   2016-01-20
	- Fixed localization support
	- Changed alert column in incident settings to read-only
	- Fixed a bug where token syntax in notifications doesn't work
	- Fixed notifications to support multi-valued fields or comma-separated list of recipients
- **v2.0**  /   2015-11-18
	- Changed from scripted alert action to Custom Alert Action framework
	- Added a customizable incident title
	- Added support for extended notification schemes
	- Added support for incident suppression (False positives, maintenance windows...)
	- Added migration script to ingest default data (email templates and notification schemes) as well as migrating old incident settings to Custom Alert Action parameters
	- Added new Splunk v6.3 style single values
	- Added support to dynamically select a template by referencing a token in the notification scheme
	- Added support for multiple dynamic recipients by using multi-valued fields and a token in the notification scheme
	- Added a search command 'modifyincidents' to update an incident trough a search
	- Added a general default email template
	- Changed token reference in e-mail templates to $result.fieldname$ syntax
	- Bugfixes and performance improvements
- **v1.1**	/ 	2015-03-12
	- Fixed support for per-result alert actions
	- Added support for search results in e-mail templates
	- Enhanced incident details with description form saved search and selectable list of fields
	- Bugfixes
- **v1.0**	/ 	2015-01-19
	- Major release with e-mail notifications and templates
	- Lots of bugfixes and enhancements
	- Final release for Splunk Apptitude submission


## Changelog
- **2016-04-14** simon@balz.me
	- Fixed a bug to reenable inline drilldown on Incident Posture again (Splunk 6.4 compatibility)
	- Merged a pull request to properly support SMTP authentication
- **2016-01-07** simon@balz.me
	- Fixed localization support (thx to mkldon)
	- Changed alert column in incident settings to read-only
	- Fixed a bug where token syntax in notifications doesn't work
	- Fixed notifications to support multi-valued fields or comma-separated list of recipients
- **2015-11-23** simon@balz.me
	- Fixed a bug where the token syntax wasn't parsed correctly in notification scheme template references
- **2015-11-09** simon@balz.me
	- Added Custom Alert Action functioanlity (introduced with Splunk v6.3)
	- Reduced complexitiy of alert configuration
	- Added support to migrate former incident settings to new Custom Alert Action parameters
- **2015-09-02** simon@balz.me
	- Fixed Notification Scheme and Suppression Rule eitor views to correctly focus when showing the edit modal
	- Fixed SuppressionHelper to correctly parse rules ('or' combination between main rules, 'and' combination between rules)
	- Added ability to remove Suppression Rules
	- Added ability to remove Notification Schemes
	- Fixed incident posture to use the correct app when drilling down to contributing events
- **2015-07-28** simon@balz.me
	- Added migration script to initially load data for new installations
	- Added check or creation of the alert_handler.py symlink to the migration script
- **2015-07-26** simon@balz.me
	- Added support for multi-valued recipient field in results for notifications
	- Added UI to manage notification schemes
	- Optimized incident settings to show searches even if they aren't shared globally
	- Released and added TA-alert_manager v2.0
- **2015-07-10** simon@balz.me
	- Added support to resolve by title for auto_previous_resolve
- **2015-06-22** simon@balz.me
	- Added "on_hold" as incident status
- **2015-06-12** simon@balz.me
	- Changed incident posture to show title (or alert if title is empty)
- **2015-06-05** simon@balz.me
	- Changed incident workflow do add a dedicated event for comments
	- Extended incident export with feature to download incident results as html file
	- Added lookup command to get incident results as fields in a search (non-generating)
	- Added support for individual incident title with field replacement
- **2015-06-04** simon@balz.me
	- Added description field to suppression rules
	- Added auto_suppress_resolve scenario
	- Added incident export view
- **2015-06-03** simon@balz.me
	- Added UI to edit suppression rules
- **2015-05-12** simon@balz.me
	- Fixed a bug in IncidentContext where unconfigured incidents run into an exception	
- **2015-05-04** simon@balz.me
	- Added support for dynamic template assignement from a field value
- **2015-05-01** simon@balz.me
	- Added support for suppression rules
- **2015-04-23** simon@balz.me
	- Fixed a bug where multiple notification recipients were not handled correctly
- **2015-04-06** simon@balz.me
	- Regression bugfixes
	- New event for event_handler: "incident_resolved"
- **2015-04-04** simon@balz.me
	- Added App logo
- **2015-04-02** simon@balz.me
	- Optimized email_template collection structure
	- Added support for static attachements to be inline-linked from a template	
- **2015-04-01** simon@balz.me
	- Added support to use incident result field in notification recipients
	- Replaced django template parsing by jinja2
	- Added support to send events when re-assigning an incident in the incident posture dashboard
- **2015-03-30** simon@balz.me
	- Fixed E-mail templates view to enable adding new templates
	- Fixed user settings to provide spare row in table
- **2015-03-29** simon@balz.me
	- Introduced Notification Schemes
	- Introduced Event Handler
	- Removed E-mail settings which are replaced by notification schemes


Please find the full changelog here: <https://github.com/simcen/alert_manager/wiki/Changelog>.

## Credits
Libraries and snippets:
- Visualization snippets from Splunk 6.x Dashboard Examples app (https://apps.splunk.com/app/1603/)
- Single value design from Splunk App from AWS (https://apps.splunk.com/app/1274/)
- Trend indicator design from Splunk App for Microsoft Exchange (https://apps.splunk.com/app/1660/)
- Handsontable (http://handsontable.com/)
- Jinja (http://jinja.pocoo.org/)
- MarkupSafe (https://pypi.python.org/pypi/MarkupSafe)

Friends who helped us:
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
	</tr>
    <tr>
        <td>Search Head</td>
        <td>x</td>
        <td>x</td>
    </tr>
    <tr>
    	<td>Indexer</td>
    	<td></td>
    	<td>x</td>
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
- Even if you forward events from the Search Head to the indexer, be sure to enable the alerts index (or your own one) on the Search Head. Since we talk with the REST API on the Search Head, Splunk requires to have the index enabled when creating events trough the API

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
see https://github.com/simcen/alert_manager/issues

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
