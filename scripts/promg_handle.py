from scripts.config import *
from promg.modules.db_management import DBManagement
from promg.database_managers.authentication import Credentials
from promg import SemanticHeader, OcedPg, authentication, Performance, DatabaseConnection, DatasetDescriptions
import os

# I have changed the library with my credentials
# set the credentials key to default

credentials_key = authentication.Connections.LOCAL

db_connection = DatabaseConnection.set_up_connection_using_key(key=credentials_key,
                                                                   verbose=False)


def load_data(header= None):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test.json')
    print(path)
    dataset_descriptions = DatasetDescriptions(path)
    oced_pg = OcedPg(dataset_descriptions=dataset_descriptions,
                         use_sample=True,
                         use_preprocessed_files=True)
    oced_pg.load_and_transform()

'''
Clean the NEO4J database
'''
def delete_db():
    # creation of performance class required by the db manager
    dataset_name = 'LOG.csv'
    use_sample = False
    performance = Performance.set_up_performance(dataset_name=dataset_name, use_sample=use_sample)
    
    db_manager = DBManagement()
    print('Clearing the database.')
    db_manager.clear_db(replace=False)
    
    performance.finish_and_save()
    db_manager.print_statistics()
