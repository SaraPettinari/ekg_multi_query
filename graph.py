import pandas as pd
from neo4j import GraphDatabase
import graphistry
import queries
import config
import datetime


class MRSGraph:
    def __init__(self, process_abstraction, event_abstraction, perspectives):

        self.edges = []
        self.nodes = []

        graphistry.register(
            api=3, username=config.GRAPHISTRY_USER, password=config.GRAPHISTRY_PASSWORD)

        self.driver = GraphDatabase.driver(**config.NEO4J)

        graphistry.register(bolt=config.NEO4J)

        process_abstraction = int(process_abstraction)
        event_abstraction = int(event_abstraction)

        self.perspectives = perspectives

        self.session = self.driver.session()

        type_id = 'Event'

        if event_abstraction == 3:
            self.aggregate_activities(process_abstraction)
            type_id = 'Class'

        if process_abstraction == 1:
            self.get_mrs_level_1(type_id)
        elif process_abstraction == 3:
            self.get_mrs_level_3(type_id)

    def aggregate_activities(self, process_abstraction):
        self.session.run(queries.CLEAR_CLASSES)
        if process_abstraction == 1:
            self.session.run("""
                MATCH (e:Event)
                WITH distinct e.Activity AS actName, e.Actor as actor
                MERGE (c:Class {Activity:actName, Type:"Activity", EventID: 'c_' + actName, Actor: actor})
                WITH c
                MATCH (c : Class) WHERE c.Type = "Activity"
                MATCH (e : Event) WHERE c.Activity = e.Activity AND c.Actor = e.Actor
                MERGE (e) -[:OBSERVED]-> (c)
                """)
        if process_abstraction == 3:
            self.session.run("""
                MATCH (e:Event)
                WITH distinct e.Activity AS actName
                MERGE (c:Class {Activity:actName, Type:"Activity", EventID: 'c_' + actName})
                WITH c
                MATCH (c : Class) WHERE c.Type = "Activity"
                MATCH (e : Event) WHERE c.Activity = e.Activity
                MERGE (e) -[:OBSERVED]-> (c)
                """)

    def get_mrs_level_1(self, node_type):
        res_nodes = self.session.run(queries.GET_NODES, type=node_type)

        self.nodes = extract_nodes(res_nodes.data(), self.perspectives)

        results = self.session.run("""
                MATCH (n:Entity:Robot)<-[:CORR]-(e)
                WITH n, e AS nodes ORDER BY e.timestamp, ID(e)
                WITH n, collect(nodes) AS event_node_list
                UNWIND range(0, size(event_node_list)-2) AS i
                WITH n, event_node_list[i] AS e1, event_node_list[i+1] AS e2
                MERGE (e1)-[df:DF {EntityType:n.EntityType, ID:n.ID}]->(e2)
                RETURN e1.EventID as source, e2.EventID as destination, type(df) as edge_label
            """)
        if node_type == 'Class':
            results = self.session.run(queries.CLASS_QUERY)

        self.edges = pd.DataFrame(results.data())

    def get_mrs_level_3(self, node_type):
        res_nodes = self.session.run(queries.GET_NODES, type=node_type)
        self.nodes = pd.DataFrame(res_nodes.data())

        results = self.session.run("""
            MATCH (e:Event)
            WITH e AS nodes ORDER BY e.timestamp, ID(e)
            WITH collect(nodes) AS event_node_list
            UNWIND range(0, size(event_node_list)-2) AS i
            WITH event_node_list[i] AS e1, event_node_list[i+1] AS e2
            MERGE (e1)-[df:DF_AGG]->(e2)
            RETURN e1.EventID as source, e2.EventID as destination, type(df) as edge_label
        """)

        if node_type == 'Class':
            results = self.session.run(queries.CLASS_QUERY)

        self.edges = pd.DataFrame(results.data())

    def generate_graph(self):
        # print(self.nodes[:5])
        # print(self.edges[:5])

        g = graphistry.nodes(self.nodes).edges(self.edges).bind(source="source", destination="destination", node="EventID",
                                                                point_label="Activity", edge_label="edge_label")

        g = g.encode_point_color('Activity', palette=[
                                 "blue", "yellow", "red"], as_continuous=True).scene_settings(show_arrows=True, edge_curvature=0)

        g = g.layout_igraph('sugiyama', directed=True).rotate(90)

        url = g.plot(render=False)
        # gL.plot()
        return url
        # g.plot()


def extract_nodes(nodes, perspectives):
    out_nodes = []
    for element in nodes:
        out_nodes.append(element['e'])

    curr_nodes = pd.DataFrame(out_nodes)

    if 'timestamp' in curr_nodes.columns:
        curr_nodes['timestamp'] = curr_nodes['timestamp'].apply(
            neo_datetime_conversion)

    # returns a dataset with only the perspectives of interest
    set_curr_nodes = curr_nodes[perspectives]
    return set_curr_nodes


def neo_datetime_conversion(timestamp):
    millis = int(timestamp.nanosecond/1000)
    t = datetime.datetime(timestamp.year, timestamp.month, timestamp.day,
                          timestamp.hour, timestamp.minute, timestamp.second, millis)
    return t


if __name__ == '__main__':
    process_abstraction = input('Select process abstraction level:')
    event_abstraction = input('Select event abstraction level:')

    mrsg = MRSGraph(process_abstraction, event_abstraction).generate_graph()
    print(mrsg)
