param = {
    # Datetime settings
    "tnow_initial": "2022-03-21 06:00:00",  # Simulation starting date
    "ev_file": "ChargingSimulator/data/ev_march_test.csv",
    "Controlled_ev": "1",
    # EV data file location (ChargingSimulator is needed, since python is run from Matlab folder)

    # Controller parameters:
    "Testbed": False,  # Determines whether or not the mouse should be moved to control the EV charger on the testbed
    "Ts_data": 5,  # [m] data sample time (for optimization model) minimum is 1 (if changed the signal in simulink needs to be changed as well)
    "Ts": 3,  # [s] simulation sample time (only applicable in stand-alone mode)
    "N": 144,  # number of iterations (this is also controlled by the matlab signal)

    # Optimization dummie values:
    "eff": 0.83,  # Total charging efficiency (from charger to EV)
    "Imin": 0.6,  # Minimum charger current (not used atm) 0.1
    "Imax": 3,  # Maximum charger current 3
    "Vcharger": 380,  # Maximum charger voltage 380

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