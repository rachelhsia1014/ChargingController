import pandas as pd
from ChargingSimulator.controller import controller
from ChargingSimulator.parameters import param
import os, sys
from pathlib import Path
import threading
import time
from time import strftime, localtime
import datetime
import matplotlib.pyplot as plt

# Prepare for plotting
plt.ion()   # Enable interactive mode
plt.figure(figsize=(12, 5))    # Create an empty plot
plt.xlabel('Time')
plt.ylabel('Charging current (A)')
plt.title('EV' + param['Controlled_ev'] + 'Charging Current')
start_time = datetime.datetime.strptime(param['tnow_initial'], '%Y-%m-%d %H:%M:%S')
end_time = start_time + datetime.timedelta(minutes=param['Ts_data'] * param['N'])
datetime_values = [start_time + datetime.timedelta(minutes=5 * i) for i in range(int((end_time - start_time).total_seconds() // 300) + 1)]
x_ticks_all = range(len(datetime_values))
x_tick_labels = [dt.strftime('%Y-%m-%d %H:%M:%S') for dt in datetime_values]
x_ticks = x_ticks_all[::12]
x_tick_labels = x_tick_labels[::12]
plt.xticks(x_ticks, x_tick_labels, rotation=45, fontsize=5)
y = [None] * (param['N'] + 1)
line, = plt.plot(x_ticks_all, y)
plt.ylim(0, 35)


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
            #print(lp.Power_Module_Status) -> not working
            lp.DC_Output_Voltage
            lp.DC_Output_Current
            lp.setSetpoint(set_voltage, set_current)
            time.sleep(0.08)
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

    tnow, set_current, charger_connect = controller(i, charger_connect)
    if charger_connect == False:
        set_current = 0

    # update the plot
    y[i] = set_current
    line.set_ydata(y)
    plt.draw()
    plt.pause(0.1)

    if testbed == True:
        send_to_chager(lp, i)
        time.sleep(2)

if testbed == True:
    lp.disablePower()
    df_Icharge.to_csv('ChargingSimulator/data/RealTime_Icharge')

print('Simulation completed.')
plt.show(block=True)



