% NOTE: This was generated using the Gemini LLM, so take any and all
% results with a few grains of salt.

% wifi_log_distance_calc
% Calculates interference using the Log-Distance Path Loss Model.
% This model allows you to simulate indoor/cluttered environments
% by adjusting the path loss exponent 'n'.

clc; clear; close all; rng(1);

%% --- 1. CONFIGURATION ---

% Positions (x, y in meters)
positions = [158.67, 164.39;97.01, 52.32;0.09, 132.56;94.05, 151.95;54.54, 160.38;145.96, 82.80;107.66, 136.41;38.60, 110.72;161.02, 53.10;160.67, 137.14;18.63, 160.06;18.76, 39.43;126.98, 58.24;190.27, 117.71;40.17, 131.08;];


% Channels (1-11)
channels = [1,6,11,6,11,11,11,1,6,6,1,1,1,1,6,];
%channels = randi([1, 11], 1, 15);

% --- LOG-DISTANCE MODEL PARAMETERS ---
n = 2.5;            % Path Loss Exponent (2.0=FreeSpace, 3.0=Office, 4.0=HardWalls)
d0 = 1.0;           % Reference distance (meters)
sigma = 0;          % Shadowing Std Dev (dB). Set to 0 for deterministic. 
                    % Set to ~3-6 dB for random realistic fluctuation.

TxPower_dBm = 10;   % Transmit Power

% Spectral Mask (dB attenuation per channel delta)
% [Delta0, Delta1, Delta2, Delta3, Delta4, Delta5+]
spec_mask = [0, 28, 35, 45, 50, 60]; 

%% --- 2. CALCULATE REFERENCE LOSS (PL0) ---
% Calculate Free Space Path Loss at reference distance d0 (1 meter)
% Center freq approx 2.44 GHz for reference
lambda = (3e8) / 2.44e9;
PL0 = 20*log10( (4*pi*d0) / lambda );

fprintf('Environment Model: Log-Distance (n=%.1f)\n', n);
fprintf('Reference Loss at 1m: %.2f dB\n', PL0);

%% --- 3. CALCULATION LOOP ---
num_tx = size(positions, 1);
interference_matrix_mW = zeros(num_tx, num_tx); 

for i = 1:num_tx
    for j = 1:num_tx
        if i == j
            continue; 
        end
        
        % A. Distance
        d = norm(positions(i,:) - positions(j,:));
        if d < d0, d = d0; end % Cap min distance
        
        % B. Log-Distance Path Loss Formula
        % PL(d) = PL0 + 10 * n * log10(d/d0)
        path_loss = PL0 + 10 * n * log10(d/d0);
        
        % Add Random Shadowing (if sigma > 0)
        if sigma > 0
            path_loss = path_loss + (randn * sigma);
        end
        
        % C. Spectral Overlap Loss
        delta = abs(channels(i) - channels(j));
        if delta >= length(spec_mask)
            spec_loss = spec_mask(end);
        else
            spec_loss = spec_mask(delta + 1);
        end
        
        % D. Received Power
        rx_dBm = TxPower_dBm - path_loss - spec_loss;
        
        % Store in mW
        interference_matrix_mW(i,j) = 10^(rx_dBm/10);
    end
end

%% --- 4. AGGREGATE & VISUALIZE ---

% Total Interference (Sum of linear powers)
total_int_mW = sum(interference_matrix_mW, 2);
total_int_dBm = 10 * log10(total_int_mW);

% Table Output
disp('--- Interference Results ---');
T = table((1:num_tx)', channels', total_int_dBm, ...
    'VariableNames', {'AP_ID', 'Channel', 'Noise_Floor_dBm'});
disp(T);

% Visualization
figure('Color','w', 'Name', 'Log-Distance Interference Model');

% 1. Heatmap of Path Loss Matrix (Visualizing the "Cost" between nodes)
axis square;
% We convert the interference matrix back to dBm for plotting
heatmap_data = 10*log10(interference_matrix_mW);
heatmap_data(heatmap_data == -Inf) = NaN; % Handle zeros
clims = [-140, -60];
h = imagesc(heatmap_data, clims);
h.AlphaData = ones(size(h.CData)); 
h.AlphaData(isnan(h.CData)) = 0;
colorbar; title('Interference Matrix (dBm)');
xlabel('Source Tx'); ylabel('Victim Rx');
