#%%
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

pd.options.display.max_columns = 10
pd.options.display.max_colwidth = 1000

# dictionary_df = {} # a dictionary of dataframes, 1 for each football league

# ## Get the data from each league and put in a df
# football_data_path = '../Football-Dataset/'
# for (dirpath, dirnames, filenames) in os.walk(football_data_path):
#     for filename in filenames:
#         if filename != '.DS_Store':
#             dictionary_df[filename[:-4]] = pd.read_csv(dirpath + '/' + filename)

# number_of_datasets = len(dictionary_df) # 448
# # remove empty dataframes from the dictionary:
# empty_dataframes = [key for key, value in dictionary_df.items() if value.empty]
# for key in empty_dataframes:
#     dictionary_df.pop(key)        
# number_of_datasets = len(dictionary_df) # 404  
##################################################################

# # calculate the match result ('H', 'A' or 'D')
# def match_result_from_goals(HG_subtract_AG):
#     if HG_subtract_AG > 0:
#         return 'H'
#     elif HG_subtract_AG < 0:
#         return 'A'
#     else:
#         return 'D'

# # add a match id col and check for missing/invalid data:

# i = 1
# for key, value in dictionary_df.items():
#     j = i+len(value.index)
#     ids = list(range(i, j))
#     # value['Match_id'] = ids
#     # match_id = [uuid.uuid4() for _ in range(len(value.index))]  
#     value.insert(0, 'Match_id', ids)  
#     value.set_index("Match_id", inplace = True)
#     i=j
    
#     value[['Home_goals', 'Away_goals']] = value['Result'].str.split('-', expand=True)
#     # # convert data type of home goals/ away goals to numeric, need to remove a few rows where the data is ambiguous 
#     errors = pd.to_numeric(value['Home_goals'], errors='coerce').isnull()
#     e = errors.loc[errors==True]
#     # drop rows where there is an invalid format 
#     value.drop(e.index.to_list(), inplace=True)
#     value[['Home_goals', 'Away_goals']] = value[['Home_goals', 'Away_goals']].apply(pd.to_numeric)
#     # value.reset_index(inplace=True)
#     value['Match_result'] = (value['Home_goals'] - value['Away_goals']).apply(match_result_from_goals)
#     value[['Round']] = value[['Round']].apply(pd.to_numeric)

#     # match_data = value.apply(lambda x: get_match_data(x, value, x = 10), axis = 1)


