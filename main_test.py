import pandas as pd
from ChargingSimulator.controller import controller
from ChargingSimulator.parameters import param
import pandas as pd
from datetime import datetime as dt
import datetime
import numpy as np


# run optimization iterations
for i in range(0, param['N']+1):
    current = controller(i)




