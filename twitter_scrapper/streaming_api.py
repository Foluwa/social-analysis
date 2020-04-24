"""
    Implemented Twitter Streaming API
    https://developer.twitter.com/en/docs/tutorials/consuming-streaming-data
"""
import eventlet
eventlet.monkey_patch()
try:
    from __main__ import socketio, credentials
    import credentials
except ImportError:
    from app import socketio

import credentials
import re
import json
import pandas as pd
from tweepy import Stream
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from collections import Counter
from textblob import TextBlob

from words import stop_words

# Enter Twitter API Keys
access_token = credentials.ACCESS_TOKEN
access_token_secret = credentials.ACCESS_TOKEN_SECRET
consumer_key = credentials.CONSUMER_KEY
consumer_secret = credentials.CONSUMER_SECRET

# Initialize Global variable
tweet_count = 0
# Input number of tweets to be downloaded
n_tweets = 300000

# Create the class that will handle the tweet stream
class StdOutListener(StreamListener):

    def clean_tweet(self, tweet):
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
        # tweet = list(map(lambda st: str.replace(st, "rt", ""), tweet))
        # trim
        tweet = tweet.strip('\'"')
        # # split the tweets to a list
        tweet = [word for word in tweet.split() if word not in stop_words]
        # convert list to sentence
        tweet_text = ' '.join(word for word in tweet)
        return tweet, tweet_text

    def on_data(self, data):
        json_data = json.loads(data)
        try:
            global tweet_count
            global n_tweets
            global stream

            # declare pandas dataframe
            all_tweets_dataframe = pd.DataFrame({"cleaned_tweets": []})
            if tweet_count < n_tweets:
                tweet_count += 1
                created_at = json_data['created_at']
                text = json_data['text']
                user = text = json_data['user']['screen_name']
                pd_text, tweet_text = self.clean_tweet(json_data['text'])
                # Assign cleaned tweets to the tweet dataframe
                tweet_dataframe = pd.DataFrame({'cleaned_tweets': pd_text})
                # Analyse sentiment
                tweet_details = TextBlob(tweet_text)
                '''
                    https://textblob.readthedocs.io/en/dev/quickstart.html#sentiment-analysis
                    Subjective sentences generally refer to personal opinion, emotion or judgment
                    Objective refers to factual information.
                '''
                if tweet_details.polarity > 0:
                    sentiment = 'POSITIVE'
                elif tweet_details.polarity == 0:
                    sentiment = 'NEUTRAL'
                elif tweet_details.polarity < 0:
                    sentiment = 'NEGATIVE'
                # Append current cleaned tweets to all tweet dataframe
                all_tweets_dataframe = all_tweets_dataframe.append(tweet_dataframe)

                # Count the most occuring words and load them into arrays
                most_occurring_words = Counter(" ".join(all_tweets_dataframe['cleaned_tweets']).split()).most_common(10)
                popular_words = [i[0] for i in most_occurring_words]
                popular_nums = [j[1] for j in most_occurring_words]

                # Emit response message
                socketio.emit('responseMessage', {'data': text, 'sentiment': sentiment,
                                                  'tweet_polarity': tweet_details.polarity,
                                                  'tweet_text': json_data['text'],
                                                  'created_at': json_data['created_at'],
                                                  'popular_words': popular_words,
                                                  'popular_nums': popular_nums
                                                  }, broadcast=True)
            else:
                stream.disconnect()
                socketio.emit("responseMessage", {"data": "STREAM DISCONNECTED!!"})
        except BaseException:
            # Error encountered
            pass

    def on_error(self, status_code):
        if status_code == 420:
            # returning False in on_data disconnects the stream
            return False

    # Handles Twitter authentication and the connection to Twitter Streaming API
    def get_search_query(self, search_query):
        print('Data received is ', search_query)
        l = StdOutListener()
        auth = OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        stream = Stream(auth, l)
        stream.filter(track=search_query)
