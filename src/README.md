# Alert Manager
- **Authors**:		Simon Balz <simon@balz.me>, Mika Borner <mika.borner@gmail.com>
- **Description**:	Extended Splunk Alert Manager with advanced reporting on alerts, workflows (modify assignee, status, severity) and auto-resolve features
- **Version**: 		@build.version@

## Introduction
The Alert Manager adds simple incident workflows to Splunk. The general purpose is to provide a common app with dashboards in order to investigate fired alerts or notable events. It can be used with every Splunk alert and works as an extension on top of Splunk's built-in alerting mechanism.

- Awareness of your current operational situation with the incident posture dashboard
- Analyze root cause of incidents with only a few clicks
- Review and adjust the urgency of incidents to improve operations scheduling
- Dispatch incidents to the person in charge
- Track and report incident workflow KPIs
- Tag and categorize incidents

## Features
- Works as Custom Alert Action to catch enriched metadata of fired alerts and stores them in a configurable separate index
- Each fired alert creates an incident
- Configured incidents to run well-known scripted alert scripts
- Reassign incidents manually or auto-assign them to specific users
- Change incidents to another priority and status
- Incidents can be configured to get auto-resolved when a new incident is created from the same alert
- Incidents can be configured to get auto-resolved when the alert's ttl is reached

## Release Notes
- **v2.1.4**/   2016-11-07
	- Fixed disabled migration scripts for fresh installations
- **v2.1.3**/   2016-10-21
	- Fixed migration scripts to check KVStore availability
	- Remove local.meta from distribution
- **v2.1.1**/   2016-10-10
	- Support for non-admin users to modify incidents from Incident Posture dashboard
	- Added capability 'am_is_owner' which is required to be an owner of incidents
	- Added new alert_manager_admin, alert_manager_supervisor and alert_manager_user role as preparation for upcoming features
	- Added support for 'AND' or 'OR' combinations in Suppression Rules
	- Added new dynamic owner selection in Custom Alert Action dialog
	- Added auto subsequent resolve option to resolve new incidents from the same title
	- Added loading indicator to incident posture dashboard when expanding incident to show details
	- Improved incident edit dialog to provide better owner search and selection
	- Fixed IncidentContext to support https scheme and custom splunk web port	 Enhanced timestamp display in incident history
	- Lot’s of bugfixes, code cleanups, enhancements and sanitizations. See changelog for details
- **v2.0.5**/   2016-04-15
	- App certification release only - no functional changes included!
- **v2.0.4**/   2016-04-15
	- App certification release only - no functional changes included!
- **v2.0.3**/   2016-04-15
	- Fixed wrong file permissions
	- Fixed wrong default notification scheme seed format
	- Added missing appIcon
	- Fixed a bug where e-mail notifications we not sent correctly
	- Fixed a bug where e-mails haven't been displayed correctly on iOS devices
	- Fixed results_link and view_link in notification context
- **v2.0.2**/   2016-04-14
	- Fixed a bug to reenable inline drilldown on Incident Posture again (Splunk 6.4 compatibility)
	- Merged a pull request to properly support SMTP authentication
	- Fixed a bug where an urgency field in results lead into an error
	- Fixed wrong modular alert description
	- Removed legacy scripted alert action
	- Merged pull request for better quotation in incident posture
	- Improved alert filter populating search
	- Fixed a bug where not all built-in users are shown in the incident edit modal
	- Fixed incident posture to refresh single values automatically
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
- **2016-10-21** simon@balz.me
	- Fixed migration scripts to check KVStore availability
	- Remove local.meta from distribution
- **2016-10-19** simon@balz.me
	- Fixed broken pagination in Splunk 6.5
	- Removed inline css and js in setup.xml (Certifiaction requirement)
	- Increased version to 2.1.1
- **2016-10-10** simon@balz.me
	- 2.1.0 release preps
- **2016-10-09** simon@balz.me
	- Added new build system (npm with ant, internal change only)
	- Fixed wrong timestamp format in modifyincidents command
	- Removed deprecated parameters from incident posture dashboard
	- Added dynamic owner selection pulldown to alert action config interface
- **2016-09-19** simon@balz.me
	- Changed Customer Alert Action configuration to support dynamic owner selection
	- Fixed an issue with forward slashes in alert names
	- Fixed unhandled exceptions in scheduler
	- Fixed unhandled exceptions in alert_manager.py
- **2016-06-28** simon@balz.me
	- Changed incident posture single values to show always todays nr of incidents compared to yesterday
- **2016-06-24** simon@balz.me	
	- 10k limit Bugfix in macro
- **2016-06-21** simon@balz.me
	- Enhanced timestamp display in incident history
- **2016-06-19** simon@balz.me		
	- Fixed IncidentContext to support https scheme and custom splunk web port	
- **2016-05-13** simon@balz.me
	- Improved logging supporting a config file
- **2016-05-12** simon@balz.me
	- Added support to auto resolve subsequent incidents
- **2016-05-11** simon@balz.me
	- Added support to choose if all or any suppression rules in a ruleset have to match for a positive suppression
	- Added 'Loading...' indicator when expanding a row in incident posture
	- Added JQuery plugin 'Select2' to provide more comfortable owner selection
	- Updated splunk defaukt admin and user roles to support Alert Manager capabilities
	- Removed legacy HTML incident posture dashboard
- **2016-05-10** simon@balz.me
	- Update NotificationHandler.py and _stringdefs.py (jinja2) to correctly close file handles
- **2016-04-22** simon@balz.me
	- Removed unsued incidentresults custom command
	- Changed deprecated <seed/> tag to <initialValue/> in several views
- **2015-04-20** simon@balz.me
	- Changed attribute 'user' in alert_users to 'name', added migration script
- **2016-04-19** simon@balz.me
	- Added support to create incidents by alerts owned by non-admin users
	- Added sync between Splunk users and alert_users kvstore to support non-admin users changing incident ownership	
	- List only users with a certain capability (am_is_owner)

Please find the full changelog here: <https://github.com/simcen/alert_manager/wiki/Changelog>.

## Credits
Libraries and snippets:
- Visualization snippets from Splunk 6.x Dashboard Examples app (https://apps.splunk.com/app/1603/)
- Single value design from Splunk App from AWS (https://apps.splunk.com/app/1274/)
- Trend indicator design from Splunk App for Microsoft Exchange (https://apps.splunk.com/app/1660/)
- Handsontable (http://handsontable.com/)
- Jinja (http://jinja.pocoo.org/)
- MarkupSafe (https://pypi.python.org/pypi/MarkupSafe)
- Select2 (https://github.com/select2/select2)

Friends who helped us:
- ziegfried (https://github.com/ziegfried/) for support
- atremar (https://github.com/atremar) for documentation reviews

## Prerequisites
- Splunk v6.5
- Alerts (Saved searches with Custom Alert Action enabled)
- Technology Add-on for Alert Manager

## Installation and Usage
Please follow the detailed installation instructions: http://docs.alertmanager.info/Documentation/AlertManager/latest/AlertManager/AbouttheAlertManager

## Roadmap
see https://github.com/simcen/alert_manager/labels/enhancement

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
