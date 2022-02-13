#%%
import os
# from turtle import home
# import sys
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath('../__file__'))
DATA_DIR = os.path.join(BASE_DIR, 'Football-Dataset/')

NO_PREV_MATCHES_TO_CALULATE_AVERAGE_FROM = 5
NO_PREV_MATCHES_AGAINST_EACH_OTHER = 2 
 
# Process, clean and prepare soccer data for machine learning models 
class ProcessSoccerData:
    def __init__(self):
        self.df_dictionary = {} #dictionary of dataframes, 1 for each league/season
        self._set_df_dictionary() #populate df_dictionary attribute
        self.df_all_data = pd.DataFrame() #dataframe of all data 
        self._set_df_all_data() #populate df_all_data
        # self.feature_df = pd.DataFrame()
        # # self._calulate_feature_df() #populate feature_df
                
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


##############   adding features  #######################

    def _calulate_feature_df(self):
        dictionary_feature_dfs = {}
        for key, df in self.df_dictionary.items(): 
            feature_df = df.apply(lambda x: self._get_feature_data(x, df), axis = 1)
            
            
            # feature_df.insert(0, 'Home_Team', self.df_all_data['Home_Team']) 
            # feature_df.insert(1, 'Away_Team', self.df_all_data['Away_Team'])
            # feature_df.insert(2, 'Round', self.df_all_data['Round'])
            # feature_df.insert(3, 'Season', self.df_all_data['Season'])
            
            # dictionary_feature_dfs[key] = feature_df
            
        # self.feature_df = pd.concat(dictionary_feature_dfs.values(), ignore_index=True)
 
            

        
    
    # calculate feature data for the given row(match) in the df_all_data dataframe 
    def _get_feature_data(self, row, df):
        feature_df = pd.DataFrame()
        home_team = row.Home_Team
        away_team = row.Away_Team
        round = row.Round
        
        
        
        home_team_goals_scored_previous_matches = self.get_goals_previous_matches(df, home_team, round, type='scored')
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
    def get_goals_previous_matches(self, team_name, round, type='scored'):  
        all_matches_for_team_df = self.input_df[(self.input_df['Home_Team'] == team_name) | (self.input_df['Away_Team'] == team_name)]
        previous_matches_df = all_matches_for_team_df[all_matches_for_team_df['Round'] < round]  
        if type == 'scored':
            return ProcessSoccerData.get_goals_scored(previous_matches_df, team_name)
        else:
            return ProcessSoccerData.get_goals_conceded(previous_matches_df, team_name)
        
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















############################################################################################     
    # return a dataframe of matches with options to filter by league and season  
    def get_df_matches(self, leagues='ALL', season_min=1990, season_max=2021):        
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
        
            
#######################################################################
#%%
soccer = ProcessSoccerData()
#%%
df = soccer.get_df_matches()
df1 = soccer.get_df_matches(season_min=2000, season_max=2020)
leagues = ['championship', 'ligue_2']
df2 = soccer.get_df_matches(leagues, season_min=1999, season_max=1999)
df3 = soccer.get_df_matches(leagues)

leagues = soccer.all_league_names()

ligue_2_teams = soccer.teams_in_league('ligue_2')

#%%
soccer.add_feature_columns()

#%%
class Feature_Data:
    pass
#%%
lg = ['championship']
df2 = soccer.get_df_matches(lg, season_min=2000, season_max=2000)
len(list(df2.Home_Team.unique()))

match_id_and_url = dict(zip(list(df2.Match_id), list(df2.Link)))
url_list = list(df2.Link)

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.remote.webelement import WebElement

def expand_shadow_element(element):
  shadow_root = driver.execute_script('return arguments[0].shadowRoot', element)
  return shadow_root

def _accept_cookies(driver):
    try:
        time.sleep(5)
        shadow_root = expand_shadow_element(driver.find_element(By.XPATH, '//*[@class="grv-dialog-host"]'))
        button = shadow_root.find_element(By.CSS_SELECTOR, 'div#grv-popup__subscribe')
        button.click()
        print('subscribe button clicked')
        time.sleep(1)
        accept_cookies = driver.find_element(By.XPATH, '//*[@id="qc-cmp2-ui"]/div[2]/div')
        accept_cookies.click()
        print('cookies button clicked')
    except:
        print("No Cookies buttons found on page")

#%%  
import datetime
from time import strptime

