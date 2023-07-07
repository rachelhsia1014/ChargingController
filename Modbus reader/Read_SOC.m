clear all;

% Create a Modbus Object.
m = modbus('tcpip', '192.168.10.212');
m.Timeout = 3;

% Save the Server ID specified.
serverId = 1;

flag = 0;
iterations = 480;

modbusData.soc = [];

while flag < iterations

% Read 1 Holding Register of type 'single' starting from address 70.
modbusData.soc(end+1) = read(m, 'holdingregs', 26172, 1, serverId, 'single');
flag = flag + 1;
pause(1)
end 