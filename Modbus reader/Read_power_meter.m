clear all;

% Create a Modbus Object.
m = modbus('tcpip', '192.168.10.40');
m.Timeout = 3;

% Save the Server ID specified.
serverId = 1;

flag = 0;
iterations = 60;

modbusData.PF1 = [];
modbusData.PF2 = [];
modbusData.PF3 = [];
modbusData.PF_total = [];

modbusData.V1_NL = [];
modbusData.V2_NL = [];
modbusData.V3_NL = [];
modbusData.V3ph_NL_avg = [];

modbusData.I1 = [];
modbusData.I2 = [];
modbusData.I3 = [];
modbusData.I3ph_avg = [];

modbusData.P1 = [];
modbusData.P2 = [];
modbusData.P3 = [];
modbusData.P_total = [];

% Read 1 Holding Register of type 'single' starting from address 70.
modbusData.I3ph_avg(end+1) = read(m, 'holdingregs', 62, 1, serverId, 'single');

while flag < iterations

% Holding Registers
% Read 3 Holding Registers of type 'single' starting from address 38.
data = read(m, 'holdingregs', 38, 3, serverId, 'single');
modbusData.PF1(end+1) = data(1);
modbusData.PF2(end+1) = data(2);
modbusData.PF3(end+1) = data(3);

% Read 1 Holding Register of type 'single' starting from address 70.
modbusData.PF_total(end+1) = read(m, 'holdingregs', 70, 1, serverId, 'single');

% Holding Registers
% Read 3 Holding Registers of type 'single' starting from address 2.
data = read(m, 'holdingregs', 2, 3, serverId, 'single');
modbusData.V1_NL(end+1) = data(1);
modbusData.V2_NL(end+1) = data(2);
modbusData.V3_NL(end+1) = data(3);

% Read 1 Holding Register of type 'single' starting from address 70.
modbusData.V3ph_NL_avg(end+1) = read(m, 'holdingregs', 58, 1, serverId, 'single');

% Read 3 Holding Registers of type 'single' starting from address 14.
data = read(m, 'holdingregs', 14, 3, serverId, 'single');
modbusData.I1(end+1) = data(1);
modbusData.I2(end+1) = data(2);
modbusData.I3(end+1) = data(3);

% Read 1 Holding Register of type 'single' starting from address 70.
modbusData.I3ph_avg(end+1) = read(m, 'holdingregs', 62, 1, serverId, 'single');


% Read 3 Holding Registers of type 'single' starting from address 26.
data = read(m, 'holdingregs', 26, 3, serverId, 'single');
modbusData.P1(end+1) = data(1);
modbusData.P2(end+1) = data(2);
modbusData.P3(end+1) = data(3);

% Read 1 Holding Register of type 'single' starting from address 70.
modbusData.P_total(end+1) = read(m, 'holdingregs', 66, 1, serverId, 'single');

flag = flag + 1;
pause(0.5)
end 