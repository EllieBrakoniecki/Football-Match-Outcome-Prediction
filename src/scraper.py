#%%
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.remote.webelement import WebElement
import datetime
from time import strptime
import sys
import os
import inspect
import json

#### For importing files in the repo
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

class Scrape_Soccer_Data: 
    def __init__(self, matches_df, headless=False):
        self.data_path='../data/'
        self.matches_data_path = self.data_path + 'matches_data'
        self.team_url_data_path = self.data_path + 'team_url_data'
        self.elo_data_path = self.data_path + 'elo_data'
        self.match_id_and_url = dict(zip(list(matches_df.Match_id), list(matches_df.Link)))
        root_url = 'https://www.besoccer.com/'
        self.chrome_options = webdriver.ChromeOptions()
        self.headless = headless
        if self.headless:
            self.set_headless_chrome_options()        
        self.driver = webdriver.Chrome(options=self.chrome_options)  
        if not self.headless:
            self.driver.maximize_window()     
        self.driver.get(root_url)
        self._accept_cookies()         
        self.team_urls = {} # team homepage urls
        self.matches_data = {} # historical data scraped for each match
        self.elo_data = {} # most recent elo for each team 
      
    def set_headless_chrome_options(self):
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("window-size=1920,1080")
        self.chrome_options.add_argument("--no-sandbox") 
        self.chrome_options.add_argument("--disable-dev-shm-usage") 
        self.chrome_options.add_argument("enable-automation")
        self.chrome_options.add_argument("--disable-extensions")
        self.chrome_options.add_argument("--dns-prefetch-disable")
        self.chrome_options.add_argument("--disable-gpu") 
        
    def _expand_shadow_element(self, element):
        shadow_root = self.driver.execute_script('return arguments[0].shadowRoot', element)
        return shadow_root

    def _accept_cookies(self):
        try:
            time.sleep(5)
            shadow_root = self._expand_shadow_element(self.driver.find_element(By.XPATH, '//*[@class="grv-dialog-host"]'))
            button = shadow_root.find_element(By.CSS_SELECTOR, 'div#grv-popup__subscribe')
            button.click()
            print('subscribe button clicked')
            time.sleep(1)
            accept_cookies = self.driver.find_element(By.XPATH, '//*[@id="qc-cmp2-ui"]/div[2]/div')
            accept_cookies.click()
            print('cookies button clicked')
        except:
            print("No Cookies buttons found on page")

    def scrape_elo_for_teams_in_match(self, match_data, analysis_url):
        self.driver.get(analysis_url)
        try:
            table = self.driver.find_element(By.XPATH, '//*[@class="comparison"]/div/div/table/tbody')
            elo = table.find_element(By.XPATH, './tr/td[contains(.,"ELO")]/parent::tr').text
            match_data['H_elo'] = elo.split(' ')[0]
            match_data['A_elo'] = elo.split(' ')[2]
        except:
            print('no elo found for match url:', analysis_url)

    #get date, time and number of yellow/red cards from match events url(so can work out cards in prev matches)  
    def _scrape_date_and_cards(self, match_data, events_url):       
        self.driver.get(events_url)
        try:  
            date_time = self.driver.find_element(By.XPATH, '//*[@class="date header-match-date "]').text
            date = date_time.split('.')[0].strip().split(' ')
            dt_date = datetime.date(int(date[2]), strptime(date[1],'%b').tm_mon, int(date[0]))    
            match_data['Match_date'] = dt_date.strftime("%B %d, %Y")
            match_data['Match_day_of_week'] = dt_date.weekday()
            match_data['Match_time'] = date_time.split('.')[1].strip() 
        except:
            print('no date found for url:', events_url)
        try:
            table = self.driver.find_element(By.XPATH, '//*[@class="panel-body pn compare-data"]/table/tbody')
            yellow_cards = table.find_element(By.XPATH, './tr/td[contains(.,"Yellow cards")]/parent::tr | ./tr/td[contains(.,"Yellow card")]/parent::tr').text
            match_data['H_yellow_cards'] = yellow_cards[0]
            match_data['A_yellow_cards'] = yellow_cards[-1]
        except:
            print('no yellow cards found for url:', events_url)
            match_data['H_yellow_cards'] = 0
            match_data['A_yellow_cards'] = 0
        try: 
            table = self.driver.find_element(By.XPATH, '//*[@class="panel-body pn compare-data"]/table/tbody')
            red_cards = table.find_element(By.XPATH, './tr/td[contains(.,"Red cards")]/parent::tr').text
            match_data['H_red_cards'] = red_cards.split(' ')[0]
            match_data['A_red_cards'] = red_cards.split(' ')[2][-1]
        except: 
            # print('no red cards found for url:', events_url)
            match_data['H_red_cards'] = 0
            match_data['A_red_cards'] = 0
     
    # get url for each player page - scrape stats and FIFA rankings?         
    @staticmethod
    def _scrape_players_and_positions(match_info, starting_lineup_web_element, home_or_away):
        player_names = starting_lineup_web_element.find_elements(By.XPATH,'./a[position()>0]/div/p | ./li[position()>0]/div/a/div[2]')
        for j,player in enumerate(player_names):
            if j == 0:
                match_info[home_or_away + '_' + 'Goalkeeper'] = player.text
            else:
                player_num = home_or_away + '_' + 'Player' + '_' + str(j)
                match_info[player_num] = player.text
                # ???remove following code as position not listed for some seasons???
                # position_and_number = player.find_elements(By.XPATH, '../../div[2]/div/span[position()>0]')
                # p_n_set = set([p_n.text for p_n in position_and_number])
                # match_info['Position'+ '_' + player_num] = list(p_n_set.intersection({'D', 'MF', 'F'}))[0] 
   
    # get starting lineup players and their position    
    def _scrape_players_and_positions_both_teams(self, match_data, line_up_url):   
        self.driver.get(line_up_url)
        try: 
            home_starting_lineup = self.driver.find_element(By.XPATH, '//*[@id="mod_match_lineup"]/section/div/div[2]/div/div[1] | //*[@class="lineup local"]')
            Scrape_Soccer_Data._scrape_players_and_positions(match_data, home_starting_lineup, 'H') 
        except:   
            print('no home starting lineup found for url:', line_up_url)
        try:
            away_starting_lineup = self.driver.find_element(By.XPATH, '//*[@id="mod_match_lineup"]/section/div/div[2]/div/div[2] | //*[@class="lineup visitor"]')
            Scrape_Soccer_Data._scrape_players_and_positions(match_data, away_starting_lineup, 'A')
        except: 
            print('no away starting lineup found for url:', line_up_url)
            
    # Get the results from the last 5 times the teams met each other            
    def _scrape_previous_meetings_results(self, match_data, preview_url):
        self.driver.get(preview_url)
        try:
            last_meetings = self.driver.find_element(By.XPATH, '//*[@class="row jc-sa ta-c pv20 ph5"]')
            last_mtgs_HW = last_meetings.find_element(By.XPATH, './div[1]/p').text
            match_data['Last_mtgs_HW'] = last_mtgs_HW
            last_mtgs_D = last_meetings.find_element(By.XPATH, './div[2]/p').text
            match_data['Last_mtgs_D'] = last_mtgs_D
            last_mtgs_AW = last_meetings.find_element(By.XPATH, './div[3]/p').text
            match_data['Last_mtgs_AW'] = last_mtgs_AW
        except:
            print('results from last meetings not found for url', preview_url)

    @staticmethod
    def _create_folder(path):
        if not os.path.exists(path):
            os.makedirs(path)

