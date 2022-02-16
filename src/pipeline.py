#%%
from initial_data_processing import ProcessSoccerData
from scraper import Scrape_Soccer_Data
from feature_eng import Feature_Engineering
from export_to_cloud import Export_to_AWS_RDS, Data_to_S3

soccer_data = ProcessSoccerData()
df1 = soccer_data.get_matches_df()
scrape_soccer = Scrape_Soccer_Data(df1, headless=True)
scrape_soccer.scrape_match_data()
feature_eng = Feature_Engineering(calc_features=True)
df2 = feature_eng.get_data(include_scraped_data=True)
export = Export_to_AWS_RDS(endpoint='', password='', database='')
export.export_soccer_dataframes(df2)      
s3 = Data_to_S3()
s3.upload_scraped_match_data()
# %%
