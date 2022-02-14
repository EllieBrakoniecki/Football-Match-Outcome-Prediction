#%%
from initial_data_processing import ProcessSoccerData
from scraper import Scrape_Soccer_Data
import pandas as pd

#%%
NO_PREV_MATCHES_TO_CALULATE_AVERAGE_FROM = 5

class Feature_Engineering: 
    def __init__(self):
        self.soccer_data = ProcessSoccerData()
        self.dictionary_df = self.soccer_data.get_dictionary_df()
        # self.input_data_df = self.soccer_data.get_matches_df()
        self.scraped_match_data_df = Feature_Engineering._get_scraped_match_data_df()
        self.feature_df = self._calculate_feature_df()
        # self.label_df = self._calculate_label_df
    
    # transform the scraped match data json into a dataframe
    # the scraped data is 2015 - 2020 (for now as takes too long to scrape locally )
    @staticmethod
    def _get_scraped_match_data_df():
        scraped_data_dict = Scrape_Soccer_Data.read_data('../data/matches_data')    
        scraped_df = pd.DataFrame.from_records(scraped_data_dict).transpose().reset_index()
        scraped_df.rename(columns = {'index':'Match_id'}, inplace = True)
        scraped_df[['Match_id']] = scraped_df[['Match_id']].apply(pd.to_numeric)
        return scraped_df
                
    def _calculate_feature_df(self):
        feature_dfs = {} #dict of dfs to  concat at end
        for i, (key, df) in enumerate(self.dictionary_df.items()): 
            feature_df = df.apply(lambda x: self._get_feature_data(x, df), axis = 1)
            
            feature_dfs[key] = feature_df
            print(feature_df)
            if i == 0:
                break
            
            # feature_df.insert(0, 'Home_Team', self.df_all_data['Home_Team']) 
            # feature_df.insert(1, 'Away_Team', self.df_all_data['Away_Team'])
            # feature_df.insert(2, 'Round', self.df_all_data['Round'])
            # feature_df.insert(3, 'Season', self.df_all_data['Season'])

            
        # self.feature_df = pd.concat(dictionary_feature_dfs.values(), ignore_index=True)
     
    # calculate feature data for the given row(match) 
    def _get_feature_data(self, row, df):
        feature_df = pd.DataFrame()
        home_team = row.Home_Team
        away_team = row.Away_Team
        round = row.Round
        home_team_goals_scored_previous_matches = Feature_Engineering._get_goals_previous_matches(df, home_team, round, type='scored')
        away_team_goals_scored_previous_matches = Feature_Engineering._get_goals_previous_matches(df, away_team, round, type='scored')
        home_team_goals_conceded_previous_matches = self._get_goals_previous_matches(df, home_team, round, type='conceded')
        away_team_goals_conceded_previous_matches = self._get_goals_previous_matches(df, away_team, round, type='conceded')
        feature_df.loc[0, 'HT_goals_scored_prev_n_matches'] = home_team_goals_scored_previous_matches
        feature_df.loc[0, 'AT_goals_scored_prev_n_matches'] = away_team_goals_scored_previous_matches
        feature_df.loc[0, 'HT_goals_conceded_prev_n_matches'] = home_team_goals_conceded_previous_matches
        feature_df.loc[0, 'AT_goals_conceded_prev_n_matches'] = away_team_goals_conceded_previous_matches
        return feature_df.loc[0]  

        # feature_df.loc[0, 'Home_GD'] = home_team_goals_scored_previous_matches - home_team_goals_conceded_previous_matches
        # feature_df.loc[0, 'Away_GD'] = away_team_goals_scored_previous_matches - away_team_goals_conceded_previous_matches
        # get goals from previous matches in the league for the team specified. (type is scored or conceded)

 

    @staticmethod
    def _get_goals_previous_matches(df, team_name, round, type='scored'):
        all_matches_for_team_df = df[(df['Home_Team'] == team_name) | (df['Away_Team'] == team_name)]
        previous_matches_df = all_matches_for_team_df[all_matches_for_team_df['Round'] < round].sort_values(by='Round', ascending=False).iloc[0:NO_PREV_MATCHES_TO_CALULATE_AVERAGE_FROM,:]
        if type == 'scored':
            return Feature_Engineering._get_goals_scored(df, previous_matches_df, team_name)
        else:
            return Feature_Engineering._get_goals_conceded(df, previous_matches_df, team_name)
        
    @staticmethod     
    def _get_goals_scored(df, previous_matches_df, team_name):
        previous_home_goals_scored = int(previous_matches_df.Home_Goals[previous_matches_df.Home_Team == team_name].sum())
        previous_away_goals_scored = int(previous_matches_df.Away_Goals[previous_matches_df.Away_Team == team_name].sum())
        return (previous_home_goals_scored + previous_away_goals_scored)
  
    @staticmethod
    def _get_goals_conceded(df, previous_matches_df, team_name):
        previous_home_goals_conceded = int(previous_matches_df.Home_Goals[previous_matches_df.Away_Team == team_name].sum())
        previous_away_goals_conceded = int(previous_matches_df.Away_Goals[previous_matches_df.Home_Team == team_name].sum())
        return (previous_home_goals_conceded + previous_away_goals_conceded)  

    
    
    
    ##### Public #### 
    # inner join of the dataframe passed in and scraped_match_data_df     
    def get_df_incl_scraped_data(self, df):
        return pd.merge(df, self.scraped_match_data_df, on='Match_id').dropna()
    
    # # just the input_df without the scraped data   
    # def get_df_excl_scraped_data(self):
    #     return self.input_data_df    
