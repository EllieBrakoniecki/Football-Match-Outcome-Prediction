#%%
from initial_data_processing import ProcessSoccerData
from scraper import Scrape_Soccer_Data
import pandas as pd
import os

#%%
NO_PREV_MATCHES_TO_CALULATE_AVERAGE_FROM = 5

class Feature_Engineering: 
    def __init__(self, calc_features=False):
        self.soccer_data = ProcessSoccerData()
        self.dictionary_df = self.soccer_data.get_dictionary_df()
        self.input_data_df = self.soccer_data.get_matches_df()
        self.scraped_match_data_df = Feature_Engineering._get_scraped_match_data_df()
        self.feature_df = self._calculate_feature_df(calc_features)
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
                
    def _calculate_feature_df(self, calc_features):
        path = '../data/calc_features.csv'
        if not calc_features:
            if os.path.exists(path): # if calc_features is false get the features from csv that have been calculated previously
                return pd.read_csv(path)        
        feature_dfs = {} #dict of dfs to  concat at end
        for i, (key, df) in enumerate(self.dictionary_df.items()): 
            feature_dfs[key] = df.apply(lambda x: self._get_feature_data(x, df), axis = 1)          
            # if i == 0:
            #     break
        df = pd.concat(feature_dfs.values(), ignore_index=True)
        Feature_Engineering._save_df_as_csv(df,path) 
        return df
             
    # calculate feature data for the given row(match) 
    def _get_feature_data(self, row, df):
        feature_df = pd.DataFrame()
        home_team = row.Home_Team
        away_team = row.Away_Team
        round = row.Round
        match_id = row.Match_id
        feature_df = pd.DataFrame()
        feature_df.loc[0, 'Match_id'] = match_id
        feature_df.loc[0, 'Round'] = round
        # all goals scored/conceded by home and away team over n previous matches  
        feature_df.loc[0, 'HomeTeam_Goals_Scored'] = Feature_Engineering.get_all_goals_previous_matches(df, home_team, round, type='scored')
        feature_df.loc[0, 'AwayTeam_Goals_Scored'] = Feature_Engineering.get_all_goals_previous_matches(df, away_team, round, type='scored')
        feature_df.loc[0, 'HomeTeam_Goals_Conceded'] = Feature_Engineering.get_all_goals_previous_matches(df, home_team, round, type='conceded')
        feature_df.loc[0, 'AwayTeam_Goals_Conceded'] = Feature_Engineering.get_all_goals_previous_matches(df, away_team, round, type='conceded')        
        # calculating attack and defense coeffs for both teams at home and away
        feature_df.loc[0, 'HomeTeam_Attack_Coeff'] = Feature_Engineering.get_home_team_coeff(df, home_team, round, match_id, type='attack')
        feature_df.loc[0, 'HomeTeam_Defense_Coeff'] = Feature_Engineering.get_home_team_coeff(df, home_team, round, match_id, type='defense')
        feature_df.loc[0, 'AwayTeam_Attack_Coeff'] = Feature_Engineering.get_away_team_coeff(df, away_team, round, match_id, type='attack')
        feature_df.loc[0, 'AwayTeam_Defense_Coeff'] = Feature_Engineering.get_away_team_coeff(df, away_team, round, match_id, type='defense')

        #calculating length of each teams win/lose/draw streak 
        H_win_streak, H_loss_streak, H_draw_streak = Feature_Engineering.get_streaks_for_team(df, home_team, match_id)
        feature_df.loc[0, 'HomeTeam_Win_Streak'] = H_win_streak
        feature_df.loc[0, 'HomeTeam_Loss_Streak'] = H_loss_streak
        feature_df.loc[0, 'HomeTeam_Draw_Streak'] = H_draw_streak    
        A_win_streak, A_loss_streak, A_draw_streak = Feature_Engineering.get_streaks_for_team(df, away_team, match_id)
        feature_df.loc[0, 'AwayTeam_Win_Streak'] = A_win_streak
        feature_df.loc[0, 'AwayTeam_Loss_Streak'] = A_loss_streak
        feature_df.loc[0, 'AwayTeam_Draw_Streak'] = A_draw_streak             
        return feature_df.loc[0] 
    
    # gets the win/loss/draw streak from the previous games for the team specified 
    @staticmethod
    def get_streaks_for_team(df, team_name, match_id):
        home_matches_team = df[(df['Home_Team'] == team_name)]
        away_matches_team = df[(df['Away_Team'] == team_name)]
        home_matches_team['Points'] = home_matches_team.Points_Home_Team
        away_matches_team['Points'] = away_matches_team.Points_Away_Team
        df = pd.concat([home_matches_team,away_matches_team], ignore_index=True).sort_values('Match_id').reset_index()
        df['streak_start'] = df.Points.ne(df.Points.shift())
        df['id_of_streak'] = df['streak_start'].cumsum()
        df['counter'] = df.groupby('id_of_streak').cumcount() + 1
        win_streak, loss_streak, draw_streak = 0, 0, 0
        prev_index = (df.index[df['Match_id']==match_id]).tolist()[0] - 1
        if prev_index > 0:
            points = df['Points']
            points_at_prev_index = int(points[prev_index])
            streak_count = df['counter']
            streak_count_at_prev_index = int(streak_count[prev_index])        
            if points_at_prev_index == 3:
                win_streak = streak_count_at_prev_index
            elif points_at_prev_index == 0:
                loss_streak = streak_count_at_prev_index
            else:
                draw_streak = streak_count_at_prev_index
        return win_streak, loss_streak, draw_streak    
        
    # get goals from previous matches in the league for the team specified.
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
    def get_home_team_coeff(df, team_name, round, match_id, type='attack'):
        all_home_matches_for_team_df = df[(df['Home_Team'] == team_name)]
        previous_matches_df = all_home_matches_for_team_df[all_home_matches_for_team_df['Round'] < round].sort_values(by='Round', ascending=False).iloc[0:NO_PREV_MATCHES_TO_CALULATE_AVERAGE_FROM,:]        
        league_previous_matches = df[df['Round'] < round].sort_values(by='Round', ascending=False)
        rounds = list(previous_matches_df.Round.unique())
        if len(rounds) != 0: 
            league_previous_matches = league_previous_matches[(league_previous_matches['Round'] >= min(rounds)) & (league_previous_matches['Round'] <= max(rounds))]
        avg_home_goals_scored_for_period = league_previous_matches.Home_Goals.mean()    
        avg_home_goals_conceded_for_period = league_previous_matches.Away_Goals.mean()
        try:
            if type == 'attack':
                return (int(previous_matches_df.Home_Goals.sum())/NO_PREV_MATCHES_TO_CALULATE_AVERAGE_FROM) / avg_home_goals_scored_for_period
            elif type == 'defense':
                return (int(previous_matches_df.Away_Goals.sum())/NO_PREV_MATCHES_TO_CALULATE_AVERAGE_FROM) / avg_home_goals_conceded_for_period
        except:
            print('Error calculating coeff for match_id:', match_id)

    # get goals scored and conceded by the away team away, av goals scored and conceded away over the whole league for the same time and divide to find the coeff
    @staticmethod   
    def get_away_team_coeff(df, team_name, round, match_id, type='attack'):
        all_away_matches_for_team_df = df[(df['Away_Team'] == team_name)]
        previous_matches_df = all_away_matches_for_team_df[all_away_matches_for_team_df['Round'] < round].sort_values(by='Round', ascending=False).iloc[0:NO_PREV_MATCHES_TO_CALULATE_AVERAGE_FROM,:]
        league_previous_matches = df[df['Round'] < round].sort_values(by='Round', ascending=False)
        rounds = list(previous_matches_df.Round.unique())
        if len(rounds) != 0: 
            league_previous_matches = league_previous_matches[(league_previous_matches['Round'] >= min(rounds)) & (league_previous_matches['Round'] <= max(rounds))]
        avg_away_goals_scored_for_period = league_previous_matches.Home_Goals.mean()    
        avg_away_goals_conceded_for_period = league_previous_matches.Away_Goals.mean() 
        try:
            if type == 'attack':
                return (int(previous_matches_df.Away_Goals.sum())/NO_PREV_MATCHES_TO_CALULATE_AVERAGE_FROM) / avg_away_goals_scored_for_period
            elif type == 'defense':
                return (int(previous_matches_df.Home_Goals.sum())/NO_PREV_MATCHES_TO_CALULATE_AVERAGE_FROM) / avg_away_goals_conceded_for_period
        except:
            print('Error calculating coeff for match_id:', match_id)


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
    def _save_df_as_csv(df, path):
        df.to_csv (path, index = None, header=True) 

    # Join dataframes on Match_id column and drop and NaN's 
    @staticmethod
    def _merge_dfs(df1, df2):
        return pd.merge(df1, df2, on='Match_id').dropna()
      
    @staticmethod
    def _df_for_seasons(df, season_min, season_max):
        return df[(df['Season'] >= season_min) & (df['Season'] <= season_max)]

    # return a dataframe of matches with options to filter by league and season 
    @staticmethod 
    def _get_matches_df(df, leagues, season_min, season_max):        
        if leagues == 'ALL':
            return df if season_min == 1990 and season_max == 2021 else Feature_Engineering._df_for_seasons(df, season_min, season_max)
        else:        
            temp_df = df[df['League'].isin(leagues)]
            return temp_df if season_min == 1990 and season_max == 2021 else Feature_Engineering._df_for_seasons(temp_df, season_min, season_max)

