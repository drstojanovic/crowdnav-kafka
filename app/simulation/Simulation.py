import json
import traci
import traci.constants as tc
from app.network.Network import Network

import sumolib

from app.streaming import RTXForword
from colorama import Fore

from app import Config
from app.logging import CSVLogger
from app.entitiy.CarRegistry import CarRegistry
from app.logging import info
from app.routing.CustomRouter import CustomRouter
from app.streaming import RTXConnector
import time
import json

# get the current system time
from app.routing.RoutingEdge import RoutingEdge

current_milli_time = lambda: int(round(time.time() * 1000))


class Simulation(object):
    """ here we run the simulation in """

    # the current tick of the simulation
    tick = 0

    # last tick time
    lastTick = current_milli_time()

    @classmethod
    def applyFileConfig(cls):
        """ reads configs from a json and applies it at realtime to the simulation """
        try:
            config = json.load(open('./knobs.json'))
            CustomRouter.explorationPercentage = config['explorationPercentage']
            CustomRouter.averageEdgeDurationFactor = config['averageEdgeDurationFactor']
            CustomRouter.maxSpeedAndLengthFactor = config['maxSpeedAndLengthFactor']
            CustomRouter.freshnessUpdateFactor = config['freshnessUpdateFactor']
            CustomRouter.freshnessCutOffValue = config['freshnessCutOffValue']
            CustomRouter.reRouteEveryTicks = config['reRouteEveryTicks']
        except:
            pass

    @classmethod
    def start(cls):
        """ start the simulation """
        info("# Start adding initial cars to the simulation", Fore.MAGENTA)
        # apply the configuration from the json file
        cls.applyFileConfig()
        CarRegistry.applyCarCounter()
        cls.loop()

    @classmethod
    # @profile
    def loop(cls):
        """ loops the simulation """

        # start listening to all cars that arrived at their target
        traci.simulation.subscribe((tc.VAR_ARRIVED_VEHICLES_IDS,))
        # traci.vehicle.subscribe((tc.VAR_WAITING_TIME,))

        # Create a file with junction -> inc_lanes mapping
        net = sumolib.net.readNet(Config.sumoNet)
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
            outgoing_conns = net.getLane(lane_id).getOutgoing()
            lanes[lane_id] = {
                'length': round(traci.lane.getLength(lane_id), 1),
                'max_speed': round(traci.lane.getMaxSpeed(lane_id) * 3.6),
                'next_junction': [junc_id for junc_id, junc in junctions.items() if lane_id in junc['inc_lanes']][0]
            }
            if junctions[lanes[lane_id]['next_junction']]['type'] == 'traffic_light':
                lanes[lane_id]['tl_id'] = outgoing_conns[0].getTLSID()
                lanes[lane_id]['tl_link_indexes'] = [conn.getTLLinkIndex() for conn in outgoing_conns]

        with open('/tmp/junctions.json', 'w') as file:
            file.write(json.dumps(junctions))

        with open('/tmp/lanes.json', 'w') as file:
            file.write(json.dumps(lanes))

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
            RTXForword.publish(msg, Config.kafkaTopicPerformance)

            current_secs = current_millis / 1000.0

            # Check for removed cars and re-add them into the system
            for removedCarId in traci.simulation.getSubscriptionResults()[122]:
                CarRegistry.findById(removedCarId).setArrived(cls.tick)

            for allCarId in traci.vehicle.getIDList():
                # w_time = traci.vehicle.getWaitingTime(allCarId)
                # x_cord, y_cord = traci.vehicle.getPosition(allCarId)
                # g_lng, g_lat = traci.simulation.convertGeo(x_cord, y_cord)
                pos_x, pos_y = traci.vehicle.getPosition(allCarId)

                road_id = traci.vehicle.getRoadID(allCarId)
                lane_id = traci.vehicle.getLaneID(allCarId)
                speed = traci.vehicle.getSpeed(allCarId)
                lon, lat = traci.simulation.convertGeo(pos_x, pos_y)
                wait_time = traci.vehicle.getWaitingTime(allCarId)

                # log to kafka
                # msgWaitTime = str(allCarId) + "," + str(w_time) + "," + str(g_lat) + "," + str(g_lng)
                # RTXForword.publish(msgWaitTime, Config.kafkaTopicNis)
                message = {
                    'car_id': allCarId,
                    'road_id': road_id,
                    'lane_id': lane_id,
                    'speed': speed,
                    'lon': lon,
                    'lat': lat,
                    'wait_time':  wait_time,
                    'timestamp': current_secs
                }
                RTXForword.publish(message, Config.kafkaTopicNis)

                # log to file Dragan
                # CSVLogger.logEvent("wait", [allCarId, cls.tick, g_lat, g_lng])

                # if w_time >= 59.0:
                #     traci.vehicle.setColor(allCarId, (0, 0, 255, 0))
                #     print(msgWaitTime)

            # timeBeforeCarProcess = current_milli_time()
            # let the cars process this step
            CarRegistry.processTick(cls.tick)
            # log time it takes for routing
            # msg = dict()
            # msg["duration"] = current_milli_time() - timeBeforeCarProcess
            # RTXForword.publish(msg, Config.kafkaTopicRouting)

            # if we enable this we get debug information in the sumo-gui using global traveltime
            # should not be used for normal running, just for debugging
            # if (cls.tick % 10) == 0:
            # for e in Network.routingEdges:
            # 1)     traci.edge.adaptTraveltime(e.id, 100*e.averageDuration/e.predictedDuration)
            #     traci.edge.adaptTraveltime(e.id, e.averageDuration)
            # 3)     traci.edge.adaptTraveltime(e.id, (cls.tick-e.lastDurationUpdateTick)) # how old the data is

            # real time update of config if we are not in kafka mode
            if (cls.tick % 10) == 0:
                if Config.kafkaUpdates is False and Config.mqttUpdates is False:
                    # json mode
                    cls.applyFileConfig()
                else:
                    # kafka mode
                    newConf = RTXConnector.checkForNewConfiguration()
                    if newConf is not None:
                        if "exploration_percentage" in newConf:
                            CustomRouter.explorationPercentage = newConf["exploration_percentage"]
                            print("setting victimsPercentage: " + str(newConf["exploration_percentage"]))
                        if "route_random_sigma" in newConf:
                            CustomRouter.routeRandomSigma = newConf["route_random_sigma"]
                            print("setting routeRandomSigma: " + str(newConf["route_random_sigma"]))
                        if "max_speed_and_length_factor" in newConf:
                            CustomRouter.maxSpeedAndLengthFactor = newConf["max_speed_and_length_factor"]
                            print("setting maxSpeedAndLengthFactor: " + str(newConf["max_speed_and_length_factor"]))
                        if "average_edge_duration_factor" in newConf:
                            CustomRouter.averageEdgeDurationFactor = newConf["average_edge_duration_factor"]
                            print("setting averageEdgeDurationFactor: " + str(newConf["average_edge_duration_factor"]))
                        if "freshness_update_factor" in newConf:
                            CustomRouter.freshnessUpdateFactor = newConf["freshness_update_factor"]
                            print("setting freshnessUpdateFactor: " + str(newConf["freshness_update_factor"]))
                        if "freshness_cut_off_value" in newConf:
                            CustomRouter.freshnessCutOffValue = newConf["freshness_cut_off_value"]
                            print("setting freshnessCutOffValue: " + str(newConf["freshness_cut_off_value"]))
                        if "re_route_every_ticks" in newConf:
                            CustomRouter.reRouteEveryTicks = newConf["re_route_every_ticks"]
                            print("setting reRouteEveryTicks: " + str(newConf["re_route_every_ticks"]))
                        if "total_car_counter" in newConf:
                            CarRegistry.totalCarCounter = newConf["total_car_counter"]
                            CarRegistry.applyCarCounter()
                            print("setting totalCarCounter: " + str(newConf["total_car_counter"]))
                        if "edge_average_influence" in newConf:
                            RoutingEdge.edgeAverageInfluence = newConf["edge_average_influence"]
                            print("setting edgeAverageInfluence: " + str(newConf["edge_average_influence"]))

            # print status update if we are not running in parallel mode
            if (cls.tick % 100) == 0 and Config.parallelMode is False:
                print(str(Config.processID) + " -> Step:" + str(cls.tick) + " # Driving cars: " + str(
                    traci.vehicle.getIDCount()) + "/" + str(
                    CarRegistry.totalCarCounter) + " # avgTripDuration: " + str(
                    CarRegistry.totalTripAverage) + "(" + str(
                    CarRegistry.totalTrips) + ")" + " # avgTripOverhead: " + str(
                    CarRegistry.totalTripOverheadAverage))

                # @depricated -> will be removed
                # # if we are in paralllel mode we end the simulation after 10000 ticks with a result output
                # if (cls.tick % 10000) == 0 and Config.parallelMode:
                #     # end the simulation here
                #     print(str(Config.processID) + " -> Step:" + str(cls.tick) + " # Driving cars: " + str(
                #         traci.vehicle.getIDCount()) + "/" + str(
                #         CarRegistry.totalCarCounter) + " # avgTripDuration: " + str(
                #         CarRegistry.totalTripAverage) + "(" + str(
                #         CarRegistry.totalTrips) + ")" + " # avgTripOverhead: " + str(
                #         CarRegistry.totalTripOverheadAverage))
                #     return
