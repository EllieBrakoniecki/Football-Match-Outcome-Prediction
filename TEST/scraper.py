#%%
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait 
# from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
import time
import os
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.abspath('../__file__'))
DATA_DIR = DATA_DIR = os.path.join(BASE_DIR, 'Football-Dataset/')

chrome_options = webdriver.ChromeOptions()
driver = webdriver.Chrome(options=chrome_options)

root_url = 'https://www.besoccer.com/competition/table/'

leagues = [name for name in os.listdir(DATA_DIR) if os.path.isdir(DATA_DIR + name)]

seasons = list(reversed(range(1990,2022)))

league_urls = [root_url + l for l in leagues]
url_list = [] # url list that will be scraped
for league_url in league_urls:
    urls_season_league = [league_url + '/' + str(season) for season in seasons]
    for url in urls_season_league:
        url_list.append(url)

def expand_shadow_element(element):
  shadow_root = driver.execute_script('return arguments[0].shadowRoot', element)
  return shadow_root


def _accept_cookies(driver):
    try:
        time.sleep(2)
        shadow_root = expand_shadow_element(driver.find_element(By.XPATH, '//*[@class="grv-dialog-host"]'))
        # shadow_root_id = shadow_root_dict['shadow-6066-11e4-a52e-4f735466cecf']
        # shadow_root = WebElement(driver, shadow_root_id)
        button = shadow_root.find_element(By.CSS_SELECTOR, 'div#grv-popup__subscribe')
        button.click()
        print('subscribe button clicked')
        time.sleep(2)
        accept_cookies = driver.find_element(By.XPATH, '//*[@id="qc-cmp2-ui"]/div[2]/div')
        accept_cookies.click()
        print('cookies button clicked')
    except:
        print("No Cookies buttons found on page")
    



for i, url in enumerate(url_list):
    driver.get(url)
    if i == 0:
        _accept_cookies(driver)
    if i == 0:
        break

df = pd.DataFrame()

def is_empty(col):
    try:
        result = col.text
    except:
        result = None
    return result


for url in url_list:

    driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser', from_encoding="utf-8")

    while True:
        previous_page = soup.find_all( 'span', attrs = {'class' : 'active-page'})[0].text

        for col in soup.find_all('tr', attrs = {'deactivate'}):
            df = df.append(
            {
            'season' : soup.find_all('span', attrs = {'class' : 'active'})[1].text,
            'date' : col.findPreviousSibling(attrs = {'center nob-border'}).text[0:-6],
            'match_name' : col.find('td', attrs = {'class' : 'name table-participant'}).text.replace('\xa0', ''),
            'result' : col.find('td', attrs = {'class' : 'center bold table-odds table-score'}).text,
            'h_odd' : is_empty(col.find('td', attrs = {'class' : "odds-nowrp"})),
            'd_odd' : is_empty(col.find('td', attrs = {'class' : "odds-nowrp"}).findNext( attrs = {'class' : "odds-nowrp"})),
            'a_odd' : is_empty(col.find('td', attrs = {'class' : "odds-nowrp"}).findNext( attrs = {'class' : "odds-nowrp"}).findNext( attrs = {'class' : "odds-nowrp"}))
            }
            , ignore_index = True)

        print('page scraped')
        element = driver.find_element_by_partial_link_text('»')
        driver.execute_script("arguments[0].click();", element)
        time.sleep(2)
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser', from_encoding="utf-8")
        new_page = soup.find_all('span', attrs = {'class' : 'active-page'})[0].text
        if previous_page != new_page:
            continue
        else:
            break
    print(url, 'done!')

driver.quit()
print('scraping finished!')

df = df[['season', 'date', 'match_name', 'result', 'h_odd', 'd_odd', 'a_odd']]

df.to_csv(os.path.join(DATA_DIR,  'matches.csv'), index = False)
# %%
