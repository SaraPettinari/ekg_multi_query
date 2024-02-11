import pandas as pd
import scripts.constants as cn

# not aggregated activities
GET_NODES = """
                MATCH (e)
                WHERE $type in LABELS(e)
                RETURN e
            """

GET_EDGE_DATA = """
            MATCH (e)-[rel]->(e1)
            WHERE e.visibility = true AND e1.visibility = true
            RETURN e.Event_Id as from, e1.Event_Id as to, type(rel) as label, properties(rel) as edge_properties
            """

GET_EDGE_DATA_TYPED = """
            MATCH (e)-[rel]->(e1)
            WHERE type(rel) = $rel_type
            RETURN e.Event_Id as from, e1.Event_Id as to, type(rel) as label, properties(rel) as edge_properties
            """

#GET_NODE_DATA = """
#            MATCH (e)
#            WHERE e.visibility = true
#            RETURN e
#            """

GET_NODE_DATA = """
            MATCH (e)
            RETURN e
            """

# DF relation between events from the same resource
NODE_DF = """
            MATCH (n:Entity)<-[:CORR]-(e)
            WHERE n.type = $entitytype
            WITH n, e AS nodes ORDER BY e.time, ID(e)
            WITH n, collect(nodes) AS event_node_list
            UNWIND range(0, size(event_node_list)-2) AS i
            WITH n, event_node_list[i] AS e1, event_node_list[i+1] AS e2
            MERGE (e1)-[df:DF {CorrelationType:n.type, ID:n.entity_id, edge_weight: 1}]->(e2)
            """

# DF relation without resource distinction
NODE_DF_MRS = """
                MATCH (e:Event)
                WITH e AS nodes ORDER BY e.Time, ID(e)
                WITH collect(nodes) AS event_node_list
                UNWIND range(0, size(event_node_list)-2) AS i
                WITH event_node_list[i] AS e1, event_node_list[i+1] AS e2
                MERGE (e1)-[df:DF_MRS {CorrelationType: 'activity', edge_weight: 1}]->(e2)
            """

GET_ENTITY = """                      
                MATCH (e:Event) 
                UNWIND e[$entity] AS entity_name
                WITH DISTINCT entity_name
                RETURN entity_name
            """

CREATE_TYPED_ENTITY = """                      
                        MATCH (e:Event) 
                        UNWIND e[$entity] AS entity_name
                        WITH DISTINCT entity_name
                        MERGE (:Entity {ID:entity_name, EntityType:$entity})
                        WITH entity_name
                        MATCH (n:Entity) 
                        WHERE n.ID = entity_name AND n.EntityType = $entity
                        MATCH (e:Event)
                        WHERE e[$entity] = entity_name
                        MERGE (e)-[c:CORR]->(n)
                    """
                    
CREATE_CORR_REL = """
                        MATCH (n:Entity)
                        WITH n, n.entity_id as id, n.type as type
                        MATCH (e:Event)
                        WHERE e[type] = id
                        MERGE (e)-[c:CORR]->(n)
                """

# Queries for handling communication
CREATE_MESSAGE_ENTITY = """
                        MATCH (e:Event) UNWIND e.Msg_Id AS msg
                        WITH DISTINCT msg, e.Msg_Payload as payload
                        MERGE (n:Entity:Message {ID:msg, EntityType:"Message", Payload:payload})
                        SET n.visibility = false
                    """

CORR_MESSAGE_ENTITY = """
                        MATCH (e:Event) UNWIND e.Msg_Id AS msg 
                        WITH e, msg
                        MATCH (n:Entity:Message) WHERE msg = n.ID
                        MERGE (e)-[c:CORR]->(n)
                        """

SET_NODE_COMM = """
            MATCH (e:Event)-[:CORR]->(m:Entity:Message) 
            WHERE e.Msg_Role = 'send' 
            UNWIND e.Msg_Id AS msg
            WITH distinct msg, m, e as nodes ORDER BY e.Time
            WITH collect(nodes) as event_list, m
            MATCH (e2:Event)-[:CORR]->(m) 
            WHERE e2.Msg_Role = 'receive'
            WITH e2, last(event_list) as e1, m
            MERGE (e1)-[comm:COMM {CorrelationType:m.EntityType, ID:m.ID, edge_weight: 1}]->(e2)

            """
           # SET e1.visibility = true
           # SET e2.visibility = true

# aggregated activities
# @param :rel_type: matching relationship type
# @param :class_rel_type: new relationship type
CLASS_AGGREGATION = """
                MATCH (c1 : Class) <-[:OBSERVED]- (e1 : Event) -[r]-> (e2 : Event) -[:OBSERVED]-> (c2 : Class)
                WHERE c1.Type = c2.Type and type(r) = $rel_type
                WITH r.CorrelationType as CType, c1, count(r) AS df_freq, c2
                CALL apoc.merge.relationship(c1, $class_rel_type, {CorrelationType:CType, edge_weight: df_freq},{}, c2, {})
                YIELD rel
                RETURN rel
                """

CLEAR_CLASSES = """
                    MATCH (e:Event)-[:OBSERVED]-> (c:Class)
                    DETACH DELETE c
                """


