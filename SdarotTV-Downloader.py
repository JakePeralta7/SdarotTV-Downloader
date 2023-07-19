# Imports
import getpass
import json
import requests
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import TimeoutException

# Constants
BASE_URL = "https://www.sdarot.tw"
WATCH_URL = f"{BASE_URL}/watch"
LOGIN_URL = f"{BASE_URL}/login"


def load_config():
    pass


def get_video_url(browser_log):
    events = [json.loads(entry['message'])['message'] for entry in browser_log]

    network_requests = [event for event in events if event['method'] == 'Network.requestWillBeSent']
    media_request = [network_request for network_request in network_requests if network_request['params']['type'] == "Media"][0]
    return media_request['params']['request']['url']


def download_episode(driver, show_id, season, episode):

    # Entering the episode page
    driver.get(f"{WATCH_URL}/{show_id}/season/{season}/episode/{episode}")

    # Waiting for the button to be clickable
    wait = WebDriverWait(driver, 60)
    wait.until(EC.element_to_be_clickable((By.ID, 'proceed')))

    # Catching the video request from the network logs
    browser_log = driver.get_log('performance')
    media_url = get_video_url(browser_log)

    # Moving the cookies from selenium to requests
    cookies = driver.get_cookies()
    s = requests.Session()
    for cookie in cookies:
        s.cookies.set(cookie['name'], cookie['value'])

    # Downloading the video
    response = s.get(media_url, stream=True)

    file_name = f"SE{season.zfill(2)} EP{episode.zfill(2)}.mp4"

    # Saving the video to file
    with open(file_name, 'wb') as f:
        f.write(response.content)


def get_driver():
    caps = DesiredCapabilities.CHROME
    caps['goog:loggingPrefs'] = {'performance': 'ALL'}
    driver = webdriver.Chrome()
    driver.caps = caps
    driver.maximize_window()
    return driver


def main():

    # Getting the credentials from the user
    username = input("Username: ")
    password = getpass.getpass("Password: ")
    show_id = input("Enter the Show ID: ")
    print("Enter Starting Point")
    season_start = int(input("Season: "))
    episode_start = int(input("Episode: "))

    # Initializing and configuring the chrome driver
    driver = get_driver()

    # Logging in to the website via the JS console
    driver.get(LOGIN_URL)
    driver.execute_script(f"document.getElementsByName('username')[1].setAttribute('value', '{username}')")
    driver.execute_script(f"document.getElementsByName('password')[1].setAttribute('value', '{password}')")
    driver.execute_script("document.getElementsByName('submit_login')[1].click()")

    driver.get(f"{WATCH_URL}/{show_id}")

    # Retrieving the show's seasons
    seasons = [season.text for season in driver.find_element(By.ID, "season").find_elements(By.TAG_NAME, "li")]
    for season in seasons:
        if int(season) < season_start:
            print(f"Skipping Season {season}...")
            continue
        print(f"Downloading Season {season}...")

        # Entering the season page
        driver.get(f"{WATCH_URL}/{show_id}/season/{season}")

        # Retrieving the season's episodes
        episodes = [episode.text for episode in driver.find_element(By.ID, "episode").find_elements(By.TAG_NAME, "li")]
        for episode in episodes:
            if int(season) == season_start and int(episode) < episode_start:
                print(f"Skipping Episode {episode}")
                continue
            print(f"Downloading Episode {episode}")

            downloaded = False
            while not downloaded:
                try:
                    download_episode(driver, show_id, season, episode)
                    downloaded = True
                except TimeoutException:
                    continue


if __name__ == "__main__":
    main()