#%%
class Matches_by_league_and_season:
    def __init__(self, league, input_df): # league is league/season change!
        self.league = league 
        self.input_df = input_df 
        self.season = self.input_df.at[1,'Season']
        self.feature_df = pd.DataFrame()
        self.label_df = pd.DataFrame()
        
    def get_match_data(self):
        self.feature_df = self.input_df.apply(lambda x: self.get_feature_data(x, self.input_df), axis = 1)
        # self.label_df = self.input_df.apply(lambda x: self.get_label_data(x, self.input_df), axis = 1)
        # return self.feature_df, self.label_df
        return self.feature_df
    
    # get features for the given row (match) in the input dataframe  
    def get_feature_data(self, row, round):
        round = row.Round
        home_team = row.Home_Team
        away_team = row.Away_Team
        # home_goals = row.Home_goals
        # away_goals = row.Away_goals
        # home_team_goals_scored_previous_matches = pd.Series(dtype='int64')
        home_team_goals_scored_previous_matches = self.get_goals_previous_matches(home_team, round, num_previous_matches=2, type='scored')
        away_team_goals_scored_previous_matches = self.get_goals_previous_matches(away_team, round, num_previous_matches=2, type='scored')
        home_team_goals_conceded_previous_matches = self.get_goals_previous_matches(home_team, round, num_previous_matches=2, type='conceded')
        away_team_goals_conceded_previous_matches = self.get_goals_previous_matches(away_team, round, num_previous_matches=2, type='conceded')
        feature_df = pd.DataFrame()
        # Home_GD - goal diff over previous matches - make ex weighted average
        feature_df.loc[0, 'HomeTeam_Goals_Scored'] = home_team_goals_scored_previous_matches
        feature_df.loc[0, 'AwayTeam_Goals_Scored'] = away_team_goals_scored_previous_matches
        feature_df.loc[0, 'HomeTeam_Goals_Conceded'] = home_team_goals_conceded_previous_matches
        feature_df.loc[0, 'AwayTeam_Goals_Conceded'] = away_team_goals_conceded_previous_matches
        feature_df.loc[0, 'Home_GD'] = home_team_goals_scored_previous_matches - home_team_goals_conceded_previous_matches
        feature_df.loc[0, 'Away_GD'] = away_team_goals_scored_previous_matches - away_team_goals_conceded_previous_matches
        return feature_df.loc[0] 

    # get goals from previous matches in the league for the team specified. (type is scored or conceded)
    def get_goals_previous_matches(self, team_name, round, num_previous_matches, type='scored'):  
        all_matches_for_team_df = self.input_df[(self.input_df['Home_Team'] == team_name) | (self.input_df['Away_Team'] == team_name)]
        previous_matches_df = all_matches_for_team_df[all_matches_for_team_df['Round'] < round]  
        if type == 'scored':
            return Matches_by_league_and_season.get_goals_scored(previous_matches_df, team_name)
        else:
            return Matches_by_league_and_season.get_goals_conceded(previous_matches_df, team_name)
        
    @staticmethod     
    def get_goals_scored(previous_matches_df, team_name):
        previous_home_goals_scored = int(previous_matches_df.Home_goals[previous_matches_df.Home_Team == team_name].sum())
        previous_away_goals_scored = int(previous_matches_df.Away_goals[previous_matches_df.Away_Team == team_name].sum())
        return (previous_home_goals_scored + previous_away_goals_scored)
  
    @staticmethod
    def get_goals_conceded(previous_matches_df, team_name):
        previous_home_goals_conceded = int(previous_matches_df.Home_goals[previous_matches_df.Away_Team == team_name].sum())
        previous_away_goals_conceded = int(previous_matches_df.Away_goals[previous_matches_df.Home_Team == team_name].sum())
        return (previous_home_goals_conceded + previous_away_goals_conceded)    
    
    # get all goals scored in previous games in the league
    # def get_all_goals_scored(self, df)
            
    def get_label_data(self):
        pass
    
#%%
########### EDA 
Av_home_goals = pd.DataFrame(columns=['League', 'Season', 'Average_home_goals', 'Average_away_goals'])
data = {}
for i, df in enumerate(dictionary_df.values()):
    Av_home_goals.loc[i] = [df.at[df.first_valid_index(), 'League']] + [df.at[df.first_valid_index(),'Season']]+[df.Home_goals.mean()]+[df.Away_goals.mean()]

# grp_by_league = Av_home_goals.groupby('League').mean().reset_index()
# plt.bar(grp_by_league['League'], grp_by_league['Average_home_goals'])  
# plt.bar(grp_by_league['League'], grp_by_league['Average_away_goals'])

# plot 1
Av_home_goals.groupby('League').mean().sort_values('Average_home_goals').plot(kind='barh')
plt.ylabel('League')
#plot 2
Av_home_goals[Av_home_goals['Season'] > 2015].groupby('League')['Average_home_goals', 'Average_away_goals'].mean().sort_values('Average_home_goals').plot(kind='barh')
    

#%%


###########    

