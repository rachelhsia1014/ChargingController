from pyModbusTCP.client import ModbusClient

ip_address = "192.168.10.212"
port = 502
client = ModbusClient(ip_address, port=port, timeout=3)
client.debug = True
read = client.read_holding_registers(26164, 1)
result = float(read[0])
print(result)
'''try:
    client.connect()
    if client.connected:
        response = client.read_holding_registers(26164)

        if response.isError():
            print('Modbus Read Error: ', response)
        else:
            soc = response.registers[0]
            print('soc = ', soc)
    else:
        print('Client not connected')
finally:
    client.close()
'''
