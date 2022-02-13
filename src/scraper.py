import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.remote.webelement import WebElement
import datetime
from time import strptime

class Scrape_Soccer_Data: 
    def __init__(self, matches_df):
        self.match_id_and_url = dict(zip(list(matches_df.Match_id), list(matches_df.Link)))
        root_url = 'https://www.besoccer.com/'
        chrome_options = webdriver.ChromeOptions()
        self.driver = webdriver.Chrome(options=chrome_options)       
        self.driver.get(root_url)
        self._accept_cookies()         
        self.team_urls = {} # list of all the team homepage urls
        self.matches_data = {} # all of the historical data scraped for each match
        self.elo = {} # most recent elo for each team 
        
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

    #get date, time and number of yellow/red cards(so can work out cards in prev matches)  
    def _scrape_date_and_cards(self, match_data, events_url):       
        self.driver.get(events_url)  
        date_time = self.driver.find_element(By.XPATH, '//*[@class="date header-match-date "]').text 
        date = date_time.split('.')[0].strip().split(' ')
        dt_date = datetime.date(int(date[2]), strptime(date[1],'%b').tm_mon, int(date[0]))    
        match_data['match_date'] = dt_date
        match_data['match_day_of_week'] = dt_date.weekday()
        match_data['match_time'] = date_time.split('.')[1].strip()
 
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

################################################################
#Public functions
                
    # get the most recent elo of the team with url specified
    def scrape_current_elo(self, team_url):
        self.driver.get(team_url)
        try:    
            home_team = self.driver.find_element(By.XPATH, '//*[@id="team"]/main/section[1]/div[1]/div/div[1]/div/h2').text
            self.elo[home_team] = int(self.driver.find_element(By.XPATH, '//*[@class="elo label-text"]/span').text)
        except:
            print('no elo found for team with url:', team_url)

# scrape current elo data for all teams - (team urls from saved data)
    def scrape_most_recent_elo_data(self):
        for url in self.team_urls.values(): # get from saved data
            self.scrape_current_elo(url)
            
    # scrape all historical match data and current elo for each team      
    def scrape_match_data(self):
        for i, (id, url) in enumerate(self.match_id_and_url.items()):
            l = url.split('/')
            home_team = l[4]
            away_team = l[5]
            self.driver.get(url) 
            preview_url = self.driver.find_element(By.XPATH, '//*[@class="menu-scroll"]/a[1]').get_attribute("href") 
            events_url = self.driver.find_element(By.XPATH, '//*[@class="menu-scroll"]/a[2]').get_attribute("href")
            line_up_url = self.driver.find_element(By.XPATH, '//*[@class="menu-scroll"]/a[3]').get_attribute("href")   
            home_team_url = self.driver.find_element(By.XPATH, '//*[@itemprop="homeTeam"]/a').get_attribute("href")
            away_team_url = self.driver.find_element(By.XPATH, '//*[@itemprop="awayTeam"]/a').get_attribute("href")
            self.team_urls[home_team] = home_team_url
            self.team_urls[away_team] = away_team_url    
            match_data = {}    
            self._scrape_date_and_cards(match_data, events_url)
            self._scrape_players_and_positions_both_teams(match_data, line_up_url)
            # self._scrape_previous_meetings_results(match_data, preview_url)   
            self.matches_data[id] = match_data  # add the data for the match  
            self.scrape_current_elo(home_team_url)
            self.scrape_current_elo(away_team_url)
            if i == 50:
                break
   
#%%
soccer = ProcessSoccerData()
df = soccer.get_matches_df()
#%%
scrape_soccer = Scrape_Soccer_Data(df)
#%%
scrape_soccer.scrape_match_data()
#%%
scrape_soccer.scrape_most_recent_elo_data()
