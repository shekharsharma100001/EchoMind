import os
from pymongo import MongoClient

# Global variables for db connection
client = None
db = None

def init_db(app=None):
    global client, db
    mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
    client = MongoClient(mongo_uri)
    db = client.get_database('echomind')
