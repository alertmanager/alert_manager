import csv
import os
import json
import gzip
import re

class CsvResultParser:

    csv_data    = []

    def __init__(self, file_path):

        if not os.path.exists(file_path):
            raise Exception("File %s not found." % file_path)

        else:
            with gzip.open(file_path) as fh:
                reader = csv.DictReader(fh)

                for row in reader:
                    self.csv_data.append(row)

    def getResults(self, base_fields):
        fields = []
        for line in self.csv_data:
            for k in line.keys():
                if k.startswith("__mv_"):
                    values = []
                    if line[k] != "":
                        for val in line[k].split(";"):
                            matches = re.match(r'\$(.+)\$', val)
                            values.append(matches.group(1))
                        line[k[5:]] = values
                        del line[k]
                    else:
                        del line[k]
                else:
                    if line[k] == "":
                        del line[k]
            fields.append(line)

        results = {}
        results.update(base_fields)
        results.update({ "fields": fields })
        return results
