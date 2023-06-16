# -*- coding: utf-8 -*-
"""
Created on Mon Feb 27 15:31:52 2023

This file runs all other python files and sends the control values to the charger.

@author: roela
"""
import ChargingSimulator.InsiteReportsHandler
import ChargingSimulator.OptimizationModel as opt
from ChargingSimulator.parameters import param
import pandas as pd
from datetime import datetime as dt
import datetime
import numpy as np


## Defining the function controller(i), for which i is the iteration number
def controller(i):
    # updating tnow
    tnow_initial = param['tnow_initial']
    Ts_data = param['Ts_data']
    tnow = dt.strptime(tnow_initial, '%Y-%m-%d %H:%M:%S') + i * datetime.timedelta(minutes=Ts_data)

    # load in the considered horizon
    df_load = ChargingSimulator.InsiteReportsHandler.InsiteReportsHandler().obtain_loads(tnow, Ts_data)[0]

    # evs to be scheduled in the horizon
    ev_input = pd.read_csv(param['ev_file'], dayfirst=True, parse_dates=[2, 3], dtype={0: np.int64})
    mask = (ev_input['T_departure'] >= tnow) & (ev_input['T_arrival'] <= tnow)
    ev_input = ev_input.loc[mask]
    if i == 0:
        columns = ['ChargerId', 'E_requested', 'T_arrival', 'T_departure']
        ev_status = pd.DataFrame(columns=columns)
    else:
        ev_status = pd.read_csv('ChargingSimulator/data/ev.csv', header=(0), parse_dates=[2, 3], dtype={0: np.int64})

    new_ev = ev_input[~ev_input['ChargerId'].isin(ev_status['ChargerId'])]
    if new_ev.empty:
        print("No new ev at time = " + str(tnow))
        df_ev = ev_status
    else:
        print("New ev comes at time = " + str(tnow))  # check feasibility and then add to the ev.csv, which is the list with involved evs
        mask = new_ev['E_requested'] > ((new_ev['T_departure'] - new_ev['T_arrival']).dt.seconds / 3600) * (
                    param['Vcharger'] * param['Imax'] * param['eff']) / 1000 * param['eff'] * param['E_factor']
        new_ev.loc[mask, 'E_requested'] = ((new_ev['T_departure'] - new_ev['T_arrival']).dt.seconds / 3600) * (
                    param['Vcharger'] * param['Imax'] * param['eff']) / 1000 * param['eff'] * param['E_factor']
        df_ev = pd.concat([ev_status, new_ev], ignore_index=False)


    df_ev.reset_index(drop=True, inplace=True)
    df_ev['T_arrival'] = df_ev['T_arrival'].mask(df_ev['T_arrival'] < tnow, tnow)
    # Running the optimization model and return the optimized current to be sent
    if len(df_ev) > 0:
          Icharge, df_result = opt.runOptimization(df_load, df_ev, tnow, Ts_data)

    else:
        print("No ev to schedule at time = " + str(tnow))
        Icharge = 0
        df_ev.to_csv("ChargingSimulator/data/ev.csv", index=False)

    return Icharge   #df_result.loc[[str(tnow)]]