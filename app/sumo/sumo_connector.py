import traci
from sumolib import checkBinary

from app.config import Config


# Starts SUMO in the background using the defined network
def start():
    sumo_binary = checkBinary('sumo')
    traci.start([sumo_binary, "-c", Config().sumo_config_file, "--no-step-log", "true", "--no-warnings", "true"])
