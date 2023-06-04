from news_processor import NewsApi, NewsBing, NewsRss, NewsYahoo

while True:
    #NewsApi().parse_article_and_save()
    #NewsRss().parse_article_and_save()
    NewsBing().parse_article_and_save()
    #NewsYahoo().parse_article_and_save()