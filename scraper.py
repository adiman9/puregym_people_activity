#! /usr/bin/env python

import requests
import os
import re
import csv
from datetime import datetime
from selenium import webdriver
from dotenv import load_dotenv
from pathlib import Path
from time import sleep
env_path = Path(os.path.dirname(os.path.realpath(__file__))) / '.env'
load_dotenv(dotenv_path=env_path)

QUERY_INTERVAL = int(os.getenv('puregym_query_interval') or 10) # minutes
DATA_SUBDIRECTORY = os.getenv('puregym_data_directory') or 'recorded_data'
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), DATA_SUBDIRECTORY, \
                           '{}.csv'.format(os.getenv('puregym_filename') \
                                           or 'puregym_activity_data'))

if not os.getenv('puregym_email') or not os.getenv('puregym_pin'):
    raise ValueError("""
    ERROR:
    Puregym email and pin not found. Have you set them in your .env file?
    """)

login_url = 'https://www.puregym.com/Login/?ReturnUrl=%2Fmembers%2F'
login_payload = {
    'email': str(os.getenv('puregym_email')),
    'pin': str(os.getenv('puregym_pin')),
}

options = webdriver.ChromeOptions()
options.add_argument("start-maximized")
options.add_argument("disable-infobars")
options.add_argument("--disable-extensions")
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--window-size=1420,1080')

def fetch_activity():
    driver = webdriver.Chrome(chrome_options=options)
    driver.get(login_url)

    # Log in
    driver.find_element_by_id('email').send_keys(login_payload['email'])
    driver.find_element_by_id('pin').send_keys(login_payload['pin'])
    driver.find_element_by_id('login-submit').click()
    sleep(2)

    # Parse out number of people at the gym
    span = driver.find_element_by_xpath("""
//*[@id="main-content"]/div[2]/div/div/div[2]/div/div/div/div[1]/div/p[1]/span
    """)
    num_people = re.search(r'\d+', span.text).group()

    driver.stop_client()
    driver.quit()

    return num_people

def init_csv():
    if not os.path.isfile(OUTPUT_FILE):
        if not os.path.exists(DATA_SUBDIRECTORY):
            os.makedirs(DATA_SUBDIRECTORY)

        f = open(OUTPUT_FILE, 'a')
        w = csv.writer(f)

        w.writerow(['Timestamp', 'Number of people'])

def write_csv(num_people):
    d = datetime.utcnow()
    f = open(OUTPUT_FILE, 'a')
    w = csv.writer(f)
    w.writerow([d.isoformat() + 'Z', num_people])


if __name__ == '__main__':
    print('PureGym web scraper...')
    init_csv()

    num_people = fetch_activity()
    write_csv(num_people)

