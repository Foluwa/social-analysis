#Sentiment Analysis

This project using python3.7, Make sure you have pip installed 

##Setup virtual environment with [venv](https://sourabhbajaj.com/mac-setup/Python/virtualenv.html)

`virtualenv venv`

`source venv/bin/activate`

To leave the virtual environment run:

`deactivate`


Link to [swagger](https://app.swaggerhub.com/apis/Foluwa/sentimentAnalysis/1.0.0)

`cd sentiment-analysis-backend`

then

`flask run`


### Routes
| Routes      | Description          | Response  |
| ------------- |:-------------:| -----:|
| /             | home route | json  |
| /v1/api/analyse     | perform analysis on tweets     |  negative, positive, neutral,  |
|  |      |    |


### Testing 
Implemented [Nose](https://nose.readthedocs.io/en/latest/#python3) for automated testing

`python3 -m "nose"`

#### OR 

`pip install nose`

then

`nosetests`


