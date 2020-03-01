class RouterResult:
    def __init__(self, path_info):
        # the list of nodes to drive to
        self.nodes = path_info[0]
        # meta information for the route
        self.meta = path_info[1]
        # the route as list of edgeIDs
        self.edges = map(lambda x: x['edgeID'], self.meta)
        # the cost for this route per edge
        self.cost_per_edge = path_info[2]
        # the total cost for this route
        self.total_cost = path_info[3]

    def __str__(self):
        return "Routing(" + str(self.edges) + "," + str(self.total_cost) + ")"
