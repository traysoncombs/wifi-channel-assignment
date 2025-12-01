import subprocess
import re
from typing import List, Optional, Tuple
import csv
import numpy as np

from src.main import create_transmitters
from src.path_loss import FreeSpacePathLossModel
from src.sir_constraint import create_and_solve_constraint_problem
from src.transmitter import Channels, Transmitter


def get_good_solution(transmitters: List[Transmitter]) -> Optional[List[Transmitter]]:
    min_pairwise_sir = 0.01
    min_avg_sir = 0.1
    pairwise_sir_step = 0.01
    avg_sir_step = 0.01
    solution = None

    # Increment min_avg_sir_step until we can't no more
    while solution is None and min_avg_sir < 1:
        solution = create_and_solve_constraint_problem(transmitters, transmitters[0].channels, min_pairwise_sir, True, min_avg_sir, max_steps=10)
        if solution is not None:
            solution = None
            min_avg_sir += avg_sir_step
        else:
            min_avg_sir -= avg_sir_step
            break

    last_solution_was_none = False
    while solution is None and pairwise_sir_step < 1:
        solution = create_and_solve_constraint_problem(transmitters, transmitters[0].channels, min_pairwise_sir, True, min_avg_sir, max_steps=10)
        if solution is not None and not last_solution_was_none:
            solution = None
            min_pairwise_sir += pairwise_sir_step
        elif solution is not None and last_solution_was_none:
            break
        else:
            last_solution_was_none = True
            min_pairwise_sir -= pairwise_sir_step
    return solution

def run_matlab_and_parse_output(matlab_cmd: str) -> Tuple[Optional[float], Optional[np.ndarray]]:
    """Executes a MATLAB command and parses for noise floor and interference matrix."""
    try:
        result = subprocess.run(
            ['matlab', '-batch', matlab_cmd],
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8'
        )
        output = result.stdout
        
        # Parse noise floor
        noise_floor = None
        noise_match = re.search(r"Average noisefloor \(mean dBm\): ([-+]?\d*\.\d+|\d+)", output)
        if noise_match:
            noise_floor = float(noise_match.group(1))
            
        # Parse matrix
        matrix = None
        matrix_match = re.search(r"START_MATRIX\s*\n(.*?)\n\s*END_MATRIX", output, re.DOTALL)
        if matrix_match:
            matrix_str = matrix_match.group(1).strip()
            
            # Handle MATLAB's scientific notation scaling factor (e.g., "1.0e-10 *")
            factor = 1.0
            factor_match = re.match(r"^\s*1.0e([+-]?\d+)\s*\*\s*\n", matrix_str)
            if factor_match:
                factor = 10.0 ** float(factor_match.group(1))
                matrix_str = re.sub(r"^.*?\*\s*\n", "", matrix_str, count=1)

            lines = matrix_str.strip().split('\n')
            parsed_matrix = []
            for line in lines:
                row = [float(x) for x in line.strip().split() if x]
                if row:
                    parsed_matrix.append(row)
            
            if parsed_matrix:
                matrix = np.array(parsed_matrix) * factor

        return noise_floor, matrix

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error calling MATLAB: {e}")
        if isinstance(e, subprocess.CalledProcessError):
            print(f"MATLAB stderr:\n{e.stderr}")
    return None, None


def format_matrix_for_matlab(matrix: np.ndarray) -> str:
    """Formats a NumPy array into a MATLAB-compatible matrix string."""
    if matrix is None:
        return "[]"
    rows = []
    for row in matrix:
        rows.append(' '.join(f'{x:.6g}' for x in row))
    return f"[{'; '.join(rows)}]"

