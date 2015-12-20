import os
from flask import Flask
from flask.ext.autodoc import Autodoc
from flask import jsonify
from flask import request 
import psycopg2
import urlparse

app = Flask(__name__)
auto = Autodoc(app)
#decorate each endpoint with @auto.doc() to generate the docs 

urlparse.uses_netloc.append("postgres")
url = urlparse.urlparse(os.environ["DATABASE_URL"])

conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)

#Models

#User object (device id)
class User(db.Model):
    uuid = db.Column(db.Integer, primary_key=True)

db.create_all()

#Routing

@app.route('/')
def hello():
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
    
	