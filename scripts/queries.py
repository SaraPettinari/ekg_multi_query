import pandas as pd
import scripts.constants as cn

class ElementType():
    EVENT = 'Event'
    CLASS = 'Class'

                             
# retrieve event log path and name
def load_mapping(path: str, log_name: str):
    log_name = log_name.split('.')[0]
    df = pd.read_csv(path)
    column_names = list(df.columns)
    path = path.replace('\\', '/')
    data_list = {}
    data_list[cn.PATH] = path
    data_list[cn.LOGNAME] = log_name
    for col_index in column_names:
        data_list[col_index] = col_index.title()

    return data_list


# create event log LOAD query
def load_generator(input_data: dict, node_type):
    data_list = ''
    path = input_data.pop(cn.PATH)
    log_name = input_data.pop(cn.LOGNAME)
    for data in input_data.keys():
        if 'time' in data:
            data_list += ', {}: datetime(line.{})'.format(
                data,input_data[data])
        else:
            data_list += ', {}: line.{}'.format(data, input_data[data])

    load_query = f'LOAD CSV WITH HEADERS FROM "file:///{path}" as line CREATE (e:{node_type} {{Log: "{log_name}" {data_list} }})'

    data = data_list.split(', ')
    data.pop(0)  # the first occurrence is empty
    data_dict = {}
    for el in data:
        res = el.split(': ')
        data_dict[res[0]] = res[1]

    print(load_query)
    return load_query


############## SETTERS ###################


def set_corr_rel(entity):
    return(f"""
            MATCH (e:Event)
            UNWIND e.{entity} AS entity_name
            MATCH (n:Entity {{entity_id: entity_name}})
            MERGE (e)-[c:CORR]->(n)
           """)


# DF relation between events with the same entity
def set_df_rel(entity_id):
    return(f"""
            MATCH (n:Entity)<-[:CORR]-(e)
            WHERE n.type = '{entity_id}'
            WITH n, e AS nodes ORDER BY e.time, ID(e)
            WITH n, collect(nodes) AS event_node_list
            UNWIND range(0, size(event_node_list)-2) AS i
            WITH n, event_node_list[i] AS e1, event_node_list[i+1] AS e2
            MERGE (e1)-[df:DF {{Type:n.type, ID:n.entity_id, edge_weight: 1}}]->(e2)
            """)


def set_entity_from_events(entity):
    return(f"""                      
            MATCH (e:Event) 
            UNWIND e.{entity} AS entity_name
            WITH DISTINCT entity_name
            MERGE (n:Entity {{entity_id:entity_name, type: '{entity}'}})
            RETURN keys(n) LIMIT 1
        """)


def set_class_multi_query(matching_perspectives):
    class_type = 'Class'
    main_query = 'MATCH (e:Event)\n'

    perspectives_dict = {}
    event_id = '"c_" + '
    for p in matching_perspectives:
        p_val = f'e.{p}'
        event_id += f' {p_val}'
        perspectives_dict[p] = p_val
        if p != matching_perspectives[-1]:
            event_id += ' + "_" +'

    perspectives_dict['Event_Id'] = event_id
    perspectives_dict['Type'] = f'"{class_type}"'
    res_dict = str(perspectives_dict).replace("'", "")

    class_creation = f'MERGE (c:Class {res_dict})'

    main_query += class_creation + '\n WITH c, e' + '\n MERGE (e) -[:OBSERVED]-> (c)'

    return main_query


def set_class_df_aggregation(rel_type, class_rel_type):
    return f"""
                MATCH (c1 : Class) <-[:OBSERVED]- (e1 : Event) -[r]-> (e2 : Event) -[:OBSERVED]-> (c2 : Class)
                WHERE c1.Type = c2.Type and type(r) = '{rel_type}'
                WITH r.Type as CType, c1, count(r) AS df_freq, c2
                MERGE (c1) -[:{class_rel_type} {{Type:CType, edge_weight: df_freq}}]-> (c2)
            """


# Entity aggregation in super entities
def set_super_entity(entity_type, agg_type):
    return(f"""
            MATCH (n:Entity)
            where n.type = '{entity_type}'
            with distinct n.{agg_type} as value
            MERGE ( sn : SEntity {{ Name:value, Type:"SuperEntity", ID: value, Type : "{entity_type}" }})
            """)


# Relationship creation from Entity -[:OBS] -> SuperEntity
def set_super_obs_entity(entity_type, agg_type):
    return(f"""
            MATCH ( sn : SEntity )
            WHERE sn.Type = '{entity_type}'
            MATCH ( n : Entity )
            WHERE sn.Name = n.{agg_type}
            MERGE ( n ) -[:OBSERVED]-> ( sn )
            """)


############## GETTERS ###################

def get_node_typed(node_type):
    return(f"""
            MATCH (n:{node_type})
            RETURN properties(n) as node
            """)


