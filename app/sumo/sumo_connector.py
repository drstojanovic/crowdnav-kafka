import traci
from sumolib import checkBinary

from app import config


# Starts SUMO in the background using the defined network
def start():
    sumo_binary = checkBinary('sumo')
    traci.start([sumo_binary, "-c", config.sumo_config, "--no-step-log", "true", "--no-warnings", "true"])
