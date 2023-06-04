from selenium import webdriver
from bs4 import BeautifulSoup
from utils import printd
import time

def init_webdriver():
    # Replace 'path/to/webdriver' with the path to your downloaded WebDriver executable
    browser = webdriver.Firefox()
    return browser

def fetch_links(url, url_list, scroll_pause_time, timeout, scroll_increment):
    # The original while loop contents
    browser = init_webdriver()
    browser.get(url)
    
    last_height = browser.execute_script("return document.body.scrollHeight")
    start_time = time.time()
    
    all_links = list()
    
    while True:
        if time.time() - start_time > timeout:
            break
        # Scroll down by the specified increment
        browser.execute_script(f"window.scrollBy(0, {scroll_increment});")
        #browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
    
        # Parse the page content with BeautifulSoup
        soup = BeautifulSoup(browser.page_source, 'html.parser')
    
        # Extract the news headlines and links
        headlines = soup.find_all('h3', class_='Mb(5px)')
    
        for headline in headlines:
            headline_link = headline.find('a')['href']
            scontent = f"https://finance.yahoo.com{headline_link}"
            if scontent in url_list:
                printd("repeat url")
                return all_links
            if scontent not in all_links:
                all_links.append(f"https://finance.yahoo.com{headline_link}")
    
    # Close the browser
    browser.quit()

    return all_links