def get_entity_data():
    return("""
            MATCH (n:Entity)
            WITH DISTINCT n.type AS tn, keys(n) as props
            RETURN tn as type, props
            """)


def get_entity(entity):
    return(f"""                      
                MATCH (e:Event) 
                UNWIND e.{entity} AS entity_name
                WITH DISTINCT entity_name
                RETURN entity_name
            """)


def get_edge_typed(rel_type):
    return(f"""
            MATCH (e)-[rel]->(e1)
            WHERE type(rel) = '{rel_type}'
            RETURN e.Event_Id as from, e1.Event_Id as to, type(rel) as label, properties(rel) as edge_properties
            """)


def get_nodes_typed(type):
    return(f"""
                MATCH (e)
                WHERE '{type}' in LABELS(e)
                RETURN e
            """)

 
# Retrieve start nodes for an entity type
def get_start_nodes(node_type, entity_type):
    if node_type == ElementType.EVENT:
        query = f""" MATCH (n:{node_type})-[:CORR]->(ent:Entity)
                WHERE NOT (n)<-[:DF {{Type: '{entity_type}'}}]-() AND ent.type = '{entity_type}'
                RETURN n as start, n.{entity_type} as entity
            """
    elif node_type == ElementType.CLASS:
        query = f""" MATCH (n:Event)-[:CORR]->(ent:Entity)
                WHERE NOT (n)<-[:DF {{Type: '{entity_type}'}}]-() AND ent.type = '{entity_type}'
                WITH n as start_node, n.{entity_type} as entity
                MATCH (start_node)-[:OBSERVED]->(c:Class)
                RETURN c as start, entity
            """
    return query


############## DELETE ###################

def delete_class():
    return("""
           MATCH (c:Class)
           DETACH DELETE c
           """)


   
###############################################################################

def query_aggregation_generator(matching_perspectives: list, class_type: str):
    main_query = 'MATCH (e:Event)\n'
    with_query = 'WITH distinct '
    match_event_class = 'MATCH (e : Event) WHERE '

    perspectives_dict = {}
    event_id = '"c_" + '
    for p in matching_perspectives:
        p_val = f'e_{p}'
        event_id += f' {p_val}'
        with_query += f'e.{p} AS {p_val}'
        perspectives_dict[p] = p_val
        perspectives_dict['Event_Id'] = event_id
        match_event_class += f'c.{p} = e.{p} '
        if p != matching_perspectives[-1]:
            with_query += ', '
            match_event_class += 'AND '
            event_id += ' + "_" +'

    perspectives_dict['Type'] = f'"{class_type}"'
    res_dict = str(perspectives_dict).replace("'", "")

    class_creation = f'MERGE (c:Class {res_dict})'
    match_class_type = f'MATCH (c : Class) WHERE c.Type = "{class_type}"'

    main_query += with_query + '\n' + class_creation + '\n' + 'WITH c' + '\n' + \
        match_class_type + '\n' + match_event_class + \
        '\n' + 'MERGE (e) -[:OBSERVED]-> (c)' 

    return main_query

    
def test_class():
    # Dovrei controllare per ogni evento correlato ad n entità, che quelle entità condividono una stessa proprietà
    """
        MATCH (n:Entity)
        UNWIND n.$type AS char
        WITH DISTINCT char
        RETURN char
    """
    
    """
        MATCH (n:Entity)
        UNWIND n.movement AS char
        WITH DISTINCT char
        MATCH (e:Event)-[:CORR]->(n:Entity)
        WHERE n.movement = char
        with distinct e.activity as actName, char
        MERGE ( c : Class { Name: actName, Type:"Activity", EntID: char})
    """
    
    """
        MATCH (n:Entity)
        UNWIND n.movement AS char
        WITH DISTINCT char
        MATCH (e:Event)-[:CORR]->(n:Entity)
        WHERE n.movement = char
        with distinct e.activity as actName, char
        MERGE ( c : Class { Name: actName, Type:"Activity", EntID: char})
    """

    """
        MATCH ( c : Class )
        MATCH ( e : Event )
        WHERE c.Name = e.activity
        CREATE ( e ) -[:OBSERVED]-> ( c )
    """

def match_rel_generator(n1_var, n1_type, rel_var, rel_type, n2_var, n2_type):
    '''
    Generate the query for retrieving relationships

    :param n1_var: first node variable
    :param n1_type: first node type (es. Event)
    :param rel_var: relationship variable
    :param rel_type: relationship type (es. DF)
    :param n2_var: second node variable
    :param n2_type: second node type (es. Event) 
    '''
    match = f'MATCH ({n1_var}:{n1_type})-[{rel_var}:{rel_type}]->({n2_var}:{n2_type})'
    ret = f'RETURN {n1_var}, {rel_var}, {n2_var}'
    return (match + ret).replace("'", "")

