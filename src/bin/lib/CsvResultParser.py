import csv
import os
import json
import gzip
import re

class CsvResultParser:

    csv_data    = []
    field_names = []

    def __init__(self, file_path):

        if not os.path.exists(file_path):
            raise Exception("File %s not found." % file_path)

        else:
            with gzip.open(file_path) as fh:
                reader = csv.DictReader(fh)
                self.field_names = reader.fieldnames
                for row in reader:
                    self.csv_data.append(row)

    def getResults(self, base_fields = None):

        fields = []
        for line in self.csv_data:
            for k in line.keys():
                if k.startswith("__mv_"):
                    values = []
                    if line[k] != "":
                        for val in line[k].split(";"):
                            try:
                                if val != '$$':
                                    matches = re.match(r'\$(.+)\$', val)
                                    values.append(matches.group(1))
                            except:
                                continue
                        line[k[5:]] = values
                        del line[k]
                    else:
                        del line[k]
            fields.append(line)

        results = {}
        results.update({ "field_list": self.getHeader() })
        if base_fields != None:
            results.update(base_fields)
        results.update({ "fields": fields })
        return results

    def getHeader(self):
        columns = []
        for col in self.field_names:
            if not col.startswith("__mv_"):
                columns.append(col)
        return columns