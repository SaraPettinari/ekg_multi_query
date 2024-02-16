from flask import Blueprint, render_template, request, session
from scripts.promg_handle import *
from pyjs_graph import MRSGraph
from werkzeug.utils import secure_filename

import scripts.queries as queries
import scripts.constants as cn
import scripts.utils as utils

graph_handler = Blueprint("graph", __name__)

ekg = MRSGraph()

# define a constant to retrieve data
PERSPECTIVES = 'perspectives'

@graph_handler.route('/set_data', methods=['POST'])
def set_data():
    if request.method == 'POST':
        form_data = request.form
        out_data = {}
        entity_list = []
        session[cn.ENTITIES] = {}

        for el in form_data.keys():
            if 'entity' in el:
                entity_name = el.replace('_entity', '')
                entity_list.append(entity_name)
                out_data[entity_name] = entity_name
                session[cn.ENTITIES][entity_name] = ''
            elif 'd-' in el:
                    value = form_data[el]
                    el = el.replace('d-', '')
                    out_data[el] = value
            else:
                out_data[el] = form_data[el]

        print(out_data)
        session[cn.ACTIVITY] = out_data[cn.ACTIVITY]
        load_query = queries.load_generator(out_data, node_type=cn.EVENT)

        # uploads log data into neo4j db
        ekg.load_data(load_query)
        
        #session[cn.ENTITIES] = entity_list
        # check if some entities needs to be created
        skip_data_upload = 'skip_data' in out_data.keys()
        if len(entity_list) > 0 and not skip_data_upload:
            return render_template('entity_data_generator.html', entity_list = entity_list)
        elif skip_data_upload:
            return entity_uploader()
        else:
            return graph()
            
            
@graph_handler.route('/entity_uploader', methods=["POST"])
def entity_uploader():
    if request.method == 'POST':
        file_list = request.files
        
        if len(file_list) > 0:
            for file in file_list:
                curr_ent = file.replace('_file', '')
                filename = secure_filename(file_list[file].filename)
                logs_path = os.getcwd() + cn.ENTITY_PATH
                if not os.path.exists(logs_path):
                    os.makedirs(logs_path)
                    final_path = logs_path + '/' + filename
                    file.save(final_path)
                else:
                    final_path = logs_path + '/' + filename
                    
                ent_data = utils.set_entity_data(final_path, log_name = filename)
                load_query = ent_data['query']
                columns = ent_data['columns']
                session[cn.ENTITIES][curr_ent] = columns
                # uploads entity data into neo4j db and create CORR relationship
                ekg.load_data(load_query)
                ekg.create_corr(curr_ent)
                ekg.create_df(curr_ent)        
        else:
            entities = session[cn.ENTITIES].keys()
            for ent in entities:
                resp = ekg.create_entity_from_events(entity_type=ent)
                ent_values = resp[0]['keys(n)']
                session[cn.ENTITIES][ent] = ent_values
                ekg.create_corr(ent)
                ekg.create_df(ent)
            
    return graph()
            

@graph_handler.route('/set_graph', methods=["GET", "POST"])
def graph():
    '''
    Returns: 
    - rendering of the slider interface 
    '''
    entity_list = session[cn.ENTITIES].keys()
    slider_dict = {}
    for entity in entity_list:
        columns = session[cn.ENTITIES][entity]
        steps = utils.put_value_in_last_position(columns, cn.ENT_TYPE)
        # Creation of Entity type slider steps based on the characteristics of each entity type
        slider_dict[entity] = { cn.THIS_STEP: 1, cn.STEPS: steps }
    session[cn.SLIDERS] = slider_dict

    # TODO automatize this selection
    #activity_id_aggregation = ['Identity', 'Predecessor identity', 'Successor identity', 'Neighbors identity', 'None']
    activity_id_aggregation = ['activity', 'event_id']
    
    session[cn.ACTIVITY] = { cn.ACTIVITY: {
        cn.THIS_STEP: 1, cn.STEPS: activity_id_aggregation
    }}

    return render_template('ekg_gui.html')


@graph_handler.route("/get_graph", methods=["POST"])
def get_graph():
    '''
    Returns the event knowledge graph based on the slider data 
    '''
    selected_perspectives = session[cn.ENTITIES]
    for perspective in selected_perspectives.keys():
        slider_identifier = perspective + '_slider'
        slider = request.form[slider_identifier]
        session[cn.SLIDERS][perspective]['selected_step'] = slider
    #resource_slider_val = request.form["resource_slider"]
    activity_slider_val = request.form["activity_slider"]
    activity_id = list(session[cn.ACTIVITY])[0]
    session[cn.ACTIVITY][activity_id]['selected_step'] = activity_slider_val

    '''
    communication_slider_val = request.form["edge_msg"]
    resource_edge_val = request.form["edge_robot"]

    if int(communication_slider_val) == 1:
        show_communication = True
        #communication_slider_val = request.form["msg_slider"]
    '''
    
    #result = ekg.generate_graph(activity_abstraction=activity_slider_val,
    #                            perspectives=selected_perspectives, communication=show_communication)

    result = ekg.generate_graph_v2(perspectives_agg=session[cn.SLIDERS], activity_agg=session[cn.ACTIVITY])
    
    nodes = result['nodes'].to_dict(orient='records')
    edges = result['edges'].to_dict(orient='records')

    resp_graph = {'nodes': nodes, 'edges': edges}

    # print(nodes)
    return render_template('ekg_gui.html', response_data=resp_graph)



@graph_handler.route('/view/activity', methods=['GET'])
def measurements_gui():
    args = request.args
    activity_name = args.get('activity_id')
    session['current_activity'] = activity_name
    return render_template('measurements_gui.html')