#%%
feature_eng = Feature_Engineering()

#%%        

        
    # def _calculate_feature_df(self):
    #     dictionary_feature_dfs = {}
    #     for key, df in self.df_dictionary.items(): 
    #         feature_df = df.apply(lambda x: self._get_feature_data(x, df), axis = 1)
            
            
    #         # feature_df.insert(0, 'Home_Team', self.df_all_data['Home_Team']) 
    #         # feature_df.insert(1, 'Away_Team', self.df_all_data['Away_Team'])
    #         # feature_df.insert(2, 'Round', self.df_all_data['Round'])
    #         # feature_df.insert(3, 'Season', self.df_all_data['Season'])
            
    #         # dictionary_feature_dfs[key] = feature_df
            
    #     # self.feature_df = pd.concat(dictionary_feature_dfs.values(), ignore_index=True)
      
    
    # calculate feature data for the given row(match) in the df_all_data dataframe 
    # def _get_feature_data(self, row, df):
    #     feature_df = pd.DataFrame()
    #     home_team = row.Home_Team
    #     away_team = row.Away_Team
    #     round = row.Round
        
        
        
        # home_team_goals_scored_previous_matches = self.get_goals_previous_matches(df, home_team, round, type='scored')
        # away_team_goals_scored_previous_matches = self.get_goals_previous_matches(away_team, round, num_previous_matches=2, type='scored')
        # home_team_goals_conceded_previous_matches = self.get_goals_previous_matches(home_team, round, num_previous_matches=2, type='conceded')
        # away_team_goals_conceded_previous_matches = self.get_goals_previous_matches(away_team, round, num_previous_matches=2, type='conceded')
        # feature_df = pd.DataFrame()
        # # Home_GD - goal diff over previous matches - make ex weighted average
        # feature_df.loc[0, 'HomeTeam_Goals_Scored'] = home_team_goals_scored_previous_matches
        # feature_df.loc[0, 'AwayTeam_Goals_Scored'] = away_team_goals_scored_previous_matches
        # feature_df.loc[0, 'HomeTeam_Goals_Conceded'] = home_team_goals_conceded_previous_matches
        # feature_df.loc[0, 'AwayTeam_Goals_Conceded'] = away_team_goals_conceded_previous_matches
    #     feature_df.loc[0, 'Home_GD'] = home_team_goals_scored_previous_matches - home_team_goals_conceded_previous_matches
    #     feature_df.loc[0, 'Away_GD'] = away_team_goals_scored_previous_matches - away_team_goals_conceded_previous_matches
    #     return feature_df.loc[0] 

    # # get goals from previous matches in the league for the team specified. (type is scored or conceded)
    # def get_goals_previous_matches(self, team_name, round, type='scored'):  
    #     all_matches_for_team_df = self.input_df[(self.input_df['Home_Team'] == team_name) | (self.input_df['Away_Team'] == team_name)]
    #     previous_matches_df = all_matches_for_team_df[all_matches_for_team_df['Round'] < round]  
    #     if type == 'scored':
    #         return PrepareSoccerData.get_goals_scored(previous_matches_df, team_name)
    #     else:
    #         return PrepareSoccerData.get_goals_conceded(previous_matches_df, team_name)
        
    # @staticmethod     
    # def get_goals_scored(previous_matches_df, team_name):
    #     previous_home_goals_scored = int(previous_matches_df.Home_goals[previous_matches_df.Home_Team == team_name].sum())
    #     previous_away_goals_scored = int(previous_matches_df.Away_goals[previous_matches_df.Away_Team == team_name].sum())
    #     return (previous_home_goals_scored + previous_away_goals_scored)
  
    # @staticmethod
    # def get_goals_conceded(previous_matches_df, team_name):
    #     previous_home_goals_conceded = int(previous_matches_df.Home_goals[previous_matches_df.Away_Team == team_name].sum())
    #     previous_away_goals_conceded = int(previous_matches_df.Away_goals[previous_matches_df.Home_Team == team_name].sum())
    #     return (previous_home_goals_conceded + previous_away_goals_conceded)  

