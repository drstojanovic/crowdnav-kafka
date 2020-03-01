import os
import sys

sys.path.append(os.path.join(os.environ.get("SUMO_HOME"), "tools"))

from app.logging import info
from app.network.network import Network
from app.simulation.simulation import Simulation
from app.routing.custom_router import CustomRouter
from .streaming.consumer import Consumer
from .streaming.producer import Producer
from colorama import Fore
from .sumo import sumo_connector, sumo_dependency
from . import config
import traci


# uuid4()
def start(process_id, parallel_mode, use_gui):
    """ main entry point into the application """
    config.process_id = process_id
    config.parallel_mode = parallel_mode
    config.use_gui = use_gui

    info('#####################################', Fore.CYAN)
    info('#      Starting CrowdNav v0.2       #', Fore.CYAN)
    info('#####################################', Fore.CYAN)
    info('# Configuration:', Fore.YELLOW)
    info('# Kafka-Host   -> ' + config.kafka_host, Fore.YELLOW)
    info('# Kafka-Topic1 -> ' + config.kafka_topic_trips, Fore.YELLOW)
    info('# Kafka-Topic2 -> ' + config.kafka_topic_performance, Fore.YELLOW)

    # init sending updates to kafka and getting commands from there
    Consumer.init()
    Producer.init()

    # Check if sumo is installed and available
    sumo_dependency.check_deps()
    info('# SUMO-Dependency check OK!', Fore.GREEN)

    # Load the sumo map we are using into Python
    Network.load()
    info(Fore.GREEN + "# Map loading OK! " + Fore.RESET)
    info(Fore.CYAN + "# Nodes: " + str(Network.nodes_count()) + " / Edges: " + str(Network.edges_count()) + Fore.RESET)

    # After the network is loaded, we init the router
    CustomRouter.init()
    # Start sumo in the background
    sumo_connector.start()
    info("\n# SUMO-Application started OK!", Fore.GREEN)
    # Start the simulation
    Simulation.start()
    # Simulation ended, so we shutdown
    info(Fore.RED + '# Shutdown' + Fore.RESET)
    traci.close()
    sys.stdout.flush()
    return None
