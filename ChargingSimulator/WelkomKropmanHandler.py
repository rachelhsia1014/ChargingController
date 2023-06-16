# -*- coding: utf-8 -*-
"""
Created on Fri Jan 13 10:24:38 2023

@author: Roeland in t Veld
"""

import pandas as pd
from datetime import datetime
import requests
import json
import numpy as np

rpc_login = {'key': 'cfb8bc47_e446_a832_cde0_2c6c9036c151',
             'url': 'https://mld.kropman.nl/insiteview/breda/rpc/'}


def loadData():
    # Here you can specificy a folder to store the data
    DIR = ""

    b = requests.post(rpc_login['url'] + 'evse/welkomkropman', data=rpc_login)
    welkomkropman = json.loads(b.text)
    df_welkomkropman = pd.json_normalize(welkomkropman['result']['wk'])
    df_chargerdata = df_welkomkropman.copy()

    # logging the EV data for later use
    now = datetime.today()
    df_welkomkropman["Timestamp"] = now

    # creating usable EV data dataframe
    if df_chargerdata.empty:
        print("No new EV data")
        return df_welkomkropman

    else:
        df_welkomkropman.to_csv(DIR + "welkomkropman_log.csv", mode='a')
        df_chargerdata.to_csv(DIR + "chargerdata.csv", mode='a')
        print("New EV data loaded")
        df = df_chargerdata.sort_values([df_chargerdata.columns[3], df_chargerdata.columns[1]]).copy()
        df = df.sort_values('ActualArrival', ascending=False).copy()
        df = df.set_index('ChargerId')
        df.rename(columns={'MinimumDesiredRangeInKWH': 'E_requested', 'ActualArrival': 'T_arrival',
                           'ExpectedDeparture': 'T_departure'}, inplace=True)

        # This loads the EV data from the previous iteration and compares it with the new data
        try: df_ev
        except NameError:
            df_ev = None

        if df_ev is None:
            df_ev = df.copy()
            df_ev = pd.concat([df_ev, df])
            df_ev = df_ev.sort_values(by=['T_arrival'], ascending=[False]).copy()

            # Deleting any duplicates and keeping the newer EV data for that ChargerId
            df_ev = df_ev.reset_index().drop_duplicates(subset='ChargerId').set_index('ChargerId').sort_index().copy()
            df_ev.to_csv(DIR + "ev_backup.csv")
            df_ev_unclean = df_ev.copy()

    df_ev_unclean['T_arrival'] = pd.to_datetime(df_ev_unclean['T_arrival']).dt.tz_convert(None)
    df_ev_unclean['T_departure'] = pd.to_datetime(df_ev_unclean['T_departure']).dt.tz_convert(None)
    df_ev_unclean['E_arrival'] = 0

    df_ev_clean = df_ev_unclean.sort_values(by=['T_arrival'], ascending=[False])
    df_ev_clean = df_ev_clean.reset_index()

    df_ev_clean = df_ev_clean.drop_duplicates(subset='ChargerId', ignore_index=True)
    df_ev_clean['ChargerId'] = df_ev_clean['ChargerId'] - 1
    df_ev_clean = df_ev_clean.set_index('ChargerId')
    df_ev_clean = df_ev_clean.sort_index(ascending=True)
    df_ev_clean = df_ev_clean.drop(labels=['LocationName'], axis=1)
    df_ev_clean['T_arrival'] = df_ev_clean['T_arrival'].dt.round('15min')
    df_ev_clean['T_departure'] = df_ev_clean['T_departure'].dt.round('15min')

    return df_ev_clean
    




