# Fans of Elon Musk Better Our Yields Sentiment Analysis Index Scraper

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
from tqdm import tqdm
from dotenv import load_dotenv
import os
import numpy as np
import pandas as pd

load_dotenv()

user = os.getenv('EMAIL')
password = os.getenv('PASSWORD')
username = os.getenv("USERNAME")

# https://stackoverflow.com/questions/53680597/how-to-find-all-elements-on-the-webpage-through-scrolling-using-seleniumwebdrive
# edge case: grabs subtweet from someone else

start = time.time()

headless_mode = False
path = "C:/chromedriver-win64/chromedriver.exe"

dest_path = "Roster"

website = (
    r"https://x.com/elonmusk?ref_src=twsrc%5Egoogle%7Ctwcamp%5Eserp%7Ctwgr%5Eauthor"
)

"""
login button: //a[@data-testid="login"]
user: //label
next button: //*[@id="layers"]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div/div/div/button[2]/div
password label: //*[@id="layers"]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div[1]/div/div/div[3]/div/label
login button 2: //*[@id="layers"]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div[2]/div/div[1]/div/div/button

//*[@id="layers"]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div[2]/div/div[1]/div/div/button

Tweet container XPATH: //article[@data-testid="tweet"]

ELON TWEET CONTAINER XPATH: //article[contains(@class, 'css-175oi2r')][@data-testid="tweet"]//div[@data-testid="User-Name"]/div/div/a[@href="/elonmusk"]/ancestor::article[contains(@class, 'css-175oi2r')][@data-testid="tweet"]

//div[@data-testid="tweetText"]
//article[@data-testid="tweet"][@role="article"]
//div[@data-testid="User-Name"]/div/div/a[@href="/elonmusk"]

Timestamp: //article[@data-testid="tweet"]//time

Full Elon tweet text path: //article[@data-testid="tweet"]//div[@class="css-175oi2r"]/div[@data-testid="tweetText"]
"""

login_button_path = '//a[@data-testid="login"]'
elon_tweet_container_path = '//article[@data-testid="tweet"]'
tweet_text_path = '//div[@class="css-175oi2r"]/div[@data-testid="tweetText"]' #specific css class to manage subtweet edge case
next_button_path = '//*[@id="layers"]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div/div/div/button[2]/div'
password_path = '//*[@id="layers"]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div[1]/div/div/div[3]/div/label'
login_button_2_path = '//*[@id="layers"]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div[2]/div/div[1]/div/div/button'
check_unusual_activity_path = '//h1[@id="modal-header"]'
next_unusual_path = '//button[@data-testId="ocfEnterTextNextButton"]'
timestamp_path = '//article[@data-testid="tweet"]//time'

webdriver_service = Service(path)
chrome_options = Options()

if headless_mode:
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--headless")

driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
processed_tweets = set()

errors = []
wait = WebDriverWait(driver, timeout=20, poll_frequency=0.2, ignored_exceptions=errors)

driver.get(website)
start_time = time.time()
(driver.page_source).encode('utf-8')

time.sleep(5)
# login
wait.until(EC.element_to_be_clickable((By.XPATH, login_button_path))).click()

wait.until(EC.element_to_be_clickable((By.XPATH, "//label"))).send_keys(user)
wait.until(EC.element_to_be_clickable((By.XPATH, next_button_path))).click()

# Check if unusual activity detected lol

wait.until(
    EC.visibility_of_all_elements_located((By.XPATH, check_unusual_activity_path))
)
if driver.find_element(By.XPATH,check_unusual_activity_path).text == "Enter your phone number or username":
    wait.until(EC.element_to_be_clickable((By.XPATH, "//label"))).send_keys(username)
    wait.until(EC.element_to_be_clickable((By.XPATH, next_unusual_path))).click()

wait.until(EC.element_to_be_clickable((By.XPATH, password_path))).send_keys(password)
wait.until(EC.element_to_be_clickable((By.XPATH, login_button_2_path))).click()


containers = []
names = []
data = []

total = 500

pbar = tqdm(total=total)
time.sleep(5)
body = driver.find_element(By.CSS_SELECTOR, "body")


lock = False

def process_containers(containers):
    global lock
    res = False
    for container in containers:
        try:
            name = container.find_element(by=By.XPATH, value=tweet_text_path).text
            ts = container.find_element(by=By.XPATH,value=timestamp_path).get_attribute("datetime")
            if name in processed_tweets or name == "\n" or name == "":
                continue
            
            data.append([name,ts])
            pbar.update()
            processed_tweets.add(name)
            res = True
        except Exception as e:
            print(f"Error")
    
    return res
    #print("Processed")

term_limit = 0

while len(data) < total:
    wait.until(
        EC.visibility_of_all_elements_located((By.XPATH, elon_tweet_container_path))
    )
    lock = True
    containers = driver.find_elements(by=By.XPATH, value=elon_tweet_container_path)
    if not process_containers(containers):
        term_limit += 1
    else:
        term_limit = 0
    lock = False
    body.send_keys(Keys.PAGE_DOWN)
    wait.until(lambda x: not lock)
    if term_limit >= 10:
        break

np.savetxt("Tweets.txt", names, delimiter=", ", fmt="% s", encoding="utf8")
res = pd.DataFrame(data=np.array(data),columns = ["Text","Timestamp"])
res.to_csv("tweets.csv",index=False)

driver.quit()

print(f"Finished: Took {time.time()-start_time:.2f} seconds.")