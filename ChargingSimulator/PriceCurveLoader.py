# -*- coding: utf-8 -*-
"""
Created on Tue May 16 11:55 2023

This file scraping energy price from
@author: Rachel
"""
import pandas as pd
def load_price():
    spot_data_5min = pd.read_csv("ChargingSimulator/data/Energy_price_20220310_20220331.csv", sep=';')
    spot_data_5min[['Datetime','Price (Euros/kWh)']] = spot_data_5min[',Forecasted energy price'].str.split(',',expand=True)
    spot_data_5min = spot_data_5min.drop([',Forecasted energy price'], axis=1)
    spot_data_5min = spot_data_5min.set_index('Datetime')

    spot_data_5min['Price (Euros/kWh)'] = spot_data_5min['Price (Euros/kWh)'].astype(float)
    spot_data_5min['sign'] = spot_data_5min/abs(spot_data_5min)
    return spot_data_5min