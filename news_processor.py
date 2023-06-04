import requests
from newspaper import Article
from datetime import datetime, timedelta
import random
import httpx
import time

from utils import send_email, save_list_to_file, load_list_from_file, get_article_data, printd, translate_to_chinese
from parse_yahoo_finance import init_webdriver, fetch_links
from openai_functions import analyze_sentiment, extract_nonce_keywords, summarize_large_text
from google_trends import get_trend_data, get_trends
import traceback
import sys
import feedparser
import os

from dotenv import load_dotenv
load_dotenv()

class NewsProcessor:
    def __init__(self, third_party_api_key, api_key, end_point, params, file_name):
        self.third_party_api_key = third_party_api_key
        self.api_key = api_key
        self.end_point = end_point
        self.params = params
        self.file_name = file_name
        self.first_link = ""
        self.first = True
        self.url_list = load_list_from_file(self.file_name)

    def save_url_list(self):
        self.url_list.append(self.first_link)
        save_list_to_file(self.url_list, self.file_name)

    def parse_article(self, title, url, source, description, message):
        # title
        printd("Title:", title)
        # link
        printd("Link:", url)
        #printd("Source:", article["source"]["name"])
        if self.first:
            self.first_link = url
            self.first = False
    
        # check article repeat
        if url in self.url_list:
            print("news in url list")
            return False
    
        # get article    
        proxies = {
        }
        
        retry_count = 0
        
        while True and retry_count < 5:
            try:
                article_response = requests.get(url, proxies=proxies, timeout=10.0)
                html_content = article_response.text
                break
            except Exception as e:
                printd(f"Error fetching article content: {e}")
                creds = str(random.randint(10000, 0x7fffffff)) + ":" + "foobar"
                proxy_url = 'socks5h://{}@localhost:9051'.format(creds)
        
                proxies = {
                    "http": proxy_url,
                    "https": proxy_url,
                }
                retry_count += 1
                time.sleep(5)
        
        if retry_count == 5:
            return True
        
        # Use Newspaper3k to extract the article content
        try:
            news_article = Article(url)
            news_article.set_html(html_content)
            news_article.parse()
            
            content = ""
            #print("Content:", news_article.text)
            if not news_article.text:
                content = title + "\n" + description
                printd(content)
            else:
                content = news_article.text
        
            content = summarize_large_text(content, self.api_key)
    
            timeout = 300.0
            start_time = time.time()  # Record the start time.
            sentiment_score = 0
            while True:
                current_time = time.time()
                elapsed_time = current_time - start_time
                if elapsed_time > timeout:
                    printd("sentiment Timeout reached!")
                    break
                try:
                    sentiment_analysis, sentiment_score = analyze_sentiment(content, self.api_key)
                    break
                except Exception as e:
                    printd("sentimental error: ", e)
        
            if not sentiment_score:
                printd("no sentiment_score")
                return True
            if abs(sentiment_score) < 0.5:
                printd("sentiment_score below 0.5")
                return True
        
            top_keywords = extract_nonce_keywords(content, self.api_key, n=5)
            for key_w in top_keywords:
                if "sorry" in key_w:
                    printd("no keywords relevant to business or investing")
                    return True
            printd("Sentiment analysis result:", translate_to_chinese(sentiment_analysis), sentiment_score)
            printd("Top 5 Keywords:", ", ".join(top_keywords))
        
            trends = get_trends(top_keywords)
            for keyword, trend in trends:
                printd(f"{translate_to_chinese(keyword)}: {trend}")
        
            trends_string = ""
            for keyword, trend_value in trends:
                trends_string += f"{translate_to_chinese(keyword)}: {trend_value}\n"
        
            send_msg = title + "\n" + source + "\n" + url + "\n" + translate_to_chinese(description) + "\n" + translate_to_chinese(sentiment_analysis) + "\n" + str(sentiment_score) + "\n" + trends_string + "\n"
            temp_msg = send_msg
        
            for keyword, trend in trends:
                if abs(float(trend)) > 0.1:
                    send_msg += translate_to_chinese(keyword) + " "  + str(trend) + "\n"
            if send_msg != temp_msg:
                send_email(send_msg, message)
            printd("-" * 80)
        except Exception as e:
            print(f"Error parsing article content: {e}")
            # Print the line number and backtrace
            traceback.print_exc()
        return True
    