CREATE_MULTI_SENDER = """
                    MATCH (n:Event)
                    WITH n.Message as msg, n.Msg_Role as rl, collect(n) as nodelist, count(*) as count
                    WHERE count > 1 and msg IS NOT NULL and rl = 'send'
                    WITH nodelist, head(nodelist) as first_el, last(nodelist) as last_el, size(nodelist) as n_rep
                    WITH nodelist, first_el, last_el, n_rep, duration.between(first_el.Time, last_el.Time) as dur
                    MERGE (s:Class:MultiSender {repetitions: n_rep, first_msg: first_el.Time, last_msg: last_el.Time})
                    SET s += properties(last_el)
                    MERGE (s)-[:DF {edge_weight: n_rep, total_duration: dur, CorrelationType:'Robot'}]->(s)
                    FOREACH (node in nodelist | 
                        MERGE (node)-[:OBSERVED]->(s))
                """


MATCH_DF_MS_POST = """
                    MATCH (s:MultiSender)<-[:OBSERVED]-(e1:Event)-[r]->(e2:Event)
                    WHERE not ((e2)-[:OBSERVED]->(:MultiSender))
                    WITH COLLECT(r) AS rels, e1, e2, s, type(r) as rel_type
                    UNWIND rels as re
                    WITH  re, e1, e2, s
                    CALL apoc.merge.relationship(s, type(re), {}, properties(re), e2, {})
                    YIELD rel
                    RETURN rel
                    """

MATCH_DF_MS_PRE = """
                    MATCH (e1:Event)-[r]->(e2:Event)-[:OBSERVED]->(s:MultiSender)
                    WHERE not ((e1)-[:OBSERVED]->(:MultiSender))
                    WITH COLLECT(r) AS rels, e1, e2, s
                    UNWIND rels as re
                    WITH  re, e1, e2, s
                    CALL apoc.merge.relationship(e1, type(re), properties(re),{}, s, {})
                    YIELD rel
                    RETURN rel
                    """

CHANGE_VISIBILITY = """
                    MATCH (e:Event)-[:OBSERVED]->(s:MultiSender)
                    SET e.visibility = $visibility
                    SET s.visibility = not e.visibility
                    """

CHANGE_ENTITY_VISIBILITY = """
                    MATCH (n:Entity)
                    SET n.visibility = false
                    """

ADD_START_ENTITY_NODE = """
                    MATCH (e:Event)
                    WHERE e.Robot = $robot 
                    RETURN e ORDER BY e.Time LIMIT 1
                    """
                    
GET_ENTITY_VALUES = """
                        MATCH (n:Entity)
                        WHERE n.type = $entity_type
                        UNWIND n[$type] AS values
                        WITH DISTINCT values
                        RETURN values
                    """
                    
CREATE_SUPER_ENTITY = """
                        MATCH (n:Entity)
                        where n.type = $entity_type
                        with distinct n[$agg_type] as value
                        MERGE ( sn : SEntity { Name:value, Type:"SuperEntity", ID: value, Type : $entity_type })
                        """

CREATE_SOBS_ENTITY = """
                    MATCH ( sn : SEntity )
                    WHERE sn.Type = $entity_type
                    MATCH ( n : Entity )
                    WHERE sn.Name = n[$agg_type]
                    MERGE ( n ) -[:OBSERVED]-> ( sn )
                    """

class ElementType():
    EVENT = 'Event'
    CLASS = 'Class'


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


def load_generator(input_data: dict, node_type):
    data_list = ''
    path = input_data.pop(cn.PATH)
    log_name = input_data.pop(cn.LOGNAME)
    for data in input_data.keys():
        if 'time' in data:
            data_list += ', {}: datetime(line.{})'.format(
                input_data[data], data)
        else:
            data_list += ', {}: line.{}'.format(input_data[data], data)

    load_query = f'LOAD CSV WITH HEADERS FROM "file:///{path}" as line CREATE (e:{node_type} {{Log: "{log_name}" {data_list} }})'

    data = data_list.split(', ')
    data.pop(0)  # the first occurrence is empty
    data_dict = {}
    for el in data:
        res = el.split(': ')
        data_dict[res[0]] = res[1]

    print(load_query)
    return load_query


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
        #+ \ 'SET c.visibility = true \n SET e.visibility = false'

    # print(main_query)
    return main_query


'''
MATCH (e:Event)-[:CORR]->(n:Entity:Robot)
WITH distinct e.Activity AS e_Activity, n.rtype AS e_Robot
MERGE (c:Class {Activity: e_Activity, Event_Id: "c_" +  e_Activity + "_" + e_Robot, Robot: e_Robot, Type: "Activity;Robot"})
WITH c
MATCH (c : Class) WHERE c.Type = "Activity;Robot"
MATCH (e : Event)-[:CORR]->(n:Entity) WHERE c.Activity = e.Activity AND c.Robot = n.rtype
MERGE (e) -[:OBSERVED]-> (c)
SET c.visibility = true
 SET e.visibility = false
 
 
Match (e:Event)-[:CORR]->(n:Entity:*)
WITH distinct e.Activity AS e_Activity, n.* AS e_Robot
'''


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
