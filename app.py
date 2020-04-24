"""
    Project's entry point
"""

# eventlet was imported first to prevent RecursionError
# https://github.com/eventlet/eventlet/issues/526
import eventlet
eventlet.monkey_patch()
from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS, cross_origin
# Twitter credentials
import credentials
import pymongo
import requests
# search api
from twitter_scrapper.search_api import TwitterStreamListner
twitter_search_api = TwitterStreamListner()

app = Flask(__name__)
socketio = SocketIO(app, logger=True, cors_allowed_origins='*')

try:
    # Database configurations
    myclient = pymongo.MongoClient(credentials.MONGODB_ADDON_URI)
    mydatabase = myclient['sentiment_analysis']
    print('Connection successful')
except pymongo.errors.ConnectionFailure as error:
    print("Could not connect to server: %s" % error)
except (AttributeError, pymongo.errors.OperationFailure):
    print('Operation error')

app.config['SECRET_KEY'] = 'asduicqdqweqweqwe9209'
CORS(app)
socketio = SocketIO(app, engineio_logger=True, cors_allowed_origins='*')

# Initialize Global variable
tweet_count = 0
# Input number of tweets to be downloaded
n_tweets = 30000000000


@app.route('/')
def index():
    return jsonify({
        'message': '<h1>Hello,welcome to social media sentiment analysis</h1>'
    })


@app.route('/v1/api/analyse', methods=['GET', 'POST'])
def sentiment():
    if request.method == 'POST':
        print(request.method == 'POST')
        # postman requests [comment when you want to use axios]
        # search_query = request.form['search_query']
        # axios requests[comment when you want to use postman]
        search_query = request.get_json()
        search_query = search_query['data']
        print(search_query)
        neutral, negative, positive, popular_words, popular_nums, today, since = twitter_search_api.twitter_search(
            search_query)
        negative = int(negative)
        neutral = int(neutral)
        positive = int(positive)
        print('Try successful')
        response = {
            'success': 'success', 'negative': negative,
            'neutral': neutral, 'positive': positive,
            'chart_title': search_query, 'popular_words': popular_words,
            'popular_nums': popular_nums, 'today': today, 'since': since
        }
    return jsonify(response)


@app.route('/get/collection')
def get_collection_names():
    try:
        myclient = pymongo.MongoClient(credentials.MONGODB_ADDON_URI, maxPoolSize=50)
        collections = dict((mongo_db, [collection for collection in myclient['sentiment_analysis'].collection_names()])
                           for mongo_db in myclient.database_names())
        print('the d is ... ', collections['sentiment_analysis'])
        db_collections = collections['sentiment_analysis']
        response = db_collections
        return jsonify(response)
    except pymongo.errors.ConnectionFailure as e:
        print("Could not connect to server: %s" % e)
    except (AttributeError, pymongo.errors.OperationFailure):
        print('Operation error')


# Get Single Collection
@app.route('/get-previous-values/<string:collection_name>/')
def previous_searches(collection_name):
    print('ID IS >>> ' + collection_name)
    myclient = pymongo.MongoClient(credentials.MONGODB_ADDON_URI)
    db_name = 'sentiment_analysis_results'
    # Database configurations
    db = myclient[db_name]
    collection_name = collection_name
    collection = db[collection_name]
    response = collection.find_one({"col_name": collection_name})
    response = {
        'col_name': response['col_name'], 'col_positive': response['col_positive'],
        'col_negative': response['col_negative'], 'col_neutral': response['col_neutral'],
        'popular_words': response['popular_words'], 'popular_nums': response['popular_nums']
    }
    try:
        return jsonify(response)
    except pymongo.errors.ConnectionFailure as e:
        print("Could not connect to server: %s" % e)
    except (AttributeError, pymongo.errors.OperationFailure):
        print('Operation error')
    except pymongo.errors.ConnectionFailure:
        print('Connection failure')
    return 'Error encountered'


"""
    Handle the webapp connecting to the websocket
"""


@socketio.on('connect')
def test_connect():
    pass


# streaming api
# import tweepy.streaming
# from tweepy.streaming import StreamListener
from twitter_scrapper.streaming_api import StdOutListener


# Handle the webapp sending a message to the websocket
@socketio.on('message')
def handle_message(data):
    while True:
        the_search_query = data['data']
        stream_twitter = StdOutListener()
        stream_twitter.get_search_query(the_search_query)


if __name__ == '__main__':
    app.auto_reload = True
    socketio.run(app, debug=True)