class NewsApi(NewsProcessor):
    def __init__(self):
        self.page = 1
        self.has_more_articles = True
        yesterday_date = datetime.now().date() - timedelta(days=2)
        self.third_party_api_key=os.getenv('NEWS_API_KEY')
        self.api_key=os.getenv('OPENAI_API_KEY')
        self.end_point="https://newsapi.org/v2/everything"
        self.file_name="news.pkl"
        self.params = {
            "apiKey": self.third_party_api_key,
            "q": "finance OR economy OR technology OR stocks OR cryptocurrency OR AI OR GPT OR chatgpt OR blockchain",
            "sortBy": "publishedAt",
            "from": yesterday_date.isoformat(),
        }
        super().__init__(self.third_party_api_key, self.api_key, self.end_point, self.params, self.file_name)
    
    def parse_article_and_save(self):
        while self.has_more_articles:
            self.params["page"] = self.page
            response = requests.get(self.end_point, params=self.params)
    
            news_data = response.json()
            if not news_data or 'articles' not in news_data:
                break
            articles = news_data["articles"]

            for article in articles:
                if not super().parse_article(article['title'],
                                             article['url'],
                                             article['source']['name'],
                                             article['description'],
                                             "News API"):
                    self.has_more_articles = False
                    break
            self.page += 1
        super().save_url_list()
        print("news api parse done")

class NewsBing(NewsProcessor):
    def __init__(self):
        self.has_more_articles = True
        self.third_party_api_key=os.getenv('BING_API_KEY')
        self.api_key=os.getenv('OPENAI_API_KEY')
        self.end_point="https://api.bing.microsoft.com/v7.0/news/search"
        self.file_name="bing.pkl"
        self.params = {
            'q': "finance OR economy OR technology OR stocks OR cryptocurrency OR AI OR GPT OR chatgpt OR blockchain",
            'count': 50,
            'offset': 0,
            "sortBy": "date",
        }
        self.headers = {
            'Ocp-Apim-Subscription-Key': self.third_party_api_key,
        }
        super().__init__(self.third_party_api_key, self.api_key, self.end_point, self.params, self.file_name)
    
    def parse_article_and_save(self):
        while self.has_more_articles:
            response = requests.get(self.end_point, params=self.params, headers=self.headers)
    
            news_data = response.json()
            if not news_data or 'value' not in news_data:
                break

            articles = news_data["value"]
            for article in articles:
                if not super().parse_article(article['name'],
                                             article['url'],
                                             article['provider'][0]['name'],
                                             "",
                                             "News Bing"):
                    self.has_more_articles = False
                    break

            if self.params['offset'] + self.params['count'] > news_data['totalEstimatedMatches']:
                break

            self.params['offset'] += self.params['count']

        super().save_url_list()
        print("bing parse done")
    
class NewsRss(NewsProcessor):
    def __init__(self):
        self.has_more_articles = True
        self.api_key=os.getenv('OPENAI_API_KEY')
        self.end_point="https://finance.yahoo.com/news/rssindex/"
        self.file_name="rss.pkl"
        super().__init__("", self.api_key, self.end_point, "", self.file_name)
    
    def parse_article_and_save(self):
        news_articles = feedparser.parse(self.end_point)
        articles = news_articles.entries
        for article in articles:
            if not super().parse_article(article.title,
                                         article.link,
                                         "",
                                         "",
                                         "News Rss"):
                break

        super().save_url_list()
        print("rss parse done")

class NewsYahoo(NewsProcessor):
    def __init__(self):
        self.has_more_articles = True
        self.api_key=os.getenv('OPENAI_API_KEY')
        self.end_point="https://finance.yahoo.com/news/"
        self.file_name="yahoo.pkl"
        super().__init__("", self.api_key, self.end_point, "", self.file_name)
    
    def parse_article_and_save(self):
        articles = fetch_links(self.end_point, self.url_list, scroll_pause_time=5, timeout=300, scroll_increment=1500)
        for article in articles:
            if not super().parse_article("",
                                         article,
                                         "",
                                         "",
                                         "News Yahoo"):
                break

        super().save_url_list()
        print("yahoo parse done")