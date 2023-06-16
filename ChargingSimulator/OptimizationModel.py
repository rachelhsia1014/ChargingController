# -*- coding: utf-8 -*-
"""
Created on Mon Feb 27 15:32:20 2023

@author: roela
"""

"""
Created on Fri Jan 13 10:37:47 2023

@author: Roeland in t Veld
"""

from pyomo.environ import *
import pandas as pd
import pyomo.environ as pyo
import datetime
from ChargingSimulator.parameters import param

def runOptimization(df_load, df_ev, tnow, Ts_data):
    #converting the datetime object to an integer which can be processed by Pyomo
    df_ev['I_arrival'] = df_ev['T_arrival'].apply(lambda x: x.value).copy()
    df_ev['I_departure'] = df_ev['T_departure'].apply(lambda x: x.value).copy()
   


    #Checking to see whether or not the arrival time is within the loads dataframe
    df_ev = df_ev[df_ev.index.isin(df_ev['I_arrival'].loc[df_ev['I_arrival'].isin(df_load.index)].index)].copy()

    if df_ev.empty:
        print("No EVs at this moment")
        
        return Icharge, df_result, df_ev

    df_ev = df_ev.sort_values(by=['ChargerId'],ascending=[True]).copy()
    dummies  = pd.DataFrame([[param['eff'],param['imin'],param['imax'],param['pmax'],param['price'],param['FIT'],param['vmax']]],columns=['eff', 'imin', 'imax', 'pmax', 'price', 'fit', 'vmax'],index=['Data'])
    

    def create_model(input1_df, input2_df, input_dummies, Ts_data):
        # Dummy variables
        dummies = input_dummies
    
        # Pyomo model
        model = ConcreteModel()
    
        # Creation of Set

        #Horizon
        model.N = Set(ordered = True, initialize = RangeSet(0,len(input1_df.index)-1))

        #Chargers
        model.V = Set(ordered = True, initialize = RangeSet(0,len(input2_df.index)-1))
    
        #Single variables
        model.S = Set(ordered = True, initialize = dummies.index)
    
        # Creation Parameters
        model.Pload = Param(model.N, within = NonNegativeReals, mutable = True)
        model.Ppv = Param(model.N, within = Reals, mutable = True)
        model.T = Param(model.N, within = NonNegativeReals, mutable = True)
    
        model.E_requested = Param(model.V, within=NonNegativeReals, mutable=True)
        model.T_arrival = Param(model.V, within=NonNegativeReals, mutable=True)
        model.T_departure = Param(model.V, within=NonNegativeReals, mutable=True)
        model.E_arrival = Param(model.V, within=NonNegativeReals, mutable=True)
        model.P_previous = Param(model.V, within=NonNegativeReals, mutable=True)
        
        model.eff = Param(model.S, within = NonNegativeReals, mutable = True)
        model.imin = Param(model.S, within = NonNegativeReals, mutable = True)
        model.imax = Param(model.S, within = NonNegativeReals, mutable = True)
        model.pmax = Param(model.S, within = NonNegativeReals, mutable = True)
        model.price = Param(model.S, within = NonNegativeReals, mutable = True)
        model.fit = Param(model.S, within = NonNegativeReals, mutable = True)
        model.vmax = Param(model.S, within = NonNegativeReals, mutable = True)
    
        # Update parameters
        #Single value first!!!!
        for s in model.S:
            model.eff[s] = dummies.loc[s, 'eff']
            model.imin[s] = dummies.loc[s, 'imin']
            model.imax[s] = dummies.loc[s, 'imax']
            model.pmax[s] = dummies.loc[s, 'pmax']
            model.price[s] = dummies.loc[s, 'price']
            model.fit[s] = dummies.loc[s, 'fit']
            model.vmax[s] = dummies.loc[s, 'vmax']
        
        # Indexed:
        for k in model.N:
            model.T[k] = input1_df.index[k]
            model.Pload[k] = input1_df['Load'].iloc[k]
            model.Ppv[k] = input1_df['PV'].iloc[k]
                
        for i in model.V:
            model.E_requested[i] = input2_df['E_requested'][i]
            model.T_arrival[i] = input2_df['I_arrival'][i]
            model.T_departure[i] = input2_df['I_departure'][i]
            model.E_arrival[i] = input2_df['E_arrival'][i]
        
  
        # Creation of Variables
        model.Pgrid = Var(model.N, within = Reals)
        model.Pevtot = Var(model.N, within = Reals)
        model.Pgrid_plus = Var(model.N, within = Reals)
        model.Pgrid_min = Var(model.N, within = Reals)
        model.Eff_cost = Var(model.N, within = Reals)

        model.Eff = Var(model.N, model.V, within = Reals)
        model.Icharge = Var(model.N, model.V, within = Reals)
        model.Pcharge = Var(model.N, model.V, within = Reals)
        model.Pev = Var(model.N, model.V, within = Reals)
        model.Eev = Var(model.N, model.V, within = Reals)
    
        # Creation of constraints
        def EV_charging(model, s, k, i):
            if pyo.value(model.T[k]) <= pyo.value(model.T_arrival[i]):
                return model.Eev[k, i] == model.E_arrival[i]
            if pyo.value(model.T_arrival[i]) < pyo.value(model.T[k]) < pyo.value(model.T_departure[i]):
                return model.Eev[k, i] == (model.Eev[model.N.prev(k),i] + (model.Pev[model.N.prev(k), i]*Ts_data/60))
            if pyo.value(model.T[k]) >= pyo.value(model.T_departure[i]):
                return model.Eev[model.N.prev(k),i] + (model.Pev[model.N.prev(k), i]*Ts_data/60) == model.E_requested[i]
            
           
        def Efficiency(model, s, k, i):
            return model.Pev[k,i] == model.eff[s]*model.Pcharge[k,i]
            
        def EV_aggregated(model, k):
            return model.Pevtot[k] == sum(model.Pcharge[k,i] for i in model.V)
            
        def Balance(model, s, k):
            return model.Pgrid[k] == model.Pload[k] + model.Ppv[k] + model.Pevtot[k]
        
        def charging(model, s, k, i):
            return model.Pcharge[k, i] == (model.Icharge[k, i] * model.vmax[s])/1000 
    
        def charging_max(model, s, k, i):
            return model.Pcharge[k, i] <= model.pmax[s]
    
        def current_max(model, s, k, i):
            return model.Icharge[k, i] <= model.imax[s]

        def current_min(model, s, k, i):
            return model.Icharge[k, i] >= model.imin[s]
        
        def current(model, k, i):
            if pyo.value(model.T[k]) < pyo.value(model.T_arrival[i]) or pyo.value(model.T[k]) >= pyo.value(model.T_departure[i]):
                return model.Icharge[k, i] == 0
            else:
                return model.Icharge[k, i] >= 0

    
        model.con_EV_charging = Constraint(model.S, model.N, model.V, rule=EV_charging)
        model.con_Efficiency = Constraint(model.S, model.N, model.V, rule=Efficiency)
        model.con_EV_aggregated = Constraint(model.N, rule=EV_aggregated)
        model.con_Balance = Constraint(model.S, model.N, rule=Balance)
        model.con_charging = Constraint(model.S, model.N, model.V, rule=charging)
        model.con_charging_max = Constraint(model.S, model.N, model.V, rule=charging_max)
        model.con_current_max = Constraint(model.S, model.N, model.V, rule=current_max)
        #model.con_current_min = Constraint(model.S, model.N, model.V, rule=current_min)
        model.con_current = Constraint(model.N, model.V, rule=current)


        def costfunction(model, k):
            return sum((model.price[s]*model.Pgrid[k])**2 for k in model.N) - 0.4*sum(((1/(1+model.price[s]))*model.Pcharge[k, i])**2 for k in model.N for i in model.V)
    
        model.obj = Objective(rule=costfunction, sense=minimize)
    
        return model

    mymodel = create_model(df_load,df_ev,dummies, Ts_data)

    
    # Done! now you have to solve the model!
    solver = SolverFactory('ipopt') # This is ipopt, locally installed nonlinear solver
    solver.options['max_iter'] = 100000 # Number of iterations
    try:
        results = solver.solve(mymodel, tee=False) # tee means to show the steps of the solver
        
        for s in mymodel.S:
            pv = [mymodel.Ppv[k]() for k in mymodel.N]
            load = [mymodel.Pload[k]() for k in mymodel.N]
            grid = [mymodel.Pgrid[k]() for k in mymodel.N]
            grid_plus = [mymodel.Pgrid_plus[k]() for k in mymodel.N]
            grid_min = [mymodel.Pgrid_min[k]() for k in mymodel.N]
            time = [mymodel.T[k]() for k in mymodel.N]
        
        E_EV = []
        P_EV = []
        Icharge = []
        
        for i in mymodel.V:
            E_EV.append([mymodel.Eev[k,i]() for k in mymodel.N]) 
            P_EV.append([mymodel.Pev[k,i]() for k in mymodel.N]) 
            Icharge.append([mymodel.Icharge[k,i]() for k in mymodel.N])

        P_EVT = [mymodel.Pevtot[k]() for k in mymodel.N] 


        result_df = pd.DataFrame()
        
        for i in mymodel.V:
            result_df['EV' + str(i+1)] = pd.DataFrame(data=E_EV[i])
            result_df['PEV' + str(i+1)] = pd.DataFrame(data=P_EV[i])
            result_df['Current' + str(i+1)] = pd.DataFrame(data=Icharge[i])
            
        result_df['PEVTot'] = pd.DataFrame(data=P_EVT)
        result_df['PV'] = pd.DataFrame(data=pv)
        result_df['Load'] = pd.DataFrame(data=load)
        result_df['Grid'] = pd.DataFrame(data=grid)
        result_df['Grid_plus'] = pd.DataFrame(data=grid_plus)
        result_df['Grid_min'] = pd.DataFrame(data=grid_min)
        result_df['Time'] = pd.DataFrame(data=time)
        result_df.index = df_load.index
        pd.set_option('display.max_rows', 50)
        
        df_result = result_df.copy()
        df_result.index = pd.to_datetime(df_load.index)


        for i in mymodel.V:
            Icharge[i] = [x for x in Icharge[i]]
            df_ev.iloc[i,3] = df_result['EV' + str(i+1)][str(tnow + datetime.timedelta(minutes=Ts_data))].clip(0)
        
        df_ev.to_csv("ChargingSimulator/data/ev.csv")
        
        
        
    except Exception as SolverError: 
        print("Error with solver error:" + str(SolverError))
        
       
    
    return Icharge, df_result, df_ev