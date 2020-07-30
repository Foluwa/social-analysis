"""
    Project's entry point
"""
from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS, cross_origin
import pymongo

# from logging.config import fileConfig
# fileConfig('logging.ini')
# import logging
import logging.config

logging.config.fileConfig('logging.ini')
logger = logging.getLogger('SENTIMENT-ANALYSIS')

# Twitter credentials
import credentials
# search api
from twitter_scrapper.search_api import TwitterStreamListner

twitter_search_api = TwitterStreamListner()
# instagram scrapper
from instagram_scrapper.username_scrapper import InstagramCommentScrapper

instagram_search_api = InstagramCommentScrapper()

# youtube
from youtube_scrapper.single_video import CommentsScrapper

youtube_api = CommentsScrapper()

app = Flask(__name__)
# logging.basicConfig(filename='logs.log', level=logging.DEBUG)

app.config['SECRET_KEY'] = credentials.SECRET_KEY
# socketio = SocketIO(app, engineio_logger=True, cors_allowed_origins='*')
socketio = SocketIO(app=app, cors_allowed_origins='*')
# Enable CORS on all routes
CORS(app, supports_credentials=True)


try:
    # Database configuration
    myclient = pymongo.MongoClient(credentials.DB_CONNECTION)
    mydatabase = myclient['sentiment_analysis']

except pymongo.errors.ConnectionFailure as error:
    app.logging.error('Connection failure: ', error)
except (AttributeError, pymongo.errors.OperationFailure):
    app.logging.error('Connection failure: ', AttributeError)


@app.route('/')
def index():
    response = 'Hello,welcome to social media sentiment analysis'
    return jsonify({
        'message': response
    })


""":arg
        Twitter Analysis Routes
"""

@app.route('/v1/api/analyse', methods=['GET', 'POST'])
def twitter_analyse_sentiment():
    if request.method == 'POST':
        # postman requests [comment when you want to use axios]
        # search_query = request.form['search_query']
        # axios requests[comment when you want to use postman]
        search_query = request.get_json()
        search_query = search_query['data']
        neutral, negative, positive, popular_words, popular_nums, collection_positive_created_at, collection_positive_polarity, collection_negative_created_at, collection_negative_polarity, collection_neutral_created_at, collection_neutral_polarity, today, since = twitter_search_api.twitter_search(
            search_query)
        negative = int(negative)
        neutral = int(neutral)
        positive = int(positive)
        response = {
            'status': 200,
            'success': 'success', 'negative': negative,
            'neutral': neutral, 'positive': positive,
            'chart_title': search_query,
            'popular_words': popular_words,
            'popular_nums': popular_nums,
            'collection_positive_created_at': collection_positive_created_at,
            'collection_positive_polarity': collection_positive_polarity,
            'collection_negative_created_at': collection_negative_created_at,
            'collection_negative_polarity': collection_negative_polarity,
            'collection_neutral_created_at': collection_neutral_created_at,
            'collection_neutral_polarity': collection_neutral_polarity,
            'today': today,
            'since': since
        }
    return jsonify(response)


@app.route('/get/collection')
def get_collection_names():
    try:
        collections = dict(
            (mongo_db, [collection for collection in myclient[credentials.DB_TWEET_COLLECTION].list_collection_names()])
            for mongo_db in myclient.list_database_names())
        db_collections = collections[credentials.DB_TWEET_COLLECTION]
        response = db_collections
        return jsonify(response)
    except pymongo.errors.ConnectionFailure as err:
        app.logging.error('Connection failure: ', err)
    except (AttributeError, pymongo.errors.OperationFailure):
        app.logging.error('Pymongo.errors.OperationFailure', AttributeError)


# Get Single Collection
@app.route('/get-previous-values/<string:collection_name>/')
def previous_searches_collection(collection_name):
    #
    db_name = credentials.DB_RETRIEVED_TWEETS_RESULTS
    # Database configurations
    db = myclient[db_name]
    collection_name = collection_name
    collection = db[collection_name]
    response = collection.find_one({"col_name": collection_name})
    response = {
        'col_name': response['col_name'], 'col_positive': response['col_positive'],
        'col_negative': response['col_negative'], 'col_neutral': response['col_neutral'],
        'popular_words': response['popular_words'], 'popular_nums': response['popular_nums'],
        'collection_positive_created_at': response['collection_positive_created_at'],
        'collection_positive_polarity': response['collection_positive_polarity'],
        'collection_negative_created_at': response['collection_negative_created_at'],
        'collection_negative_polarity': response['collection_negative_polarity'],
        'collection_neutral_created_at': response['collection_neutral_created_at'],
        'collection_neutral_polarity': response['collection_neutral_polarity']
    }
    try:
        return jsonify(response)
    except pymongo.errors.ConnectionFailure as err:
        app.logging.error('Connection failure: ', err)
    except (AttributeError, pymongo.errors.OperationFailure):
        app.logging.error('Pymongo.errors.OperationFailure', AttributeError)
    return 'Error encountered'


