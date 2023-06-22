import pandas as pd
from ChargingSimulator.controller import controller
from ChargingSimulator.parameters import param
import os, sys
from pathlib import Path
import threading
import time
import random
from time import strftime, localtime


# starting main
# variable initialization
sim_out = pd.DataFrame()
testbed = param['Testbed']
connect_with_charger = True
df_Icharge = pd.DataFrame(columns=['Datetime', 'Icharge'])
charger_connect = False
set_current = 0
set_voltage = param["Vcharger"]


def send_to_chager(lp, i):
    global connect_with_charger, df_Icharge, set_current, set_voltage
    set_voltage = param["Vcharger"]

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
        time_now = strftime('%Y-%m-%d %H:%M:%S', localtime(time.time()))
        new_df_row = pd.DataFrame([[time_now, set_current]], columns=['Datetime', 'Icharge'])
        df_Icharge = pd.concat([df_Icharge, new_df_row])
        lp.setSetpoint(set_voltage, set_current)


def send_current_periodically():   # send signal every 0.5 secs
    global set_current, set_voltage
    while connect_with_charger:
        try:
            #status = lp.Power_Module_Status
            lp.setSetpoint(set_voltage, set_current)
            time.sleep(0.1)
        except:
            print('Module uptime:' + str(lp.Module_uptime()))
            print('Switch off reason:' + str(lp.Turn_off_reason))
            print('Warning status:' + str(lp.Warning_status()))
            print('Error source:' + str(lp.Error_source()))



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

    set_current, charger_connect = controller(i, charger_connect)
    if charger_connect == False:
        set_current = 0

    if testbed == True:
        send_to_chager(lp, i)
        time.sleep(2)

lp.disablePower()
df_Icharge.to_csv('ChargingSimulator/data/RealTime_Icharge')
print('Simulation completed.')

