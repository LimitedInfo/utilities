import undetected_chromedriver as uc
import json
import datetime as dt
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
import requests
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import time
from selenium.webdriver.chrome.options import Options

load_dotenv()


def login_chrome(credentials_file):
    # Open json file that contains login_chrome info
    try:
        with open(credentials_file, 'r') as f:
            creds = json.load(f)
        email = creds['email']
        password = creds['password']
    except FileNotFoundError:
        print(f"Error: Credentials file not found at {credentials_file}")
        return None
    except KeyError as e:
        print(f"Error: Missing key {e} in credentials file {credentials_file}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {credentials_file}")
        return None

    # print(creds)
    # Setup webdriver

    # Set up Chrome options
    driver = uc.Chrome()

    # Login to Google
    driver.get('https://accounts.google.com/signin')
    # wait a second for login_chrome page to load
    time.sleep(2)
    driver.find_element(By.XPATH, '//*[@id="identifierId"]').send_keys(email)
    driver.find_element(By.XPATH, '//*[@id="identifierNext"]/div/button/span').click()
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="password"]/div[1]/div/div[1]/input'))
    )
    driver.find_element(By.XPATH, '//*[@id="password"]/div[1]/div/div[1]/input').send_keys(password)
    driver.find_element(By.XPATH, '//*[@id="passwordNext"]/div/button/span').click()
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, "//a[@aria-label='Google Account settings']"))
    )

    return driver


async def login_twitter(driver):
    # Login to Twitter
    driver.get('https://x.com/')

    # Wait for sign in to appear
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.TAG_NAME, 'iframe'))
    )
    curWindow = driver.current_window_handle
    driver.find_element(By.TAG_NAME, 'iframe').click()
    wait = WebDriverWait(driver, 10)
    wait.until(EC.number_of_windows_to_be(3))

    for window in driver.window_handles:
        if window != curWindow:
            driver.switch_to.window(window)

        try:
            driver.find_element(By.CSS_SELECTOR, '.VV3oRb.YZVTmd.SmR8').click()
        except Exception as e:
            print(f"Error clicking element: {e}")

    # Find the input field with the specified classes
    # Switch back to the original window
    driver.switch_to.window(curWindow)
    print(f"Switched back to original window: {curWindow}")
    try:
        input_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'input'))
        )
        input_field.send_keys("5stack5")

        # Click the Next button
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']"))
        )
        next_button.click()

        print("Successfully entered text and clicked Next button")

        return driver
    except Exception as e:
        print(f"Error interacting with elements: {e}")
        return None # Indicate login failure



async def get_latest_tweet_text(credentials_file, login=False, driver=None):
    """Logs in (if requested) and retrieves the text of the most recent tweet from the Following timeline."""
    if login:
        if not driver:
            driver = login_chrome(credentials_file)
            if driver is None:
                print("Chrome login failed during initial setup.")
                return None # Stop if Chrome login fails
        driver = await login_twitter(driver)
        if driver is None:
            print("Twitter login failed during initial setup.")
            return None # Stop if Twitter login fails
        time.sleep(5)
    elif not driver:
        print("Error: A driver instance must be provided if login=False")
        return None

    print("Navigating to following tab")
    # Following tab
    try:
        element = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, "//*[text()='Following']"))
            )
        element.click()
        print("Clicked 'Following' tab.")
        time.sleep(5) # Allow time for timeline to load after click
    except Exception as e:
        print(f"Error clicking 'Following' tab: {e}. Attempting to continue...")
        # Might fail if already on the tab or element changes, try to proceed cautiously
        time.sleep(2)

    print("Attempting to find timeline and first tweet...")
    try:
        # Wait for the timeline element to be present
        timeline = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Home timeline'] | //div[@aria-label='Timeline: Search timeline']"))
        )
        print("Timeline element found.")

        # Find tweet articles within the timeline
        # Wait briefly for at least one tweet article to appear
        posts = WebDriverWait(timeline, 15).until(
            EC.presence_of_all_elements_located((By.XPATH, ".//article[@data-testid='tweet']"))
        )
        # posts = timeline.find_elements(By.XPATH, ".//article[@data-testid='tweet']") # Alternative if wait fails

        print(f"{len(posts)} posts found in current view.")

        if posts:
            first_post = posts[0]
            try:
                # Extract text from the first post
                tweet_content_element = first_post.find_element(By.XPATH, ".//div[@data-testid='tweetText']")
                tweet_text = tweet_content_element.text
                print(f"Found latest tweet text.")
                return tweet_text
            except Exception as e:
                print(f"Error extracting text from the first tweet: {e}")
                return None
        else:
            print("No tweet articles found in the timeline.")
            return None

    except TimeoutException:
        print("Timed out waiting for timeline or tweets to appear.")
        # Maybe refresh and retry once?
        # print("Refreshing and trying again...")
        # driver.refresh()
        # time.sleep(10)
        # Add retry logic here if desired
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

# The old gather_tweets function is removed.