##################Public functions ##############################

    @staticmethod
    def read_data(path):
        with open(path) as f:
            data = f.read()
            return json.loads(data) 

    def save_data(self, filename, data, mode='w', indent=4):
        Scrape_Soccer_Data._create_folder(self.data_path)
        with open(self.data_path + f'{filename}', mode=mode) as f:
            json.dump(data, f, indent=indent) 
               
    # get the most recent elo of the team with url specified
    def scrape_current_elo(self, team_url):
        self.driver.get(team_url)
        try:    
            team = self.driver.find_element(By.XPATH, '//*[@id="team"]/main/section[1]/div[1]/div/div[1]/div/h2').text
            self.elo_data[team] = int(self.driver.find_element(By.XPATH, '//*[@class="elo label-text"]/span').text)
        except:
            print('no elo found for team with url:', team_url)

    # scrape current elo data for all teams - (team urls from saved data)
    def scrape_most_recent_elo_data(self):
        if os.path.exists(self.team_url_data_path):                        
            for url in Scrape_Soccer_Data.read_data(self.team_url_data_path).values(): 
                self.scrape_current_elo(url)
            self.save_data("elo_data", self.elo_data)
        else: 
            print('no team urls saved, run scrape_match_data instead')
            
    # scrape match data for each team      
    def scrape_match_data(self, scrape_elo=False, scrape_players=False, scrape_cards=False, scrape_previous_mtgs=False, scrape_latest_elo=False):
        if os.path.exists(self.matches_data_path):                        
            self.matches_data = Scrape_Soccer_Data.read_data(self.matches_data_path) 
        if os.path.exists(self.elo_data_path):            
            self.elo_data = Scrape_Soccer_Data.read_data(self.elo_data_path) 
        if os.path.exists(self.team_url_data_path):            
            self.team_urls = Scrape_Soccer_Data.read_data(self.team_url_data_path) 
        for i, (id, url) in enumerate(self.match_id_and_url.items()):
            l = url.split('/')
            home_team = l[4]
            away_team = l[5]
            match_data = {}  
            match_data['Link'] = url  
            self.driver.get(url)  
            if scrape_elo:
                menu_scroll = self.driver.find_element(By.XPATH, '//*[@class="menu-scroll"]')          
                analysis_url = menu_scroll.find_element(By.XPATH, './a[contains(.,"Analysis")]').get_attribute("href")
                self.scrape_elo_for_teams_in_match(match_data, analysis_url)
            if scrape_cards:
                menu_scroll = self.driver.find_element(By.XPATH, '//*[@class="menu-scroll"]')          
                events_url = menu_scroll.find_element(By.XPATH, './a[contains(.,"Events")]').get_attribute("href")
                self._scrape_date_and_cards(match_data, events_url)
            if scrape_players: 
                menu_scroll = self.driver.find_element(By.XPATH, '//*[@class="menu-scroll"]')          
                line_up_url = menu_scroll.find_element(By.XPATH, './a[contains(.,"Line-ups")]').get_attribute("href")  
                self._scrape_players_and_positions_both_teams(match_data, line_up_url)
            if scrape_previous_mtgs:
                menu_scroll = self.driver.find_element(By.XPATH, '//*[@class="menu-scroll"]')          
                preview_url = menu_scroll.find_element(By.XPATH, './a[contains(.,"Preview")]').get_attribute("href") 
                self._scrape_previous_meetings_results(match_data, preview_url)   
            if scrape_latest_elo:
                home_team_url = self.driver.find_element(By.XPATH, '//*[@itemprop="homeTeam"]/a').get_attribute("href")
                away_team_url = self.driver.find_element(By.XPATH, '//*[@itemprop="awayTeam"]/a').get_attribute("href")
                self.team_urls[home_team] = home_team_url
                self.team_urls[away_team] = away_team_url   
                self.scrape_current_elo(home_team_url) 
                self.scrape_current_elo(away_team_url)  
            self.matches_data[id] = match_data 
            # if i == 2:
            #     break                        
        if scrape_latest_elo:
            self.save_data("elo_data", self.elo_data) 
            self.save_data("team_url_data", self.team_urls)
        self.save_data("matches_data", self.matches_data)
   
