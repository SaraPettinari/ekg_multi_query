import os
import scripts.queries as queries
import scripts.promg_handle as pg
import scripts.constants as cn

from flask import Blueprint, render_template, request, session, redirect, url_for
from werkzeug.utils import secure_filename
from pyjs_graph import MRSGraph


data_uploader = Blueprint("uploader", __name__)


@data_uploader.route('/delete_db', methods=["GET"])
def delete_db():
    pg.delete_db()
        
    return render_template('log_uploader.html', db_cleaned = True)

@data_uploader.route('/db_ready', methods=["GET"])
def db_ready():
    ekg = MRSGraph()
        
    result = ekg.get_entity_types()
    if not cn.ENTITIES in session.keys():
        session[cn.ENTITIES] = {}
    
    for el in result:
        entity = el['type']

        session[cn.ENTITIES][entity] = el['props']

    return redirect(url_for('graph.graph'))
        

@data_uploader.route('/uploader', methods=['POST'])
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

