from neo4j import GraphDatabase
from scripts.queries import ElementType
from scripts.style_ekg import StyleEKG
import pandas as pd
import scripts.queries as queries
import scripts.config as config
import datetime
import json
import scripts.constants as cn
import scripts.perspective_handler as ph


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
                        MATCH (e:Event {lifecycle: 'complete'})
                        DELETE e
                         """)
        
        self.session.run(""" 
                        MATCH (e:Event {state: 'inprogress'})
                        DELETE e
                         """)
        
    def create_entity_from_events(self, entity_type):
        '''
        Create Entities
        '''
        response = self.session.run(queries.CREATE_ENTITY_FROM_EVENTS, entity = entity_type)
        return response.data()


    def get_entity(self, entity_name):
        '''
        Get entity list
        '''
        result = self.session.run(queries.GET_ENTITY,  entity=entity_name)
        return result.data()
    
    
    def get_entity_types(self):
        '''
        Get entity types list
        '''
        result = self.session.run(queries.GET_ENTITY_DATA)
        return result.data()
    
    
    def create_corr(self, entity_type):
        '''
        Create Correlation relationship
        '''
        self.session.run(queries.CREATE_CORR_REL, entity = entity_type)
        
    def create_df(self, ent_id):
        self.session.run(queries.NODE_DF, entitytype=ent_id)
        if 'msg' or 'message' in ent_id: # fix the DF rels if there is a correlation based on messages
            self.session.run(queries.HANDLE_COMMUNICATION)
            
        
    
    '''
    def create_entity(self, entity_name):
        
        Creates an entity into Neo4j DB and adds the :CORR relationship
        @parameter :entity_name: entity type
        
        self.session.run(queries.CREATE_TYPED_ENTITY, entity=entity_name)
    '''
        
    def create_entity(self, entity_data, entity_type):
        '''
        Creates an entity into Neo4j DB and adds the :CORR relationship
        @parameter :entity_data: entity information
        '''
        self.session.run(queries.CREATE_PARAM_ENTITY, 
                         entity_data = entity_data, 
                         entity_type = entity_type)

    def init_ekg(self, activity_slider, entities_sliders):
        '''
        Initializes the nodes of the Event Knowledge Graph

        @return: the desired relationship type between nodes
        '''
        #self.session.run(queries.CHANGE_ENTITY_VISIBILITY)
        #self.session.run(queries.CLEAR_CLASSES)
        type_id = ElementType.EVENT
        #actagg = self.activity_abstraction[cn.ACTIVITY]['selected_step']
        activity_s = activity_slider[cn.ACTIVITY]
        id_act_step = int(activity_s[cn.THIS_STEP]) 
        act_agg = activity_s[cn.STEPS][id_act_step - 1]
        
        # if there is an aggregation for the activity property
        if id_act_step != len(activity_s[cn.STEPS]):
            ent_val = self.entity_aggregation(entities_sliders)
            self.aggregate_activities(act_agg, ent_val)
            type_id = ElementType.CLASS
        
        #if int(actagg) == 1:
        #    self.aggregate_activities(self.robot_abstraction)
        #    type_id = ElementType.CLASS

        n = self.session.run(queries.GET_NODES, type=type_id)
        
        self.nodes = n.data()

        relationship = 'DF'

#        if self.robot_abstraction == 3:
#            relationship = relationship + '_MRS'

        relationship_out = self.event_rel_extraction(type_id, relationship)
        return relationship_out

    def aggregate_activities(self, act_agg, ent_val):
        '''
        Creates aggregation classes based on the level of abstraction given as input
        @parameter :robot_abstraction: defines the abstraction level chosen by the user
        '''            
        aggps = [act_agg, 'robot']

        res_query = queries.query_aggregation_generator(
            aggps, ';'.join(aggps))
        self.session.run(res_query)
        print(res_query)

    def entity_aggregation(self, entity_sliders):
        entities_val = {}
        for entity in entity_sliders:
            curr_slider = entity_sliders[entity]
            curr_id = int(curr_slider[cn.THIS_STEP])
            curr_val = curr_slider[cn.STEPS][curr_id - 1]
            entities_val[entity] = curr_val
            
            #query_out = self.session.run(queries.GET_ENTITY_VALUES, entity_type = entity, type = curr_val)
            
            #result = pd.DataFrame(query_out.data())
            #ent_values = result['values'].tolist()
            #entities_val[entity] = ent_values
            
            self.session.run(queries.CREATE_SUPER_ENTITY, entity_type = entity, agg_type = curr_val)
            self.session.run(queries.CREATE_SOBS_ENTITY, entity_type = entity, agg_type = curr_val)
                        
        return entities_val       
        
    def event_rel_extraction(self, node_type: str, relationship: str):
        '''
        Creates a relationship between events based on the input parameters
        @parameter :node_type: to distinguish Events from Classes
        @parameter :relationship: defines the label of the relationship that will be created
        '''
        #res_nodes = self.session.run(queries.GET_NODE_DATA)
        
        #ciao = res_nodes.data()

        #self.nodes = extract_nodes(ciao, self.perspectives)

        if node_type == 'Class':
            # append _C suffix to identify the relation between classes
            class_relationship = relationship + '_C'
            self.session.run(queries.CLASS_AGGREGATION,
                             rel_type=relationship, class_rel_type=class_relationship)
            return class_relationship
        else:
            self.session.run(queries.NODE_DF, entitytype='Robot')
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
        
        
    def generate_graph_v2(self, perspectives_agg, activity_agg):
        '''
        Generates the dataframes with data related to EKG nodes and edges
        @parameter :perspectives_agg: process aggregation level chosen by the user over multiple perspectives
        @parameter :activity_agg: event aggregation level chosen by the user
        
        @return a dictionary with nodes and edges
        '''   
        self.activity_abstraction = activity_agg
        self.perspectives = perspectives_agg
        
        relationship_type = self.init_ekg(activity_slider=activity_agg, entities_sliders=perspectives_agg)
        
        resp = self.session.run(
            queries.GET_EDGE_DATA_TYPED, rel_type=relationship_type)
        
        
        self.edges = pd.DataFrame(resp.data())
        
        self.nodes = pd.DataFrame(self.nodes)
        
        return {'nodes': self.nodes, 'edges': self.edges}
        

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
                act_name = new_node['e'][cn.ACTIVITY]
                node = self.nodes[self.nodes[cn.ACTIVITY].str.contains(act_name) & self.nodes['Robot'].str.contains(rob)].copy()
                destination = node['Event_Id'].to_string().split()[-1]
                node['Type'] = 'HiddenNode'
                node[cn.ACTIVITY] = rob
                node['Event_Id'] = rob + '_start'
                                
                self.nodes = self.nodes.append(node)
                edge = self.edges.iloc[-1].copy()
                edge['source'] =  rob + '_start'
                print(destination)
                edge['destination'] =  destination
                edge['edge_label'] = 'start'
                edge['edge_properties'] = {'edge_weight': 1, 'CorrelationType': 'Robot'}
                
                self.edges = self.edges.append(edge)

        self.edges.to_csv('edges.csv', sep=';')
        #self.nodes.to_csv('nodes.csv', sep=';')
        

        return {'nodes': self.nodes, 'edges': self.edges}


    def get_space(self, activity = None, robot = None):
        if activity == None and robot == None:
            resp = self.session.run(ph.GET_SPACE)
            data = resp.data()
        else:
            resp = self.session.run(ph.GET_SPACE_PARAM, activity = activity, robot = robot)
            data = resp.data()
            
        ph.generate_graph(data)
        return data
    

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
    perspectives = ['Event_Id', cn.ACTIVITY, 'Robot', 'Time']

    mrsg = MRSGraph().generate_graph(
        robot_abstraction, activity_abstraction, perspectives, communication=False)
    print(mrsg)
