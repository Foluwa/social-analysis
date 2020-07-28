"""
    tweets processing
"""
import re
import logging
from .words import stop_words


class CommonMethods:

    def __init__(self):
        logging.info('init method')

    def clean_tweet(self, tweet):
        # Convert to lower case
        tweet = tweet.lower()
        # Removes www.* or https?://*
        tweet = re.sub('((www\.[^\s]+)|(https?://[^\s]+))', '', tweet)
        # Remove @username
        tweet = re.sub('@[^\s]+', '', tweet)
        # Remove additional white spaces
        tweet = re.sub('[\s]+', ' ', tweet)
        # Replace #word with word
        tweet = re.sub(r'#([^\s]+)', r'\1', tweet)
        # Replace none english characters with nothing
        tweet = re.sub(r'[^a-zA-Z ]', '', tweet)  # Make sure there is a space after Z
        # Trim
        tweet = tweet.strip('\'"')
        # Split the tweets to a list
        # TODO: Convert to sets and Refactor to numpy intersects
        tweet = [word for word in tweet.split() if word not in stop_words]
        # Convert list to sentence
        tweet_text = ' '.join(word for word in tweet)
        return tweet_text, tweet
