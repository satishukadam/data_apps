# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 16:56:50 2020

@author: Satish
"""
# import libraries
import os

PROJECT_DIR = 'D:\\Study\\DataScience\\Projects\\DataApps\\TollRevenueForecast'

DATA_DIR = os.path.join(PROJECT_DIR, 'data')
MODEL_DIR = os.path.join(PROJECT_DIR, 'models')
GEOJSON_URL = os.path.join(PROJECT_DIR, 'ward.json')

toll_dict = {'1': 'Ambad', '2': 'Shaneshwar Nager', '3': 'Gangapur', '4': 'Shreerang Nagar',             
            '5': 'Shivaji Nagar', '6': 'Saraf Bazar',
            '7': 'Ozhar', '8': 'Vijay Nagar', '9': 'Deolali'}
