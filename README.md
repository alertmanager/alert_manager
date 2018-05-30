# Alert Manager
- **Authors**:		Simon Balz <simon@balz.me>, Mika Borner <mika.borner@gmail.com>
- **Description**:	Extended Splunk Alert Manager with advanced reporting on alerts, workflows (modify assignee, status, severity) and auto-resolve features
- **Version**: 		@version@

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

### Donations
If you'd like to support further development of the Alert Manager, please use the donate button below. All donations go to the project maintainer.

[![Donate](https://www.paypalobjects.com/en_US/i/btn/btn_donate_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=NTQJBX5VJZYHG)

## Release Notes
- **v2.3.0**/   2018-05-29
	- Added new feature to append an alert to existing ones, if title is identical
	- Deprecating auto_previous_resolve auto_subsequent_resolve due to new append feature
	- Added support to hide unused Alert Statuses
	- Optimized alert_metadata event size
	- Fixed bugs in datamodel. Added action and previous_status attributes to fix state transition dashboard
	
- **v2.2.0**/   2017-12-??
	- Added support for custom alert status in KVStore
	- Added support to index data results from a given alert
	- Added support for Conditional Tables in the Incident Posture View
	- Added support for automatically resolve informational events
	- Added support for external workflow actions
	- Added support for external reference ids
	- Improved Alert History
	- Fixed a bug when email notification still were sent for suppressed incidents
	- Fixed a bug where comments are not shown in incident posture
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
	- Fixed IncidentContext to support https scheme and custom splunk web port
	- Enhanced timestamp display in incident history
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
- **2018-05-29** my2ndhead
	- Fixed bug with missing action in datamodel.
	- Deprecating auto_previous_resolve auto_subsequent_resolve due to new append feature
	- Increasing alert history timespan to 1 year to show old incidents, setting page size to 10
- **2018-05-29** simcen
	- Added tooltips to Incident Posture actions
- **2018-05-25** my2ndhead
	- Added new feature to append an alert to existing ones, if title is identical
- **2018-04-17** my2ndhead
	- Added support to hide unused Alert Statuses
	- Optimized alert_metadata event size
	- Fixed bugs in datamodel. Added action and previous_status attributes to fix state transition dashboard
- **2018-03-26** simcen
	- Added ability to resolve inherited roles to find enabled built-in users
- **2018-03-24** simcen
	- Fixed a bug in Suppression Rules where "contain" and "does not contain" comparators didn't work
- **2018-03-20** simcen
	- Added a check to prevent built-in Alert Status deletion
- **2018-03-17** simcen
	- Improved External Workflow Actions by adding a pulldown to select the Alert Action
	- Changed namespace for custom splunkd endpoints
	- Fixed a bug where Suppression Rules didn't work on Alert Metadata fields
- **2018-03-14** simcen
	- Changed external workflow action command retrieval to \_key instead title
- **2018-03-12** simcen
	- Renamed ExternalWorkflowActionSettings to ExternalWorkflowActions and moved related helper endpoints to EWA REST Handler
	- Added Alert Status edit view
- **2018-03-11** simcen
	- Changed build system to gradle
- **2018-03-09** simcen
	- Fixed a bug when Email Notifications were not sent anymore (#206)
	- Fixed a bug where Alert Manager was not compatible with Search Head Clustering (#200)
	- Fixed a bug where priority column wasn't colored correctly when value is "informational" (#180)
	- Fixed drilldown for realtime searches and searches which start with a seeding command (#186)
- **2018-03-07** simcen
	- Migrated user_settings REST endpoint (#203)
	- Migrated email_templates REST endpoint (#203)
	- Moved incident_workflow REST endpoint to helpers (#203)
	- Migrated incident_settings REST endpoint  (#203)
	- Migrated externalworkflowaction_settings REST endpoint  (#203)
- **2018-03-06** simcen
	- Finally migrated all helpers to new REST style endpoints
	- Fixed a bug where externalworkflowaction was not executed
- **2018-03-06** my2ndhead
	- Added external reference id feature (#204)
- **2018-02-26** my2ndhead
	- Removed custom drilldown feature
	- Fixed a bug in the datamodel and posture, where comments were not displayed (#182)
	- Added feature to improve logging with log_event helper function (#199)
	- Added more columns to history table
	- Added feature for external workflow action
	- Improved incident_posture to reload tables always when expanding a row.
	- Fixed a bug in incident_posture, to hide Loading text correctly
- **2018-02-26** simcen
	- Cherry-picked a couple of changes from the release branch
  	- Added back new role alert_manager_user for read-only access to Splunk objects
	- Re-enabled old-fashioned Alert Results drilldown temporarly
- **2018-02-02** simcen
	- Changed user synchronization to check for a role instead of capabilities
	- Removed capabilities as they are not allowed for certification
- **2017-12-18** simcen
	- Added migration script which supports prepopulating empty alert status collection
	- Added a check to the incident edit modal to wait for the owner and status dropdown to be ready before save button gets active (#189)
- **2017-06-25** johnfromthefuture
	- Added support for Conditional Tables in the Incident Posture View (#177)
	- Added support for automatically resolve informational events (#181)
- **2017-05-26** johnfromthefuture
	- Changed checking if "incident created" notification needs to be fired (#178)
- **2017-04-22** johnfromthefuture
	- Changed incident posture with cosmetic enhancements (#177)
	- Changed Incident setting display_fields to be now optional (#177)
- **2017-03-28** johnfromthefuture
	- Added support to index data results from a given alert (#143)
- **2017-03-03** johnfromthefuture
	- Reduced alert metadata (#173)
- **2017-03-02** johnfromthefuture
		- Added role 'alert_manager_user' to have read-only perms. (#168)
		- Modified the event that is generated when auto_previous_resolved happens. The event will now record the resolving incident (#172)
- **2016-10-21** simon@balz.me
	- Fixed migration scripts to check KVStore availability
	- Remove local.meta from distribution
	- Updated jinja2 to the latest version
- **2016-10-20** simon@balz.me
	- Improved helper endpoint and CsvLookup library to output csv data
	- Support for dynamic status parsing in incident posture
	- Fixed a CSS bug which hid an element showing "No results found" message
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
- Splunk SDK for Python (http://dev.splunk.com/python)
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
- Splunk v6.5 or later
- Alerts (Saved searches with Custom Alert Action enabled)
- Technology Add-on for Alert Manager

## Installation and Usage
Please follow the detailed installation instructions: http://docs.alertmanager.info/en/latest/installation_manual/

## Roadmap
see https://github.com/simcen/alert_manager/labels/enhancement

## Known Issues
see https://github.com/simcen/alert_manager/issues

## License
**Alert Manager is licensed under a Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.** [1]

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-nc-sa/4.0/>.

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
