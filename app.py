from flask import Flask, render_template, jsonify, request
from flask_bootstrap import Bootstrap
import json
import queries, config
from graph import MRSGraph
from neo4j import GraphDatabase


app = Flask(__name__)
Bootstrap(app)
selected_perspectives = []

@app.route('/')
def index():
    driver = GraphDatabase.driver(**config.NEO4J)
    with driver.session() as session:
        res_nodes = session.run(queries.GET_NODES, type='Event')
        params = list(res_nodes.data()[0]['e'].keys())
        params.sort()
    return render_template('perspectives.html', perspectives= params, p_size = len(params))

@app.route('/set_graph', methods=["POST"])    
def graph():
    global selected_perspectives
    selected_perspectives = list(request.form.values())
    return render_template('index.html', mission_abstraction=1, event_abstraction=1)


@app.route("/get_graph", methods=["POST"])
def test():
    global selected_perspectives
    mission_slider_val = request.form["mission_slider"]
    event_slider_val = request.form["event_slider"]

    graph = MRSGraph(process_abstraction=mission_slider_val,
                     event_abstraction=event_slider_val, perspectives=selected_perspectives).generate_graph()

    return render_template('index.html', mission_abstraction=mission_slider_val, event_abstraction=event_slider_val, iframe=graph)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=3000)
