from flask import Flask, render_template, jsonify, request
from flask_bootstrap import Bootstrap
import json
import scripts.queries as queries
import scripts.config as config
#from graph import MRSGraph
from pyjs_graph import MRSGraph
from neo4j import GraphDatabase
from nx_graph import gen_graph

app = Flask(__name__)
Bootstrap(app)
selected_perspectives = []
graphistry_graph = MRSGraph()


@app.route('/')
def index():
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
    return render_template('perspectives.html', perspectives=params, p_size=len(params))


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
    return render_template('index.html', mission_abstraction=1, event_abstraction=1, communication=communication_perspective)


@app.route("/get_graph", methods=["POST"])
def get_graph():
    '''
    Returns the event knowledge graph based on the slider data 
    '''
    global selected_perspectives
    show_communication = False
    mission_slider_val = request.form["mission_slider"]
    event_slider_val = request.form["event_slider"]
    if "communication_link" in request.form:
        show_communication = True

    result = graphistry_graph.generate_graph(process_abstraction=mission_slider_val, event_abstraction=event_slider_val,
                                             perspectives=selected_perspectives, communication=show_communication)

    nodes = result['nodes'].to_dict(orient='records')
    edges = result['edges'].to_dict(orient='records')

    resp = {'nodes': nodes, 'edges': edges}


    #gen_graph(nodes, edges)
    
    return render_template('index.html', mission_abstraction=mission_slider_val, event_abstraction=event_slider_val, communication=show_communication, response_data=resp)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=3000)
