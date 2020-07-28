#Sentiment Analysis

This project using python3.6, Make sure you have pip installed 

##Setup virtual environment with
`cd sentiment-analysis-backend`
 
 Make sure you have [venv](https://sourabhbajaj.com/mac-setup/Python/virtualenv.html) installed
 
`virtualenv venv`

`source venv/bin/activate`



`gunicorn -w 4 app:app`

To leave the virtual environment run:

`deactivate`


Link to [swagger](https://app.swaggerhub.com/apis/Foluwa/sentimentAnalysis/1.0.0)



### Routes
| Routes      | Description          | Type  |
| ------------- |:-------------:| -----:|
| /             | home route | GET  |
| /v1/api/analyse     | perform analysis on tweets     |  POST  |
| /get/collection     | Returns values of all twitter previous searches     |  GET  |
| /get-previous-values/<string:collection_name>/    | Returns specific value of previously searched keywords     |  GET |
| /v1/api/instagram/analyse     | Retrieves and perform analysis on instagram comments     |  POST  |
| /instagram/get/collection     | Returns analysis of instagram     |  GET  |
| /instagram/previous-values/<string:collection_name>/     | Returns specific value of previously searched keywords     |  GET  |
|  |      |    |


### Sockets
| Routes      | Description          | Response  |
| ------------- |:-------------:| -----:|
| connect             | home route | sockets data  |
| message    | perform real-time analysis on tweets with sockets    |  sockets data  |
| disconnect     | perform analysis on tweets     |  none  |
|  |      |    |



### Testing 
Implemented [Unnittest Framework](https://docs.python.org/3/library/unittest.html) a python standard library which means it is distributed with Python. Unittest provides tons of tools for constructing and running tests.

To run test: 

`python -m unittest app_test.py`