chrome_options = webdriver.ChromeOptions()
driver = webdriver.Chrome(options=chrome_options)   

root_url = 'https://www.besoccer.com/'
driver.get(root_url)
_accept_cookies(driver)  

# get starting lineup players and their position 
# home_or_away = 'H' or 'A'
def get_players_and_positions(match_info, starting_lineup_web_element, home_or_away):
    player_names = starting_lineup_web_element.find_elements(By.XPATH,'./a[position()>0]/div/p')
    for j,player in enumerate(player_names):
        if j == 0:
            match_info[home_or_away + '_' + 'Goalkeeper'] = player.text
        else:
            player_num = home_or_away + '_' + 'Player' + '_' + str(j)
            match_info[player_num] = player.text
            position_and_number = player.find_elements(By.XPATH, '../../div[2]/div/span[position()>0]')
            p_n_set = set([p_n.text for p_n in position_and_number])
            match_info['Position'+ '_' + player_num] = list(p_n_set.intersection({'D', 'MF', 'F'}))[0] 



match_scraped_info = {}
most_recent_elo = {}

for i, (id, url) in enumerate(match_id_and_url.items()):
    
# for i, url in enumerate(url_list): 
    ls = url.split('/')
    home_team = ls[4]
    # print(home_team)
    away_team = ls[5]
    # print(away_team)
    driver.get(url)
    # get all the urls we should click to get info from  
    preview_url = driver.find_element(By.XPATH, '//*[@class="menu-scroll"]/a[1]').get_attribute("href") 
    events_url = driver.find_element(By.XPATH, '//*[@class="menu-scroll"]/a[2]').get_attribute("href")
    line_up_url = driver.find_element(By.XPATH, '//*[@class="menu-scroll"]/a[3]').get_attribute("href")   
    home_team_url = driver.find_element(By.XPATH, '//*[@itemprop="homeTeam"]/a').get_attribute("href")
    away_team_url = driver.find_element(By.XPATH, '//*[@itemprop="awayTeam"]/a').get_attribute("href")
 
    match_info = {}
    
    # get date, time and number of yellow/red cards(so can work out cards in prev matches)  
    driver.get(events_url)  
    date_time = driver.find_element(By.XPATH, '//*[@class="date header-match-date "]').text 
    date = date_time.split('.')[0].strip()

    ls = date.split(' ')
    dt_date = datetime.date(year, month, day)
    
    
    # match_info['date'] = date
    match_info['time'] = date_time.split('.')[1].strip()
    
    ls = date.split(' ')
    day = int(ls[0])
    month = strptime(ls[1],'%b').tm_mon
    year = int(ls[2])  
    
    day_of_week = datetime.date(year, month, day).weekday()      
    print(day_of_week)
    
    
    # get starting lineup players and their position 
    driver.get(line_up_url)
    home_starting_lineup = driver.find_element(By.XPATH, '//*[@id="mod_match_lineup"]/section/div/div[2]/div/div[1]')
    get_players_and_positions(match_info, home_starting_lineup, 'H')    
    away_starting_lineup = driver.find_element(By.XPATH, '//*[@id="mod_match_lineup"]/section/div/div[2]/div/div[2]')
    get_players_and_positions(match_info, away_starting_lineup, 'A')
    
    match_scraped_info[id] = match_info
    
    
    # get elo of each team - create function!
    driver.get(home_team_url)
    home_team = driver.find_element(By.XPATH, '//*[@id="team"]/main/section[1]/div[1]/div/div[1]/div/h2').text
    most_recent_elo[home_team] = int(driver.find_element(By.XPATH, '//*[@class="elo label-text"]/span').text)
    driver.get(away_team_url)
    away_team = driver.find_element(By.XPATH, '//*[@id="team"]/main/section[1]/div[1]/div/div[1]/div/h2').text
    most_recent_elo[away_team] = int(driver.find_element(By.XPATH, '//*[@class="elo label-text"]/span').text)

    
            

    # goals_and_yellow_cards = player.find_elements(By.XPATH, '../div/div[position()>0]/p')
    # g_y_c = [g_y.text for g_y in goals_and_yellow_cards]
    # print(player.text, g_y_c)        
        
    # df = df.append(
    #     {
    #     'Match_ID' : ,
    #     'date' : ,
    #     'h_odd' : ,
    #     }
    #     , ignore_index = True)
        
    if i == 30:
        break
    


        

#%%














      




# %%
