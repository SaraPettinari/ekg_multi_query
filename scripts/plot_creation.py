import os 
import pandas as pd
import plotly.express as px



def generate_communication_graph(data : dict):
    df = pd.DataFrame(data)
    # Assuming 'start_time' and 'complete_time' are in string format, convert them to datetime
    df['start_time'] = pd.to_datetime(df['start_time'])
    df['complete_time'] = pd.to_datetime(df['complete_time'])

    # Calculate performance metrics
    df['duration'] = df['complete_time'] - df['start_time']
    df['success_rate'] = 1 - (df['lost_msgs'] / df['attempts'])

    print(df['attempts'].mean())

    # Calculate duration
    df['duration'] = (df['complete_time'] - df['start_time']).dt.total_seconds()
    
    df['activity'] = [x[0] for x in df['activity']]
    
    activities_counts = df['activity'].value_counts().reset_index()
    activities_counts.columns = ['activity', 'received_msgs']

    # Grouping data by activities and calculating sum of messages sent, lost, and total duration
    grouped_data = df.groupby('activity').agg({'msg_id': 'count', 'lost_msgs': 'sum', 'duration': 'mean', 'attempts': 'mean'}).reset_index()


    # Merge the counts of rows for each activities into the grouped data DataFrame
    grouped_data = pd.merge(grouped_data, activities_counts, on='activity')
    
    fig = px.bar(grouped_data, x="activity", y=["received_msgs", "lost_msgs"], text_auto=True)

    fig.update_layout(xaxis_title="activity", yaxis_title="Messages Count",
                    title="Communication Metrics")


    out_file = "commumication_plot.html"
    
    plot_path =  os.path.join(os.getcwd(), "templates", "home")
    if not os.path.exists(plot_path):
        os.makedirs(plot_path)
    fig_path = os.path.join(plot_path, out_file)
    
    fig.write_html(fig_path)
    
    template_path = "home" + '/' + out_file
    print(template_path)
    return(template_path)

 

def generate_space_graph(df, activity_name = None):
    if activity_name != None:
        filtered_df = df[df['activity'] == activity_name]
        fig = px.scatter_3d(filtered_df, x='x', y='y', z='z',
                            color='case',
                            symbol='activity',
                            title="Space for: " + activity_name,
                            range_x=[0, 10],
                            range_y=[0, 10],
                            range_z=[0, 2],
                            )
    else:
        activity_name = 'home'
        fig = px.scatter_3d(df, x='x', y='y', z='z',
                            color='activity',
                            symbol='robot',
                            title="Space for MRS",
                            range_x=[0, 10],
                            range_y=[0, 10],
                            range_z=[0, 2],                            
                            )
    
    fig.update_layout(scene=dict(
        yaxis=dict(
            backgroundcolor="rgb(227, 227, 250)",
            gridcolor="white",
            showbackground=True,
            zerolinecolor="white"),
        zaxis=dict(
            backgroundcolor="rgb(227, 227, 227)",
            gridcolor="white",
            showbackground=True,
            zerolinecolor="white",),),
    )
        
    out_file = "space_plot.html"
   
    plot_path =  os.path.join(os.getcwd(), "templates", activity_name)
    if not os.path.exists(plot_path):
        os.makedirs(plot_path)
    fig_path = os.path.join(plot_path, out_file)
    
    fig.write_html(fig_path)
    
    template_path = activity_name + '/' + out_file
    print(template_path)
    return template_path        