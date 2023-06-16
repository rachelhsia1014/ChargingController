param = {
    # Datetime settings
    "tnow_initial": "2022-03-21 06:00:00",  # Simulation starting date
    "ev_file": "ChargingSimulator/data/ev_march_test.csv",
    # EV data file location (ChargingSimulator is needed, since python is run from Matlab folder)

    # charger setting
    "v_charger": 380,

    # Controller parameters:
    "Testbed": True,  # Determines whether or not the mouse should be moved to control the EV charger on the testbed
    "Ts_data": 5,  # [m] data sample time (for optimization model) minimum is 1 (if changed the signal in simulink needs to be changed as well)
    "Ts": 3,  # [s] simulation sample time (only applicable in stand-alone mode)
    "N": 10,  # number of iterations (this is also controlled by the matlab signal)

    # Optimization dummie values:
    "eff": 0.83,  # Total charging efficiency (from charger to EV)
    "imin": 0.1,  # Minimum charger current (not used atm)
    "imax": 3,  # Maximum charger current
    "pmax": 10,  # Maximum charger power output
    "vmax": 400,  # Maximum charger voltage
    "price": 0.44,  # Electricity price
    "FIT": 0.18,  # Feed-in-tarrif

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