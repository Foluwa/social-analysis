#!/usr/bin/env python

import datetime
import json

import nltk
import pandas as pd
import pymongo
import tweepy
from nltk.corpus import stopwords
from textblob import TextBlob
import os

#nltk.download('stopwords')
from nltk.tokenize import word_tokenize

from collections import Counter

stop_words = set(stopwords.words('english'))

now = datetime.datetime.now()
prefix = now.strftime("%Y-%m-%d-%H:%M:%S")

ACCESS_TOKEN = ""
ACCESS_TOKEN_SECRET = ""
CONSUMER_KEY = ""
CONSUMER_SECRET = ""

auth = tweepy.auth.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)


class TwitterStreamListner():
    

    # Method to open a file and append data to that specific file
    def ConvertTweetToCSV(self, search_query):
        search_query = search_query
        sentiment_list = []

        self.search_query = search_query
        self.sentiment_list = sentiment_list
        type(self.sentiment_list)

        # Database configurations
        try:
            myclient = pymongo.MongoClient(
                'mongodb+srv://admin:VGoLDnP82lPth3KJ@analysis-vfudj.mongodb.net/test?retryWrites=true&w=majority')
            mydatabase = myclient['sentiment_analysis']  # get database

            # Check if collection name already exists
            mycollection = mydatabase[search_query]
            if mycollection in mydatabase.list_collection_names():
                print(mycollection, ' exists in the database.')
            else:
                print(mycollection, ' does not exist in the database.')
                mycollection = mydatabase[search_query]
            print("Connected successfully and collection created!!!", mycollection, search_query, mydatabase)
        except:
            print("Could not connect to MongoDB")

        retrieved_tweets = []

        for tweet in tweepy.Cursor(api.search, q=['{search_query}'.format(search_query=search_query)],
                                   since="2020-03-15", until="2020-03-17", lang="en", limit=2).items():
#
            # to get full tweets of tweets that were trauncated
            if tweet.truncated == 'true':
                tweet.text = tweet.extended_tweet.full_text

            tweet_tokens = word_tokenize(tweet.text)

            filtered_sentence = [w for w in tweet_tokens if not w in stop_words]
            filtered_sentence = []

            for w in tweet_tokens:
                if w not in stop_words:
                    filtered_sentence.append(w)

            print(tweet_tokens)
            print(filtered_sentence)
            cleaned_tweet = ' '.join(filtered_sentence)
            print('The cleaned tweet is ', cleaned_tweet)
            print('_______________________________________________________________________________________')

            # performing sentiment analysis on the cleaned tweets
            tweet_details = TextBlob(cleaned_tweet)

            # https://textblob.readthedocs.io/en/dev/quickstart.html#sentiment-analysis
            # Subjective sentences generally refer to personal opinion, emotion or judgment
            # Objective refers to factual information.
            if tweet_details.polarity >= 0.2:
                sentiment = 'POSITIVE'
            elif tweet_details.polarity == 0:
                sentiment = 'NEUTRAL'
            else:
                sentiment = 'NEGATIVE'

            def datetime_handler(x):
                if isinstance(x, datetime.datetime):
                    return x.isoformat()
                raise TypeError("Unknown type")

            tweet_date = json.dumps(tweet.created_at, default=datetime_handler)
            collecttweet = {}
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
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(retrieved_tweets, f, ensure_ascii=False, indent=4)

        # Check if collection name already exists
        if mycollection in mydatabase.list_collection_names():
            mycollection.insert_many(retrieved_tweets)
            print('All Data saved')
        else:
            mycollection.insert_many(retrieved_tweets)
            print('All Data saved')

        # TODO: LOAD MONGODB INTO PANDAS
        try:
            mycollection = pd.DataFrame(list(mycollection.find()))
            highest_occurring_words = Counter(" ".join(mycollection['tweet_clean']).split()).most_common(10)

            sentiment_list = mycollection['tweet_sentiment'].value_counts()
            print('data frame loaded')

            if hasattr(sentiment_list, 'NEGATIVE'):
                print('NEGATIVE exists')
                negative = sentiment_list.NEGATIVE
            else:
                print('NEGATIVE DOES NOT exists')
                negative = 0

            if hasattr(sentiment_list, 'NEUTRAL'):
                print('NEUTRAL exists')
                neutral = sentiment_list.NEUTRAL
            else:
                print('NEUTRAL DOES NOT exists')
                neutral = 0

            if hasattr(sentiment_list, 'POSITIVE'):
                print('POSITIVE exists')
                positive = sentiment_list.POSITIVE
            else:
                print('POSITIVE DOES NOT exists')
                sentiment_list.POSITIVE = 0
                positive = 0

            print('Type of my sentiment list  ', type(sentiment_list))
            print('The highest occurring words are:  ', highest_occurring_words)
        except:
            print('Could not load data frame')

        popular_words = [i[0] for i in highest_occurring_words]
        popular_nums = [j[1] for j in highest_occurring_words]

        print('POSITIVE is : ', positive, 'NEGATIVE is :', negative, 'NEUTRAL IS : ', neutral)
        print('Words are ', popular_words, 'Numbers are ', popular_nums)
        return neutral, negative, positive, popular_words, popular_nums
