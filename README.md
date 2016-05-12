# Alert Manager
- **Authors**:		Simon Balz <simon@balz.me>, Mika Borner <mika.borner@gmail.com>
- **Description**:	Extended Splunk Alert Manager with advanced reporting on alerts, workflows (modify assignee, status, severity) and auto-resolve features
- **Version**: 		2.0.5

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

## Release Notes
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
- **2016-04-15** simon@balz.me
	- Fixed wrong file permissions
	- Fixed wrong default notification scheme seed format
	- Added missing appIcon
	- Fixed a bug where e-mail notifications we not sent correctly
	- Fixed a bug where e-mails haven't been displayed correctly on iOS devices
	- Fixed results_link and view_link in notification context
- **2016-04-14** simon@balz.me
	- Fixed a bug to reenable inline drilldown on Incident Posture again (Splunk 6.4 compatibility)
	- Merged a pull request to properly support SMTP authentication
	- Fixed a bug where an urgency field in results lead into an error
	- Fixed wrong modular alert description
	- Removed legacy scripted alert action
	- Merged pull request for better quotation in incident posture
	- Improved alert filter populating search
	- Fixed a bug where not all built-in users are shown in the incident edit modal
	- Fixed incident posture to refresh single values automatically
	- Fixed a bug where Alert Manager internal users were not show in incident edit modal
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
- Select2 (https://github.com/select2/select2)

Friends who helped us:
- ziegfried (https://github.com/ziegfried/) for support
- atremar (https://github.com/atremar) for documentation reviews

## Prerequisites
- Splunk v6.3+ (we use the App Key Value Store and new Single Value visualizations)
- Alerts (Saved searches with alert actions)
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
