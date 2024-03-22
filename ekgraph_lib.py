from neo4j import GraphDatabase
from scripts.queries import ElementType
import pandas as pd
import scripts.queries as queries
import scripts.config as config
import scripts.constants as cn
import scripts.perspective_handler as ph


class EKGraph:
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
        
        # retrieve data
        events = self.session.run(queries.get_node_typed('Event'))
        events = events.values()
        
        # create communication plot        
        comm_path = ph.get_communication_data(events)
        
        # create space plot        
        space_path = ph.get_space_data(events)
        
        # delete events with lifecycle different from start
        self.session.run(""" 
                        MATCH (e:Event)
                        WHERE NOT e.lifecycle = 'start'
                        DELETE e
                        """)
        
        return {'communication_path': comm_path, 'space_path': space_path}        

    def set_entity_from_events(self, entity_type):
        '''
        Create Entities
        '''
        res = self.session.run(queries.set_entity_from_events(entity_type))
        return res.data()


    def get_entity(self, entity_name):
        '''
        Get entity list
        '''
        res = self.session.run(queries.get_entity(entity_name))
        return res.data()
    
    
    def get_entity_types(self):
        '''
        Get entity types list
        '''
        res = self.session.run(queries.get_entity_data())
        return res.data()
    
    
    def set_corr(self, entity_type):
        '''
        Create Correlation relationship
        '''
        self.session.run(queries.set_corr_rel(entity = entity_type))
        
        
    def set_df(self, entity_id):
        '''
        Create Directly-Follows relationship
        '''
        self.session.run(queries.set_df_rel(entity_id))            
        

    def init_ekg(self, activity_slider, entities_sliders):
        '''
        Initializes the nodes of the Event Knowledge Graph
        
        @parameter :activity_slider: get the value of the activity slider from the interface
        @parameter :entities_sliders: get the values of the entity sliders from the interface

        @return: the desired relationship type between nodes
        '''
        
        type_id = ElementType.EVENT

        activity_slider = activity_slider[cn.ACTIVITY]
        activity_step = int(activity_slider[cn.THIS_STEP]) 
        activity_agg = activity_slider[cn.STEPS][activity_step - 1] # aggregation level
        
        relationship = 'DF'

        # if there is an aggregation for the activity property
        if activity_step != len(activity_slider[cn.STEPS]):
            # check aggregation for entities
            entities_agg = self.entity_aggregation(entities_sliders)
            # aggregate for activity name
            self.ent_agg_list = self.aggregate_activities(activity_agg, entities_agg)
            type_id = ElementType.CLASS
            relationship = 'DF_C'
        
        nodes = self.session.run(queries.get_nodes_typed(type_id))
        self.nodes = nodes.data()

        return relationship

    def aggregate_activities(self, activity_aggregation_id, entities_aggregation):
        '''
        Creates aggregation classes based on the level of abstraction given as input
        @parameter :activity_aggregation_id: the activity aggregation level chosen by the user
        @parameter :entities_aggregation: the entities aggregation level chosen by the user
        '''
        entity_list = [key for key, value in entities_aggregation.items() if value != cn.ENT_TYPE]
        
        self.curr_entities = entity_list
          
        entity_list.append(activity_aggregation_id) # add the aggregation on the activity
        
        res_query = queries.set_class_multi_query(entity_list)
        self.session.run(res_query)
        
        df_c_query = queries.set_class_df_aggregation(rel_type='DF', class_rel_type='DF_C')
        self.session.run(df_c_query)
        
        return entity_list
        

    def entity_aggregation(self, entity_sliders):
        '''
        Aggregate entities
        '''
        entities_val = {}
        # for each entity get the aggregation level and aggregate entities
        for entity in entity_sliders:
            curr_slider = entity_sliders[entity]
            curr_id = int(curr_slider[cn.THIS_STEP])
            curr_val = curr_slider[cn.STEPS][curr_id - 1]
            entities_val[entity] = curr_val
            
            self.session.run(queries.set_super_entity(entity_type = entity, agg_type = curr_val))
            self.session.run(queries.set_super_obs_entity(entity_type = entity, agg_type = curr_val))
                        
        return entities_val       

        
    def generate_graph_v2(self, entities_agg, activity_agg):
        '''
        Generates the dataframes with data related to EKG nodes and edges
        @parameter :entities_agg: process aggregation level chosen by the user over multiple perspectives
        @parameter :activity_agg: event aggregation level chosen by the user
        
        @return a dictionary with nodes and edges
        '''
        
        #delete old classes
        self.session.run(queries.delete_class())   
        
        # get aggregations
        self.activity_abstraction = activity_agg
        self.perspectives = entities_agg
        
        # create the ekg and retrieve the relationship
        relationship_type = self.init_ekg(activity_slider=activity_agg, entities_sliders=entities_agg)
        
        # get all the edges
        res = self.session.run(queries.get_edge_typed(relationship_type))
        
        
        self.edges = pd.DataFrame(res.data())
        self.nodes = pd.DataFrame(self.nodes)
        
        for ent in self.curr_entities:
            start_node = self.session.run(queries.get_start_nodes('Class', ent))
            node = start_node.data()
            for n in node:
                entity = n['entity']
                related_node = n['start'][cn.EVENT_ID]
                
                this_node = n['start'].copy()
                
                for key in this_node:
                    this_node[key] = entity
                this_node['Type'] = ent       

                self.nodes.loc[len(self.nodes)] = {'e': this_node}
                
                this_edge = {'from': entity, 'to': related_node, 'label': 'start', 'edge_properties': ''}
                self.edges.loc[len(self.edges)] = this_edge
            
        
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
    

