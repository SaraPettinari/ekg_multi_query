GET_SPACE = """
            MATCH (e:Event)
            WITH e.activity AS activity, e.robot as robot, COLLECT(DISTINCT [e.x, e.y, e.z]) AS coordinates
            RETURN activity, robot, coordinates
            """
            
            
GET_SPACE_PARAM = """
            MATCH (e:Event)
            WHERE e.activity = $activity and e.robot = $robot
            WITH COLLECT(DISTINCT [e.x, e.y, e.z]) AS coordinates
            RETURN coordinates
            """
            
            

def generate_graph(data):
    print(data)