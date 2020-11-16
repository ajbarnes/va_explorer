#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 16 17:31:39 2020

@author: babraham
"""

from django.core.management.base import BaseCommand
#from va_explorer.va_data_management.models import VerbalAutopsy, Location
#from simple_history.utils import bulk_create_with_history
from utils.data_import import load_records_from_dataframe  
from utils import odk_api as odk
import argparse
import pandas as pd
#import re

class Command(BaseCommand):

    help = 'Pulls in CSV data from ODK and loads it into the database'

    def add_arguments(self, parser):
        parser.add_argument('--domain_name', default="127.0.0.1", help="Domain name of ODK instance")
        parser.add_argument('--project_name', default="zambia-test", help="Name of ODK project")
        parser.add_argument('--project_id', type=int, default=None, help="ODK Project ID")


    def handle(self, *args, **options):
        
        self.stdout.write("=======1. Pulling down ODK data======")
        # download records from odk
        odk_records = odk.download_responses(domain_name=options["domain_name"],\
                                             project_name=options["project_name"],\
                                             project_id=options["project_id"],\
                                             fmt='csv', export=False)
        
        self.stdout.write("=======2. Inserting ODK data into database=======")
        # load odk records into database
        load_records_from_dataframe(odk_records)

#        # CSV can prefix column names with a dash or more, remove everything up to and including last dash
#        csv_data.rename(columns=lambda c: re.sub('^.*-', '', c), inplace=True)
#
#        # Figure out the common field names across the CSV and our model
#        model_field_names = pd.Index([f.name for f in VerbalAutopsy._meta.get_fields()])
#        
#        # But first, account for case differences in csv columns (i.e. ensure id10041 maps to Id10041)
#        fieldCaseMapper = {field.lower(): field for field in model_field_names} 
#        csv_data.rename(columns=lambda c: fieldCaseMapper.get(c.lower(), c), inplace=True)
#
#        csv_field_names = csv_data.columns
#        common_field_names = csv_field_names.intersection(model_field_names)
#
#        # Just keep the fields in the CSV that we have columns for in our VerbalAutopsy model
#        # Also track extras or missing fields for eventual debugging display
#        missing_field_names = model_field_names.difference(common_field_names)
#        extra_field_names = csv_field_names.difference(common_field_names)
#        csv_data = csv_data[common_field_names]
#
#        # Populate the database!
#        verbal_autopsies = [VerbalAutopsy(**row) for row in csv_data.to_dict(orient='records')]
#        # TODO: For now treat this as synthetic data and randomly assign a facility as the location
#        for va in verbal_autopsies:
#            va.location = Location.objects.filter(location_type='facility').order_by('?').first()
#        bulk_create_with_history(verbal_autopsies, VerbalAutopsy)
#
#        self.stdout.write(f'Loaded {len(verbal_autopsies)} verbal autopsies')