from CsvResultParser import *

parser = CsvResultParser('/opt/splunk/var/run/splunk/dispatch/scheduler__admin_U0EtYWxlcnRfbWFuYWdlcl9kZW1v__RMD5ad7b61a9b44b3088_at_1422814680_605/results.csv.gz')
print parser.getResults()