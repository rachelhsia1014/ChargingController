# -*- coding: utf-8 -*-
"""
Created on Mon Feb 27 15:31:52 2023
Final modification on Fri Sep 01 09:20

This file runs implement MPC and sends the data in the according future horizon to the optimization model

@author: Roeland and Rachel
"""
import ChargingSimulator.OptimizationModel as opt
from ChargingSimulator.PriceCurveLoader import load_price
from ChargingSimulator.parameters import param
import pandas as pd
from datetime import datetime as dt
import datetime
import numpy as np

## Defining the function controller(i, charging_session)
# i indicates the iteration number
# charging_session indicates whether the simulated ev has arrived
def controller(i, charging_session):
    # updating tnow
    tnow_initial = param['tnow_initial']
    Ts_data = param['Ts_data']
    tnow = dt.strptime(tnow_initial, '%Y-%m-%d %H:%M:%S') + i * datetime.timedelta(minutes=Ts_data)

    # reading load from the local file
    df_load = pd.read_csv(param['load_file'], sep=';', decimal=',', thousands='.')
    df_load['Datetime'] = pd.to_datetime(df_load['Datetime'], format='%d/%m/%Y %H:%M')
    df_load = df_load[df_load['Datetime'] >= tnow]
    df_load['Datetime'] = df_load['Datetime'].apply(lambda x: x.value).copy()
    df_load = df_load.set_index('Datetime')
    df_load['Load'] = df_load['Load'].astype(float)
    df_load['PV'] = df_load['PV'].astype(float)
    df_load['PV'] = df_load['PV'] * param['PV_scale_factor']

    # load the price curve in the considered horizon from the local file
    df_price = load_price()
    df_price = df_price[df_price.index.isin(df_load.index)]

    # distinguish the evs in the according horizon and add to the to-be-scheduled ev list
    # ev_input is the full ev list where all the ev that will present on the day is listed (historical data)
    # A temporary file "ev.csv" is used to save the present ev status, including their ID, present time, and validated requested energy.
    # ev_status read "ev.csv" to obtain the ev status that was processed in the previous iteration.
    # new_ev distinguish the newly arrived ev, which will be added to the "sim_out.csv"
    # leaving_ev is the ev that is leaving in this iteration
    # df_ev is the complete ev list that will be scheduled in this iteration (ev_status + new_ev - leaving_ev)    ev_input = pd.read_csv(param['ev_file'], dayfirst=True, parse_dates=[2, 3], dtype={0: np.int64})
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
    else:
        # check feasibility and then update to the ev.csv
        # and add their columns in sim_out.csv that will store their charging current and power
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
                charging_session = True
            sim_out['EV' + str(new_ev['ChargerId'][i]) + ' (A)'] = default_Icharge
            sim_out['EV' + str(new_ev['ChargerId'][i]) + ' (kW)'] = default_Pcharge

        sim_out.to_csv('ChargingSimulator/data/sim_out.csv', header=True, index=True)

    leaving_ev = df_ev.index[df_ev['T_departure'] == tnow]
    for leaving_index in leaving_ev:
        print('EV' + str(df_ev.loc[leaving_index, 'ChargerId']) + ' is leaving.')
        if param['Controlled_ev'] in str(df_ev.loc[leaving_index, 'ChargerId']):
            charging_session = False
        df_ev = df_ev.drop(leaving_index)

    df_ev.reset_index(drop=True, inplace=True)
    sim_out = pd.read_csv('ChargingSimulator/data/sim_out.csv', index_col=0)
    if len(df_ev) > 0:
        if param['Enable_controller']:
            # run the optimization model and return the optimized current to be sent
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

    return tnow, Icharge, charging_session
