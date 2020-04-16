#!/usr/bin/env python
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from flask_socketio import SocketIO, emit, send
import re
from server import socketio

# Enter Twitter API Keys
access_token = "465633653-x7NHimVAVuMGieuVi9GIRFL8TcuCFUxSQ4NjIdHR"
access_token_secret = "hSwFbdEv906tsZ67igSuKXrR8kh3yg1CDg2ElVo9ZO7dK"
consumer_key = "VoPZQmgqLLn9fO3TdSVgdza6q"
consumer_secret = "F1HEnesPeHSn514KYJNRbBFQumbRmrCf74IPsEKXJhIttj3aMT"

# Initialize Global variable
tweet_count = 0
# Input number of tweets to be downloaded
n_tweets = 3


#STDOUT CLASS
# Create the class that will handle the tweet stream
class StdOutListener(StreamListener):

    def on_data(self, data):
        tweet_data = data
        try:
            global tweet_count
            global n_tweets
            global stream
            if tweet_count < n_tweets:
                #send(data)
                # print(data)
                print('_______________________________')
                # emit('responseMessage', {'data': data})
                socketio.emit('responseMessage', {'data': 'Moronfoluwa Connected!00'})
                #send(data)
                tweet_count += 1
                return True
            else:
                #stream.disconnect()
                print('Stream disconnected!')
        except Exception as error:
            print(error)

    def on_error(self, status_code):
        if status_code == 420:
            #returning False in on_data disconnects the stream
            print('Stream disconnected!')
            return False

    # Handles Twitter authentication and the connection to Twitter Streaming API
    def get_search_query(self, search_query):
        print('Inside stream listener ..... ',search_query)
        l = StdOutListener()
        auth = OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        stream = Stream(auth, l)
        stream.filter(track=search_query)


# END OF STDOUT CLASS