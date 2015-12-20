import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask.ext.autodoc import Autodoc
from flask import jsonify
from flask import request 
import psycopg2
import urlparse

import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
auto = Autodoc(app)
#TODO decorate each endpoint with @auto.doc() to generate the docs 

#Talk to postgres 
#SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://mhevgpfchwsopm:Ip8BtqNWSBzqsQralgNCFOm4Um@ec2-75-101-143-150.compute-1.amazonaws.com:5432/dckn2j5felndns'
db = SQLAlchemy(app)

#Postgres connection stuff  (according to heroku) 

#urlparse.uses_netloc.append("postgres")
#url = urlparse.urlparse(os.environ["DATABASE_URL"])

#database connection 
#conn = psycopg2.connect(
#    database=url.path[1:],
#    user=url.username,
#    password=url.password,
#    host=url.hostname,
#    port=url.port
#)


#ENDPOINTS

@app.route('/')
def hello():
	app.logger.info('Infohello')
	return 'Hello World!'
    
@app.route('/endpointone')
def dummy1():
	return 'Endpoint 1'
	
@app.route('/endpointtwo')
def dummy2():
	return jsonify(endpoint2="hi",otherval=3)   
	
#Provide global photo count 
#@app.route('/v1/photos/count/')
#def get_count():
#	count = Count.
#	return jsonify(count=count)

#Create photo record 
#@app.route('/v1/photos/', methods=['POST'])
#def create_photo():
#	write the method to create the record for the photo 
#	return jsonify(photo_id=photo_id)

#Provide list of scores 
#@app.route('/v1/photos/score')
#def get_count():
#	count = Count.
#	return jsonify(count=count)	 

#Delete photos
#@app.route('/v1/photos/<photo_id>')
#def get_count():
#	count = Count.
#	return jsonify(count=count)	 

#Submit a rating 
#@app.route('/v1/photos/rate/')
#def get_count():
#	count = Count.
#	return jsonify(count=count)	 

#Get list of photos to rate 
#@app.route('/v1/photos/rating_list')
#def get_count():
#	count = Count.
#	return jsonify(count=count)	 

#Flagging 
#@app.route('/v1/photos/flag')
#def get_count():
#	count = Count.
#	return jsonify(count=count)	 	 	 	 

#Documentation Auto-generator 	
#@app.route('/documentation')
#def documentation():
#    return auto.html()
    
	