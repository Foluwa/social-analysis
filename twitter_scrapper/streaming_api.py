"""
    Implemented Twitter Streaming API
    https://developer.twitter.com/en/docs/tutorials/consuming-streaming-data
"""
try:
    from __main__ import socketio, credentials
    import credentials
except ImportError:
    from app import socketio
import credentials
import json
import pandas as pd
import logging
from tweepy import OAuthHandler, Stream, StreamListener
from collections import Counter
from textblob import TextBlob
from .process_tweets import CommonMethods

common_methods = CommonMethods()
# Enter Twitter API Keys
access_token = credentials.ACCESS_TOKEN
access_token_secret = credentials.ACCESS_TOKEN_SECRET
consumer_key = credentials.CONSUMER_KEY
consumer_secret = credentials.CONSUMER_SECRET

all_tweets_dataframe = None


# Create the class that will handle the tweet stream
class StdOutListener(StreamListener):
    """
        the __init__ method initialises the class and makes it possible to call the get_search_query method
        with the search keywords
    """

    def __init__(self):
        # declare pandas dataframe
        super(StdOutListener, self).__init__()
        # global all_tweets_dataframe
        self.all_tweets_dataframe = pd.DataFrame({"cleaned_tweets": []})

    """
        the on_data method streams tweets in realtime, the method is from the tweepy module
    """

    def on_data(self, data):
        # Load streamed data into JSON format
        json_data = json.loads(data)

        # Reassigning variables to streamed data
        created_at = json_data['created_at']
        text = json_data['text']
        user = text = json_data['user']['screen_name']

        # Tweet Cleaning: Calls method on tweet  to remove non-english characters and stopwords from tweet
        tweet_text, pd_text = common_methods.clean_tweet(json_data['text'])

        # Assign cleaned tweets to a dataframe
        tweet_dataframe = pd.DataFrame({'cleaned_tweets': pd_text})

        try:
            # Analyse retrieved tweet with Textblob sentiment
            tweet_details = TextBlob(tweet_text)
            logging.info('Tweet details is : ', tweet_details, tweet_details.polarity, tweet_details.subjectivity)

            """
                https://textblob.readthedocs.io/en/dev/quickstart.html#sentiment-analysis
                Subjective sentences generally refer to personal opinion, emotion or judgment
                Objective refers to factual information.
            """
            if tweet_details.polarity > 0:
                sentiment = 'POSITIVE'
            elif tweet_details.polarity == 0:
                sentiment = 'NEUTRAL'
            elif tweet_details.polarity < 0:
                sentiment = 'NEGATIVE'

            # Concatenate the all_tweets_dataframe with the single retrieved tweets dataframe
            self.all_tweets_dataframe = pd.concat([self.all_tweets_dataframe, tweet_dataframe], ignore_index=True)

            # Count the most occurring words and load them into arrays
            most_occurring_words = Counter(" ".join(self.all_tweets_dataframe['cleaned_tweets']).split()).most_common(
                15)
            popular_words = [i[0] for i in most_occurring_words]
            popular_nums = [j[1] for j in most_occurring_words]

            # Use socket to emit processed data to client
            socketio.emit('response', {
                'data': text, 'sentiment': sentiment, 'tweet_polarity': tweet_details.polarity,
                'tweet_text': json_data['text'], 'created_at': created_at,
                'popular_words': popular_words, 'popular_nums': popular_nums
            }, broadcast=True)
        except BaseException:
            # Error encountered
            socketio.sleep(0)
            pass

    """
        the on_error method
    """

    def on_error(self, status):
        logging.info('Status : ', status)

    """
        Handles Twitter authentication and the connection to Twitter Streaming API
    """

    def get_search_query(self, search_query):
        l = StdOutListener()
        auth = OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        stream = Stream(auth, l)
        stream.filter(track=[search_query], languages=['en'])
