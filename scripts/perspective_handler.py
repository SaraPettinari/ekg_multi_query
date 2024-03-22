import pandas as pd
import plotly.express as px
import os 
import datetime
import scripts.plot_creation as pc

from itertools import chain

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


def get_communication_data(events):
    event_list = list(chain.from_iterable(events))
    df = pd.DataFrame(event_list)
    
    dff = generate_comm_data(df)
    
    path = pc.generate_communication_graph(dff)

    return path
            
def generate_graph(data):
    print(data)
   
    
def generate_comm_data(df : pd.DataFrame):
    df['time'] = df['time'].apply(lambda x: neo_datetime_conversion(x))

    grouped_df = df.groupby('msg_id')
    lost_msgs = 0
    tentativi = 0
    results = []
    # Iterate over each group and store it in the dictionary
    for msg_id, group in grouped_df:
        lost_msgs = 0
        tentativi = 0
        activity = group['activity'].iloc[0]
        receive_rows = group[group['msg_role'] == 'receive']
        
            
        # Find the first row with 'lifecycle' equal to 'start'
        start_rows = group[(group['lifecycle'] == 'start')]
        if not start_rows.empty:
            start_row = start_rows.iloc[0]
            tentativi = len(start_rows)
            if receive_rows.empty:
                lost_msgs += 1
        else:
            continue
        
        # Find the last row with 'lifecycle' equal to 'complete'
        complete_rows = group[(group['lifecycle'] == 'complete')]
        if not complete_rows.empty:
            complete_row = complete_rows.iloc[-1]
        else:
            continue
        
        # Calculate timestamp difference
        timestamp_diff = pd.to_datetime(complete_row['time']) - pd.to_datetime(start_row['time'])
        
        # Store results
        results.append({
            'msg_id': msg_id,
            'activity': activity,
            'start_time': start_row['time'],
            'complete_time': complete_row['time'],
            'timestamp_diff': timestamp_diff,
            'lost_msgs': lost_msgs,
            'attempts': tentativi
        })
        # Store both send and receive rows in a dictionary


    dff = pd.DataFrame(results)

    return dff


def get_space_data(events):  
    event_list = list(chain.from_iterable(events))
    df = pd.DataFrame(event_list)     
    
    df['x'] = df['x'].apply(lambda x: float(x))
    df['y'] = df['y'].apply(lambda x: float(x))
    df['z'] = df['z'].apply(lambda x: float(x))
    
    
    
    sub_df = df[['activity','x', 'y', 'z', 'robot']]
    
    
    plot_path = pc.generate_space_graph(sub_df)
    
    return plot_path


        
def neo_datetime_conversion(Time):
    '''
    From Neo4j datetime to datetime
    '''
    if type(Time) != float:
        millis = int(Time.nanosecond/1000)
        t = datetime.datetime(Time.year, Time.month, Time.day,
                              Time.hour, Time.minute, Time.second, millis)
        return t
