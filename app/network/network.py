import sumolib

from app.config import Config
from app.routing.routing_edge import RoutingEdge


class Network(object):
    """ simply ready the network in its raw form and creates a router on this network """

    # empty references to start with
    edges = None
    nodes = None
    node_ids = None
    edge_ids = None
    routing_edges = None

    @classmethod
    def load(cls):
        """ loads the network and applies the results to the Network static class """
        # parse the net using sumolib
        parsed_network = sumolib.net.readNet(Config().sumo_map_file)
        # apply parsing to the network
        Network._apply_network(parsed_network)

    @classmethod
    def _apply_network(cls, net):
        """ internal method for applying the values of a SUMO map """
        cls.nodes = net.getNodes()
        cls.edges = net.getEdges()
        cls.node_ids = [x.getID() for x in cls.nodes]
        cls.edge_ids = [x.getID() for x in cls.edges]
        cls.routing_edges = [RoutingEdge(x) for x in cls.edges]

    @classmethod
    def nodes_count(cls):
        """ count the nodes """
        return len(cls.nodes)

    @classmethod
    def edges_count(cls):
        """ count the edges """
        return len(cls.edges)

    @classmethod
    def get_edge_from_node(cls, edge):
        return edge.getFromNode()

    @classmethod
    def get_edge_by_id(cls, edgeID):
        return [x for x in cls.edges if x.getID() == edgeID][0]

    @classmethod
    def get_edge_ids_to_node(cls, edgeID):
        return cls.get_edge_by_id(edgeID).getToNode()

    @classmethod
    def get_edge_position(cls, edge):
        return edge.getFromNode().getCoord()
