from neo4j import GraphDatabase
from scripts.queries import ElementType
from scripts.style_ekg import StyleEKG
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
        self.session.run(queries.CHANGE_ENTITY_VISIBILITY)
        self.session.run(queries.CLEAR_CLASSES)
        relationship_type = ''
        type_id = ElementType.EVENT
        if self.event_abstraction == 3:
            self.aggregate_activities(self.process_abstraction)
            type_id = ElementType.CLASS

        self.session.run(queries.GET_NODES, type=type_id)

        if self.process_abstraction == 1:
            relationship_type = self.get_mrs_level_1(type_id)
        elif self.process_abstraction == 3:
            relationship_type = self.get_mrs_level_3(type_id)
            
        return relationship_type

    def aggregate_activities(self, process_abstraction):
        aggregation_perspectives = []
        if process_abstraction == 1:
            aggregation_perspectives = ['Activity', 'Actor']
        elif process_abstraction == 3:
            aggregation_perspectives = ['Activity']

        res_query = queries.query_aggregation_generator(
            aggregation_perspectives, ';'.join(aggregation_perspectives))
        self.session.run(res_query)

    def get_mrs_level_1(self, node_type):
        res_nodes = self.session.run(queries.GET_NODE_DATA)

        self.nodes = extract_nodes(res_nodes.data(), self.perspectives)

        if node_type == 'Class':
            self.session.run(queries.CLASS_AGGREGATION, rel_type='DF', class_rel_type='DF_C')
            return 'DF_C'
        else:
            self.session.run(queries.NODE_DF)
            return 'DF'

    def get_mrs_level_3(self, node_type):
        res_nodes = self.session.run(queries.GET_NODE_DATA)
        self.nodes = extract_nodes(res_nodes.data(), self.perspectives)

        if node_type == 'Class':
            self.session.run(queries.CLASS_AGGREGATION, rel_type='DF_MRS', class_rel_type='DF_MRS_C')
            return 'DF_MRS_C'
        else:
            self.session.run(queries.NODE_DF_MRS)
            return 'DF_MRS'

    def handle_communication(self, message_aggregation):
        '''
        Firstly creates the Message entity
        '''
        self.session.run(queries.CREATE_MESSAGE_ENTITY)
        self.session.run(queries.CORR_MESSAGE_ENTITY)
        self.session.run(queries.SET_NODE_COMM)

        if self.event_abstraction == 3:
            self.session.run(queries.CLASS_AGGREGATION, rel_type='COMM', class_rel_type='COMM_C')
            res = self.session.run(
                queries.GET_EDGE_DATA_TYPED, rel_type='COMM_C')

        else:
            '''if message_aggregation == 1:
                self.session.run(queries.CREATE_MULTI_SENDER)
                self.session.run(queries.MATCH_DF_MS_PRE)
                self.session.run(queries.MATCH_DF_MS_POST)
                self.session.run(queries.CHANGE_VISIBILITY, visibility=False)

            elif message_aggregation == 0:
                self.session.run(queries.CHANGE_VISIBILITY, visibility=True)'''

            res = self.session.run(
                queries.GET_EDGE_DATA_TYPED, rel_type='COMM')

        comm_edges = pd.DataFrame(res.data())
        self.edges = pd.concat([self.edges, comm_edges])

    def generate_graph(self, process_abstraction, event_abstraction, perspectives, communication):
        self.process_abstraction = int(process_abstraction)
        self.event_abstraction = int(event_abstraction)

        self.perspectives = perspectives
        relationship_type = self.set_properties()
        resp = self.session.run(queries.GET_EDGE_DATA_TYPED, rel_type=relationship_type)
        self.edges = pd.DataFrame(resp.data())

        if communication[0]:
            message_aggregation = -1
            if communication[1] != None:
                message_aggregation = int(communication[1])
            self.handle_communication(message_aggregation)

        # association of colors useful for representing EKG
        self.edges['color'] = self.edges['edge_label'].apply(
            StyleEKG.set_edge_color)

        if 'Actor' in self.nodes.columns:
            nodecolors = StyleEKG.set_nodes_color(self.nodes)
            self.nodes['color'] = self.nodes['Actor'].apply(nodecolors.get)
            
        return {'nodes': self.nodes, 'edges': self.edges}


def extract_nodes(nodes, perspectives):
    out_nodes = []
    for element in nodes:
        out_nodes.append(element['e'])

    curr_nodes = pd.DataFrame(out_nodes)

    matching = [x for x in curr_nodes.columns if 'Time' in x or 'time' in x]

    if len(matching) > 0:
        col_time = matching[0]
        curr_nodes[col_time] = curr_nodes[col_time].apply(
            neo_datetime_conversion)

    if 'first_msg' in curr_nodes.columns:
        curr_nodes['first_msg'] = curr_nodes['first_msg'].apply(
            neo_datetime_conversion)
        curr_nodes['last_msg'] = curr_nodes['last_msg'].apply(
            neo_datetime_conversion)
        curr_nodes = curr_nodes.dropna()

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
    if type(timestamp) != float:
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
