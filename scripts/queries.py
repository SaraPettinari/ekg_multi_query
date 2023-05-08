import pandas as pd

# not aggregated activities
GET_NODES = """
                MATCH (e)
                WHERE $type in LABELS(e)
                SET e.visibility = true
                RETURN e
            """
            
INIT_EVENT_NODES = """
                MATCH (e:Event)
                SET e.visibility = true
                RETURN e
            """

GET_DATA = """
            MATCH (e)-[rel]->(e1)
            WHERE e.visibility = true AND e1.visibility = true
            RETURN e, e1, type(rel) as edge_label, properties(rel) as edge_properties
            """

NODE_DF = """
            MATCH (n:Entity:Robot)<-[:CORR]-(e)
            WITH n, e AS nodes ORDER BY e.timestamp, ID(e)
            WITH n, collect(nodes) AS event_node_list
            UNWIND range(0, size(event_node_list)-2) AS i
            WITH n, event_node_list[i] AS e1, event_node_list[i+1] AS e2
            MERGE (e1)-[df:DF {CorrelationType:n.EntityType, ID:n.ID, edge_weight: 1}]->(e2)
            RETURN e1.EventID as source, e2.EventID as destination, type(df) as edge_label, properties(df) as edge_properties
            """


CREATE_MESSAGE_ENTITY = """
                        MATCH (e:Event) UNWIND e.Message AS msg
                        WITH DISTINCT msg, e.Payload as payload
                        MERGE (n:Entity:Message {ID:msg, EntityType:"Message", Payload:payload})
                        SET n.visible = false
                    """

CORR_MESSAGE_ENTITY = """
                        MATCH (e:Event) UNWIND e.Message AS msg 
                        WITH e, msg
                        MATCH (n:Entity:Message) WHERE msg = n.ID
                        MERGE (e)-[c:CORR]->(n)
                        """
                        
SET_NODE_COMM = """
            MATCH (e:Event)-[:CORR]->(m:Entity:Message) 
            WHERE e.Msg_Role = 'send' 
            UNWIND e.Message AS msg
            WITH distinct msg, m, e as nodes ORDER BY e.timestamp
            WITH collect(nodes) as event_list, m
            MATCH (e2:Event)-[:CORR]->(m) 
            WHERE e2.Msg_Role = 'receive'
            WITH e2, last(event_list) as e1, m
            MERGE (e1)-[comm:COMM {CorrelationType:m.EntityType, ID:m.ID, edge_weight: 1}]->(e2)
            SET e1.visibility = true
            SET e2.visibility = true
            RETURN e1.EventID as source, e2.EventID as destination, type(comm) as edge_label, properties(comm) as edge_properties
            """
            
# aggregated resources
NODE_DF_MRS = """
                MATCH (e:Event)
                WITH e AS nodes ORDER BY e.timestamp, ID(e)
                WITH collect(nodes) AS event_node_list
                UNWIND range(0, size(event_node_list)-2) AS i
                WITH event_node_list[i] AS e1, event_node_list[i+1] AS e2
                MERGE (e1)-[df:DF_MRS {CorrelationType:'Activity', edge_weight: 1}]->(e2)
                RETURN e1.EventID as source, e2.EventID as destination, type(df) as edge_label, properties(df) as edge_properties
            """

# aggregated activities
CLASS_QUERY = """
                MATCH (c1 : Class) <-[:OBSERVED]- (e1 : Event) -[df:DF]-> (e2 : Event) -[:OBSERVED]-> (c2 : Class)
                WHERE c1.Type = c2.Type
                WITH df.CorrelationType as CType, c1, count(df) AS df_freq, c2
                MERGE (c1) -[rel2:DF_C {CorrelationType:CType}]-> ( c2 ) ON CREATE SET rel2.edge_weight = df_freq
                WITH c1, df_freq
                MATCH (c1:Class) WHERE c1.Type = "Activity"
                OPTIONAL MATCH (c1)-[df:DF_C]->(c2) WHERE c1.Type = c2.Type
                RETURN c1.EventID as source, c2.EventID as destination, type(df) as edge_label, properties(df) as edge_properties
                """

CLASS_MRS_QUERY = """
                    MATCH ( c1 : Class ) <-[:OBSERVED]- (e1 : Event) -[df:DF_MRS]-> (e2 : Event) -[:OBSERVED]-> (c2 : Class)
                    WHERE c1.Type = c2.Type
                    WITH df.CorrelationType as CType, c1, count(df) AS df_freq, c2
                    MERGE ( c1 )-[rel2:DF_MRS_C {CorrelationType:CType}]-> ( c2 ) ON CREATE SET rel2.edge_weight=df_freq
                    WITH c1, rel2.count as freq
                    MATCH (c1:Class) WHERE c1.Type = "Activity"
                    OPTIONAL MATCH (c1)-[df:DF_MRS_C]->(c2) WHERE c1.Type = c2.Type
                    RETURN c1.EventID as source, c2.EventID as destination, type(df) as edge_label, properties(df) as edge_properties
                """