###################### Public functions ###########################

    # gets all the data for the given value of the params. Note that if include_scraped_data 
    # is set to true only years 2015-2021 will be returned as this is only years that
    # have been scraped so far
    def get_data(self, include_scraped_data=False, leagues='ALL', season_min=1991, season_max=2021):
        df = Feature_Engineering._merge_dfs(self.input_data_df, self.feature_df)         
        if include_scraped_data:
            df = Feature_Engineering._merge_dfs(df, self.scraped_match_data_df)
        return Feature_Engineering._get_matches_df(df, leagues, season_min, season_max )
        # return df
    
    def get_scraped_data(self):
        return self.scraped_match_data_df
           
    # return a list of all leagues
    def all_league_names(self, df):
        return list(df['League'].unique())

    # return a list of teams in the specified league
    @staticmethod
    def teams_in_league(df, league):
        temp_df = df[df['League'] == league]
        return list(temp_df['Home_Team'].unique())    
          
#%%
feature_eng = Feature_Engineering(calc_features=True)


#%%
# df = feature_eng.dictionary_df['Results_1997_serie_b']
# home_team = 'Chievo'
# #%%
# home_matches_for_team_df = df[(df['Home_Team'] == home_team)]
# away_matches_for_team_df = df[(df['Away_Team'] == home_team)]
# #%%
# home_matches_for_team_df['Points'] = home_matches_for_team_df.Points_Home_Team
# away_matches_for_team_df['Points'] = away_matches_for_team_df.Points_Away_Team
# df = pd.concat([home_matches_for_team_df,away_matches_for_team_df], ignore_index=True).sort_values('Match_id').reset_index()
# #%%
# df['start_of_streak'] = df.Points.ne(df.Points.shift())
# df['streak_id'] = df['start_of_streak'].cumsum()
# df['streak_counter'] = df.groupby('streak_id').cumcount() + 1
# # df.to_csv('../data/test.csv')
# #%%
# prev_index = (df.index[df['Match_id']==131332]).tolist()[0] -1
# # if prev_index>0:
# points = df['Points']
# points_at_prev_index = points[prev_index] 
#
