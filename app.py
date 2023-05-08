from flask import Flask, render_template, jsonify, request
from flask_bootstrap import Bootstrap
from werkzeug.utils import secure_filename
import json
import os
import scripts.queries as queries
import scripts.config as config
#from graph import MRSGraph
from pyjs_graph import MRSGraph
from neo4j import GraphDatabase


app = Flask(__name__)
Bootstrap(app)
selected_perspectives = []
show_communication = False
graphistry_graph = MRSGraph()


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
        
        load_query = queries.load_generator(final_path, filename)

        return load_query


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
    Returns the slider interface (based on the chosen perspectives [TODO]) 
    '''
    communication_perspective = False
    global selected_perspectives
    selected_perspectives = list(request.form.values())
    if "Message" in selected_perspectives:
        communication_perspective = True
    return render_template('ekg_gui.html', mission_abstraction=1, event_abstraction=1, communication=communication_perspective)


@app.route("/get_graph", methods=["POST"])
def get_graph():
    '''
    Returns the event knowledge graph based on the slider data 
    '''
    global selected_perspectives, show_communication
    mission_slider_val = request.form["mission_slider"]
    event_slider_val = request.form["event_slider"]
    communication_slider_val = None
    if "communication_link" in request.form:
        show_communication = True
        communication_slider_val = request.form["msg_slider"]
        

    result = graphistry_graph.generate_graph(process_abstraction=mission_slider_val, event_abstraction=event_slider_val,
                                             perspectives=selected_perspectives, communication=[show_communication, communication_slider_val])

    nodes = result['nodes'].to_dict(orient='records')
    edges = result['edges'].to_dict(orient='records')

    resp = {'nodes': nodes, 'edges': edges}

    #print(nodes)
    return render_template('ekg_gui.html', mission_abstraction=mission_slider_val, event_abstraction=event_slider_val, communication=show_communication, response_data=resp)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=3000)
