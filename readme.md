# Overview
The goal of this project was to develop an algorithm that assigns channels to routers given their position within a room, the path loss within the room, and the transmission power of each.

# Quick Start
This was built using python 3.13 however it should work just fine with most versions of Python.

1. Install all the necessary packages using `pip install -r requirements.txt`
2. Run the script with `python src/main.py`
3. If a solution is found you will be presented with a graph where each point represents a transmitter
with the channel labeled above it. A line between points indicates that two transmitters are interfering.
Each line is labeled with the signal-interference-ratio between the two transmitters. A value of 1 indicates no interference
and a value of 0 indicates maximal interfernce.

There are a number of parameters that can be altered within `src/main.py` starting on line 67. 
They each have a small description as to their purpose within the code.

# Project Organization
All the source code can be found within `src/` and tests are located within the `test/` directory.
The code is organized as follows:

- src/
  - **main.py**-- This file contains the functionality for running and visualizing everything.
  - **path_loss.py**-- This file contains the logic for path loss modelling which is primarily for computing received power.
  - **sir_constraint.py**-- This file contains the logic for formulating the problem as a set of constraints and solving them using the python-constraint library.
  - **transmitter.py**-- This file contains the logic for computing the received power and SIR between transmitters.

