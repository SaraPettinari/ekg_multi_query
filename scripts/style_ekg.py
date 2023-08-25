import pandas as pd


node_color_list = ['#8A2BE2', '#FF4500', '#00CED1', '#2E8B57', '#FF8C00', '#00008B', '#FF1493']
class StyleEKG:
    def __init__(self) -> None:
        pass
    
    '''
    Sets edges colors
    '''
    def set_edge_color(edge_label):
        if 'DF' in edge_label:
            return '#666666'
        elif 'COMM' in edge_label:
            return '#FF0000'
        else:
            return '#000000'
        
    
    def set_nodes_color(nodes: pd.DataFrame):
        actor_color = {}
        i = 0
        actors = nodes['Robot'].unique()
        for actor in actors:
            actor_color[actor] = node_color_list[i]
            i += 1
            
        return actor_color