#%%
########## *************************************************
dictionary_of_feature_dfs = {}
for league_season, df_results in dictionary_df.items():

    print('League and season:',league_season)
    matches = Matches_by_league_and_season(league_season, df_results)
    # feature_df, label_df = matches.get_match_data()
    feature_df = matches.get_match_data()
    feature_df.insert(0, 'Home_Team', matches.input_df['Home_Team'])  
    feature_df.insert(1, 'Away_Team', matches.input_df['Away_Team'])  
    feature_df.insert(2, 'Round', matches.input_df['Round'])  
    feature_df.insert(2, 'Match_result', matches.input_df['Match_result'])  


    
    last_round_df = feature_df[feature_df.Round == max(feature_df.Round)]

    # last_round_df['Home_GD'].hist()
    import matplotlib.pyplot as plt
    plt.bar(last_round_df['Home_Team'], last_round_df['Home_GD'])    
    plt.show()

    
    # feature_df['Home_EWA_GD'] = feature_df['Home_GD'].ewm(span=5, adjust=False).mean()
    
    x_cols = ['Home_GD', 'Away_GD']
    feature_df[x_cols].hist(figsize=(10,10))
    
    # feature_df.home_team_historical_goals_difference.ewm() !!
    # exponentially weighted moving average
    # dictionary_of_feature_dfs['league'] = feature_df 
    break

#$$$$$$$$$$
#https://github.com/Caldass/pl-matches-predictor/blob/master/feature_eng/feature_eng.py

# #make exponentially weighted average
# full_table['w_avg_points'] = full_table.points.ewm(span=3, adjust=False).mean()
# full_table['w_avg_goals'] = full_table.goals.ewm(span=3, adjust=False).mean()
# full_table['w_avg_goals_sf'] = full_table.goals_sf.ewm(span=3, adjust=False).mean()



#$$$$$$$$$$$$


####################################################################
  
#%%
from pathlib import Path  
filepath = Path('./out.csv')  
filepath.parent.mkdir(parents=True, exist_ok=True)  
feature_df.to_csv(filepath)   
#%%      
    
# for key, value in dictionary_df.items():
#     print('league:',key)
#     match_data = value.apply(lambda x: get_match_data(x, value, x = 10), axis = 1)
#     break
##########################################################









# def get_match_data(row, df, x = 10):
#     # match = Match
#     round = row.Round
#     home_team = row.Home_Team
#     away_team = row.Away_Team
    
    # #Get last x matches of home and away team
    # matches_home_team = get_last_matches(matches, date, home_team, x = 10)
    # matches_away_team = get_last_matches(matches, date, away_team, x = 10)
    
    # #Get last x matches of both teams against each other
    # last_matches_against = get_last_matches_against_eachother(matches, date, home_team, away_team, x = 3)
    
    # #Create goal variables
    # home_goals = get_goals(matches_home_team, home_team)
    # away_goals = get_goals(matches_away_team, away_team)
    # home_goals_conceided = get_goals_conceided(matches_home_team, home_team)
    # away_goals_conceided = get_goals_conceided(matches_away_team, away_team)
    
    # #Define result data frame
    # result = pd.DataFrame()
    
    # #Define ID features
    # result.loc[0, 'match_api_id'] = match.match_api_id
    # result.loc[0, 'league_id'] = match.league_id

    # #Create match features
    # result.loc[0, 'home_team_goals_difference'] = home_goals - home_goals_conceided
    # result.loc[0, 'away_team_goals_difference'] = away_goals - away_goals_conceided
    # result.loc[0, 'games_won_home_team'] = get_wins(matches_home_team, home_team) 
    # result.loc[0, 'games_won_away_team'] = get_wins(matches_away_team, away_team)
    # result.loc[0, 'games_against_won'] = get_wins(last_matches_against, home_team)
    # result.loc[0, 'games_against_lost'] = get_wins(last_matches_against, away_team)
    
    # #Return match features
    # return result.loc[0]

     
 
 
 
#%%
# set match not index col
# all_leagues_df = pd.concat(dictionary_df.values(), ignore_index=True)
# all_leagues_df.set_index('Match_id')

#%%    

class Team:
    def __init__(self, name, league):
        self.name = name
        self.league = league
        self.matches = {}
        self.populate_matches()
        
    def populate_matches(self):
        self.matches = {season}
        
        

