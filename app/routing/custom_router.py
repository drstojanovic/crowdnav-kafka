from dijkstar import Graph, find_path

from app.network.network import Network
from app.routing.router_result import RouterResult


def cost_func(curr, next, edge, prev_edge):
    return edge['length'] / edge['maxSpeed']


class CustomRouter(object):
    graph = None

    @classmethod
    def init(cls):
        """ set up the router using the already loaded network """
        cls.graph = Graph()
        for edge in Network.routing_edges:
            cls.graph.add_edge(edge.from_node.getID(), edge.to_node.getID(),
                               {'length': edge.length, 'maxSpeed': edge.max_speed,
                                'lanes': len(edge.lanes), 'edgeID': edge.id})

    @classmethod
    def minimal_route(cls, from_node, to_node):
        """creates a minimal route based on length / speed  """
        route = find_path(cls.graph, from_node, to_node, cost_func=cost_func)
        return RouterResult(route)
