import pandas as pd
from ChargingSimulator.controller_local_load import controller
from ChargingSimulator.parameters import param
import os, sys
from pathlib import Path
import threading
import time
from time import strftime, localtime

# Starting main

# global variable and initialization
testbed = param['Testbed']
set_voltage = param["Vcharger"]
set_current = 0 # send 0 when the simulated ev is not yet arrives or is staying idled after finishing charging

start_simulation = True # become False when the simulation reaches the last iteration
charging_session = False # become False when the simulated EV has left but the iteration hasn't finished

df_measurement = pd.DataFrame(columns=['Datetime', 'Iset', 'Igrid_avg','Vgrid_avg','Icharger', 'Vcharger'])
df_measurement.to_csv('ChargingSimulator/data/charger_measurement.csv', header=True)


# Function to send commends to charger
def send_to_charger(lp, i):
    global start_simulation, set_current, set_voltage

    # Enable power module for the first iteration and disable it for the last iteration
    if i == 0:
        lp.Power_Module_Enable = 'Enable'
        print('1st iteration: ' + str(lp.Power_Module_Status))

    if i == param['N'] - 1:
        print('last iteration')
        lp.setSetpoint(0, 0)
        start_simulation = False

    # Send current charging current to the charger
    # at the same time, also collect the data from the charger, and update to the csv file
    if set_current is not None:
        print(str(i) + ' iteration current sent = ', set_current)
        df_measurement = pd.read_csv('ChargingSimulator/data/charger_measurement.csv')
        time_now = strftime('%Y-%m-%d %H:%M:%S', localtime(time.time()))
        try:
            Igrid_avg = lp.AC_Input_Current / 100
            Vgrid_avg = lp.AC_Input_Voltage / 100
            Vcharger = lp.DC_Output_Voltage / 100
            Icharger = lp.DC_Output_Current / 100
        except:
            Igrid_avg = 0
            Vgrid_avg = 0
            Vcharger = 0
            Icharger = 0
        new_df_row = pd.DataFrame([[time_now, set_current, Igrid_avg, Vgrid_avg, Icharger, Vcharger]], columns=['Datetime', 'Iset', 'Igrid_avg', 'Vgrid_avg','Icharger', 'Vcharger'])
        df_measurement = pd.concat([df_measurement, new_df_row])
        df_measurement.to_csv('ChargingSimulator/data/realtime_measurement.csv', header=True, index=False)
        lp.setSetpoint(set_voltage, set_current)

# Thread sending current periodically (every 0.08 seconds)
# in order to keep connection with the charger,
def send_current_periodically():
    global set_current, set_voltage
    while start_simulation:
        try:
            lp.setSetpoint(set_voltage, set_current)
            time.sleep(0.08)
        except:
            print('Conflict!!')

# Initialize communication with charger and start the thread above
if testbed == True:
    from CANopen_laadpaal.node import laadpaal
    eds = os.path.join(Path(sys.path[0]), "CANopen_laadpaal/V2G500V30A.eds")
    lp = laadpaal(node_id=48, object_dictionary=eds)

    lp.Power_Module_Enable = 'Disable' # make sure the charger starts in the disable mode
    send_current_thread = threading.Thread(target=send_current_periodically)
    send_current_thread.start()

# Run optimization iterations
for i in range(0, param['N']):

    tnow, set_current, charging_session = controller(i, charging_session)

    if charging_session == False:
        set_current = 0

    if testbed == True:
        send_to_charger(lp, i)
        time.sleep(2)

# Disable power if testbed is running
if testbed == True:
    lp.disablePower()

print('Simulation completed.')
