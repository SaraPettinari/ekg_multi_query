from flask import Flask, render_template, jsonify, request
from flask_bootstrap import Bootstrap
from werkzeug.utils import secure_filename
import json
import os
import scripts.queries as queries
import scripts.config as config
from pyjs_graph import MRSGraph
from neo4j import GraphDatabase


app = Flask(__name__)
Bootstrap(app)
selected_perspectives = []
show_communication = False
ekg = MRSGraph()


@app.route('/')
def index():
    return render_template('log_uploader.html')


@app.route('/uploader', methods=['POST'])
def uploader():
    if request.method == 'POST':
        f = request.files['log_file']
        filename = secure_filename(f.filename)
        logs_path = os.getcwd() + '/logs'
        if not os.path.exists(logs_path):
            os.makedirs(logs_path)
        final_path = logs_path + '/' + filename
        f.save(final_path)        
        
        load_query = queries.load_mapping(final_path, filename)
        
       
        return render_template('log_uploader.html', query_data=load_query)
    
@app.route('/data_uploader', methods=['POST'])
def data_uploader():
    if request.method == 'POST':
        form_data = request.form
        out_data = {}
        entity_list = []
        
        for el in form_data.keys():
            if 'entity' in el:
                entity_name = el.split('_')[0]
                entity_list.append(form_data[entity_name])
            else:
                out_data[el] = form_data[el]
        
        print(out_data)
        load_query = queries.load_generator(out_data)
        
        print(load_query)

        # uploads log data into neo4j db
        ekg.load_data(load_query)
        
        # check if some entities needs to be created
        if len(entity_list) > 0:
            for entity in entity_list:
                print('TO FIX')
                #ekg.create_entity(entity)

        return get_perspectives()


@app.route('/get_perspectives', methods=["GET"])
def get_perspectives():
    '''
    Extract the perspectives saved in the event log 
    '''
    driver = GraphDatabase.driver(**config.NEO4J)
    with driver.session() as session:
        res_nodes = session.run(queries.GET_NODES, type='Event').data()
        params = []
        # get the unique columns from all the events
        for dictionary in res_nodes:
            if 'e' in dictionary:
                event_keys = dictionary['e'].keys()
                for ek in event_keys:
                    if not ek in params:
                        params.append(ek)
        params.sort()
    return render_template('perspectives_selector.html', perspectives=params, p_size=len(params))


@app.route('/set_graph', methods=["POST"])
def graph():
    '''
    Returns the slider interface (based on the chosen perspectives) 
    '''
    communication_perspective = False
    global selected_perspectives
    selected_perspectives = list(request.form.values())
    #ho bisogno di distinguere local e global [match (e:Event) where e.$perspective is null return e]
    unique_eid = list(filter(lambda x : 'key' in  x, selected_perspectives))[0].replace('key: ', '')
    #if "Message" in selected_perspectives:
    #    communication_perspective = True
    return render_template('ekg_gui.html', activity_abstraction=1, resource_abstraction=1, activity_id = unique_eid)


@app.route("/get_graph", methods=["POST"])
def get_graph():
    '''
    Returns the event knowledge graph based on the slider data 
    '''
    global selected_perspectives, show_communication
    resource_slider_val = request.form["resource_slider"]
    activity_slider_val = request.form["activity_slider"]
    communication_slider_val = request.form["edge_msg"]
    resource_edge_val = request.form["edge_robot"]
    
    if int(communication_slider_val) == 1:
        show_communication = True
        #communication_slider_val = request.form["msg_slider"]
        

    result = ekg.generate_graph(process_abstraction=resource_slider_val, event_abstraction=activity_slider_val,
                                             perspectives=selected_perspectives, communication=[show_communication])

    nodes = result['nodes'].to_dict(orient='records')
    edges = result['edges'].to_dict(orient='records')

    resp = {'nodes': nodes, 'edges': edges}

    #print(nodes)
    return render_template('ekg_gui.html', ev_id_abstraction=resource_slider_val, event_abstraction=activity_slider_val, communication=show_communication, response_data=resp)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=3000)
