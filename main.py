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



def send_to_chager(lp, i, set_current):
    set_voltage = param["v_charger"]

    # Enable for the 1st iteration and disable at the last iteration
    if i == 0:
        lp.Power_Module_Enable = 'Enable'
        print('1st iteration: '+ str(lp.Power_Module_Status))
    if i == param['N'] - 1:
        print('last iteration')
        lp.setSetpoint(0, 0)
        lp.disablePower()

    if set_current is not None:
        print('current sent = ', set_current)
        lp.setSetpoint(set_voltage, set_current)

def send_current_periodically():
    # send signal every 0.5 secs
    while True:
        print(lp.Power_Module_Status)
        time.sleep(0.5)


# initialize communication with charger and start periodically sending the set current
if testbed == True:
    from CANopen_laadpaal.node_old import laadpaal
    eds = os.path.join(Path(sys.path[0]), "CANopen_laadpaal/V2G500V30A.eds")
    lp = laadpaal(node_id=48, object_dictionary=eds)

    send_current_thread = threading.Thread(target=send_current_periodically)
    send_current_thread.start()

# run optimization iterations
for i in range(0, param['N']):
    time.sleep(1)
    #Icharge_result, df_result = controller(i)
    #Icharge_set = Icharge_result[0][0]
    #shared_variable['set_current_sent'] = Icharge_set
    Icharge_set = i/10
    send_to_chager(lp, i, Icharge_set)



# wait for the thread to finish and stop it
#if testbed == True:
    #send_current_thread.join()
send_current_thread.join()
print('Simulation completed.')


"""
from tkinter import *
from threading import Thread
import time
from controller import controller
from parameters import param
import pandas as pd

def running():
    print("Starting...")
    sim_out = pd.DataFrame()
    try: i
    except NameError: i = None
    if i is None:
        i = 0
    while True:
        df_result = controller(i)
        Icharge, sim_out = pd.concat([sim_out, df_result], axis=0)
        sim_out.to_csv("data/sim_out.csv")
        i += 1
        time.sleep(param['Ts'])
        if i == param['N']:
            print("Simulation complete")
            break
        if stop == 1:
            print("Stopped")
            break   #Break while loop when stop = 1
            
def start_thread():
    # Assign global variable and initialize value
    global stop
    stop = 0

    # Create and launch a thread 
    t = Thread (target = running)
    t.start()

def stop():
   # Assign global variable and set value to stop
   global stop
   print("Stop button pressed")
   stop = 1


root = Tk()
root.title("Controller")
root.geometry("200x200")

app = Frame(root)
app.grid()

start = Button(app, text="Start",command=start_thread)
stop = Button(app, text="Stop",command=stop)

start.grid()
stop.grid()

app.mainloop()
"""
