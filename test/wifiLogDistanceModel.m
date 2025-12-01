function results = wifiLogDistanceModel(positions, channels, opts)
% wifiLogDistanceModel  Log-distance interference simulation (modular)
%
% results = wifiLogDistanceModel(positions, channels, opts)
%
% Inputs:
%   positions  - N-by-2 array of [x,y] (meters). If empty, a default set is used.
%   channels   - 1-by-N vector of channel indices (1..11). If empty, randomized.
%   opts       - struct or name-value with fields:
%                .n (path loss exponent, default 2.5)
%                .d0 (reference distance m, default 1)
%                .sigma (shadowing std dB, default 0)
%                .TxPower_dBm (default 10)
%                .spec_mask (vector, default [0 28 35 45 50 60])
%                .iterations (default 1000)
%                .doPlot (logical, default true)
%                .rngSeed (numeric or [], default [])
%
% Output:
%   results - struct with fields:
%             .avgInterferenceByIter (iterations x 1)
%             .finalInterferenceMatrix_dBm (N x N)
%             .channels, .opts, .positions

arguments
    positions {mustBeNumeric} = []
    channels = []
    opts.n double = 2.5
    opts.d0 double = 1.0
    opts.sigma double = 0
    opts.TxPower_dBm double = 10
    opts.spec_mask double = [0,28,35,45,50,60]
    opts.iterations (1,1) double = 1
    opts.doPlot (1,1) logical = true
    opts.rngSeed = []
end

% Default positions if not provided
if isempty(positions)
    positions = [158.67,164.39;97.01,52.32;0.09,132.56;94.05,151.95;54.54,160.38;...
                 145.96,82.80;107.66,136.41;38.60,110.72;161.02,53.10;160.67,137.14;...
                 18.63,160.06;18.76,39.43;126.98,58.24;190.27,117.71;40.17,131.08];
end
num_tx = size(positions,1);

% Default channels if not provided
use_random_channels = isempty(channels)

% Seed RNG if requested
if ~isempty(opts.rngSeed)
    rng(opts.rngSeed);
end

% Precompute PL0 (free-space at d0) using center freq 2.44 GHz
lambda = 3e8 / 2.44e9;
PL0 = 20*log10((4*pi*opts.d0)/lambda);

% Prepare outputs
avgInterferenceByIter = zeros(opts.iterations,1);
running_avg_interference_mW = zeros(num_tx, num_tx);

for it = 1:opts.iterations
    % optionally reassign random channels each iter
    if use_random_channels
        channels = randi([1,11], 1, num_tx);
    end
    
    interference_mW = computeInterferenceMatrix(positions, channels, PL0, opts);
    
    % Update running average
    running_avg_interference_mW = running_avg_interference_mW + (interference_mW - running_avg_interference_mW) / it;

    total_per_tx_mW = sum(interference_mW, 2);
    total_per_tx_dBm = 10*log10(total_per_tx_mW + eps);
    avgInterferenceByIter(it) = mean(total_per_tx_dBm);
end

% --- Finalization & Output ---
finalInterferenceMatrix_dBm = 10*log10(running_avg_interference_mW + eps);

num_rows = floor(num_tx/2);
num_cols = ceil(num_tx/2);

% Remove all entries from the matrix that are redundant
tmp_interference_matrix = zeros(num_rows, num_cols);

for i = 1:num_rows
	for j = num_cols:num_tx
        tmp_interference_matrix(i, j - num_cols + 1) = finalInterferenceMatrix_dBm(i, j);
    end
end

results = struct();
results.avgInterferenceByIter = avgInterferenceByIter;
results.finalInterferenceMatrix_dBm = finalInterferenceMatrix_dBm;
results.interferenceMatrixUnsymmetric = tmp_interference_matrix;
results.channels = channels;
results.positions = positions;
results.opts = opts;
results.PL0 = PL0;

% --- Formatted Output for Python ---
fprintf('Average noisefloor (mean dBm): %.3f\n', mean(results.avgInterferenceByIter));
fprintf('START_MATRIX\n');
disp(results.interferenceMatrixUnsymmetric);
fprintf('END_MATRIX\n');


if opts.doPlot
    displayResults(results);
end

end


%% Local helper functions

function interference_mW = computeInterferenceMatrix(positions, channels, PL0, opts)
% Compute pairwise interference (linear mW) matrix for given positions & channels.

num_tx = size(positions,1);
interference_mW = zeros(num_tx,num_tx);

for i = 1:num_tx
    for j = 1:num_tx
        if i == j
            continue;
        end
        d = norm(positions(i,:) - positions(j,:));
        if d < opts.d0, d = opts.d0; end
        path_loss = PL0 + 10*opts.n*log10(d/opts.d0);
        if opts.sigma > 0
            path_loss = path_loss + (randn * opts.sigma);
        end
        delta = abs(channels(i) - channels(j));
        spec_loss = spectralLoss(delta, opts.spec_mask);
        rx_dBm = opts.TxPower_dBm - path_loss - spec_loss;
        interference_mW(i,j) = 10^(rx_dBm/10);
    end
end
end


function L = spectralLoss(delta, spec_mask)
% Return spectral attenuation (dB) given channel delta and spec_mask table.
% spec_mask is vector [Delta0, Delta1, Delta2, ...] with last element = Delta_{>=k}
kmax = numel(spec_mask)-1;
if delta <= kmax
    L = spec_mask(delta+1);
else
    L = spec_mask(end);
end
end


function displayResults(results)
% Simple text and figures for quick inspection.
set(groot, {'DefaultAxesXColor','DefaultAxesYColor','DefaultAxesZColor'}, {'k','k','k'});

opts = results.opts;
channels = results.channels;
num_tx = size(results.positions,1);

% Print table of last-iteration interference (per-AP aggregate)
total_per_tx_mW = sum(10.^(results.finalInterferenceMatrix_dBm/10),2); % convert back to mW
total_per_tx_dBm = 10*log10(total_per_tx_mW + eps);
T = table((1:num_tx)', channels', total_per_tx_dBm, ...
    'VariableNames', {'AP_ID','Channel','Noise_Floor_dBm'});
disp('--- Interference Results (last iteration) ---');
disp(T);


% Plot heatmap of final interference matrix (dBm)
figure('Name','Interference Matrix (dBm)','Color','w');
M = results.interferenceMatrixUnsymmetric;
M(isinf(M)) = NaN;
imagesc(M, [-140 -60]);
colorbar;
xlabel('Source Tx'); ylabel('Victim Rx');
title('Interference Matrix (dBm)', 'Color', 'black');
axis square;
end