if __name__ == "__main__":
    # --- Configuration ---
    iterations = 100
    output_filename = 'results.csv'
    path_loss_exponent = 2.5
    reference_power = -40
    room_size = (200, 200)
    min_tx_distance = 20
    number_of_transmitters = 15
    transmission_power = 10
    initial_seed = 6

    # --- Setup ---
    path_loss = FreeSpacePathLossModel(path_loss_exponent)
    channels_config = Channels(2402, 11, 20, 5)
    matlab_script_path = 'C:/Users/trays/Desktop/wifi-channel-assignment/test/'
    
    running_avg_algo_matrix = None
    running_avg_baseline_matrix = None
    total_algo_runs = 0
    total_baseline_runs = 0

    # --- Main Loop ---
    with open(output_filename, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        header = ['seed', 'positions', 'algo_channels', 'algo_noise_floor_dbm', 'baseline_noise_floor_dbm']
        csv_writer.writerow(header)
        print(f"Running {iterations} iterations, logging to {output_filename}...")

        for i in range(iterations):
            current_seed = initial_seed + i * 13
            print(f"\n--- Iteration {i+1}/{iterations} (Seed: {current_seed}) ---")

            transmitters = create_transmitters(room_size[0], room_size[1], current_seed, number_of_transmitters, path_loss,
                                               transmission_power, channels_config, reference_power, min_tx_distance)
            
            solution = get_good_solution(transmitters)

            if not solution:
                print("No solution found for this iteration, skipping.")
                continue

            # --- Prepare data for MATLAB ---
            pos_list = [f"{tx.position.x},{tx.position.y}" for tx in solution]
            pos_str_matlab = f"[{';'.join(pos_list)}]"
            pos_str_csv = f"\"[{';'.join(pos_list)}]\"" # For CSV logging

            chan_list_algo = [f"{tx.channel}" for tx in solution]
            chan_str_algo_matlab = f"[{','.join(chan_list_algo)}]"
            chan_str_algo_csv = f"\"[{','.join(chan_list_algo)}]\"" # For CSV

            # --- 1. Run with Python Algorithm Channels ---
            print("Running MATLAB with algorithm channels...")
            matlab_cmd_algo = (
                f"cd '{matlab_script_path}'; "
                f"results = wifiLogDistanceModel({pos_str_matlab}, {chan_str_algo_matlab}, 'doPlot', false); "
                f"exit;"
            )
            algo_noise_floor, algo_matrix = run_matlab_and_parse_output(matlab_cmd_algo)
            print(f"  -> Algo Noise Floor: {algo_noise_floor} dBm")

            if algo_matrix is not None:
                if running_avg_algo_matrix is None:
                    running_avg_algo_matrix = algo_matrix
                else:
                    running_avg_algo_matrix += (algo_matrix - running_avg_algo_matrix) / (total_algo_runs + 1)
                total_algo_runs += 1

            print("Running MATLAB with random baseline channels...")
            matlab_cmd_baseline = (
                f"cd '{matlab_script_path}'; "
                f"results = wifiLogDistanceModel({pos_str_matlab}, [], 'doPlot', false, 'iterations', 1000); "
                f"exit;"
            )
            baseline_noise_floor, baseline_matrix = run_matlab_and_parse_output(matlab_cmd_baseline)
            print(f"  -> Baseline Noise Floor: {baseline_noise_floor} dBm")
            
            if baseline_matrix is not None:
                if running_avg_baseline_matrix is None:
                    running_avg_baseline_matrix = baseline_matrix
                else:
                    running_avg_baseline_matrix += (baseline_matrix - running_avg_baseline_matrix) / (total_baseline_runs + 1)
                total_baseline_runs += 1

            # --- 3. Log Results ---
            csv_writer.writerow([current_seed, pos_str_csv, chan_str_algo_csv, algo_noise_floor, baseline_noise_floor])

    print(f"\nProcessing complete. Results saved to {output_filename}.")
    
    np.set_printoptions(precision=4, suppress=True)
    if running_avg_algo_matrix is not None:
        print("\n--- Average Algorithm Interference Matrix (dB) ---")
        print(format_matrix_for_matlab(running_avg_algo_matrix))
        
    if running_avg_baseline_matrix is not None:
        print("\n--- Average Baseline Interference Matrix (dB) ---")
        print(format_matrix_for_matlab(running_avg_baseline_matrix))
