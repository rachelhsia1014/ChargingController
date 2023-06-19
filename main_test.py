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

from CANopen_laadpaal.node import laadpaal
eds = os.path.join(Path(sys.path[0]), "CANopen_laadpaal/V2G500V30A.eds")
lp = laadpaal(node_id=48, object_dictionary=eds)
lp.Power_Module_Enable = 'Enable'

# run optimization iterations
for i in range(0, param['N']+1):
    #current = controller(i)
    Icharge_set = random.uniform(0.0, 3.0)
    lp.setSetpoint(350, Icharge_set)
    print('iteration = ' + str(i))
    time.sleep(0.8)

lp.disablePower()