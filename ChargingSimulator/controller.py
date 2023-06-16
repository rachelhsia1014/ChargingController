# -*- coding: utf-8 -*-
"""
Created on Mon Feb 27 15:31:52 2023

This file runs all other python files and sends the control values to the charger.

@author: roela
"""
import ChargingSimulator.InsiteReportsHandler
import ChargingSimulator.OptimizationModel as opt
import datetime
import pandas as pd
from datetime import datetime as dt
import datetime
import numpy as np
from ChargingSimulator.parameters import param

## Defining the function controller(i), for which i is the iteration number
def controller(i):
    tnow_initial = param['tnow_initial']
    Ts_data = param['Ts_data']
    tnow = dt.strptime(tnow_initial, '%Y-%m-%d %H:%M:%S') + i * datetime.timedelta(minutes=Ts_data)

    df_load = ChargingSimulator.InsiteReportsHandler.InsiteReportsHandler().obtain_loads(tnow, Ts_data)[0]

    try: df_result
    except NameError: df_result = None
        ## Formatting the EV dataframe for the first iteration
    if i == 0:
        df = pd.read_csv(r''+param['ev_file'],index_col=(0), header=(0), parse_dates=[2,3], dtype={0: np.int64})
        df['E_arrival'] = 0
        mask = (df['T_departure'] >= tnow)
        df = df.loc[mask]
        df_ev = df.copy()
        df_ev['E_requested'] = df_ev['E_requested'] * param['eff']
        mask = df_ev['E_requested'] > ((df_ev['T_departure']- df_ev['T_arrival']).dt.seconds/3600) * (param['vmax'] * param['imax'])/1000 * param['eff'] * param['E_factor']
        df_ev.loc[mask,'E_requested'] = ((df_ev['T_departure']- df_ev['T_arrival']).dt.seconds/3600) * (param['vmax'] * param['imax'])/1000 * param['eff'] * param['E_factor']
  
    ## Loading the previous data frame for iterations i > 0
    else:
        df_ev = pd.read_csv(r'ChargingSimulator/data/ev.csv',index_col=(0), header=(0), parse_dates=[2,3], dtype={0: np.int64})
        df_ev['T_arrival'] = df_ev['T_arrival'].mask(df_ev['T_arrival'] < str(tnow), str(tnow))
        df_ev = df_ev.sort_values(by=['ChargerId'],ascending=[True]).copy()
     
        
    ## Running the optimization model 
    Icharge, df_result, df_ev = opt.runOptimization(df_load, df_ev, tnow, Ts_data)

    print("Running...")
    print("Iteration: " + str(i+1))
    print(tnow)
    
    ## Printing the calculated values
    #for i in range(len(Icharge)):
    #    print("EV: " + str(i+1))
    #    print("Current: " + str(df_result['Current' + str(i+1)].loc[str(tnow)]))
    #    print("Energy: " + str(df_result['EV' + str(i+1)].loc[str(tnow)]))
    #    print("Power : " + str(df_result['PEV' + str(i+1)].loc[str(tnow)]))
    
    ## If charger is controlled through python, current values can be send by adding code below:
    

    ## Returning the values to the SimulinkConnection file
    return Icharge, df_result.loc[[str(tnow)]]