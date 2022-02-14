#%%
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath('../__file__'))
DATA_DIR = os.path.join(BASE_DIR, 'Football-Dataset/')
 
# Process, clean and prepare soccer data for machine learning models 
class ProcessSoccerData:
    def __init__(self):
        self.df_dictionary = {} #dictionary of dataframes, 1 for each league/season
        self._set_df_dictionary() #populate df_dictionary attribute
        self.df_all_data = pd.DataFrame() #dataframe of all data 
        self._set_df_all_data() #populate df_all_data
                
    def _set_df_dictionary(self):
        for (dirpath, dirnames, filenames) in os.walk(DATA_DIR):
            for filename in filenames:
                if filename != '.DS_Store':
                    self.df_dictionary[filename[:-4]] = pd.read_csv(dirpath + '/' + filename)
        self._remove_empty_dfs_and_duplicates()
        self._add_match_ids()
        self._add_calculated_columns()
                    
    def _remove_empty_dfs_and_duplicates(self):
        dfs_to_remove = []
        for key, df in self.df_dictionary.items():
            duplicates = df[df.duplicated(subset='Link')]
            if df.empty or not duplicates.empty:
                dfs_to_remove.append(key)
        for key in dfs_to_remove:        
            self.df_dictionary.pop(key) 
            
    def _add_match_ids(self):
        i = 1
        for key, value in self.df_dictionary.items():
            j = i+len(value.index)
            ids = list(range(i, j))
            value.insert(0, 'Match_id', ids)  
            # value.set_index("Match_id", inplace = True)
            i=j        
                    
    # add columns that are functions of the basic data (Home goals, away goals, goal difference etc)
    # and match result which we will use to predict as our label data
    def _add_calculated_columns(self):
        for key, df in self.df_dictionary.items():    
            df[['Home_Goals', 'Away_Goals']] = df['Result'].str.split('-', expand=True)
            ProcessSoccerData._remove_invalid_rows(df)
            df[['Home_Goals', 'Away_Goals', 'Round', 'Season']] = df[['Home_Goals', 'Away_Goals', 'Round', 'Season']].apply(pd.to_numeric)
            df['Match_Goal_Difference'] = df['Home_Goals'] - df['Away_Goals']
            df['Match_Result'] = (df['Match_Goal_Difference']).apply(ProcessSoccerData._match_result_from_goals)
            df['Points_Home_Team'] = (df['Match_Result']).apply(ProcessSoccerData._points_from_match_result, home=True) 
            df['Points_Away_Team'] = (df['Match_Result']).apply(ProcessSoccerData._points_from_match_result, home=False) 
    
    @staticmethod
    def _remove_invalid_rows(df):
        errors = pd.to_numeric(df['Home_Goals'], errors='coerce').isnull()
        e = errors.loc[errors==True]
        df.drop(e.index.to_list(), inplace=True)
        
    #calculate the match result ('H', 'A' or 'D')
    @staticmethod
    def _match_result_from_goals(goal_difference):
        if goal_difference > 0:
            return 'H'
        return 'A' if goal_difference < 0 else 'D'
    
    #calculate points per match for each team
    @staticmethod
    def _points_from_match_result(match_result, home):    
        if match_result == 'D':
            return 1 
        else:
            return 3 if ((match_result == 'H' and home == True) or (match_result == 'A' and home == False)) else 0
    
    def _set_df_all_data(self):
        self.df_all_data = pd.concat(self.df_dictionary.values(), ignore_index=True)


############################################################################################   
    def get_dictionary_df(self):
        return self.df_dictionary
  
    # return a dataframe of matches with options to filter by league and season  
    def get_matches_df(self, leagues='ALL', season_min=1990, season_max=2021):        
        if leagues == 'ALL':
            return self.df_all_data if season_min == 1990 and season_max == 2021 else ProcessSoccerData._df_for_seasons(self.df_all_data, season_min, season_max)
        else:        
            temp_df = self.df_all_data[self.df_all_data['League'].isin(leagues)]
            return temp_df if season_min == 1990 and season_max == 2021 else ProcessSoccerData._df_for_seasons(temp_df, season_min, season_max)
    
    # utility function for above function 
    @staticmethod
    def _df_for_seasons(df, season_min, season_max):
        return df[(df['Season'] >= season_min) & (df['Season'] <= season_max)]

    # return a list of all leagues
    def all_league_names(self):
        return list(self.df_all_data['League'].unique())

    # return a list of teams in the specified league
    def teams_in_league(self, league):
        temp_df = self.df_all_data[self.df_all_data['League'] == league]
        return list(temp_df['Home_Team'].unique())         



# %%
