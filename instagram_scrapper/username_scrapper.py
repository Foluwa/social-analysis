"""
Scrapes comments from instagram username account

Variables:
    shortcodes: refers to instagram uniques code for each user account post (similar to id for a post)
"""

import requests
import urllib.request
import json
from bson import ObjectId
import pandas as pd
from datetime import datetime
import time
from textblob import TextBlob
import pymongo
import credentials
import logging


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


class InstagramCommentScrapper:
    def __init__(self):
        self.shortcodes_list = []  # list of retrieved short codes

    #
    def timestamp_to_weekday(self, timestamp):
        """Method for converting time stamp to weekday equivalent
            Args:
                timestamp (int)
            Returns:
                String: weekday equivalent
         """
        return time.strftime('%A', time.localtime(timestamp))

    def link_to_account_url(self, username):
        """Method for scrapping url for the username supplied
            Args:
                username (String)
            Returns:
                String: url to scrape
         """
        string1 = 'https://www.instagram.com/'
        string2 = username
        string3 = '/?__a=1'
        return ''.join([string1, string2, string3])

    #    this function
    def account_shortcodes(self, account_url):

        """Method accepts the url of an account as a parameter and returns the shortcode of each post found on that account as a list
            Args:
                account_url (String)
            Returns:
                List:  shortcodes of useraccounts
         """
        # Todo:  check if parameter account_url is not empty
        # Todo:  check if  account_url exists first to know if the account exists

        # pass parameter to # link_to_account_url username
        account_url = self.link_to_account_url(account_url)
        r = requests.get(account_url)
        # Check if the URL and username return http statuscode of 200
        if r.status_code == 200:
            user_id = r.json()['graphql']['user']['id']
            end_cursor = ''

            r = requests.get('https://www.instagram.com/graphql/query/',
                             params={
                                 'query_id': '17880160963012870',
                                 'id': user_id,
                                 'first': 10,  # check the number of data they have and replace it here, limit to 30
                                 'after': end_cursor
                             }
                             )
            graphql = r.json()['data']
            for edge in graphql['user']['edge_owner_to_timeline_media']['edges']:
                self.shortcodes_list.append(edge['node']['shortcode'])
            return self.shortcodes_list
        else:
            logging.info('Account not found error or typo in username or keyword')
            return 'Account not found error or typo in username or keyword'

    def join_shortcode_url(self, shortcode):
        """Method is called in a loop and  concatenates the shortcode for each post in each loop to get the url of the post.
            Args:
                shortcode (String)
            Returns:
                String:  url to each post found in the user account
         """
        string1 = 'https://www.instagram.com/p/'
        string2 = shortcode
        string3 = '/?__a=1'
        return ''.join([string1, string2, string3])

    def pandas_operations(self, pd_data):
        """Method performs pandas dataframe operations.
            Args:
                pd_data (Pandas Dataframe)
            Returns:
                Dictionary:  weekday and sentiment dictionaries
         """
        print('PANDAS OPERATIONS :: ', pd_data)
        df = pd.DataFrame.from_dict(pd_data, orient='columns')
        result = df['sentiment'].value_counts()

        if hasattr(result, 'NEGATIVE'):
            negative = result.NEGATIVE
        else:
            result.NEGATIVE = 0
        if hasattr(result, 'NEUTRAL'):
            neutral = result.NEUTRAL
        else:
            result.NEUTRAL = 0
        if hasattr(result, 'POSITIVE'):
            positive = result.POSITIVE
        else:
            result.POSITIVE = 0

        sentiment_dict = {
            'NEUTRAL': result.NEUTRAL,
            'POSITIVE': result.POSITIVE,
            'NEGATIVE': result.NEGATIVE
        }
        # Get weekday and their values
        weekday_result = df['weekday'].value_counts()

        weekday = pd.Series(weekday_result).to_dict()
        sentiment = pd.Series(sentiment_dict).to_dict()

        return sentiment, weekday

    def save_to_database(self, data, username):
        """:arg
            Args:

            Returns:

        """

    def entry_point(self, username):
        """Method is the entry point to the methods above, it provides the sequence of execution.
            Args:
                username (String)
            Returns:
                Dictionary:  response (weekday, sentiment and parsed comment)
         """

        logging.info('ENTRY POINT :: ', username)
        # shortcodes_list stores a list(array) of shortcodes retrieved from a particular username
        # the list is used to iterate and retrieve comments in the for loop below.
        self.shortcodes_list = self.account_shortcodes(account_url=username)
        logging.info('SELF.SHORTCODES_LIST :: ', self.shortcodes_list)

        retrieved_data = []
        positive_comments = []
        negative_comments = []
        neutral_comments = []
        for index, shortcode in enumerate(self.shortcodes_list):
            data = urllib.request.urlopen(self.join_shortcode_url(shortcode=shortcode))
            data = data.read()
            comments_data = json.loads(data)
            comment_text = comments_data['graphql']['shortcode_media']['edge_media_preview_comment']['edges']
            count = comments_data['graphql']['shortcode_media']['edge_media_preview_comment']['count']
            nodes = comments_data['graphql']['shortcode_media']['edge_media_preview_comment']['edges']

            for i, node in enumerate(nodes):
                time = nodes[i]['node']['created_at']
                comment_id = nodes[i]['node']['id']
                # Convert unix time stamp to weekday
                weekday = self.timestamp_to_weekday(time)

                # Convert unix time stamp to readable time format
                time = datetime.utcfromtimestamp(time).strftime('%Y-%m-%d %H:%M:%S')
                text = nodes[i]['node']['text']

                # result and polarity & subjectivity of textblob analysis
                result = TextBlob(text)
                polarity = result.polarity
                subjectivity = result.subjectivity

                """
                    https://textblob.readthedocs.io/en/dev/quickstart.html#sentiment-analysis
                    Subjective sentences generally refer to personal opinion, emotion or judgment
                    Objective refers to factual information.
                """
                if polarity > 0:
                    sentiment = 'POSITIVE'
                elif polarity == 0:
                    sentiment = 'NEUTRAL'
                elif polarity < 0:
                    sentiment = 'NEGATIVE'

                values = {
                    'comment_id': comment_id,
                    'date': time,
                    'weekday': weekday,
                    'text': text,
                    'polarity': polarity,
                    'subjectivity': subjectivity,
                    'sentiment': sentiment
                }

                # group comments into positive negative and neutral
                if values['polarity'] > 0:
                    # positive
                    positive_comments.append(values)
                elif values['polarity'] < 0:
                    # negative
                    negative_comments.append(values)
                else:
                    # neutral
                    neutral_comments.append(values)

                # Appends all comments retrieved for pandas processing
                retrieved_data.append(values)
                len(retrieved_data)
                len_positive_comments = len(positive_comments)
                len_negative_comments = len(negative_comments)
                len_neutral_comments = len(neutral_comments)

        sentiment, weekday = self.pandas_operations(pd_data=retrieved_data)

        response = {
            'collection_name': str(username),
            'weekday': weekday,
            'sentiment': sentiment,
            'comments_data': {
                'positive_comments': positive_comments,
                'negative_comments': negative_comments,
                'neutral_comments': neutral_comments
            },
            'comments_length': {
                'positive_length': len_positive_comments,
                'negative_length': len_negative_comments,
                'neutral_length': len_neutral_comments,

            }

        }

        # save data to DB
        data = response
        try:
            myclient = pymongo.MongoClient(credentials.DB_CONNECTION)
            mydatabase = myclient[credentials.DB_INSTAGRAM_COLLECTION]
            db_collection = mydatabase[username]

            # Check if collection name already exists
            if db_collection in mydatabase.list_collection_names():
                logging.info('Collection exists')
                db_collection.insert_one(data)
            else:
                db_collection.insert_one(data)
            logging.info('Data saved successfully into Database.')
        except pymongo.errors.ConnectionFailure as e:
            logging.error('pymongo.errors.ConnectionFailure: ', e)
            # return e
        except (AttributeError, pymongo.errors.OperationFailure) as error:
            logging.error('AttributeError, pymongo.errors.OperationFailure: ', error)
            # return 'DB Attribute error'

        if "_id" in response:
            del response["_id"]
        return response
