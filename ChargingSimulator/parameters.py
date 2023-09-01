param = {
    # Datetime settings
    "tnow_initial": "2022-12-12 06:00:00",  # Simulation starting date
    "ev_file": "ChargingSimulator/data/ev_data.csv", # please check if the data corresponds to the tnow_intital
    "load_file": "ChargingSimulator/data/load_data.csv",
    "price_file": "ChargingSimulator/data/price_data.csv",
    "Enable_controller": True,
    "Controlled_ev": "2",
    "PV_scale_factor": 1,
    # EV data file location (ChargingSimulator is needed, since python is run from Matlab folder)

    # Controller parameters:
    "Testbed": True,  # Determines whether or not the mouse should be moved to control the EV charger on the testbed
    "Ts_data": 5,  # [m] data sample time (for optimization model) minimum is 1 (if changed the signal in simulink needs to be changed as well)
    "Ts": 3,  # [s] simulation sample time (only applicable in stand-alone mode)
    "N": 144,  # number of iterations (this is also controlled by the matlab signal)

    # Optimization dummie values:
    "eff_battery": 0.97,  # battery efficiency
    "eff_charger": 0.88,  # charger efficiency
    "Imin": 6,  # Minimum charger current (not used atm) 0.1
    "Imax": 20,  # Maximum charger current 3
    "Vcharger": 380,  # Maximum charger voltage 350

    # Troubleshooting
    "E_factor": 1,
    # (default = 1) Requested energy is multiplied by this value, use this if optimization problem becomes infeasable.

}

'''
grid power available around 11 kW
charger power available around 10 kW
if three batteries: each car can have around 3 kW power max
(which according to max current at around 8 amps)
'''