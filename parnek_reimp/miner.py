from dcr_graph import DcrGraph
from templates import AtMostOne, Response, Precedence, ChainPrecedence


class Miner:
    def __init__(self, templates=None):
        if templates is None:
            templates = [AtMostOne(), Response(), Precedence(), ChainPrecedence()]
        self.templates = templates

    def mine(self, log):
        graph = DcrGraph(log.activities)
        for template in self.templates:
            template.check_constraint(log, graph)
        return graph