CLASS_COMM_QUERY = """
                MATCH (c1 : Class) <-[:OBSERVED]- (e1 : Event) -[c_rel:COMM]-> (e2 : Event) -[:OBSERVED]-> (c2 : Class)
                WHERE c1.Type = c2.Type
                WITH c_rel.CorrelationType as CType, c1, count(c_rel) AS c_freq, c2
                MERGE (c1) -[comm2:COMM_C {CorrelationType:CType}]-> ( c2 ) ON CREATE SET comm2.edge_weight = c_freq
                WITH c1, c_freq
                MATCH (c1:Class) WHERE c1.Type = "Activity"
                OPTIONAL MATCH (c1)-[cc:COMM_C]->(c2) WHERE c1.Type = c2.Type
                RETURN c1.EventID as source, c2.EventID as destination, type(cc) as edge_label, properties(cc) as edge_properties
                """

CLEAR_CLASSES = """
                    MATCH (e:Event)-[:OBSERVED]-> (c:Class)
                    DETACH DELETE c
                """

'''
Alternative:


MATCH (c:Class)
SET c.visibility = false
'''

CREATE_MULTI_SENDER = """
                    MATCH (n:Event)
                    WITH n.Message as msg, n.Msg_Role as rl, collect(n) as nodelist, count(*) as count
                    WHERE count > 1 and msg IS NOT NULL and rl = 'send'
                    WITH nodelist, head(nodelist) as first_el, last(nodelist) as last_el, size(nodelist) as n_rep
                    WITH nodelist, first_el, last_el, n_rep, duration.between(first_el.timestamp, last_el.timestamp) as dur
                    MERGE (s:Class:MultiSender {repetitions: n_rep, first_msg: first_el.timestamp, last_msg: last_el.timestamp, visible: true})
                    SET s += properties(last_el)
                    MERGE (s)-[:DF {repetitions: n_rep, total_duration: dur}]->(s)
                    FOREACH (node in nodelist | 
                        MERGE (node)-[:COLLECT]->(s))
                """


MATCH_DF_MS_POST = """
                    MATCH (s:MultiSender)<-[:COLLECT]-(e1:Event)-[r]->(e2:Event)
                    WHERE not ((e2)-[:COLLECT]->(:MultiSender))
                    WITH COLLECT(r) AS rels, e1, e2, s, type(r) as rel_type
                    UNWIND rels as re
                    WITH  re, e1, e2, s
                    CALL apoc.merge.relationship(s, type(re), {}, properties(re), e2, {})
                    YIELD rel
                    RETURN rel
                    """
                    
MATCH_DF_MS_PRE = """
                    MATCH (e1:Event)-[r]->(e2:Event)-[:COLLECT]->(s:MultiSender)
                    WHERE not ((e1)-[:COLLECT]->(:MultiSender))
                    WITH COLLECT(r) AS rels, e1, e2, s
                    UNWIND rels as re
                    WITH  re, e1, e2, s
                    CALL apoc.merge.relationship(e1, type(re), properties(re),{}, s, {})
                    YIELD rel
                    RETURN rel
                    """
                    
CHANGE_VISIBILITY = """
                    MATCH (e:Event)-[:COLLECT]->(s:MultiSender)
                    SET e.visible = $visibility
                    SET s.visible = not e.visible
                    """
                    
CHANGE_ENTITY_VISIBILITY = """
                    MATCH (n:Entity)
                    SET n.visible = false
                    """

class ElementType():
    EVENT = 'Event'
    CLASS = 'Class'


def load_generator(path: str, log_name: str):
    log_name = log_name.split('.')[0]
    df = pd.read_csv(path)
    column_names = list(df.columns)
    path = path.replace('\\', '/')
    data_list = ''
    for col_index in column_names:
        if 'time' in col_index:
            data_list += ', {}: datetime(line.{})'.format(
                col_index.title(), col_index)
        else:
            data_list += ', {}: line.{}'.format(col_index.title(), col_index)

    load_query = f'LOAD CSV WITH HEADERS FROM "file:///{path}" as line CREATE (e:Event {{Log: "{log_name}" {data_list} }})'
    return load_query





'''
Potential output:

MATCH ( e : Event )
WITH distinct e.Activity AS actName, e.Actor as actor
MERGE ( c : Class { Name:actName, Type:"Activity;Actor", ID: actName, Actor: actor})

MATCH ( c : Class ) WHERE c.Type = "Activity;Actor"
MATCH ( e : Event ) WHERE c.Name = e.Activity AND c.Actor = e.Actor
CREATE ( e ) -[:OBSERVED]-> ( c )
SET c.visibility = true
SET e.visibility = false
'''
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
        perspectives_dict['EventID'] = event_id
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
        '\n' + 'MERGE (e) -[:OBSERVED]-> (c) \n' + 'SET c.visibility = true \n SET e.visibility = false'

    # print(main_query)
    return main_query


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
