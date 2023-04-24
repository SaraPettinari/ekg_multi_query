# --- conteggia gli archi doppi
CLASS_QUERY = """
                    MATCH ( c1 : Class ) <-[:OBSERVED]- ( e1 : Event ) -[df:DF]-> ( e2 : Event ) -[:OBSERVED]-> ( c2 : Class )
                    MATCH (e1) -[:CORR] -> (n) <-[:CORR]- (e2)
                    WHERE c1.Type = c2.Type AND n.EntityType = df.EntityType
                    WITH n.EntityType as EType, c1, count(df) AS df_freq, c2
                    MERGE ( c1 ) -[rel2:DF_C {EntityType:EType}]-> ( c2 ) ON CREATE SET rel2.count = df_freq
                    WITH c1, df_freq
                    MATCH (c1:Class) WHERE c1.Type = "Activity"
                    OPTIONAL MATCH (c1)-[df:DF_C]->(c2) WHERE c1.Type = c2.Type
                    RETURN c1.EventID as source, c2.EventID as destination, type(df) as edge_label, df_freq as edge_weight
                """

CLASS_MRS_QUERY = """
                    MATCH ( c1 : Class ) <-[:OBSERVED]- ( e1 : Event ) -[df:DF_MRS]-> ( e2 : Event ) -[:OBSERVED]-> ( c2 : Class )
                    WHERE c1.Type = c2.Type
                    WITH c1, count(df) AS df_freq, c2
                    MERGE ( c1 )-[rel2:DF_MRS_C]-> ( c2 ) ON CREATE SET rel2.count=df_freq
                    WITH c1, rel2.count as freq
                    MATCH (c1:Class) WHERE c1.Type = "Activity"
                    OPTIONAL MATCH (c1)-[df:DF_MRS_C]->(c2) WHERE c1.Type = c2.Type
                    RETURN c1.EventID as source, c2.EventID as destination, type(df) as edge_label, freq as edge_weight
                """

CLEAR_CLASSES = """
                    MATCH (e:Event)-[:OBSERVED]-> (c:Class)
                    DETACH DELETE c
                """

GET_NODES = """
                MATCH (e)
                WHERE $type in LABELS(e)
                RETURN e
            """

NODE_DF = """
                    MATCH (n:Entity:Robot)<-[:CORR]-(e)
                    WITH n, e AS nodes ORDER BY e.timestamp, ID(e)
                    WITH n, collect(nodes) AS event_node_list
                    UNWIND range(0, size(event_node_list)-2) AS i
                    WITH n, event_node_list[i] AS e1, event_node_list[i+1] AS e2
                    MERGE (e1)-[df:DF {EntityType:n.EntityType, ID:n.ID}]->(e2)
                    RETURN e1.EventID as source, e2.EventID as destination, type(df) as edge_label
            """

NODE_DF_MRS = """
                MATCH (e:Event)
                WITH e AS nodes ORDER BY e.timestamp, ID(e)
                WITH collect(nodes) AS event_node_list
                UNWIND range(0, size(event_node_list)-2) AS i
                WITH event_node_list[i] AS e1, event_node_list[i+1] AS e2
                MERGE (e1)-[df:DF_MRS]->(e2)
                RETURN e1.EventID as source, e2.EventID as destination, type(df) as edge_label
            """


class ElementType():
    EVENT = 'Event'
    CLASS = 'Class'


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
        '\n' + 'MERGE (e) -[:OBSERVED]-> (c)'

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
