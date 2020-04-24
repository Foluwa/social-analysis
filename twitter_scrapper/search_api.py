"""
    Twitter Search API
    https://developer.twitter.com/en/docs/tweets/search/api-reference/get-search-tweets
"""
import re
import datetime
import json
import pymongo
import tweepy
import pandas as pd
from textblob import TextBlob
from collections import Counter
from words import stop_words
from datetime import date, timedelta

# Twitter credentials
import credentials

ACCESS_TOKEN = credentials.ACCESS_TOKEN
ACCESS_TOKEN_SECRET = credentials.ACCESS_TOKEN_SECRET
CONSUMER_KEY = credentials.CONSUMER_KEY
CONSUMER_SECRET = credentials.CONSUMER_SECRET
auth = tweepy.auth.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

# Date
today = date.today()
since = date.today() - timedelta(7)
now = datetime.datetime.now()
prefix = now.strftime("%Y-%m-%d-%H:%M:%S")

class TwitterStreamListner:

    def clean_tweet(self, tweet):
        print('CLEAN_TWEET  ', tweet)
        # process the tweets
        # Convert to lower case
        tweet = tweet.lower()
        # Remove www.* or https?://*
        tweet = re.sub('((www\.[^\s]+)|(https?://[^\s]+))', '', tweet)
        # Remove @username
        tweet = re.sub('@[^\s]+', '', tweet)
        # Remove additional white spaces
        tweet = re.sub('[\s]+', ' ', tweet)
        # Replace #word with word
        tweet = re.sub(r'#([^\s]+)', r'\1', tweet)
        # Replace none english characters with nothing
        tweet = re.sub(r'[^a-zA-Z ]', '', tweet)  # Make sure there is a space after Z
        # trim
        tweet = tweet.strip('\'"')
        # # split the tweets to a list
        tweet = [word for word in tweet.split() if word not in stop_words]
        # conver list to sentence
        tweet_text = ' '.join(word for word in tweet)
        print('inside clean tweet_  ', tweet_text)
        return tweet_text

    # Method to open a file and append data to that specific file
    def twitter_search(self, search_query):
        search_query = search_query
        print('inside twitter search method', search_query)
        sentiment_list = []
        self.search_query = search_query
        self.sentiment_list = sentiment_list
        type(self.sentiment_list)
        today_database = str(today)
        since_database = str(since)
        try:
            # Database configurations
            myclient = pymongo.MongoClient(credentials.MONGODB_ADDON_URI)
            mydatabase = myclient['sentiment_analysis']

            # Check if collection name already exists
            mycollection = mydatabase[search_query + '_' + today_database + '_' + 'to' + '_' + since_database]
            if mycollection in mydatabase.list_collection_names():
                print(mycollection, ' exists in the database.')
            else:
                mycollection = mydatabase[search_query + '_' + today_database + '_' + 'to' + '_' + since_database]
                print(mycollection, ' exists in the database.222')
        except pymongo.errors.ConnectionFailure as e:
            print("Could not connect to server: %s" % e)
        except (AttributeError, pymongo.errors.OperationFailure):
            print('Operation error')

        retrieved_tweets = []
        try:
            for tweet in tweepy.Cursor(api.search, q=['{search_query}'.format(search_query=search_query)],
                                       since=since, until=today, lang="en", limit=2).items():
                # to get full tweets of tweets that were truncated
                if tweet.truncated == 'true':
                    tweet.text = tweet.extended_tweet.full_text
                cleaned_tweet = self.clean_tweet(tweet.text)
                print('Cleaned tweet is .. ', cleaned_tweet)

                # performing sentiment analysis on the cleaned tweets
                tweet_details = TextBlob(cleaned_tweet)
                """
                    https://textblob.readthedocs.io/en/dev/quickstart.html#sentiment-analysis
                    Subjective sentences generally refer to personal opinion, emotion or judgment
                    Objective refers to factual information.
                """
                if tweet_details.polarity >= 0.2:
                    sentiment = 'POSITIVE'
                    print('POSITIVE')
                elif tweet_details.polarity == 0:
                    sentiment = 'NEUTRAL'
                    print('NEUTRAL')
                else:
                    sentiment = 'NEGATIVE'
                    print('NEGATIVE')

                def datetime_handler(x):
                    if isinstance(x, datetime.datetime):
                        return x.isoformat()
                    raise TypeError("Unknown type")

                tweet_date = json.dumps(tweet.created_at, default=datetime_handler)
                # collecttweet = {}
                collecttweet = {
                    'tweet_date': tweet_date,
                    'tweet_userid': tweet.id,
                    'tweet_username': tweet.user.screen_name,
                    'tweet_clean': cleaned_tweet,
                    'tweet_text': tweet.text,
                    'tweet_user_followers': tweet.user.followers_count,
                    'tweet_polarity': tweet_details.polarity,
                    'tweet_subjectivity': tweet_details.subjectivity,
                    'tweet_sentiment': sentiment
                }
                retrieved_tweets.append(collecttweet)
                # Check if list retrieved_tweets is empty
                if not retrieved_tweets:
                    return 'No tweets were retrieved list could be empty'
        except tweepy.error.TweepError as e:
            print('Tweepy error encountered ', e)
        except tweepy.error.RateLimitError as e:
            print('Rate limit exceeded ', e)

        # Check if list retrieved_tweets is empty
        if not retrieved_tweets:
            print('No tweets were retrieved list could be empty')

        # Check if collection name already exists
        if mycollection in mydatabase.list_collection_names():
            print('Retrieved tweets... ', retrieved_tweets)
            mycollection.insert_many(retrieved_tweets)
        else:
            mycollection.insert_many(retrieved_tweets)
            print('Retrieved tweets... ', retrieved_tweets)

        try:
            mycollection = pd.DataFrame(list(mycollection.find()))
            highest_occurring_words = Counter(" ".join(mycollection['tweet_clean']).split()).most_common(15)
            sentiment_list = mycollection['tweet_sentiment'].value_counts()

            if hasattr(sentiment_list, 'NEGATIVE'):
                negative = sentiment_list.NEGATIVE
            else:
                negative = 0
            if hasattr(sentiment_list, 'NEUTRAL'):
                neutral = sentiment_list.NEUTRAL
            else:
                neutral = 0
            if hasattr(sentiment_list, 'POSITIVE'):
                positive = sentiment_list.POSITIVE
            else:
                sentiment_list.POSITIVE = 0
                positive = 0
            print('Dataframe loaded')
        except:
            # Could not load dataframe
            print('Could not load dataframe')

        popular_words = []
        popular_nums = []
        popular_words = [i[0] for i in highest_occurring_words]
        popular_nums = [j[1] for j in highest_occurring_words]

        mydatabase = myclient['sentiment_analysis_results']
        mycollection = search_query + '_' + today_database + '_' + 'to' + '_' + since_database
        db_collection = mydatabase[search_query + '_' + today_database + '_' + 'to' + '_' + since_database]

        coll_record = {
            'col_name': str(mycollection),
            'col_positive': int(positive),
            'col_negative': int(negative),
            'col_neutral': int(neutral),
            'popular_words': popular_words,
            'popular_nums': popular_nums
        }

        # Check if collection name already exists
        if db_collection in mydatabase.list_collection_names():
            # Do nothing
            print(db_collection, ' exists in the database.')
        else:
            db_collection.insert_one(coll_record)
            print(coll_record, ' Inserted successfully')

        return neutral, negative, positive, popular_words, popular_nums, today, since
