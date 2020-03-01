from app.util import add_to_average


class RoutingEdge:
    """ a wrapper we use to add information to an edge that we use for routing """

    # how important old data can be at maximum (x times old + 1 times new value)
    edge_average_influence = 140

    def __init__(self, edge):
        """ init the edge based on a SUMO edge """
        self.id = edge.getID()
        self.lanes = edge.getLanes()
        self.max_speed = edge.getSpeed()
        self.length = edge.getLength()
        self.from_node = edge.getFromNode()
        self.to_node = edge.getToNode()
        self.predicted_duration = self.length / self.max_speed
        self.average_duration = self.predicted_duration
        self.last_duration_update_tick = 0

    def apply_edge_duration_to_average(self, duration, tick):
        """ adds a duration to drive on this edge to the calculation """
        # VARIANT 1
        # new values should be more important
        old_data_influence = max(1, self.edge_average_influence - (tick - self.last_duration_update_tick))
        self.average_duration = add_to_average(old_data_influence, self.average_duration, duration)
        self.last_duration_update_tick = tick

        # VARIANT 2
        # self.averageDurationCounter += 1
        # self.averageDuration = addToAverage(self.averageDurationCounter, self.averageDuration, duration)
        # self.lastDurationUpdateTick = tick

    def __str__(self):
        return "Edge(" + self.from_node.getID() \
               + "," + self.to_node.getID() \
               + "," + str(len(self.lanes)) \
               + "," + str(self.max_speed) \
               + "," + str(self.length) + ")"
