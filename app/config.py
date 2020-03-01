#
# Config file for SUMOS
#

# should use kafka for config changes (else it uses json file)
kafka_updates = True
# the kafka host we want to send our messages to
kafka_host = "kafka:9092"

# the topic we send the kafka messages to
kafka_topic_trips = "crowd-nav-trips"
kafka_topic_performance = "crowd-nav-performance"
kafka_topic_traffic = "traffic"

# where we receive system changes
kafka_tl_actions_topic = "tl-actions"

# True if we want to use the SUMO GUI (always of in parallel mode)
use_gui = False  # False

# The network config (links to the net) we use for our simulation
sumo_config = "./app/map/map.sumo.cfg"

# The network net we use for our simulation
sumo_net = "./app/map/map.net.xml"

# Initial wait time before publishing overheads
initial_wait_ticks = 50

# the total number of cars we use in our simulation
total_car_counter = 1000

# runtime dependent variable
process_id = 0
parallel_mode = False
