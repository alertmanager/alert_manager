import csv
import os
import json

class CsvLookup:

    csv_data    = []

    def __init__(self, file_path):

        if not os.path.exists(file_path):
            raise Exception("File %s not found." % file_path)

        else:
            with open(file_path) as fh:
                reader = csv.DictReader(fh)

                for row in reader:
                    self.csv_data.append(row)

    def lookup(self, input_data, output_fields = None):
        match = {}
        for row in self.csv_data:
            if all(item in row.items() for item in input_data.items()):
                match = row
                break

        if output_fields != None:
            for k in match.keys():
                if k not in output_fields:
                    del match[k]

        return match

