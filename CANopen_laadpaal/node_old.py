import canopen
from can.interfaces.vector import VectorBus



class laadpaal(canopen.RemoteNode):
    def __init__(self, node_id, object_dictionary):
        super().__init__(node_id, object_dictionary)
        network = canopen.Network()
        network.bus = VectorBus(channel=0, bitrate=500000)
        network.connect(bustype='vector', channel=0, bitrate=500000)
        network.add_node(self)

    def setSetpoint(self, voltage, current):  # TODO define limits
        """
        Set the setpoint of the laadpaal
        """
        if voltage > 500:
            print("Error; voltage must be between 0 and 500")
            return
        #time.sleep(2)
        self.DC_Input_Voltage_Setpoint = voltage

        if -3 > current > 3:
            print("Error; current must be between -3 and 3")
            return
        #time.sleep(2)
        self.DC_Input_Current_Setpoint = current



    def getSetpoint(self):
        """
        Get the REAL setpoint of the laadpaal
        """
        return self.IDC_setpoint, self.UDC_setpoint

    def disablePower(self):
        """
        Disable the laadpaal
        """
        self.Power_Module_Enable = 'Disable'

    @property
    def Power_Module_Enable(self) -> str:
        """Returns whether the power module is enabled or disabled.

        Returns:
            A string indicating whether the power module is "Enabled" or "Disabled".
        """
        print(self.sdo[0x2100].raw)
        if self.sdo[0x2100].bits[0] == 0:
            return "Disabled"
        else:
            return "Enabled"

    @Power_Module_Enable.setter
    def Power_Module_Enable(self, Power_Module_Enable: str):
        """
        Sets the power module enable property to either Enable or Disable.

        Args:
            Power_Module_Enable (str): The value to set the power module enable property to.
            Must be either "Enable" or "Disable".
        """
        if Power_Module_Enable == "Enable":
            self.sdo[0x2100].raw = 1
        elif Power_Module_Enable == "Disable":
            self.sdo[0x2100].raw = 0
        else:
            print("Error; Value can only be Disable or Enable")

    @property
    def Power_Module_Status(self) -> list:
        """Returns the status of the power module.

        Returns:
            A list of strings indicating the status of the power module.
        """
        returnlist = []
        if self.sdo[0x2101].bits[0] == 1:
            returnlist.append("Charger on")
        else:
            returnlist.append("Charger off")
        if self.sdo[0x2101].bits[1] == 1:
            returnlist.append("Power error")
        if self.sdo[0x2101].bits[2] == 1:
            returnlist.append("Input over voltage detect")
        if self.sdo[0x2101].bits[3] == 1:
            returnlist.append("Input under voltage detect")
        if self.sdo[0x2101].bits[4] == 1:
            returnlist.append("Output over voltage detect")
        if self.sdo[0x2101].bits[5] == 1:
            returnlist.append("Output under voltage detect")
        if self.sdo[0x2101].bits[7] == 1:
            returnlist.append("Over temperature detect")
        if self.sdo[0x2101].bits[8] == 1:
            returnlist.append("Uaux error, UV / OV")
        if self.sdo[0x2101].bits[10] == 1:
            returnlist.append("V2G mode")
        else:
            returnlist.append("CHARGE mode")
        if self.sdo[0x2101].bits[11] == 1:
            returnlist.append("Grid error (AC voltage, frequency, phase)")
        if self.sdo[0x2101].bits[12] == 1:
            returnlist.append("HW interlock error")
        if self.sdo[0x2101].bits[13] == 1:
            returnlist.append("Service mode enabled")
        return returnlist

    @property
    def Power_Module_Temperature(self):
        """
        This read-only object contains the highest temperature of all temperature measurements in the module.
        """
        return self.sdo[0x2104].raw * 10

    @property
    def AC_Input_Voltage(self):
        """
        This read-only object contains the measured average input voltage of the three AC phases (line-neutral).
        """
        return self.sdo[0x2105].raw * 10

    @property
    def AC_Input_Current(self):
        """
        This read-only object contains the measured average input current of the three AC phases
        """
        return self.sdo[0x2106].raw * 10

    @property
    def DC_Output_Voltage(self):
        """
        This read-only object contains the measured output voltage
        """
        return self.sdo[0x2107].raw * 10

    @property
    def DC_Output_Current(self):
        """
        This read-only object contains the measured output current
        """
        return self.sdo[0x2108].raw * 10

    @property
    def DC_Input_Voltage_Setpoint(self):
        """
        This read/write object contains the output voltage setpoint
        """
        return self.sdo[0x2109].raw * 10

    @DC_Input_Voltage_Setpoint.setter
    def DC_Input_Voltage_Setpoint(self, DC_Input_Voltage_Setpoint):
        self.sdo[0x2109].raw = DC_Input_Voltage_Setpoint * 10

    @property
    def DC_Input_Current_Setpoint(self):
        """
        This read/write object contains the output current setpoint
        """
        return self.sdo[0x210A].raw / 10

    @DC_Input_Current_Setpoint.setter
    def DC_Input_Current_Setpoint(self, DC_Input_Current_Setpoint):
        self.sdo[0x210A].raw = DC_Input_Current_Setpoint * 10

    @property
    def DC_Bus_Voltage(self):
        """
        This read-only object contains the internal DC bus voltage
        """
        return self.sdo[0x210D].raw / 10

    @property
    def Power_Module_DC_Undervoltage_Setpoint(self):
        """
        This read/write object contains the output undervoltage setpoint
        """
        return self.sdo[0x210F].raw / 10

    @Power_Module_DC_Undervoltage_Setpoint.setter
    def Power_Module_DC_Undervoltage_Setpoint(self, Power_Module_DC_Undervoltage_Setpoint):
        self.sdo[0x210F].raw = Power_Module_DC_Undervoltage_Setpoint / 10

    @property
    def UDC_setpoint(self):
        """
        This read-only object contains the real (current) setpoint of UDC that is used by the module
        """
        return self.sdo[0x2149].raw / 10

    @property
    def IDC_setpoint(self):
        """
        This read-only object contains the real (current) setpoint of UDC that is used by the module
        """
        return self.sdo[0x214A].raw / 10

    @property
    def Available_power_charge_mode(self):
        """
        This read-only object contains the available power if the module is in charge mode
        """
        return self.sdo[0x214B].raw / 10

    @property
    def Available_power_V2G_mode(self):
        """
        This read-only object contains the available power if the module is in V2G mode
        """
        return self.sdo[0x214C].raw / 10

    @property
    def Turn_off_reason(self):
        """
        This read-only object contains the available power if the module is in V2G mode
        """
        return self.sdo[0x2150].raw

    @property
    def Maximum_DC_current_charge(self):
        """
        This read/write object contains the maximum current allowed in charge mode on the DC side of the module
        """
        return self.sdo[0x214D].raw / 10

    @Maximum_DC_current_charge.setter
    def Maximum_DC_current_charge(self, Maximum_DC_current_charge):
        self.sdo[0x214D].raw = Maximum_DC_current_charge / 10

    @property
    def Maximum_DC_current_V2G(self):
        """
        This read/write object contains the maximum current allowed in V2G mode on the DC side of the module.
        """
        return self.sdo[0x214D].raw / 10

    @Maximum_DC_current_V2G.setter
    def Maximum_DC_current_V2G(self, Maximum_DC_current_V2G):
        self.sdo[0x214D].raw = Maximum_DC_current_V2G / 10





