# %%
import pandas as pd
import numpy as np
import os

pd.options.display.max_columns = 10
pd.options.display.max_colwidth = 1000

dictionary_df = {} # a dictionary of dataframes, 1 for each football league

## Get the data from each league and put in a df
football_data_path = '../Football-Dataset/'
for (dirpath, dirnames, filenames) in os.walk(football_data_path):
    for filename in filenames:
        if filename != '.DS_Store':
            dictionary_df[filename[:-4]] = pd.read_csv(dirpath + '/' + filename)


number_of_datasets = len(dictionary_df) # 448
#%%
## concat the df's into 1 dataframe 
all_leagues_df = pd.concat(dictionary_df.values(), ignore_index=True)
#%%
all_leagues_df.describe()
all_leagues_df.head()
columns = all_leagues_df.columns
teams = all_leagues_df['Home_Team'].unique()
seasons = np.sort(all_leagues_df['Season'].unique())
rounds = all_leagues_df['Round'].unique()
#%% 
## TO-DO 
# 1. check for missing values
# 2. check home away
#%% 
## Feature selection 
# 1. create new columns home_goals and away_goals from the score column 
all_leagues_df[['Home_goals', 'Away_goals']] = all_leagues_df['Result'].str.split('-', expand=True)

#%%




# %%

def get_goals_scored(playing_stat):
    print("get_goals_scored")
    # Create a dictionary with team names as keys
    teams = {}
    for i in playing_stat.groupby('HomeTeam').mean().T.columns:
#         print("check {} \n".format(i))
        teams[i] = []
    
#     # the value corresponding to keys is a list containing the match location.
#     for i in range(len(playing_stat)):
#         HTGS = playing_stat.iloc[i]['FTHG']
#         ATGS = playing_stat.iloc[i]['FTAG']
#         teams[playing_stat.iloc[i].HomeTeam].append(HTGS)
#         teams[playing_stat.iloc[i].AwayTeam].append(ATGS)
        
#     # Create a dataframe for goals scored where rows are teams and cols are matchweek.
#     GoalsScored = pd.DataFrame(data=teams, index = [i for i in range(1,39)]).T
#     GoalsScored[0] = 0
#     # Aggregate to get uptil that point
#     for i in range(2,39):
#         GoalsScored[i] = GoalsScored[i] + GoalsScored[i-1]
#     return GoalsScored



# # Gets the goals conceded agg arranged by teams and matchweek
# def get_goals_conceded(playing_stat):
#     # Create a dictionary with team names as keys
#     teams = {}
#     for i in playing_stat.groupby('HomeTeam').mean().T.columns:
# #         print("check {} \n".format(i))
#         teams[i] = []
    
#     # the value corresponding to keys is a list containing the match location.
#     for i in range(len(playing_stat)):
#         ATGC = playing_stat.iloc[i]['FTHG']
#         HTGC = playing_stat.iloc[i]['FTAG']
#         teams[playing_stat.iloc[i].HomeTeam].append(HTGC)
#         teams[playing_stat.iloc[i].AwayTeam].append(ATGC)
    
#     # Create a dataframe for goals scored where rows are teams and cols are matchweek.
#     GoalsConceded = pd.DataFrame(data=teams, index = [i for i in range(1,39)]).T
#     GoalsConceded[0] = 0
#     # Aggregate to get uptil that point
#     for i in range(2,len(teams["Arsenal"])+1):
#         GoalsConceded[i] = GoalsConceded[i] + GoalsConceded[i-1]
#     return GoalsConceded

# def get_gss(playing_stat):
#     GC = get_goals_conceded(playing_stat)
#     GS = get_goals_scored(playing_stat)
   
#     j = 0
#     HTGS = []
#     ATGS = []
#     HTGC = []
#     ATGC = []

#     for i in range(380):
#         ht = playing_stat.iloc[i].HomeTeam
#         at = playing_stat.iloc[i].AwayTeam
#         HTGS.append(GS.loc[ht][j])
#         ATGS.append(GS.loc[at][j])
#         HTGC.append(GC.loc[ht][j])
#         ATGC.append(GC.loc[at][j])
        
#         if ((i + 1)% 10) == 0:
#             j = j + 1
    
# #     print("check line 87")
# #     print(playing_stat.shape,len(HTGS))
    
#     playing_stat['HTGS'] = HTGS
#     playing_stat['ATGS'] = ATGS
#     playing_stat['HTGC'] = HTGC
#     playing_stat['ATGC'] = ATGC
    
#     return playing_stat

# # Apply to each dataset
# playing_statistics_1516=get_gss(playing_statistics_1516)
# playing_statistics_1415=get_gss(playing_statistics_1415)
# playing_statistics_1314=get_gss(playing_statistics_1314)
# playing_statistics_1213=get_gss(playing_statistics_1213)
# playing_statistics_1112=get_gss(playing_statistics_1112)
# playing_statistics_1011=get_gss(playing_statistics_1011)
# playing_statistics_0910=get_gss(playing_statistics_0910)
# playing_statistics_0809=get_gss(playing_statistics_0809)