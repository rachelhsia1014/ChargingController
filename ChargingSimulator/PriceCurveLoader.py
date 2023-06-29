# -*- coding: utf-8 -*-

import pandas as pd
from ChargingSimulator.parameters import param
def load_price():
    spot_data_5min = pd.read_csv(param['price_file'], sep=';')
    spot_data_5min[['Datetime','Price (Euros/kWh)']] = spot_data_5min[',Forecasted energy price'].str.split(',',expand=True)
    spot_data_5min = spot_data_5min.drop([',Forecasted energy price'], axis=1)
    spot_data_5min['Datetime'] = pd.to_datetime(spot_data_5min['Datetime'], format='%Y-%m-%d %H:%M:%S')
    spot_data_5min['Datetime'] = spot_data_5min['Datetime'].apply(lambda x: x.value).copy()
    spot_data_5min = spot_data_5min.set_index('Datetime')
    spot_data_5min['Price (Euros/kWh)'] = spot_data_5min['Price (Euros/kWh)'].astype(float)
    spot_data_5min['sign'] = spot_data_5min/abs(spot_data_5min)
    return spot_data_5min