#%%
from initial_data_processing import ProcessSoccerData
soccer_data = ProcessSoccerData()
#%%
df = soccer_data.get_matches_df(season_min=2000, season_max=2021)
scrape_soccer = Scrape_Soccer_Data(df, headless=False)
scrape_soccer.scrape_match_data(scrape_elo=True, scrape_previous_mtgs=True)

#%%
# df1 = soccer_data.get_matches_df()
# leagues = list(df1.League.unique())
# l = ['primeira_liga'] 
# df2 = soccer_data.get_matches_df(l, season_min=2000, season_max=2000)
# df3 = soccer_data.get_matches_df(l,season_min=2018, season_max=2018 )

# #%%
# scrape_soccer = Scrape_Soccer_Data(df3, headless=True)
# scrape_soccer.scrape_match_data()
# #%%
# leagues = list(df1.League.unique())
# for league in leagues:
#     df = soccer_data.get_matches_df(league,season_min=2018, season_max=2018)
#     scrape_soccer = Scrape_Soccer_Data(df3, headless=True)
#     scrape_soccer.scrape_match_data()

# # for i in range(2015, 2022):
# #     season_min, season_max = i, i
# #         df = soccer_data.get_matches_df(ch,season_min=2017, season_max=2017 )
# #         scrape_soccer = Scrape_Soccer_Data(df3, headless=True)
# #         scrape_soccer.scrape_match_data()
# #%%
# scrape_soccer.scrape_most_recent_elo_data()

# %%
############### TESTING #########################
# chrome_options = webdriver.ChromeOptions()
# driver = webdriver.Chrome(options=chrome_options)       
# driver.get('https://www.besoccer.com/match/charlton-athletic-fc/barnsley-fc/200020934')
# table = driver.find_element(By.XPATH, '//*[@class="panel-body pn compare-data"]/table/tbody')
# yellow_cards = table.find_element(By.XPATH, './tr/td[contains(.,"Yellow cards")]/parent::tr | ./tr/td[contains(.,"Yellow card")]/parent::tr').text
# #%%
# chrome_options = webdriver.ChromeOptions()
# driver = webdriver.Chrome(options=chrome_options)       
# driver.get('https://www.besoccer.com/match/birmingham-city-fc/fulham/200020932/preview')
# # %%
# last_meetings = driver.find_element(By.XPATH, '//*[@class="row jc-sa ta-c pv20 ph5"]')
# last_mtgs_HW = last_meetings.find_element(By.XPATH, './div[1]/p').text
# print(last_mtgs_HW)
# last_mtgs_D = last_meetings.find_element(By.XPATH, './div[2]/p').text
# print(last_mtgs_D)
# last_mtgs_AW = last_meetings.find_element(By.XPATH, './div[3]/p').text
# print(last_mtgs_AW)

#%%
# chrome_options = webdriver.ChromeOptions()
# driver = webdriver.Chrome(options=chrome_options)       
# driver.get('https://www.besoccer.com/match/watford-fc/middlesbrough-fc/202175607/table')
# #%%
# menu_scroll = driver.find_element(By.XPATH, '//*[@class="menu-scroll"]')
# analysis_url = menu_scroll.find_element(By.XPATH, './a[contains(.,"Analysis")]').get_attribute("href")

# %%
