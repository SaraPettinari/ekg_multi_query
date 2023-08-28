from neo4j import GraphDatabase
from scripts.queries import ElementType
from scripts.style_ekg import StyleEKG
import pandas as pd
import scripts.queries as queries
import scripts.config as config
import datetime
import json


class MRSGraph:
    def __init__(self):
        self.edges = []
        self.nodes = []

        # init neo4j connection
        self.driver = GraphDatabase.driver(**config.NEO4J)
        self.session = self.driver.session()

    def load_data(self, load_query):
        '''
        Uploads log data into Neo4j DB
        @parameter :load_query: query to execute
        '''
        self.session.run(load_query)

        self.session.run(""" 
                        MATCH (e:Event {Lifecycle: 'complete'})
                        DELETE e
                         """)

    def create_entity(self, entity_name):
        '''
        Creates an entity into Neo4j DB
        @parameter :entity_name: entity type
        '''
        self.session.run(queries.CREATE_TYPED_ENTITY, entity=entity_name)

    def init_ekg(self):
        '''
        Initializes the nodes of the Event Knowledge Graph

        @return: the desired relationship type between nodes
        '''
        self.session.run(queries.CHANGE_ENTITY_VISIBILITY)
        self.session.run(queries.CLEAR_CLASSES)
        type_id = ElementType.EVENT
        if self.activity_abstraction == 1:
            self.aggregate_activities(self.robot_abstraction)
            type_id = ElementType.CLASS

        self.session.run(queries.GET_NODES, type=type_id)

        relationship = 'DF'

        if self.robot_abstraction == 3:
            relationship = relationship + '_MRS'

        relationship_out = self.event_rel_extraction(type_id, relationship)
        return relationship_out

    def aggregate_activities(self, robot_abstraction):
        '''
        Creates aggregation classes based on the level of abstraction given as input
        @parameter :robot_abstraction: defines the abstraction level chosen by the user
        '''
        aggregation_perspectives = []
        if robot_abstraction == 1:
            aggregation_perspectives = ['Activity', 'Robot']
        if robot_abstraction == 2:
            aggregation_perspectives = ['Activity', 'Robot.rtype']
        elif robot_abstraction == 3:
            aggregation_perspectives = ['Activity']

        res_query = queries.query_aggregation_generator(
            aggregation_perspectives, ';'.join(aggregation_perspectives))
        self.session.run(res_query)
        print(res_query)

    def event_rel_extraction(self, node_type: str, relationship: str):
        '''
        Creates a relationship between events based on the input parameters
        @parameter :node_type: to distinguish Events from Classes
        @parameter :relationship: defines the label of the relationship that will be created
        '''
        res_nodes = self.session.run(queries.GET_NODE_DATA)

        self.nodes = extract_nodes(res_nodes.data(), self.perspectives)

        if node_type == 'Class':
            # append _C suffix to identify the relation between classes
            class_relationship = relationship + '_C'
            self.session.run(queries.CLASS_AGGREGATION,
                             rel_type=relationship, class_rel_type=class_relationship)
            return class_relationship
        else:
            self.session.run(queries.NODE_DF)
            return relationship

    def handle_communication(self, message_aggregation):
        '''
        Firstly creates the Message entity
        '''
        self.session.run(queries.CREATE_MESSAGE_ENTITY)
        self.session.run(queries.CORR_MESSAGE_ENTITY)
        self.session.run(queries.SET_NODE_COMM)

        if self.activity_abstraction == 1:
            self.session.run(queries.CLASS_AGGREGATION,
                             rel_type='COMM', class_rel_type='COMM_C')
            res = self.session.run(
                queries.GET_EDGE_DATA_TYPED, rel_type='COMM_C')

        else:
            '''
            if message_aggregation == 2:
                self.session.run(queries.CREATE_MULTI_SENDER)
                self.session.run(queries.MATCH_DF_MS_PRE)
                self.session.run(queries.MATCH_DF_MS_POST)
                self.session.run(queries.CHANGE_VISIBILITY, visibility=False)

            elif message_aggregation == 1:
                self.session.run(queries.CHANGE_VISIBILITY, visibility=True)
            '''
            updated_edges = self.session.run(
                queries.GET_EDGE_DATA_TYPED, rel_type='DF')
            self.edges = updated_edges.to_df()

            res = self.session.run(
                queries.GET_EDGE_DATA_TYPED, rel_type='COMM')

            updated_nodes = self.session.run(queries.GET_NODE_DATA)

            self.nodes = extract_nodes(updated_nodes.data(), self.perspectives)

        comm_edges = res.to_df()
        self.edges = pd.concat([self.edges, comm_edges])

    def generate_graph(self, robot_abstraction, activity_abstraction, perspectives, communication):
        '''
        Generates the dataframes with data related to EKG nodes and edges
        @parameter :robot_abstraction: process abstraction level chosen by the user
        @parameter :activity_abstraction: event abstraction level chosen by the user
        @parameter :perspectives: desired perspectives chosen by the user
        @parameter :communication: desired communication details

        @return a dictionary with nodes and edges

        '''
        self.robot_abstraction = int(robot_abstraction)
        self.activity_abstraction = int(activity_abstraction)

        self.perspectives = perspectives
        relationship_type = self.init_ekg()
        resp = self.session.run(
            queries.GET_EDGE_DATA_TYPED, rel_type=relationship_type)
        self.edges = pd.DataFrame(resp.data())

        if communication == 1:
            message_aggregation = -1
            self.handle_communication(message_aggregation)

        # association of colors useful for representing EKG
        self.edges['color'] = self.edges['edge_label'].apply(
            StyleEKG.set_edge_color)

        if 'Robot' in self.nodes.columns:
            nodecolors = StyleEKG.set_nodes_color(self.nodes)
            self.nodes['color'] = self.nodes['Robot'].apply(nodecolors.get)
            for rob in self.nodes['Robot'].unique():
                resp = self.session.run(queries.ADD_START_ENTITY_NODE, robot=rob)
                new_node = (resp.data()[0]).copy()
                act_name = new_node['e']['Activity']
                node = self.nodes[self.nodes['Activity'].str.contains(act_name) & self.nodes['Robot'].str.contains(rob)].copy()
                destination = node['Event_Id'].to_string().split()[-1]
                node['Type'] = 'HiddenNode'
                node['Activity'] = rob
                node['Event_Id'] = rob + '_start'
                                
                self.nodes = self.nodes.append(node)
                edge = self.edges.iloc[-1].copy()
                edge['source'] =  rob + '_start'
                print(destination)
                edge['destination'] =  destination
                edge['edge_label'] = 'start'
                edge['edge_properties'] = {'edge_weight': '', 'CorrelationType': 'Robot'}
                
                self.edges = self.edges.append(edge)

        self.edges.to_csv('edges.csv', sep=';')
        #self.nodes.to_csv('nodes.csv', sep=';')
        

        return {'nodes': self.nodes, 'edges': self.edges}


