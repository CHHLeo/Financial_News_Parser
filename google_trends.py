import time
import random
import numpy as np
from scipy.stats import linregress
from pytrends.request import TrendReq
import concurrent.futures
from utils import printd

def get_trend_data(keyword):
    flag1 = False
    flag2 = False
    timeout = 900.0  # Set the desired timeout duration in seconds.
    start_time = time.time()  # Record the start time.
    pytrends = TrendReq(hl='en-US', tz=360, timeout=(500, 500))
    while True:
        current_time = time.time()
        elapsed_time = current_time - start_time
        if elapsed_time > timeout:
            printd("trend Timeout reached!")
            break
        try:
            if not flag1:
                pytrends.build_payload([keyword], cat=0, timeframe='now 7-d', geo='', gprop='')
                flag1 = True
            if not flag2:
                interest_over_time_df = pytrends.interest_over_time()
                flag2 = True
            break
        except Exception as e:
            creds = str(random.randint(10000, 0x7fffffff)) + ":" + "foobar"
            pytrends.proxies = []
            pytrends.proxies.insert(0, 'socks5h://{}@localhost:9051'.format(creds))
            time.sleep(random.randint(1, 5))

    if not interest_over_time_df.empty:
        x = np.arange(len(interest_over_time_df))
        y = interest_over_time_df[keyword].values
        #TODO: maybe another regression?
        slope, _, _, _, _ = linregress(x, y)
        return (keyword, slope)
    else:
        return (keyword,0)

def get_trends(keywords):
    trends_data = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        trends_data = list(executor.map(get_trend_data, keywords))

    return trends_data

