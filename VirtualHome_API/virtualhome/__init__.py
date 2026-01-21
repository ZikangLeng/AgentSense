import glob
import os
import sys
from sys import platform

# Add the simulator package using the local path instead of a fixed sys.path index
module_dir = os.path.dirname(os.path.abspath(__file__))
simulation_path = os.path.join(module_dir, "simulation")
if simulation_path not in sys.path:
    sys.path.append(simulation_path)

from unity_simulator.comm_unity import UnityCommunication
from unity_simulator import utils_viz