def extract_nodes(nodes, perspectives):
    '''
        Generates the dataframes with data related to EKG nodes and edges
        @parameter :nodes: extracted node list
        @parameter :perspectives: set of desired perspectives

        @return a dictionary with nodes
    '''
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
        curr_nodes['delta_time'] = curr_nodes['last_msg'].sub(
            curr_nodes['first_msg'])
        curr_nodes['delta_time'] = curr_nodes['delta_time'].apply(json.dumps)
        curr_nodes = curr_nodes.drop(columns=['first_msg', 'last_msg'])

    # returns a dataset with only the perspectives of interest
    if all(item in perspectives for item in curr_nodes.columns):
        set_curr_nodes = curr_nodes[perspectives]
        return set_curr_nodes
    else:
        return curr_nodes


def neo_datetime_conversion(Time):
    '''
    From Neo4j datetime to datetime
    '''
    if type(Time) != float:
        millis = int(Time.nanosecond/1000)
        t = datetime.datetime(Time.year, Time.month, Time.day,
                              Time.hour, Time.minute, Time.second, millis)
        return t


if __name__ == '__main__':
    robot_abstraction = input('Select process abstraction level:')
    activity_abstraction = input('Select event abstraction level:')
    perspectives = ['Event_Id', 'Activity', 'Robot', 'Time']

    mrsg = MRSGraph().generate_graph(
        robot_abstraction, activity_abstraction, perspectives, communication=False)
    print(mrsg)
