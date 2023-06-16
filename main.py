import pandas as pd
from ChargingSimulator.controller import controller
from ChargingSimulator.parameters import param
import os, sys
from pathlib import Path
import threading
import time



# starting main
# variable initialization
sim_out = pd.DataFrame()
testbed = param['Testbed']
connect_with_charger = True


def send_to_chager(lp, i, set_current):
    global connect_with_charger
    set_voltage = param["Vcharger"]

    # Enable for the 1st iteration and disable at the last iteration
    if i == 0:
        lp.Power_Module_Enable = 'Enable'
        print('1st iteration: ' + str(lp.Power_Module_Status))

    if i == param['N'] - 1:
        print('last iteration')
        lp.setSetpoint(0, 0)
        lp.disablePower()
        connect_with_charger = False

    if set_current is not None:
        print('current sent = ', set_current)
        lp.setSetpoint(set_voltage, set_current)

def send_current_periodically():   # send signal every 0.5 secs

    while connect_with_charger:
        print(lp.Power_Module_Status)
        time.sleep(0.5)


# initialize communication with charger and start periodically sending the set current
if testbed == True:
    from CANopen_laadpaal.node import laadpaal
    eds = os.path.join(Path(sys.path[0]), "CANopen_laadpaal/V2G500V30A.eds")
    lp = laadpaal(node_id=48, object_dictionary=eds)

    send_current_thread = threading.Thread(target=send_current_periodically)
    send_current_thread.start()

# run optimization iterations
for i in range(0, param['N']):
    Icharge_result = controller(i)
    Icharge_set = Icharge_result
    send_to_chager(lp, i, Icharge_set)



print('Simulation completed.')

