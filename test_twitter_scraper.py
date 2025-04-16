import asyncio
from myutils.twitter_scraper import login_chrome, login_twitter, get_latest_tweet_text
import datetime as dt
import time # Import time for sleep after refresh

async def main():
    driver = None # Initialize driver to None
    try:
        print("Starting Chrome login...")
        driver = login_chrome('login.json')
        if not driver:
            print("Chrome login failed. Exiting.")
            return

        print("Attempting Twitter login...")
        driver = await login_twitter(driver)
        if not driver:
            print("Twitter login failed. Exiting.")
            return # Driver will be closed in finally block

        print("Starting continuous monitoring for latest tweet...")
        last_tweet_text = None

        while True:
            try:
                print(f"[{dt.datetime.now()}] Checking for latest tweet...")
                current_tweet_text = await get_latest_tweet_text(driver=driver, credentials_file='login.json')

                if current_tweet_text is not None:
                    if current_tweet_text != last_tweet_text:
                        print("-"*20)
                        print(f"[{dt.datetime.now()}] NEW Latest Tweet Text Found:")
                        print(current_tweet_text)
                        print("-"*20)
                        last_tweet_text = current_tweet_text
                    else:
                        print(f"[{dt.datetime.now()}] No new tweet text found.")
                else:
                    print(f"[{dt.datetime.now()}] Failed to retrieve tweet text this cycle.")

                print(f"[{dt.datetime.now()}] Waiting 30 seconds...")
                await asyncio.sleep(30)

                print(f"[{dt.datetime.now()}] Refreshing page...")
                driver.refresh()
                # Wait a bit after refresh for elements to potentially reload
                # get_latest_tweet_text has its own waits, but a small buffer can help
                await asyncio.sleep(5)

            except KeyboardInterrupt:
                print("\nMonitoring stopped by user.")
                break
            except Exception as e:
                print(f"[{dt.datetime.now()}] An error occurred during monitoring cycle: {e}")
                print(f"[{dt.datetime.now()}] Attempting to continue after 15 seconds...")
                await asyncio.sleep(15)
                # Optionally try to refresh again or add more robust error handling/recovery
                try:
                    driver.refresh()
                    await asyncio.sleep(5)
                except Exception as refresh_error:
                    print(f"[{dt.datetime.now()}] Failed to refresh after error: {refresh_error}. Exiting loop.")
                    break

    finally:
        print("Closing driver...")
        if driver:
            driver.quit()
        print("Driver closed.")

if __name__ == "__main__":
    # On Windows, the default event loop policy might need adjustment for Selenium
    # If you encounter issues, uncomment the following line:
    # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())