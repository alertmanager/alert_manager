[settings]
	* If you do not specify an entry for each attribute, the event manager will use the default value.

index	= <index_name>
	* Name of the index where the alert meta events will be written to
	* Defaults to "alerts"

default_owner = <owner_name>
	* Default owner for new alerts
	* Defaults to "unassigned"

default_priority = <owner_name>
        * Default priority for new alerts
        * Defaults to "unknown"

user_directories = [both | builtin | alert_manager]
	* Configure which user directories are enabled
	* Defaults to both

default_notify_user_template = <default_notify_user_template_name>
	* Default template used to notify users on incident assignment
	* Defaults to notify_user