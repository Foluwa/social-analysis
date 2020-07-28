"""
    Twitter Search API
    https://developer.twitter.com/en/docs/tweets/search/api-reference/get-search-tweets
"""
from flask import jsonify
import datetime
import json
import pymongo
import tweepy
import logging
import pandas as pd
from textblob import TextBlob
from collections import Counter
from datetime import date, timedelta

# Twitter credentials
import credentials
import app
from .process_tweets import CommonMethods

common_methods = CommonMethods()

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

    # Method to open a file and append data to that specific file
    def twitter_search(self, search_query):
        search_query = search_query
        sentiment_list = []
        self.search_query = search_query
        self.sentiment_list = sentiment_list
        type(self.sentiment_list)
        today_database = str(today)
        since_database = str(since)
        try:
            mydatabase = app.mydatabase

            # Check if collection name already exists
            mycollection = mydatabase[search_query + '_' + today_database + '_' + 'to' + '_' + since_database]
            if mycollection in mydatabase.list_collection_names():
                logging.info('This Collection exists')
            else:
                mycollection = mydatabase[search_query + '_' + today_database + '_' + 'to' + '_' + since_database]
        except pymongo.errors.ConnectionFailure as e:
            logging.error('Could not connect to server: %s' % e)
            return "Could not connect to server: %s" % e
        except (AttributeError, pymongo.errors.OperationFailure):
            logging.error('This is an error message : ', AttributeError)
            return 'Database operation failure'

        retrieved_tweets = []
        collection_positive_created_at = []
        collection_positive_polarity = []
        collection_negative_created_at = []
        collection_negative_polarity = []
        collection_neutral_created_at = []
        collection_neutral_polarity = []
        try:
            for tweet in tweepy.Cursor(api.search, q=['{search_query}'.format(search_query=search_query)],
                                       since=since, until=today, lang="en", limit=2).items():
                # to get full tweets of tweets that were truncated
                if tweet.truncated == 'true':
                    tweet.text = tweet.extended_tweet.full_text
                cleaned_tweet, the_tweet = common_methods.clean_tweet(tweet=tweet.text)

                # Clean date format
                def datetime_handler(x):
                    if isinstance(x, datetime.datetime):
                        return x.isoformat()
                    raise TypeError("Unknown type")

                tweet_date = json.dumps(tweet.created_at, default=datetime_handler)

                # performing sentiment analysis on the cleaned tweets
                tweet_details = TextBlob(cleaned_tweet)
                """
                    https://textblob.readthedocs.io/en/dev/quickstart.html#sentiment-analysis
                    Subjective sentences generally refer to personal opinion, emotion or judgment
                    Objective refers to factual information.
                """
                if tweet_details.polarity >= 0.2:
                    sentiment = 'POSITIVE'
                    # Collects collection of all tweets created time for timeseries plot
                    collection_positive_created_at.append(tweet.created_at)
                    # Collects collection of all tweets polarity for timeseries plot
                    collection_positive_polarity.append(tweet_details.polarity)
                elif tweet_details.polarity == 0:
                    sentiment = 'NEUTRAL'
                    # Collects collection of all tweets created time for timeseries plot
                    collection_negative_created_at.append(tweet.created_at)
                    # Collects collection of all tweets polarity for timeseries plot
                    collection_negative_polarity.append(tweet_details.polarity)
                else:
                    sentiment = 'NEGATIVE'
                    # Collects collection of all tweets created time for timeseries plot
                    collection_neutral_created_at.append(tweet.created_at)
                    # Collects collection of all tweets polarity for timeseries plot
                    collection_neutral_polarity.append(tweet_details.polarity)

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

                if len(retrieved_tweets) == 0:
                    logging.debug('dict1 is Empty')

        except tweepy.error.TweepError as e:
            logging.error('Tweepy error encountered ', e)
        except tweepy.error.RateLimitError as e:
            logging.error('Tweepy rate limit error encountered ', e)

        # Check if list retrieved_tweets is empty
        if not retrieved_tweets:
            logging.info('No tweets were retrieved list could be empty')
        else:
            # Check if collection name already exists
            if mycollection in mydatabase.list_collection_names():
                # Drop the collection
                mycollection.my_collection.drop()
                # insert new data into the collection
                mycollection.insert_many(retrieved_tweets)
            else:
                mycollection.insert_many(retrieved_tweets)

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
            except:
                # Could not load dataframe
                return 'Could not load dataframe'

            popular_words = []
            popular_nums = []
            popular_words = [i[0] for i in highest_occurring_words]
            popular_nums = [j[1] for j in highest_occurring_words]

            # FOR A COLLECTION OF SEARCH
            try:
                myclient = pymongo.MongoClient(credentials.DB_CONNECTION)
                mydatabase = myclient[credentials.DB_RETRIEVED_TWEETS_RESULTS]
                mycollection = search_query + '_' + today_database + '_' + 'to' + '_' + since_database
                db_collection = mydatabase[search_query + '_' + today_database + '_' + 'to' + '_' + since_database]

                coll_record = {
                    'col_name': str(mycollection),
                    'col_positive': int(positive),
                    'col_negative': int(negative),
                    'col_neutral': int(neutral),
                    'popular_words': popular_words,
                    'popular_nums': popular_nums,
                    'collection_positive_created_at': collection_positive_created_at,
                    'collection_positive_polarity': collection_positive_polarity,
                    'collection_negative_created_at': collection_negative_created_at,
                    'collection_negative_polarity': collection_negative_polarity,
                    'collection_neutral_created_at': collection_neutral_created_at,
                    'collection_neutral_polarity': collection_neutral_polarity
                }

                # Check if collection name already exists
                if db_collection in mydatabase.list_collection_names():
                    # Do nothing
                    logging.info('Collection exists')
                else:
                    db_collection.insert_one(coll_record)
            except pymongo.errors.ConnectionFailure as e:
                return e
            except (AttributeError, pymongo.errors.OperationFailure):
                return 'DB Attribute error'

            return neutral, negative, positive, popular_words, popular_nums, collection_positive_created_at, collection_positive_polarity, collection_negative_created_at, collection_negative_polarity, collection_neutral_created_at, collection_neutral_polarity, today, since