#%%
###################
    # utility function for below function 
    @staticmethod
    def _df_for_seasons(df, season_min, season_max):
        return df[(df['Season'] >= season_min) & (df['Season'] <= season_max)]

    def all_data_df(self, include_scraped_data=False, season_min=1991, season_max=2021):
        if include_scraped_data == False:
            
            return self.all_data_df if season_min == 1990 and season_max == 2021 else Feature_Engineering._df_for_seasons(self.df_all_data, season_min, season_max)
        else:        
            temp_df = self.all_data_df[self.all_data_df['League'].isin(leagues)]
            return temp_df if season_min == 1990 and season_max == 2021 else Feature_Engineering._df_for_seasons(temp_df, season_min, season_max)
 
        
        
        
        if include_scraped_data:
            
        return self.all_data_df
    
    def feature_df(self, include_scraped_data=False, season_min=1991, season_max=2021):
        return self.feature_df
    
    def label_df(self, include_scraped_data=False, season_min=1991, season_max=2021):
        return self.label_df
####################

    # return a dataframe of matches with options to filter by league and season  
    def get_matches_df(self, leagues='ALL', season_min=1990, season_max=2021):        
        if leagues == 'ALL':
            return self.df_all_data if season_min == 1990 and season_max == 2021 else Feature_Engineering._df_for_seasons(self.df_all_data, season_min, season_max)
        else:        
            temp_df = self.df_all_data[self.df_all_data['League'].isin(leagues)]
            return temp_df if season_min == 1990 and season_max == 2021 else Feature_Engineering._df_for_seasons(temp_df, season_min, season_max)
#%%

# %%
soccer_data = ProcessSoccerData()
input_data_df = soccer_data.get_matches_df()

# scraped_match_data_df = _get_scraped_match_data_df()
# %%
scraped_data_dict = Scrape_Soccer_Data.read_data('../data/matches_data')    
# %%
scraped_df = pd.DataFrame.from_records(scraped_data_dict).transpose().reset_index()
scraped_df.rename(columns = {'index':'Match_id'}, inplace = True)
scraped_df[['Match_id']] = scraped_df[['Match_id']].apply(pd.to_numeric)

#%%

