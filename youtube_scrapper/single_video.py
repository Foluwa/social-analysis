"""
Scrapes comments from youtube channel

Variables:
    # shortcodes: refers to instagram uniques code for each user account post (similar to id for a post)
"""
import os
import json
import datetime
from bson.objectid import ObjectId
from werkzeug import Response
import requests
from textblob import TextBlob
import googleapiclient.discovery
import pymongo
import credentials
import logging


class MongoJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        elif isinstance(obj, ObjectId):
            return unicode(obj)
        return json.JSONEncoder.default(self, obj)


# https://www.googleapis.com/youtube/v3/videos?part=snippet&id=wtLJPvx7-ys&key=AIzaSyDQwKqbOEH3_YpCh6NZCpJc0CS5mBjbsF8

class CommentsScrapper:
    def __init__(self):
        # print('server started!')
        self.video_info = []
        self.positive_comments = []
        self.negative_comments = []
        self.neutral_comments = []
        self.API_KEY = "AIzaSyDQwKqbOEH3_YpCh6NZCpJc0CS5mBjbsF8"

    def save_to_db(self, video_id, video_info):
        # data = json.dumps(video_info)
        data = video_info
        # Save data to DB
        try:
            myclient = pymongo.MongoClient(credentials.DB_CONNECTION)
            mydatabase = myclient[credentials.DB_YOUTUBE_COLLECTION]
            db_collection = mydatabase[video_id]

            # Check if collection name already exists
            if db_collection in mydatabase.list_collection_names():
                logging.info('Collection exists')
                print('type iss', type(video_info))
                db_collection.insert_one(dict(data))
            else:
                db_collection.insert_one(dict(data))
                print('type iss', type(video_info))
            logging.info('Data saved successfully into Database.')
        except pymongo.errors.ConnectionFailure as e:
            logging.error('pymongo.errors.ConnectionFailure: ', e)
        except (AttributeError, pymongo.errors.OperationFailure) as error:
            logging.error('AttributeError, pymongo.errors.OperationFailure: ', error)
            # return 'DB Attribute error'

    def retrieve_video_info(self, video_id, api_key):
        """Method is called in a loop and  concatenates the shortcode for each post in each loop to get the url of the post.
            Args:
                :param api_key:
                :param video_id:
            Returns:
                String:  url to video information
         """
        string1 = 'https://www.googleapis.com/youtube/v3/videos?part=snippet&id='
        string2 = video_id
        string3 = '&key='
        string4 = api_key
        video_url = ''.join([string1, string2, string3, string4])

        # TODO retrieve video information
        # video_url = 'https://www.googleapis.com/youtube/v3/videos?part=snippet&id=wtLJPvx7-ys&key=AIzaSyDQwKqbOEH3_YpCh6NZCpJc0CS5mBjbsF8'
        try:
            r = requests.get(video_url)
            r.raise_for_status()
            # check if URL is valid and return 200
            if r.status_code == 200:
                data = r.json()
                title = data['items'][0]['snippet']['title']
                description = data['items'][0]['snippet']['description']
                video_publishedAt = data['items'][0]['snippet']['publishedAt']
                channelTitle = data['items'][0]['snippet']['channelTitle']

                video_info = {
                    'title': title,
                    'description': description,
                    'video_publishedAt': video_publishedAt,
                    'channelTitle': channelTitle,

                }
                return video_info

            elif r.status_code == 400:
                print('Req is 400')
                return 'Error Encountered!'
            else:
                print('Error with video id or api key')
                return 'Error Encountered!'
        except requests.exceptions.HTTPError as err:
            print(err)

    def retrieve_comments(self, video_id):
        """:keyword
        """
        # https://stackoverflow.com/questions/36585824/how-to-get-all-comments-more-than-100-of-a-video-using-youtube-data-api-v3
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        api_service_name = "youtube"
        api_version = "v3"
        DEVELOPER_KEY = "AIzaSyDQwKqbOEH3_YpCh6NZCpJc0CS5mBjbsF8"

        youtube = googleapiclient.discovery.build(api_service_name, api_version, developerKey=DEVELOPER_KEY)
        request = youtube.commentThreads().list(
            part="snippet", maxResults=100, videoId=video_id, textFormat="plainText",
            order="time").execute()  # order= time(default), orderUnspecified, relevance

        comments_data = request['items']

        for i, comment in enumerate(comments_data):
            user_id = comments_data[i]['id']
            videoId = comments_data[i]['snippet']['videoId']
            totalReplyCount = comments_data[i]['snippet']['totalReplyCount']
            viewerRating = comments_data[i]['snippet']['topLevelComment']['snippet']['viewerRating']
            likeCount = comments_data[i]['snippet']['topLevelComment']['snippet']['likeCount']
            textOriginal = comments_data[i]['snippet']['topLevelComment']['snippet']['textOriginal']
            publishedAt = comments_data[i]['snippet']['topLevelComment']['snippet']['publishedAt']
            authorChannelUrl = comments_data[i]['snippet']['topLevelComment']['snippet']['authorChannelUrl']
            authorDisplayName = comments_data[i]['snippet']['topLevelComment']['snippet']['authorDisplayName']

            text_analysis = TextBlob(textOriginal)
            polarity = text_analysis.polarity
            subjectivity = text_analysis.subjectivity

            values = {
                'user_id': user_id,
                'videoId': videoId,
                'totalReplyCount': totalReplyCount,
                'viewerRating': viewerRating,
                'likeCount': likeCount,
                'textOriginal': textOriginal,
                'publishedAt': publishedAt,
                'authorChannelUrl': authorChannelUrl,
                'authorDisplayName': authorDisplayName,
                'sentiment': {
                    'polarity': polarity,
                    'subjectivity': subjectivity
                }

            }
            if values['sentiment']['polarity'] > 0:
                # positive
                self.positive_comments.append(values)
            elif values['sentiment']['polarity'] < 0:
                # negative
                self.negative_comments.append(values)
            else:
                # neutral
                self.neutral_comments.append(values)
        return self.positive_comments, self.negative_comments, self.neutral_comments  # self.video_info

    def input_main(self, video_id):
        """":arg
        https://developers.google.com/youtube/v3/docs/commentThreads/list?apix=true#parameters

        """
        print('Channel Name input main :', video_id)

        # Retrieve Comments Data

        positive_comments, negative_comments, neutral_comment = self.retrieve_comments(video_id=video_id)

        # Retrieve video information
        video_info = self.retrieve_video_info(video_id=video_id, api_key='AIzaSyDQwKqbOEH3_YpCh6NZCpJc0CS5mBjbsF8')
        number_of_comments = len(positive_comments) + len(negative_comments) + len(neutral_comment)
        print(number_of_comments)
        # Append comments data to video info
        video_info.update({'comments_data': {'positive_comments': positive_comments,
                                             'negative_comments': negative_comments,
                                             'neutral_comments': neutral_comment},
                           'comments_length': number_of_comments,
                           'comments_size': {
                               'positive_length': len(positive_comments),
                               'negative_length': len(negative_comments),
                               'neutral_length': len(neutral_comment)
                           }})
        print(type(video_info))
        self.save_to_db(video_id=video_id, video_info=video_info)

        return video_info
