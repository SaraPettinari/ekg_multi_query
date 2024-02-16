from flask import Flask, render_template
from flask_bootstrap import Bootstrap
import os
import scripts.queries as queries
import scripts.config as config
from neo4j import GraphDatabase

from routes.data_uploader import data_uploader
from routes.graph_handler import graph_handler

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1  # disable caching
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config['SECRET_KEY'] = os.urandom(24)

Bootstrap(app)
selected_perspectives = []
show_communication = False


app.register_blueprint(data_uploader)
app.register_blueprint(graph_handler)


@app.route('/')
def index():
    return render_template('log_uploader.html')



if __name__ == '__main__':
     app.run(host='127.0.0.1', port=3000, debug=True)
