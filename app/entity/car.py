import random

import traci
import traci.constants as tc

from app.config import Config
from app.util import add_to_average
from app.network.network import Network
from app.routing.custom_router import CustomRouter
from app.streaming.producer import Producer


class Car:

    def __init__(self, id):
        self.id = id
        self.rounds = 0
        self.current_router_result = None
        self.current_route_begin_tick = None
        self.current_route_id = None
        self.current_edge_id = None
        self.current_edge_begin_tick = None
        self.target_node_id = None
        self.source_node_id = None
        self.disabled = False
        self.acceleration = max(1, random.gauss(4, 2))
        self.deceleration = max(1, random.gauss(6, 2))
        self.imperfection = min(0.9, max(0.1, random.gauss(0.5, 0.5)))
        self.last_reroute_counter = 0

    def set_arrived(self, tick):
        """ car arrived at its target, so we add some statistic data """

        # import here because python can not handle circular-dependencies
        from app.entity.car_registry import CarRegistry
        # add a round to the car
        self.rounds += 1
        self.last_reroute_counter = 0
        if tick > 50:  # as we ignore the first N ticks for this
            # add a route to the global registry
            CarRegistry.total_trips += 1
            # add the duration for this route to the global tripAverage
            trip_duration = (tick - self.current_route_begin_tick)
            CarRegistry.total_trip_average = add_to_average(CarRegistry.total_trips,
                                                            CarRegistry.total_trip_average,
                                                            trip_duration)

            minimal_costs = CustomRouter.minimal_route(self.source_node_id, self.target_node_id).total_cost
            trip_overhead = trip_duration / minimal_costs / 1.1  # 1.6 is to correct acceleration and deceleration
            # when the distance is very short, we have no overhead
            if trip_duration < 10:
                trip_overhead = 1
            # in rare cases a trip does take very long - as most outliers are <30, we cap the overhead to 30 here
            if trip_overhead > 30:
                print("-> capped overhead to 30 - " + str(minimal_costs) + " - " + str(trip_duration) + " - " + str(
                    trip_overhead))
                trip_overhead = 30

            CarRegistry.total_trip_overhead_average = add_to_average(CarRegistry.total_trips,
                                                                     CarRegistry.total_trip_overhead_average,
                                                                     trip_overhead)
            msg = dict()
            msg["tick"] = tick
            msg["overhead"] = trip_overhead
            Producer.publish(msg, Config().kafka_topic_trips)
        # if car is still enabled, restart it in the simulation
        if self.disabled is False:
            self.add_to_simulation(tick)

    def _create_new_route(self, tick):
        """ creates a new route to a random target and uploads this route to SUMO """
        if self.target_node_id is None:
            self.source_node_id = random.choice(Network.nodes).getID()
        else:
            self.source_node_id = self.target_node_id  # We start where we stopped
        # random target
        self.target_node_id = random.choice(Network.nodes).getID()
        self.current_route_id = self.id + "-" + str(self.rounds)
        self.current_router_result = CustomRouter.minimal_route(self.source_node_id, self.target_node_id)
        
        if len(self.current_router_result.edges) > 0:
            traci.route.add(self.current_route_id, self.current_router_result.edges)
            return self.current_route_id
        else:
            # try again
            return self._create_new_route(tick)

    def process_tick(self, tick):
        """ process changes that happened in the tick to this car """
        pass

    def add_to_simulation(self, tick):
        """ adds this car to the simulation through the traci API """
        self.current_route_begin_tick = tick
        try:
            traci.vehicle.add(self.id, self._create_new_route(tick), tick, -4, -3)
            traci.vehicle.subscribe(self.id, (tc.VAR_ROAD_ID,))
            # ! currently disabled for performance reasons
            # traci.vehicle.setAccel(self.id, self.acceleration)
            # traci.vehicle.setDecel(self.id, self.deceleration)
            # traci.vehicle.setImperfection(self.id, self.imperfection)

            # dump car is using SUMO default routing, so we reroute using the same target
            # putting the next line left == ALL SUMO ROUTING
            traci.vehicle.changeTarget(self.id, self.current_router_result.edges[-1])
        except Exception as e:
            print("error adding --> " + str(e))
            # try recursion, as this should normally work
            # self.addToSimulation(tick)

    def remove(self):
        """" removes this car from the sumo simulation through traci """
        traci.vehicle.remove(self.id)
