import json

import sumolib
import traci
import traci.constants as tc
from colorama import Fore

from app import config
from app.entity.car_registry import CarRegistry
from app.logging import info
from app.streaming.consumer import Consumer
# get the current system time
from app.streaming.producer import Producer
from app.tl_control.tl_controller import TLController
from app.util import current_milli_time


class Simulation(object):
    """ here we run the simulation in """

    # the current tick of the simulation
    tick = 0

    # last tick time
    lastTick = current_milli_time()

    @classmethod
    def start(cls):
        """ start the simulation """
        info("# Start adding initial cars to the simulation", Fore.MAGENTA)
        # apply the configuration from the json file
        # cls.applyFileConfig()
        CarRegistry.apply_car_counter()
        cls.generate_map_files()
        cls.loop()

    @classmethod
    def generate_map_files(cls):
        # Create a file with junction -> inc_lanes mapping
        net = sumolib.net.readNet(config.sumo_net, withLatestPrograms=True)
        junction_ids = traci.junction.getIDList()
        junctions = {}
        for junction_id in junction_ids:
            pos_x, pos_y = traci.junction.getPosition(junction_id)
            lon, lat = traci.simulation.convertGeo(pos_x, pos_y)
            junction_type = net.getNode(junction_id).getType()
            inc_edges = [edge.getID() for edge in net.getNode(junction_id).getIncoming()]
            inc_lanes_per_edge = [net.getEdge(edge_id).getLanes() for edge_id in inc_edges]
            inc_lane_ids = [lane.getID() for lanes in inc_lanes_per_edge for lane in lanes]
            junctions[junction_id] = {
                'id': junction_id,
                'type': junction_type,
                'lat': lat,
                'lon': lon,
                'inc_lanes': inc_lane_ids
            }

        lane_ids = traci.lane.getIDList()
        lanes = {}
        for lane_id in lane_ids:
            lanes[lane_id] = {
                'length': round(traci.lane.getLength(lane_id), 1),
                'max_speed': round(traci.lane.getMaxSpeed(lane_id) * 3.6),
                'next_junction': [junc_id for junc_id, junc in junctions.items() if lane_id in junc['inc_lanes']][0]
            }
            outgoing_conns = net.getLane(lane_id).getOutgoing()
            if junctions[lanes[lane_id]['next_junction']]['type'] == 'traffic_light':
                tl_id = outgoing_conns[0].getTLSID()
                tl_program = net.getTLSSecure(tl_id).getPrograms()['0']
                tl_phases = [p[0] for p in tl_program.getPhases()]
                tl_link_indexes = [conn.getTLLinkIndex() for conn in outgoing_conns]
                green_phases = []
                for i, phase in enumerate(tl_phases):
                    if any(phase[link_idx].lower() == 'g' for link_idx in tl_link_indexes):
                        green_phases.append(i)
                lanes[lane_id]['tl_id'] = tl_id
                lanes[lane_id]['green_phases'] = green_phases

        with open('/tmp/junctions.json', 'w') as file:
            file.write(json.dumps(junctions))

        with open('/tmp/lanes.json', 'w') as file:
            file.write(json.dumps(lanes))

    @classmethod
    # @profile
    def loop(cls):
        """ loops the simulation """

        # start listening to all cars that arrived at their target
        traci.simulation.subscribe((tc.VAR_ARRIVED_VEHICLES_IDS,))
        # traci.vehicle.subscribe((tc.VAR_WAITING_TIME,))

        tl_controller = TLController()

        while 1:
            # Do one simulation step
            cls.tick += 1
            traci.simulationStep()

            # Log tick duration to kafka
            current_millis = current_milli_time()
            duration = current_millis - cls.lastTick
            cls.lastTick = current_millis
            msg = dict()
            msg["duration"] = duration
            Producer.publish(msg, config.kafka_topic_performance)

            current_secs = current_millis / 1000.0

            # Check for removed cars and re-add them into the system
            for removedCarId in traci.simulation.getSubscriptionResults()[122]:
                CarRegistry.find_by_id(removedCarId).set_arrived(cls.tick)

            for car_id in traci.vehicle.getIDList():
                pos_x, pos_y = traci.vehicle.getPosition(car_id)

                road_id = traci.vehicle.getRoadID(car_id)
                lane_id = traci.vehicle.getLaneID(car_id)
                speed = traci.vehicle.getSpeed(car_id)
                lon, lat = traci.simulation.convertGeo(pos_x, pos_y)
                wait_time = traci.vehicle.getWaitingTime(car_id)

                message = {
                    'car_id': car_id,
                    'road_id': road_id,
                    'lane_id': lane_id,
                    'speed': speed,
                    'lon': lon,
                    'lat': lat,
                    'wait_time':  wait_time,
                    'timestamp': current_secs
                }
                Producer.publish(message, config.kafka_topic_traffic)

            new_tls_actions = Consumer.read_new_tls_actions()
            tl_controller.update_tls(new_tls_actions)
