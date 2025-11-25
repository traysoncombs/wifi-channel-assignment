% Necessary MATLAB add ons: Communications Toolbox, WLAN Toolbox, Wireless Network Simulator

%% Wireless Network Simulation — Router Placement Optimization
clear; clc; close all;

%% Simulation parameters
numRouters = 5;              % Number of routers (APs)
areaSize = [100 100];        % Simulation area in meters
iterations = 10;            % Optimization iterations
stepSize = 2;                % Step size for movement

%% Initialize wireless network simulator
sim = wirelessNetworkSimulator.init;

%% Create AP nodes
apNodes = [];

for i = 1:numRouters
    % Random initial position
    pos = [rand()*areaSize(1), rand()*areaSize(2), 1.5];  % x, y, z
    
    % WLAN device configuration
    apCfg = wlanDeviceConfig("TransmitPower", 20);  % dBm
    
    % Create WLAN node
    ap = wlanNode("DeviceConfig", apCfg);
    
    % Set position
    ap.Position = pos;
    
    % Store node
    apNodes = [apNodes; ap];
end

%% Add nodes to simulator
addNodes(sim, apNodes);

%% Path-loss model using 'close-in' (log-distance equivalent)
plModel = propagationModel("close-in", ...
    "ReferenceDistance", 1, ...      % 1 meter reference
    "PathLossExponent", 3.0);        % typical NLOS

%% Function to compute total network path loss
function totalPL = computeTotalPathLoss(nodes, model)
    totalPL = 0;
    N = numel(nodes);
    txPowerW = 10^(20/10) / 1000;  % convert 20 dBm to watts

    for i = 1:N
        for j = i+1:N
            % Create txsite with Cartesian coordinate system
            tx = txsite("cartesian", ...
                        "AntennaPosition", nodes(i).Position(:), ...
                        "TransmitterPower", txPowerW);

            % Create rxsite with Cartesian coordinates
            rx = rxsite("cartesian", ...
                        "AntennaPosition", nodes(j).Position(:));

            pl = pathloss(model, rx, tx);
            totalPL = totalPL + pl;
        end
    end
end

%% Optimization loop (hill climbing)
for iter = 1:iterations
    for i = 1:numRouters
        current = apNodes(i).Position;
        bestPos = current;
        bestCost = computeTotalPathLoss(apNodes, plModel);
        
        % 8 directions to try
        dirs = [1 0; -1 0; 0 1; 0 -1; 1 1; 1 -1; -1 1; -1 -1];
        
        for d = 1:size(dirs,1)
            candidate = current;
            candidate(1:2) = candidate(1:2) + stepSize * dirs(d,:);
            
            % Keep inside area
            candidate(1) = min(max(candidate(1),0), areaSize(1));
            candidate(2) = min(max(candidate(2),0), areaSize(2));
            
            % Test candidate
            apNodes(i).Position = candidate;
            cost = computeTotalPathLoss(apNodes, plModel);
            
            if cost < bestCost
                bestCost = cost;
                bestPos = candidate;
            end
        end
        
        % Update to best position found
        apNodes(i).Position = bestPos;
    end
end

%% Display final total path loss
finalCost = computeTotalPathLoss(apNodes, plModel);
disp("Final Total Path Loss (dB): " + finalCost);

%% Visualize final router positions
figure;
% Extract positions
positions = reshape([apNodes.Position], 3, []).';  % Nx3 matrix

% 2D scatter plot
scatter(positions(:,1), positions(:,2), 100, 'filled');
xlabel('X (m)');
ylabel('Y (m)');
title('Optimized Router Layout');
axis([0 areaSize(1) 0 areaSize(2)]);
grid on;

% 3D scatter plot
figure;
scatter3(positions(:,1), positions(:,2), positions(:,3), 100, 'filled');
xlabel('X (m)');
ylabel('Y (m)');
zlabel('Z (m)');
title('Optimized Router Layout (3D)');
grid on;
