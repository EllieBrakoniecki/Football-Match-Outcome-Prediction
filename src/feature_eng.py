#%%
from initial_data_processing import ProcessSoccerData
from scraper import Scrape_Soccer_Data
import pandas as pd
import os

#%%
NO_PREV_MATCHES_TO_CALULATE_AVERAGE_FROM = 5

class Feature_Engineering: 
    def __init__(self):
        self.soccer_data = ProcessSoccerData()
        self.dictionary_df = self.soccer_data.get_dictionary_df()
        # self.input_data_df = self.soccer_data.get_matches_df()
        self.scraped_match_data_df = Feature_Engineering._get_scraped_match_data_df()
        self.calculated_features_df = self._calculate_feature_df()
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
        path = '../data/calc_features.csv'
        if os.path.exists(path):
            return pd.read_csv(path)        
        feature_dfs = {} #dict of dfs to  concat at end
        for i, (key, df) in enumerate(self.dictionary_df.items()): 
            feature_dfs[key] = df.apply(lambda x: self._get_feature_data(x, df), axis = 1) 
            Feature_Engineering.save_df_as_csv(path)          
            if i == 1:
                break
        return pd.concat(feature_dfs.values(), ignore_index=True)
             
    # calculate feature data for the given row(match) 
    def _get_feature_data(self, row, df):
        feature_df = pd.DataFrame()
        home_team = row.Home_Team
        away_team = row.Away_Team
        round = row.Round
        feature_df = pd.DataFrame()
        feature_df.loc[0, 'Match_id'] = row.Match_id
        feature_df.loc[0, 'Round'] = round
        # all goals scored/conceded by home and away team over n previous matches  
        feature_df.loc[0, 'HomeTeam_Goals_Scored'] = Feature_Engineering.get_all_goals_previous_matches(df, home_team, round, type='scored')
        feature_df.loc[0, 'AwayTeam_Goals_Scored'] = Feature_Engineering.get_all_goals_previous_matches(df, away_team, round, type='scored')
        feature_df.loc[0, 'HomeTeam_Goals_Conceded'] = Feature_Engineering.get_all_goals_previous_matches(df, home_team, round, type='conceded')
        feature_df.loc[0, 'AwayTeam_Goals_Conceded'] = Feature_Engineering.get_all_goals_previous_matches(df, away_team, round, type='conceded')        
        # calculating attack and defense coeffs for both teams at home and away
        feature_df.loc[0, 'HomeTeam_Attack_Coeff'] = Feature_Engineering.get_home_team_coeff(df, home_team, round, type='attack')
        feature_df.loc[0, 'HomeTeam_Defense_Coeff'] = Feature_Engineering.get_home_team_coeff(df, home_team, round, type='defense')
        feature_df.loc[0, 'AwayTeam_Attack_Coeff'] = Feature_Engineering.get_away_team_coeff(df, away_team, round, type='attack')
        feature_df.loc[0, 'AwayTeam_Defense_Coeff'] = Feature_Engineering.get_away_team_coeff(df, away_team, round, type='defense')
        return feature_df.loc[0] 
        
    # get goals from previous matches in the league for the team specified. (type is scored or conceded)
    @staticmethod
    def get_all_goals_previous_matches(df, team_name, round, type='scored'):
        all_matches_for_team_df = df[(df['Home_Team'] == team_name) | (df['Away_Team'] == team_name)]
        previous_matches_df = all_matches_for_team_df[all_matches_for_team_df['Round'] < round].sort_values(by='Round', ascending=False).iloc[0:NO_PREV_MATCHES_TO_CALULATE_AVERAGE_FROM,:]
        if type == 'scored':
            return Feature_Engineering.get_goals_scored(df, previous_matches_df, team_name)
        else:
            return Feature_Engineering.get_goals_conceded(df, previous_matches_df, team_name)
        
    @staticmethod     
    def get_goals_scored(df, previous_matches_df, team_name):
        previous_home_goals_scored = int(previous_matches_df.Home_Goals[previous_matches_df.Home_Team == team_name].sum())
        previous_away_goals_scored = int(previous_matches_df.Away_Goals[previous_matches_df.Away_Team == team_name].sum())
        return (previous_home_goals_scored + previous_away_goals_scored)
  
    @staticmethod
    def get_goals_conceded(df, previous_matches_df, team_name):
        previous_home_goals_conceded = int(previous_matches_df.Home_Goals[previous_matches_df.Away_Team == team_name].sum())
        previous_away_goals_conceded = int(previous_matches_df.Away_Goals[previous_matches_df.Home_Team == team_name].sum())
        return (previous_home_goals_conceded + previous_away_goals_conceded)  

    # get goals scored and conceded by the home team at home, av goals scored and conceded at home over the whole league for the same time and divide to find the coeff
    @staticmethod   
    def get_home_team_coeff(df, team_name, round, type='attack'):
        all_home_matches_for_team_df = df[(df['Home_Team'] == team_name)]
        previous_matches_df = all_home_matches_for_team_df[all_home_matches_for_team_df['Round'] < round].sort_values(by='Round', ascending=False).iloc[0:NO_PREV_MATCHES_TO_CALULATE_AVERAGE_FROM,:]        
        league_previous_matches = df[df['Round'] < round].sort_values(by='Round', ascending=False)
        rounds = list(previous_matches_df.Round.unique())
        if len(rounds) != 0: 
            league_previous_matches = league_previous_matches[(league_previous_matches['Round'] >= min(rounds)) & (league_previous_matches['Round'] <= max(rounds))]
        avg_home_goals_scored_for_period = league_previous_matches.Home_Goals.mean()    
        avg_home_goals_conceded_for_period = league_previous_matches.Away_Goals.mean() 
        goals = 0
        if type == 'attack':
            return (int(previous_matches_df.Home_Goals.sum())/NO_PREV_MATCHES_TO_CALULATE_AVERAGE_FROM) / avg_home_goals_scored_for_period
        elif type == 'defense':
            return (int(previous_matches_df.Away_Goals.sum())/NO_PREV_MATCHES_TO_CALULATE_AVERAGE_FROM) / avg_home_goals_conceded_for_period

    # get goals scored and conceded by the away team away, av goals scored and conceded away over the whole league for the same time and divide to find the coeff
    @staticmethod   
    def get_away_team_coeff(df, team_name, round, type='attack'):
        all_away_matches_for_team_df = df[(df['Away_Team'] == team_name)]
        previous_matches_df = all_away_matches_for_team_df[all_away_matches_for_team_df['Round'] < round].sort_values(by='Round', ascending=False).iloc[0:NO_PREV_MATCHES_TO_CALULATE_AVERAGE_FROM,:]
        league_previous_matches = df[df['Round'] < round].sort_values(by='Round', ascending=False)
        rounds = list(previous_matches_df.Round.unique())
        if len(rounds) != 0: 
            league_previous_matches = league_previous_matches[(league_previous_matches['Round'] >= min(rounds)) & (league_previous_matches['Round'] <= max(rounds))]
        avg_away_goals_scored_for_period = league_previous_matches.Home_Goals.mean()    
        avg_away_goals_conceded_for_period = league_previous_matches.Away_Goals.mean() 
        goals = 0
        if type == 'attack':
            return (int(previous_matches_df.Away_Goals.sum())/NO_PREV_MATCHES_TO_CALULATE_AVERAGE_FROM) / avg_away_goals_scored_for_period
        elif type == 'defense':
            return (int(previous_matches_df.Home_Goals.sum())/NO_PREV_MATCHES_TO_CALULATE_AVERAGE_FROM) / avg_away_goals_conceded_for_period

    # get goals scored and conceded by the away team away
    @staticmethod
    def get_away_goals_previous_matches(df, team_name, round, type='scored'):
        all_away_matches_for_team_df = df[(df['Away_Team'] == team_name)]
        previous_matches_df = all_away_matches_for_team_df[all_away_matches_for_team_df['Round'] < round].sort_values(by='Round', ascending=False).iloc[0:NO_PREV_MATCHES_TO_CALULATE_AVERAGE_FROM,:]
        if type == 'scored':
            return int(previous_matches_df.Away_Goals.sum())
        elif type == 'conceded':
            return int(previous_matches_df.Home_Goals.sum())
        
    @staticmethod
    def save_df_as_csv(df, path):
        df.to_csv (path, index = None, header=True) 

        
    
    ##### Public #### 
    # inner join of the dataframe passed in and scraped_match_data_df     
    # def get_df_incl_scraped_data(self, df):
    #     return pd.merge(df, self.scraped_match_data_df, on='Match_id').dropna()
    
    # def get_df_for_model(self, incl_scraped_data=False):
    #     if incl_scraped_data:
    #         pass
            # return self.get_df_incl_scraped_data(feature_df? )
    # # just the input_df without the scraped data   
    # def get_df_excl_scraped_data(self):
    #     return self.input_data_df    
#%%
feature_eng = Feature_Engineering()
        
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

feature_eng.calculated_features_df.to_csv('../data/test.csv')
# df.to_csv (r'C:\Users\John\Desktop\export_dataframe.csv', index = None, header=True) 

# %%