# Handle the app connecting to the websocket
@socketio.on('connect')
def test_connect():
    # socketio.sleep(0)
    socketio.emit('connect', {
        'message': 'Websocket connected!',
    }, broadcast=True)
    pass


from twitter_scrapper.streaming_api import StdOutListener

# Handle the app sending a message to the websocket
@socketio.on('message')
def handle_message(data):
    while True:
        the_search_query = data['data']
        stream_twitter = StdOutListener()
        stream_twitter.get_search_query(the_search_query)
        # socketio.sleep(0)

@socketio.on('disconnect')
def on_disconnect():
    socketio.stop()


# End of Twitter

""":arg
        INSTAGRAM Analysis Routes
"""


@app.route('/v1/api/instagram/analyse', methods=['GET', 'POST'])
def instagram_analyse_sentiment():
    global myresponse
    if request.method == 'POST':
        # postman requests [comment when you want to use axios]
        # search_query = request.form['search_query']
        # axios requests[comment when you shortcodes_list'want to use postman]
        search_query = request.get_json()
        search_query = search_query['data']
        # convert search query to lower case
        search_query = search_query.lower()
        response = instagram_search_api.entry_point(search_query)

    return jsonify(response)


@app.route('/instagram/get/collection')
def instagram_get_collection():
    try:
        # Connect Client to database
        # myclient = pymongo.MongoClient(credentials.DB_CONNECTION, maxPoolSize=50)
        # using list comprehensions to all collections in the database
        collections = dict(
            (mongo_db,
             [collection for collection in myclient[credentials.DB_INSTAGRAM_COLLECTION].list_collection_names()])
            for mongo_db in myclient.list_database_names())
        db_collections = collections[credentials.DB_INSTAGRAM_COLLECTION]
        response = db_collections
        return jsonify(response)
    except pymongo.errors.ConnectionFailure as err:
        app.logging.error("Could not connect to database: %s" % err)
    except (AttributeError, pymongo.errors.OperationFailure):
        app.logging.error("AttributeError, pymongo.errors.OperationFailure")


# Instgram Get Single Collection
@app.route('/instagram/previous-values/<string:collection_name>/')
def instagram_previous_collection(collection_name):
    try:
        # Database configurations
        db_name = credentials.DB_INSTAGRAM_COLLECTION
        db = myclient[db_name]
        collection = db[collection_name]
        response = collection.find_one()
        if response is not None:
            if "_id" in response:
                del response["_id"]
                return jsonify(response)
        else:
            response = {"message": "No data found for that collection name"}
            return jsonify(response)
    except pymongo.errors.ConnectionFailure as e:
        app.logging.error('Pymongo.errors.OperationFailure', e)
    except (AttributeError, pymongo.errors.OperationFailure):
        app.logging.error('Pymongo.errors.OperationFailure', AttributeError)
    return 'Error encountered'


# End of Instagram


""":arg
        YOUTUBE Analysis Routes    
"""


# ANALYSIS A SINGLE YOUTUBE VIDEO
@app.route('/youtube/video/', methods=['GET', 'POST'])
def youtube_video():
    print('GOT HERE !!')
    if request.method == 'POST':
        print('route youtube_channel')

        video_id = request.get_json()
        print('VIDEO_ID 1', video_id)
        data = video_id['video_id']
        print('VIDEO_ID 2', data)
        response = youtube_api.input_main(data)
        # print(response)
    return jsonify(response)


# RETRIEVE ALL YOUTUBE VIDEO SAVED
@app.route('/youtube/video/all')
def retreive_all_video_info():
    try:
        collections = dict((mongo_db, [collection for collection in
                                       myclient[credentials.DB_YOUTUBE_COLLECTION].list_collection_names()])
                           for mongo_db in myclient.list_database_names())
        response = collections[credentials.DB_YOUTUBE_COLLECTION]
        return jsonify(response)
    except pymongo.errors.ConnectionFailure as err:
        app.logging.error('Connection failure: ', err)
    except (AttributeError, pymongo.errors.OperationFailure):
        app.logging.error('Pymongo.errors.OperationFailure', AttributeError)


# Youtube Get Single Video Info
@app.route('/youtube/video/<string:video_id>/')
def youtube_video_info(video_id):
    try:
        # Database configurations
        db_name = credentials.DB_YOUTUBE_COLLECTION
        db = myclient[db_name]
        collection = db[video_id]
        response = collection.find_one()
        if response is not None:
            if "_id" in response:
                del response["_id"]
                return jsonify(response)
        else:
            response = {"message": "No data found for that collection name"}
            return jsonify(response)
    except pymongo.errors.ConnectionFailure as e:
        app.logging.error('Pymongo.errors.OperationFailure', e)
    except (AttributeError, pymongo.errors.OperationFailure):
        app.logging.error('Pymongo.errors.OperationFailure', AttributeError)
    return 'Error encountered'


if __name__ == '__main__':
    socketio.run(app, debug=True)
