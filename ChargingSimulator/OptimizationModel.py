# -*- coding: utf-8 -*-
from pyomo.environ import *
import pandas as pd
import pyomo.environ as pyo
import datetime
from ChargingSimulator.parameters import param

def runOptimization(df_load, df_ev, tnow, Ts_data):
    #converting the datetime object to an integer which can be processed by Pyomo
    #df_ev = df_ev.loc[df_ev['E_requested'] >= 0.01]
    df_ev['T_arrival'] = tnow
    df_ev['I_arrival'] = df_ev['T_arrival'].apply(lambda x: x.value).copy()
    df_ev['I_departure'] = df_ev['T_departure'].apply(lambda x: x.value).copy()

    #Checking to see whether or not the arrival time is within the loads dataframe
    df_ev = df_ev[df_ev.index.isin(df_ev['I_arrival'].loc[df_ev['I_arrival'].isin(df_load.index)].index)].copy()
    dummies  = pd.DataFrame([[param['eff'],param['Imin'],param['Imax'], param['price'], param['Vcharger']]],columns=['eff', 'Imin', 'Imax', 'price', 'Vcharger'],index=['Data'])
    

    def create_model(input_load, input_ev, dummies, Ts_data):
        # Pyomo model
        model = ConcreteModel()
    
        # Creation of Set
        model.N = Set(ordered = True, initialize = RangeSet(0,len(input_load.index)-1)) #Horizon
        model.V = Set(ordered = True, initialize = RangeSet(0,len(input_ev.index)-1))   #Chargers
        model.S = Set(ordered = True, initialize = dummies.index)                       #Single variables
    
        # Creation Parameters
        model.Pload = Param(model.N, within = NonNegativeReals, mutable = True)
        model.Ppv = Param(model.N, within = Reals, mutable = True)
        model.T = Param(model.N, within = NonNegativeReals, mutable = True)
    
        model.E_requested = Param(model.V, within=NonNegativeReals, mutable=True)
        model.T_arrival = Param(model.V, within=NonNegativeReals, mutable=True)
        model.T_departure = Param(model.V, within=NonNegativeReals, mutable=True)
        model.P_previous = Param(model.V, within=NonNegativeReals, mutable=True)
        
        model.eff = Param(model.S, within = NonNegativeReals, mutable = True)
        model.imin = Param(model.S, within = NonNegativeReals, mutable = True)
        model.imax = Param(model.S, within = NonNegativeReals, mutable = True)
        model.price = Param(model.S, within = NonNegativeReals, mutable = True)
        model.vcharger = Param(model.S, within = NonNegativeReals, mutable = True)
    
        # Update parameters
        for s in model.S:
            model.eff[s] = dummies.loc[s, 'eff']
            model.imin[s] = dummies.loc[s, 'Imin']
            model.imax[s] = dummies.loc[s, 'Imax']
            model.price[s] = dummies.loc[s, 'price']
            model.vcharger[s] = dummies.loc[s, 'Vcharger']
        
        # Indexed:
        for k in model.N:
            model.T[k] = input_load.index[k]
            model.Pload[k] = input_load['Load'].iloc[k]
            model.Ppv[k] = input_load['PV'].iloc[k]
                
        for i in model.V:
            model.E_requested[i] = input_ev['E_requested'][i]
            model.T_arrival[i] = input_ev['I_arrival'][i]
            model.T_departure[i] = input_ev['I_departure'][i]

  
        # Creation of Variables
        model.Pgrid = Var(model.N, within = Reals)
        model.Pevtot = Var(model.N, within = Reals)
        model.Icharge = Var(model.N, model.V, within = Reals)
        model.Pcharge = Var(model.N, model.V, within = Reals)
        model.Pev = Var(model.N, model.V, within = Reals)
        model.Eev = Var(model.N, model.V, within = Reals)
    
        # Creation of constraints
        def Energy(model, k, i):
            if pyo.value(model.T[k]) <= pyo.value(model.T_arrival[i]):
                return model.Eev[k, i] == 0
            if pyo.value(model.T_arrival[i]) < pyo.value(model.T[k]) < pyo.value(model.T_departure[i]):
                return model.Eev[k, i] == (model.Eev[model.N.prev(k),i] + (model.Pev[model.N.prev(k), i]*Ts_data/60))
            if pyo.value(model.T[k]) >= pyo.value(model.T_departure[i]):
                return model.Eev[model.N.prev(k),i] + (model.Pev[model.N.prev(k), i]*Ts_data/60) == model.E_requested[i]

        def Power_ev(model, s, k, i):
            return model.Pev[k, i] == model.eff[s] * model.Pcharge[k, i]

        def Pev_aggregated(model, k):
            return model.Pevtot[k] == sum(model.Pcharge[k, i] for i in model.V)
            
        def Balance(model, k):
            return model.Pgrid[k] == model.Pload[k] + model.Ppv[k] + model.Pevtot[k]

        def Power_charger(model, s, k, i):
            return model.Pcharge[k, i] == (model.Icharge[k, i] * model.vcharger[s]) / 1000

        def Icharge_max(model, s, k, i):
            return model.Icharge[k, i] <= model.imax[s]

        def Current(model, s, k, i):
            if pyo.value(model.T[k]) < pyo.value(model.T_arrival[i]) or pyo.value(model.T[k]) >= pyo.value(
                    model.T_departure[i]):
                return model.Icharge[k, i] == 0
            else:
                return model.Icharge[k, i] >= model.imin[s]

        model.con_Energy = Constraint(model.N, model.V, rule=Energy)
        model.con_Power_ev = Constraint(model.S, model.N, model.V, rule=Power_ev)
        model.con_P_aggregated = Constraint(model.N, rule=Pev_aggregated)
        model.con_Balance = Constraint(model.N, rule=Balance)
        model.con_Power_charger = Constraint(model.S, model.N, model.V, rule=Power_charger)
        model.con_Icharge_max = Constraint(model.S, model.N, model.V, rule=Icharge_max)
        model.con_Current = Constraint(model.S, model.N, model.V, rule=Current)


        def costfunction(model, k):
            return sum((model.price[s]*model.Pgrid[k])**2 for k in model.N) - 0.4*sum(((1/(1+model.price[s]))*model.Pcharge[k, i])**2 for k in model.N for i in model.V)
    
        model.obj = Objective(rule=costfunction, sense=minimize)
    
        return model

    mymodel = create_model(df_load, df_ev, dummies, Ts_data)
    solver = SolverFactory('ipopt') # This is ipopt, locally installed nonlinear solver
    solver.options['max_iter'] = 100000 # Number of iterations
    try:
        results = solver.solve(mymodel, tee=False)  # tee means to show the steps of the solver

        pv = [mymodel.Ppv[k]() for k in mymodel.N]
        load = [mymodel.Pload[k]() for k in mymodel.N]
        grid = [mymodel.Pgrid[k]() for k in mymodel.N]
        time = [mymodel.T[k]() for k in mymodel.N]

        E_EV = []
        P_EV = []
        Icharge = []

        for i in mymodel.V:
            E_EV.append([mymodel.Eev[k, i]() for k in mymodel.N])
            P_EV.append([mymodel.Pev[k, i]() for k in mymodel.N])
            Icharge.append([mymodel.Icharge[k, i]() for k in mymodel.N])
        Icharge = [[round(num, 2) for num in sublist] for sublist in Icharge]

        P_EVT = [mymodel.Pevtot[k]() for k in mymodel.N]

        result_df = pd.DataFrame()
        for i in mymodel.V:
            result_df['EV' + str(df_ev['ChargerId'][i])] = pd.DataFrame(data=E_EV[i])
            result_df['PEV' + str(df_ev['ChargerId'][i])] = pd.DataFrame(data=P_EV[i])
            result_df['Current' + str(df_ev['ChargerId'][i])] = pd.DataFrame(data=Icharge[i])

        result_df['PEVTot'] = pd.DataFrame(data=P_EVT)
        result_df['PV'] = pd.DataFrame(data=pv)
        result_df['Load'] = pd.DataFrame(data=load)
        result_df['Grid'] = pd.DataFrame(data=grid)
        result_df['Time'] = pd.DataFrame(data=time)
        result_df.index = df_load.index # with datetime index presented by int

        df_result = result_df.copy()
        df_result.index = pd.to_datetime(df_load.index) # with datetime index

        print("Optimization at time = " + str(tnow))
        ## Printing the calculated values
        for i in range(len(Icharge)):
            print("EV" + str(df_ev['ChargerId'][i]) + " (requesting " + str(df_ev.iloc[i, 1]) + " kWh) is charged at " + str(round(df_result['Current' + str(df_ev['ChargerId'][i])].loc[str(tnow)], 2)) + "A at " + str(tnow))
            sim_out = pd.read_csv('ChargingSimulator/data/sim_out.csv', index_col=0)
            sim_out.index = pd.to_datetime(sim_out.index)
            sim_out["EV" + str(df_ev['ChargerId'][i])] = sim_out["EV" + str(df_ev['ChargerId'][i])].combine(df_result['Current' + str(df_ev['ChargerId'][i])], lambda x1, x2: x1 if pd.isna(x2) else x2)
            sim_out.to_csv('ChargingSimulator/data/sim_out.csv', header=True, index=True)

        for i in mymodel.V:
            df_ev.iloc[i, 1] = df_ev.iloc[i, 1] - df_result['EV' + str(df_ev['ChargerId'][i])][str(tnow + datetime.timedelta(minutes=Ts_data))]
            if df_ev.iloc[i, 1] < 0 or round(df_ev.iloc[i, 1], 2) == 0.00:
                df_ev.iloc[i, 1] = 0

        df_ev.to_csv("ChargingSimulator/data/ev.csv", index=False)
        #print('ev status updated.')


    except Exception as SolverError:
        print("!! Error with solver error:" + str(SolverError))

    if ('EV' + param['Controlled_ev']) in df_result.columns:
        Inow = round(df_result['Current' + param['Controlled_ev']].loc[str(tnow)], 2)
    else:
        Inow = param['Imin']

    return Inow