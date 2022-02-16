#%%
### Export all the dataframes to AWS RDS and JSON to S3 bucket ###

import sys
import inspect
import os
import pandas as pd
import boto3 
import os
import requests
from feature_eng import Feature_Engineering
from sqlalchemy import create_engine

#### For importing files in the repo
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

BUCKET_NAME = 'soccer-bucket'
REGION_NAME = 'us-east-1'

DATABASE_TYPE = 'postgresql'
DBAPI = 'psycopg2'
ENDPOINT = 'soccerdb.vughg1hggq0r.eu-west-2.rds.amazonaws.com' # AWS endpoint
USER = 'postgres'
PASSWORD = '' #### Add password in here ###
PORT = 5432
DATABASE = 'soccer' 

class Export_to_AWS_RDS:
    def __init__(self, input_df, database_type=DATABASE_TYPE, dbapi=DBAPI, user=USER, port=PORT, endpoint=ENDPOINT, password=PASSWORD, database=DATABASE):
        self.engine = create_engine(f"{database_type}+{dbapi}://{user}:{password}@{endpoint}:{port}/{database}")
        self.engine.connect()
        self.input_df = input_df
        self.feature_eng = Feature_Engineering()
        
    def export_data_and_features(self):
        self.input_df.to_sql('soccer_data_and_features', self.engine, if_exists='replace', index=False) 
        
    ## pass in instead?? ##
    def export_scraped_data(self):
        self.feature_eng.get_scraped_data().to_sql('scraped_soccer_data', self.engine, if_exists='replace', index=False)   
    
    def export_soccer_dataframes(self, df):
        self.export_data_and_features(df)
        self.export_scraped_data()
        
#################################################################################

class Data_to_S3:
    def __init__(self, bucket_name=BUCKET_NAME, region_name=REGION_NAME):
        self.s3_client = boto3.client('s3', region_name)
        self.s3_resource = boto3.resource('s3',region_name)
        self.bucket_name = bucket_name
 
    def _upload_data_to_s3(self, path, name):
        self.s3_client.upload_file(path, self.bucket_name, name)
        
    def upload_scraped_match_data(self):
        path = '../data/matches_data' # put paths in env file
        name = 'matches_data.json'
        self._upload_data_to_s3(path, name)
        path = '../data/elo_data'
        name = 'elo_data.json'
        self._upload_data_to_s3(path, name)

    # prints all the files we have stored in the S3 bucket
    def print_all_file_keys(self):
        bucket = self.s3_resource.Bucket(self.bucket_name)
        for file in bucket.objects.all():
            print(file.key)

    # use a file key from the above function to pass into this function
    def download_file_from_s3(self, file_key, name ):
        self.s3_client.download_file(self.bucket_name, file_key, name)
                    
#%%
# Fill in your details below
# Note: create server with endpoint details in pgAdmin and a database inside the server to view the tables 
# export = Export_to_AWS_RDS(endpoint='', password='', database='')
# #%%
# export.export_soccer_dataframes()
# %%          
# s3 = Data_to_S3()
# s3.upload_scraped_match_data()
#%%