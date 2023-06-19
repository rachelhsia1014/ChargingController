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
from ChargingSimulator.PriceCurveLoader import load_price


## Defining the function controller(i), for which i is the iteration number
def controller(i):
    # updating tnow
    tnow_initial = param['tnow_initial']
    Ts_data = param['Ts_data']
    tnow = dt.strptime(tnow_initial, '%Y-%m-%d %H:%M:%S') + i * datetime.timedelta(minutes=Ts_data)

    # load in the considered horizon
    df_load = ChargingSimulator.InsiteReportsHandler.InsiteReportsHandler().obtain_loads(tnow, Ts_data)[0]

    # price curve in the considered horizon
    #df_price = load_price()

    # evs to be scheduled in the horizon
    ev_input = pd.read_csv(param['ev_file'], dayfirst=True, parse_dates=[2, 3], dtype={0: np.int64})
    mask = (ev_input['T_departure'] >= tnow) & (ev_input['T_arrival'] <= tnow)
    ev_input = ev_input.loc[mask]
    if i == 0:
        columns = ['ChargerId', 'E_requested', 'T_arrival', 'T_departure']
        ev_status = pd.DataFrame(columns=columns)

        # create a file to store the calculated current schedule
        start_time = dt.strptime(tnow_initial, '%Y-%m-%d %H:%M:%S') - datetime.timedelta(minutes=param['Ts_data'])
        end_time = dt.strptime(str(start_time), '%Y-%m-%d %H:%M:%S') + (param['N'] + 1) * datetime.timedelta(
            minutes=param['Ts_data'])
        time_range = pd.date_range(start=start_time, end=end_time, freq=str(param['Ts_data']) + 'T')
        df = pd.DataFrame(index=time_range)
        df = df.rename(index={df.index[0]: 'Datetime'})
        df.to_csv('ChargingSimulator/data/sim_out.csv', header=False, index=True)

    else:
        ev_status = pd.read_csv('ChargingSimulator/data/ev.csv', header=(0), parse_dates=[2, 3], dtype={0: np.int64})
        mask = (ev_status['T_departure'] >= tnow)
        ev_status = ev_status.loc[mask]

    new_ev = ev_input[~ev_input['ChargerId'].isin(ev_status['ChargerId'])]
    if new_ev.empty:
        print("No new ev at time = " + str(tnow))
        df_ev = ev_status
    else:
        print("New ev comes at time = " + str(tnow))  # check feasibility and then add to the ev.csv, which is the list with involved evs
        new_ev = new_ev.reset_index()
        new_ev.drop('index', axis=1, inplace=True)
        new_ev['E_requested'] = new_ev['E_requested'] * 1.1 # request more to ensure enough delivery
        mask = new_ev['E_requested'] > ((new_ev['T_departure'] - new_ev['T_arrival']).dt.seconds / 3600) * (
                    param['Vcharger'] * param['Imax'] * param['eff']) / 1000 * param['eff'] * param['E_factor']
        new_ev.loc[mask, 'E_requested'] = ((new_ev['T_departure'] - new_ev['T_arrival']).dt.seconds / 3600) * (
                    param['Vcharger'] * param['Imax'] * param['eff']) / 1000 * param['eff'] * param['E_factor']
        df_ev = pd.concat([ev_status, new_ev], ignore_index=False)
        default_Icharge = [0] * (param['N'] + 1)
        sim_out = pd.read_csv('ChargingSimulator/data/sim_out.csv', index_col=0)
        for i in range(0, len(new_ev)):
            sim_out['EV' + str(new_ev['ChargerId'][i])] = default_Icharge
        sim_out.to_csv('ChargingSimulator/data/sim_out.csv', header=True, index=True)

    leaving_ev = df_ev.index[df_ev['T_departure'] == tnow]
    for leaving_index in leaving_ev:
        print('EV' + str(df_ev.loc[leaving_index, 'ChargerId']) + ' is leaving.')
        df_ev = df_ev.drop(leaving_index)

    df_ev.reset_index(drop=True, inplace=True)
    # Running the optimization model and return the optimized current to be sent
    if len(df_ev) > 0:
          Icharge = opt.runOptimization(df_load, df_ev, tnow, Ts_data)

    else:
        print("No ev to schedule at time = " + str(tnow))
        Icharge = 0
        df_ev.to_csv("ChargingSimulator/data/ev.csv", index=False)

    return Icharge