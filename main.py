import pandas as pd
from ChargingSimulator.controller_local_load import controller
from ChargingSimulator.parameters import param
import os, sys
from pathlib import Path
import threading
import time
from time import strftime, localtime

# starting main
# variable initialization
sim_out = pd.DataFrame()
testbed = param['Testbed']
connect_with_charger = True
df_measurement = pd.DataFrame(columns=['Datetime', 'Iset', 'Igrid_avg','Vgrid_avg','Icharger', 'Vcharger'])
df_measurement.to_csv('ChargingSimulator/data/charger_measurement.csv', header=True)
charger_connect = False
set_current = 0
set_voltage = param["Vcharger"]


def send_to_chager(lp, i):
    global connect_with_charger, set_current, set_voltage

    # Enable for the 1st iteration and disable at the last iteration
    if i == 0:
        lp.Power_Module_Enable = 'Enable'
        print('1st iteration: ' + str(lp.Power_Module_Status))

    if i == param['N'] - 1:
        print('last iteration')
        lp.setSetpoint(0, 0)
        connect_with_charger = False

    if set_current is not None:
        print(str(i) + 'iteration current sent = ', set_current)
        df_measurement = pd.read_csv('ChargingSimulator/data/realtime_measurement.csv')
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


def send_current_periodically():   # send signal every 0.08 secs
    global set_current, set_voltage
    while connect_with_charger:
        try:
            lp.setSetpoint(set_voltage, set_current)
            time.sleep(0.08)
        except:
            print('conflict!!')


# initialize communication with charger and start periodically sending the set current
if testbed == True:
    from CANopen_laadpaal.node import laadpaal
    eds = os.path.join(Path(sys.path[0]), "CANopen_laadpaal/V2G500V30A.eds")
    lp = laadpaal(node_id=48, object_dictionary=eds)

    lp.Power_Module_Enable = 'Disable'
    send_current_thread = threading.Thread(target=send_current_periodically)
    send_current_thread.start()

# run optimization iterations
for i in range(0, param['N']):

    tnow, set_current, charger_connect = controller(i, charger_connect)

    if charger_connect == False:
        set_current = 0

    if testbed == True:
        send_to_chager(lp, i)
        time.sleep(2)

if testbed == True:
    lp.disablePower()

print('Simulation completed.')



