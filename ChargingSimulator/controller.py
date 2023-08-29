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
def controller(i, charger_connect):
    # updating tnow
    tnow_initial = param['tnow_initial']
    Ts_data = param['Ts_data']
    tnow = dt.strptime(tnow_initial, '%Y-%m-%d %H:%M:%S') + i * datetime.timedelta(minutes=Ts_data)

    # load in the considered horizon
    df_load = ChargingSimulator.InsiteReportsHandler.InsiteReportsHandler().obtain_loads(tnow, Ts_data)[0]
    df_load['PV'] = df_load['PV'] * param['PV_scale_factor']

    # price curve in the considered horizon
    df_price = load_price()
    df_price = df_price[df_price.index.isin(df_load.index)]

    # evs to be scheduled in the horizon
    ev_input = pd.read_csv(param['ev_file'], dayfirst=True, parse_dates=[2, 3], dtype={0: np.int64})
    mask = (ev_input['T_departure'] >= tnow) & (ev_input['T_arrival'] <= tnow)
    ev_input = ev_input.loc[mask]
    if i == 0:
        columns = ['ChargerId', 'E_requested', 'T_arrival', 'T_departure']
        ev_status = pd.DataFrame(columns=columns)

        # create a file to store the calculated current schedule
        df = pd.DataFrame()
        df['Building Load (kWh)'] = df_load['Load']
        df['PV (kWh)'] = df_load['PV']
        df['Price (Euros/kWh)'] = df_price['Price (Euros/kWh)']
        df.index = pd.to_datetime(df.index)
        df.to_csv('ChargingSimulator/data/sim_out.csv', header=True, index=True)

    else:
        ev_status = pd.read_csv('ChargingSimulator/data/ev.csv', header=(0), parse_dates=[2, 3], dtype={0: np.int64})
        mask = (ev_status['T_departure'] >= tnow)
        ev_status = ev_status.loc[mask]

    new_ev = ev_input[~ev_input['ChargerId'].isin(ev_status['ChargerId'])]
    if new_ev.empty:
        # print("No new ev at time = " + str(tnow))
        df_ev = ev_status
    else:  # check feasibility and then add to the ev.csv, which is the list with involved evs
        new_ev = new_ev.reset_index()
        new_ev.drop('index', axis=1, inplace=True)
        new_ev['E_requested'] = new_ev['E_requested'].astype(float)
        mask = new_ev['E_requested'] > ((new_ev['T_departure'] - new_ev['T_arrival']).dt.seconds / 3600) * ( param['Vcharger'] * param['Imax'] ) / 1000 * param['eff_battery'] * param['E_factor']
        new_ev.loc[mask, 'E_requested'] = ((new_ev['T_departure'] - new_ev['T_arrival']).dt.seconds / 3600) * ( param['Vcharger'] * param['Imax'] ) / 1000 * param['eff_battery'] * param['E_factor']


        df_ev = pd.concat([ev_status, new_ev], ignore_index=False)
        default_Icharge = [0] * (param['N'] + 1)
        default_Pcharge = [0] * (param['N'] + 1)

        sim_out = pd.read_csv('ChargingSimulator/data/sim_out.csv', index_col=0)
        for i in range(0, len(new_ev)):
            print("EV" + str(new_ev['ChargerId'][i]) + " comes at time = " + str(tnow) + '. Requesting ' + str(new_ev['E_requested'][i]))
            if str(new_ev['ChargerId'][i]) == param['Controlled_ev']:
                charger_connect = True
            sim_out['EV' + str(new_ev['ChargerId'][i]) + ' (A)'] = default_Icharge
            sim_out['EV' + str(new_ev['ChargerId'][i]) + ' (kW)'] = default_Pcharge

        sim_out.to_csv('ChargingSimulator/data/sim_out.csv', header=True, index=True)

    leaving_ev = df_ev.index[df_ev['T_departure'] == tnow]
    for leaving_index in leaving_ev:
        print('EV' + str(df_ev.loc[leaving_index, 'ChargerId']) + ' is leaving.')
        if param['Controlled_ev'] in str(df_ev.loc[leaving_index, 'ChargerId']):
            charger_connect = False
        df_ev = df_ev.drop(leaving_index)

    df_ev.reset_index(drop=True, inplace=True)
    # Running the optimization model and return the optimized current to be sent
    sim_out = pd.read_csv('ChargingSimulator/data/sim_out.csv', index_col=0)
    if len(df_ev) > 0:
        if param['Enable_controller']:
            Icharge = opt.runOptimization(df_load, df_ev, tnow, Ts_data, df_price)
        else:
            Icharge = 0
            print("Optimization at time = " + str(tnow))
            for i in range(len(df_ev)):
                if df_ev.iloc[i, 1] > 0:
                    Icharge = param['Imax']
                    print("EV" + str(df_ev['ChargerId'][i]) + " (requesting " + str(
                        df_ev.iloc[i, 1]) + " kWh) is charged at " + str(Icharge) + "A at " + str(tnow))
                    df_ev.iloc[i, 1] = df_ev.iloc[i, 1] - param['Vcharger'] * param['Imax'] / 1000 * param['eff_battery'] * Ts_data / 60
                    if df_ev.iloc[i, 1] < 0 or round(df_ev.iloc[i, 1], 2) == 0.00:
                        df_ev.iloc[i, 1] = 0
                else:
                    if str(df_ev['ChargerId'][i]) == param['Controlled_ev']:
                        Icharge = 0
                    print("EV" + str(df_ev['ChargerId'][i]) + " is fully charged at time " + str(tnow))
                sim_out.loc[str(tnow), 'EV' + str(df_ev['ChargerId'][i]) + ' (A)'] = Icharge
                sim_out.loc[str(tnow), 'EV' + str(df_ev['ChargerId'][i]) + ' (kW)'] = Icharge * param['Vcharger'] / 1000 * param['eff_battery']

            sim_out.to_csv('ChargingSimulator/data/sim_out.csv', header=True, index=True)
            df_ev.to_csv("ChargingSimulator/data/ev.csv", index=False)

    else:
        print("No ev to schedule at time = " + str(tnow))
        Icharge = param['Imin']
        df_ev.to_csv("ChargingSimulator/data/ev.csv", index=False)

    return tnow, Icharge, charger_connect