class Match:
    def __init__(self, match_id, df):
        # self.league = league
        # self.season = season
        self.match_id = match_id
        self.round = None
        self.home_team = Team()
        self.home_team = None
        self.away_team = None
        self.link = None
        self.home_goals = None
        self.populate_data_from_df(df)
        
    def populate_data_from_df(self, df):
        self.round = df.at[self.match_id, 'Round']
        self.home_team = df.at[self.match_id, 'Home_Team']
        self.away_team = df.at[self.match_id, 'Away_Team']
        self.link = df.at[self.match_id, 'Link']
        # self.home_goals = 

match = Match(143645, dictionary_df['Results_2003_serie_b'])

        
        
        
        
        
        
                

#%%


# calculate features for each league dataframe: 
# Home team cumulative goals scored,	
# Home team cumulative goals conceded	
# Home team goal difference	
# Away team cumulative goals scored 	
# Away team cumulative goals conceded	
# Away team goal difference	
# Home team points scored	
# Home team cumulative points	
# Away team points scored	
# Away team cumulative points 	
# Points difference. 
#%%

#################################################################################################

all_leagues_df = pd.concat(dictionary_df.values(), ignore_index=True)
all_leagues_df[['Home_goals', 'Away_goals']] = all_leagues_df['Result'].str.split('-', expand=True)

## checking for missing or invalid data
all_leagues_df.info() # check data types and if there are missing values - None 
all_leagues_df[all_leagues_df.duplicated()].shape[0] # check for duplicates - None 
# all_leagues_df.dropna(inplace = True) 

#%%
# # convert data type of home goals/ away goals to numeric, need to remove a few rows where the data is ambiguous 
errors1 = pd.to_numeric(all_leagues_df['Home_goals'], errors='coerce').isnull()
e1 = errors1.loc[errors1==True]
errors2 = pd.to_numeric(all_leagues_df['Away_goals'], errors='coerce').isnull()
e2 = errors2.loc[errors2==True]
#%%
# check e1 and e2 are same rows - yes
all_leagues_df.loc[e1.index.to_list(), :] # show the rows where the format is invalid 
#%%
# drop rows 25832 and 108086 as these were postponed
all_leagues_df.drop([25832,108086], inplace=True)
#%%
errors = pd.to_numeric(all_leagues_df['Home_goals'], errors='coerce').isnull()
e = errors.loc[errors==True]
print(all_leagues_df.loc[e.index.to_list(), :])
#%%
## fix the formatting in the rest of the invalid rows 
for index in e.index.to_list():
    print(index)
    all_leagues_df.at[index,'Home_goals'] = all_leagues_df.at[index,'Home_goals'][0]
    all_leagues_df.at[index,'Away_goals'] = all_leagues_df.at[index,'Away_goals'][-1]
                                                     
#%%
all_leagues_df.loc[e.index.to_list(), :]

all_leagues_df[['Home_goals', 'Away_goals']] = all_leagues_df[['Home_goals', 'Away_goals']].apply(pd.to_numeric)
all_leagues_df.reset_index(inplace=True)
# calculate the match result ('H', 'A' or 'D')
def match_result_from_goals(HG_subtract_AG):
    if HG_subtract_AG > 0:
        return 'H'
    elif HG_subtract_AG < 0:
        return 'A'
    else:
        return 'D'
    
all_leagues_df['Match_result'] = (all_leagues_df['Home_goals'] - all_leagues_df['Away_goals']).apply(match_result_from_goals)



# %%
import pandas as pd

#create DataFrame
df = pd.DataFrame({'period': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                   'sales': [25, 20, 14, 16, 27, 20, 12, 15, 14, 19]})
# %%
df['4dayEWM'] = df['sales'].ewm(span=4, adjust=False).mean()

#%%

import matplotlib.pyplot as plt

#plot sales and 4-day exponentially weighted moving average 
plt.plot(df['sales'], label='Sales')
plt.plot(df['4dayEWM'], label='4-day EWM')

#add legend to plot
plt.legend(loc=2)