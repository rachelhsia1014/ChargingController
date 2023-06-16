from CANopen_laadpaal.node_old import laadpaal
import os, sys
from pathlib import Path
eds = os.path.join(Path(sys.path[0]), "CANopen_laadpaal/V2G500V30A.eds")
lp = laadpaal(node_id=48, object_dictionary=eds)
lp.Power_Module_Enable = 'Disable'
#lp.Power_Module_Enable = 'Enable'
#lp.setSetpoint(380, 2)
print(lp.Power_Module_Status)




