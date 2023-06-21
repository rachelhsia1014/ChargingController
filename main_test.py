import time

import pandas as pd
from ChargingSimulator.controller import controller
from ChargingSimulator.parameters import param
import pandas as pd
from datetime import datetime as dt
import datetime
import numpy as np
import random
import os, sys
from pathlib import Path
from time import strftime, localtime

from CANopen_laadpaal.node import laadpaal
eds = os.path.join(Path(sys.path[0]), "CANopen_laadpaal/V2G500V30A.eds")
lp = laadpaal(node_id=48, object_dictionary=eds)
lp.Power_Module_Enable = 'Disable'
time.sleep(2)
lp.Power_Module_Enable = 'Enable'


df_Icharge = pd.DataFrame(columns=['Datetime', 'Icharge'])
# run optimization iterations
for i in range(0, 20):
    #current = controller(i)

    Icharge_set = random.uniform(0.0, 3.0)

    time_now = strftime('%Y-%m-%d %H:%M:%S', localtime(time.time()))
    new_df_row = pd.DataFrame([[time_now, Icharge_set]],columns=['Datetime', 'Icharge'])
    df_Icharge = pd.concat([df_Icharge, new_df_row])

    lp.setSetpoint(350, Icharge_set)
    print('iteration = ' + str(i) + ' sends ' + str(Icharge_set))
    time.sleep(0.9)

df_Icharge.to_csv('ChargingSimulator/data/RealTime_Icharge')
lp.disablePower()