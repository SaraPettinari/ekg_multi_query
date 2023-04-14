CLASS_QUERY = """
                    MATCH ( c1 : Class ) <-[:OBSERVED]- ( e1 : Event ) -[df:DF]-> ( e2 : Event ) -[:OBSERVED]-> ( c2 : Class )
                    MATCH (e1) -[:CORR] -> (n) <-[:CORR]- (e2)
                    WHERE c1.Type = c2.Type AND n.EntityType = df.EntityType
                    WITH n.EntityType as EType,c1,count(df) AS df_freq,c2
                    MERGE ( c1 ) -[rel2:DF_C {EntityType:EType}]-> ( c2 ) ON CREATE SET rel2.count=df_freq
                    WITH c1
                    MATCH (c1:Class) WHERE c1.Type = "Activity"
                    OPTIONAL MATCH (c1)-[df:DF_C]->(c2) WHERE c1.Type = c2.Type
                    RETURN c1.EventID as source, c2.EventID as destination, type(df) as edge_label
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