"""
    Database connection
"""
import pymongo
import credentials


def database_connection():
    try:
        # Database configurations
        myclient = pymongo.MongoClient(credentials.DB_CONNECTION)
        # Get database
        mydatabase = myclient['sentiment_analysis']
        return 'Connection Successful'
    finally:
        print('Connection not successful')

