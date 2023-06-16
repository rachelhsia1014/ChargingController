# -*- coding: utf-8 -*-
"""
Created on Mon Feb 27 15:31:52 2023

This file loads data from InsiteReports to a Pandas dataframe.

@author: roela
"""


import requests
import datetime
import io
import json
import pandas as pd
from datetime import datetime as dt
import numpy as np
import os, sys
from pathlib import Path


## Initializing the insitereportshandler
class InsiteReportsHandler:
    def __init__(self):
        self.creds = json.load(open("ChargingSimulator/creds.txt"))
        self.serverpath = 'https://portal.insitereports.nl/data.php?'
        try:
            print('Loading local InsiteReports token file')
            self.token = open("ChargingSimulator/_InsideReportsToken", "r").read()
        except FileNotFoundError:
            print('No local token found')
            self.obtain_token()
        print('Insitereports handler initialized')

    def obtain_token(self):
        print('Obtaining new InsiteReports token')
        result = requests.post(self.serverpath + 'action=login', data=self.creds).json()  # obtain new token
        if result['success']:
            print('Succesfull obtained new token')
            self.token = result['token']
            file = open("ChargingSimulator/_InsideReportsToken", "w")
            file.write(self.token)
        else:
            print('Unable to obtain InsiteReports token: {}'.format(result['error']))
        return

    def obtain_data(self, report_id, from_date, to_date):
        print('Requesting InsiteReports data')
        report = requests.get(self.serverpath + 'action=getdata&token=' + str(self.token) + '&report=' +
                              str(report_id) + '&from=' + str(from_date) + '&to=' + str(to_date) + '&output=csv')
        if report.text[13:18] == 'false':
            print('Current token invaled, requesting new token')
            self.obtain_token()
            report = requests.get(self.serverpath + 'action=getdata&token=' + str(self.token) + '&report=' +
                                  str(report_id) + '&from=' + str(from_date) + '&to=' + str(to_date) + '&output=csv')
        textfile = report.text
        textfile = io.StringIO(textfile)
        df = pd.read_csv(textfile, sep=';', parse_dates=True, index_col='Tijdpunten [jaar-maand-dag uur:min:sec]')
        print('Succesfull InsiteReports server connection')
        return df if not df.empty else False

    ## Creating the function responsible for loading the building loads
    def obtain_loads(self, tnow, Ts_data):
        success = True
        try:
            print('Requesting Loads data')
            # timing context:
            today = tnow.date()
            tomorrow = today + datetime.timedelta(days=1)
            # load data:
            print('Loads start loading data')
            raw_loads = self.obtain_data(report_id="35940", from_date=today.strftime("%Y-%m-%d"),
                                      to_date=tomorrow.strftime("%Y-%m-%d"))

            building = raw_loads.copy()
            
            ## Collecting NaN values
            def nan_values(df):
                nans = df.isnull().sum()
                return nans

            ## Resampling the data to the selected sample time
            def resampling(building, Ts_data):
                building_resampled = building.resample(str(Ts_data) + ' min').mean()
                return building_resampled

            building_resampled= resampling(building, Ts_data)

            nans_building_resampled = nan_values(building_resampled)
            
            # Filling NaN values
            def fill_nan_values(series, df):
                if np.count_nonzero(series) != 0:
                    df.interpolate(method='linear', limit=16, inplace=True, )
                else:
                    pass
                return df
            
            # Calculating the aggregated building load
            building_resampled = fill_nan_values(nans_building_resampled, building_resampled)

            building_resampled['actual_demand'] = building_resampled['05 Werkelijk vermogen [Hoofd Kracht] [kW]'] - \
                                                  building_resampled['06 Werkelijk vermogen [PV] [kW]'] - \
                                                  building_resampled['07 Werkelijk vermogen [BMS] [kW]'] - \
                                                  building_resampled['08 Werkelijk vermogen [AutoA] [W]'] / 1000 - \
                                                  building_resampled['09 Werkelijk vermogen [AutoV] [W]'] / 1000 + \
                                                  building_resampled['04 Werkelijk vermogen [Licht] [kW]']
            building_resampled['actual_demand'] = building_resampled['actual_demand'].drop(building_resampled[building_resampled['actual_demand'] < 0].index)
            building_resampled['EV'] = building_resampled['08 Werkelijk vermogen [AutoA] [W]'] / 1000 + building_resampled['09 Werkelijk vermogen [AutoV] [W]'] / 1000
            df_load = building_resampled.copy()
            df_load.reset_index(inplace=True)
            
            
            # Selecting the building load until 12 hours into the future
            fromDate = tnow
            toDate = tnow + datetime.timedelta(hours=12)
            mask = (df_load['Tijdpunten [jaar-maand-dag uur:min:sec]'] >= fromDate) & (df_load['Tijdpunten [jaar-maand-dag uur:min:sec]'] <= toDate)
            df_load = df_load.loc[mask]   
            df_load.columns = ['Datetime', 'Kracht', 'PV', 'BMS', 'AutoA', 'AutoV', 'Light', 'Load', 'EV']
            df_load['Datetime'] = df_load['Datetime'].apply(lambda x: x.value).copy()            
            df_load = df_load.set_index('Datetime')
            df_load.drop(['Kracht', 'BMS', 'AutoA', 'AutoV', 'Light', 'EV'], axis=1, inplace=True)
            df_load['Load'] = df_load['Load'].mask(df_load['Load'] < 0, 0)

            
        except Exception as current_error:
            print("Failed obtaining loads. Error: {}".format(current_error))
            success = False      

        return df_load, success
    