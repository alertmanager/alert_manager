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

disable_save_results = [0 | 1]
	* Wheter to save results to alerts index or not
	* Defaults to 0
