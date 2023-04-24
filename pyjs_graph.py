from neo4j import GraphDatabase
from scripts.queries import ElementType
import pandas as pd
import scripts.queries as queries
import scripts.config as config
import datetime


class MRSGraph:
    def __init__(self):
        self.edges = []
        self.nodes = []

        # init neo4j connection
        self.driver = GraphDatabase.driver(**config.NEO4J)
        self.session = self.driver.session()

    def set_properties(self):
        type_id = ElementType.EVENT
        if self.event_abstraction == 3:
            self.aggregate_activities(self.process_abstraction)
            type_id = ElementType.CLASS

        if self.process_abstraction == 1:
            self.get_mrs_level_1(type_id)
        elif self.process_abstraction == 3:
            self.get_mrs_level_3(type_id)

    def aggregate_activities(self, process_abstraction):
        self.session.run(queries.CLEAR_CLASSES)
        aggregation_perspectives = []
        if process_abstraction == 1:
            aggregation_perspectives = ['Activity', 'Actor']
        if process_abstraction == 3:
            aggregation_perspectives = ['Activity']

        res_query = queries.query_aggregation_generator(
            aggregation_perspectives, 'Activity')
        self.session.run(res_query)

    def get_mrs_level_1(self, node_type):
        res_nodes = self.session.run(queries.GET_NODES, type=node_type)

        self.nodes = extract_nodes(res_nodes.data(), self.perspectives)

        if node_type == 'Class':
            results = self.session.run(queries.CLASS_QUERY)
        else:
            results = self.session.run(queries.NODE_DF)

        self.edges = pd.DataFrame(results.data())

    def get_mrs_level_3(self, node_type):
        res_nodes = self.session.run(queries.GET_NODES, type=node_type)
        self.nodes = extract_nodes(res_nodes.data(), self.perspectives)

        if node_type == 'Class':
            results = self.session.run(queries.CLASS_MRS_QUERY)
        else:
            results = self.session.run(queries.NODE_DF_MRS)

        self.edges = pd.DataFrame(results.data())

    def handle_communication(self):
        self.session.run("""
                        MATCH (e:Event) UNWIND e.Message AS msg
                        WITH DISTINCT msg, e.Payload as payload
                        MERGE (n:Entity:Message {ID:msg, EntityType:"Message", Payload:payload})
                          """)
        self.session.run("""
                        MATCH (e:Event) UNWIND e.Message AS msg WITH e,msg
                        MATCH (n:Entity:Message) WHERE msg = n.ID
                        MERGE (e)-[c:CORR]->(n)
                          """)
        self.session.run("""
                        MATCH (e1:Event)-[:CORR]->(n:Message)<-[:CORR]-(e2:Event)
                        WHERE e1.Msg_Role = 'send' AND e2.Msg_Role = 'receive' AND e1.timestamp <= e2.timestamp
                        MERGE (e1)-[comm:COMM {EntityType:n.EntityType, ID:n.ID}]->(e2)
                          """)

        res = self.session.run("""
                        MATCH (e1:Event)-[c:COMM]->(e2:Event)
                        RETURN e1.EventID as source, e2.EventID as destination, type(c) as edge_label
                          """)
        comm_edges = pd.DataFrame(res.data())
        self.edges = pd.concat([self.edges, comm_edges])

    def generate_graph(self, process_abstraction, event_abstraction, perspectives, communication):
        self.process_abstraction = int(process_abstraction)
        self.event_abstraction = int(event_abstraction)

        self.perspectives = perspectives
        self.set_properties()

        if communication:
            self.handle_communication()

        self.edges = self.edges.rename(
            columns={'destination': 'to', 'source': 'from', 'edge_label': 'label'})

        return {'nodes': self.nodes, 'edges': self.edges}



def extract_nodes(nodes, perspectives):
    out_nodes = []
    for element in nodes:
        out_nodes.append(element['e'])

    curr_nodes = pd.DataFrame(out_nodes)

    if 'timestamp' in curr_nodes.columns:
        curr_nodes['timestamp'] = curr_nodes['timestamp'].apply(
            neo_datetime_conversion)

    # returns a dataset with only the perspectives of interest
    if all(item in perspectives for item in curr_nodes.columns):
        set_curr_nodes = curr_nodes[perspectives]
        return set_curr_nodes
    else:
        return curr_nodes


def neo_datetime_conversion(timestamp):
    '''
    From Neo4j datetime to datetime
    '''
    millis = int(timestamp.nanosecond/1000)
    t = datetime.datetime(timestamp.year, timestamp.month, timestamp.day,
                          timestamp.hour, timestamp.minute, timestamp.second, millis)
    return t


if __name__ == '__main__':
    process_abstraction = input('Select process abstraction level:')
    event_abstraction = input('Select event abstraction level:')
    perspectives = ['EventID', 'Activity', 'Actor', 'timestamp']

    mrsg = MRSGraph().generate_graph(
        process_abstraction, event_abstraction, perspectives, communication=False)
    print(mrsg)
