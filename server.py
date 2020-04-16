#!/usr/bin/python3
from flask import Flask, request, render_template, jsonify, make_response
from flask_socketio import SocketIO, emit, send
from flask_cors import CORS, cross_origin


# search api
from twitter_scrapper.search_api import TwitterStreamListner
TwitterSearchAPI = TwitterStreamListner()

from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import re
# streaming api
# from tweepy.streaming import StreamListener
# from twitter_scrapper.streaming_api import StdOutListener

import pandas as pd
from collections import Counter

import json
from textblob import TextBlob
import eventlet
eventlet.monkey_patch()

from nltk.corpus import stopwords
stoplist = stopwords.words('english')

app = Flask(__name__) 
app.config['SECRET_KEY'] = "asduicqdqweqweqwe9209"
CORS(app)
socketio = SocketIO(app, logger=True, cors_allowed_origins='*')



# Enter Twitter API Keys
access_token = "465633653-x7NHimVAVuMGieuVi9GIRFL8TcuCFUxSQ4NjIdHR"
access_token_secret = "hSwFbdEv906tsZ67igSuKXrR8kh3yg1CDg2ElVo9ZO7dK"
consumer_key = "VoPZQmgqLLn9fO3TdSVgdza6q"
consumer_secret = "F1HEnesPeHSn514KYJNRbBFQumbRmrCf74IPsEKXJhIttj3aMT"

# Initialize Global variable
tweet_count = 0
# Input number of tweets to be downloaded
n_tweets = 30000000000


# STDOUT CLASS
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
        re.sub(r'[^a-zA-Z]', '', tweet)
        # trim
        tweet = tweet.strip('\'"')
        # # split the tweets to a list
        # tweet = list(tweet.split(" "))

        tweet = [word for word in tweet.split() if word not in stoplist]

        print('Inside clean_tweet ', tweet)

        return tweet

    def on_data(self, data): #change data to tweet
        json_data = json.loads(data)
        # if (not json_data['retweeted']) and ('RT @' not in json_data['text']):
        try:
            global tweet_count
            global n_tweets
            global stream
            # declare pandas dataframe
            df = pd.DataFrame({"cleaned_tweets": []})
            if tweet_count < n_tweets:
                tweet_count +=1
                created_at = json_data['created_at']
                text = json_data['text']
                user = text = json_data['user']['screen_name']

                    # print(' Created At ', created_at )
                    # print( 'Text ', text)
                    # print('User name ', user)
                    # print('TWEET COUNT IS... ', tweet_count)
                print('________________________________________________________________')

                pd_text = self.clean_tweet(json_data['text'])
                print('CLEANED LOWER CASE IS ...', pd_text)

                df2 = pd.DataFrame({"cleaned_tweets": pd_text})
                print('The df2. ', df2)
                # df["cleaned_tweets"] = df["cleaned_tweets"]
                df = df.append(df2, ignore_index=True)
                df["cleaned_tweets"]
                print('PANDAS DATAFRAME ... ', df)
                most_occurring_words = Counter(" ".join(df['cleaned_tweets']).split()).most_common(10)
                print('Most occuring words: ', most_occurring_words)
                popular_words = [i[0] for i in most_occurring_words]
                popular_nums = [j[1] for j in most_occurring_words]
                print('Most popular words are: ',  popular_words, 'Most popular number are ',  popular_nums)

                tweet_details = TextBlob(text)
                    # https://textblob.readthedocs.io/en/dev/quickstart.html#sentiment-analysis
                    # Subjective sentences generally refer to personal opinion, emotion or judgment
                    # Objective refers to factual information.
                if tweet_details.polarity >= 0.2:
                    sentiment = 'POSITIVE'
                elif tweet_details.polarity == 0:
                    sentiment = 'NEUTRAL'
                else:                  
                    sentiment = 'NEGATIVE'

                with open('tweet.json', 'w') as json_file:
                    json.dump(json_data, json_file)
                socketio.emit('responseMessage', {'data': text, 'sentiment': sentiment, 'tweet_count': tweet_count,
                                                  'tweet_polarity': tweet_details.polarity,
                                                  'tweet_text': json_data['text'],                                                      'created_at': json_data['created_at'],
                                                  'popular_words': popular_words,
                                                  'highest_number': popular_nums
                                              })
            else:
                stream.disconnect()
                socketio.emit('responseMessage',  {'data': 'STREAM DISCONNECTED!!'})
                print('Stream disconnected!')
        except:
            print('error')

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






















# Database configurations
try:
    myclient = pymongo.MongoClient('mongodb+srv://admin:VGoLDnP82lPth3KJ@analysis-vfudj.mongodb.net/test?retryWrites=true&w=majority')
    mydatabase = myclient['sentiment_analysis']  # get database
    print('Connected successfully and collection created')
except:
    print('Could not connect to MongoDB')

@app.route('/')
def index():
    return jsonify({'message': '<h1>Hello,welcome to <strike>jumanji</strike> social media sentiment analysis</h1>'})

@app.route('/v1/api/analyse', methods=['GET', 'POST'])
def sentiment():
    if request.method == 'POST':
        print(request.method == 'POST')
        #search_query = request.form['search_query']  # for postman requests [comment when you want to use axios]
        search_query = request.get_json()  # for axios requests[comment when you want to use postman]
        search_query = search_query['data']  # for axios requests [comment when you want to use postman]
        print(search_query)

        neutral, negative, positive, popular_words, popular_nums = TwitterSearchAPI.ConvertTweetToCSV(search_query)

        print('Routes Page: ', 'POSITIVE is : ', positive, 'NEGATIVE is :', negative, 'NEUTRAL IS : ', neutral,
              'Popular words are: ', popular_words, 'Popular Numbers are: ', popular_nums)
        negative = int(negative)
        neutral = int(neutral)
        positive = int(positive)
    else:
        return '/v1/api/analyse'
    return jsonify({'negative': negative, 'neutral': neutral,
                    'positive': positive, 'chart_title': search_query,
                    'popular_words': popular_words, 'popular_nums': popular_nums
                    })

@app.route('/get/collection')
def get_collection_names():

    # Database configurations
    try:
        myclient = pymongo.MongoClient(
            'mongodb+srv://admin:VGoLDnP82lPth3KJ@analysis-vfudj.mongodb.net/test?retryWrites=true&w=majority')
        mydatabase = myclient['sentiment_analysis']  # get database
        mydatabase.listCollections()
        print('Connected successfully and collection created')
        return 'true'
    except:
        print('Could not connect to MongoDB')
        return 'false'


# Handle the webapp connecting to the websocket
@socketio.on('connect')
def test_connect():
    print('someone connected to websocket')
    pass
    # emit('responseMessage', {'data': 'Socket Connected!'})

# Handle the webapp sending a message to the websocket
@socketio.on('message')
def handle_message(data):
    print('someone sent to the websocket')
    print('Data is ', data['data'])
    the_search_query = data['data']
    print(type(data))
    # emit('responseMessage', {'data': 'Moronfoluwa Connected!'})
    # StreamTwitter = StdOutListener()
    # StreamTwitter.get_search_query(the_search_query)
    StreamTwitter = StdOutListener()
    StreamTwitter.get_search_query(the_search_query)



if __name__ == '__main__':
    print ("Socket is starting program")
    socketio.run(app, debug=True, host='127.0.0.1', port=5000)


    

