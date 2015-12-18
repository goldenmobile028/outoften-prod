import os
from flask import Flask
from flask.ext.autodoc import Autodoc
from flask import jsonify

app = Flask(__name__)
auto = Autodoc(app)
#decorate each endpoint with @auto.doc() to generate the docs 

@app.route('/')
def hello():
    return 'Hello World!'
    
@app.route('/endpointone')
def dummy1():
	return 'Endpoint 1'
	
@app.route('/endpointtwo')
def dummy2():
	return jsonify(endpoint2="hi")	   
	
#Provide global photo count 
@app.route('/v1/photos/count/')
#def get_count():
#	count = Count.
#	return jsonify(count=count)

#Create photo record 
@app.route('/v1/photos/')
#def get_count():
#	count = Count.
#	return jsonify(count=count)

#Provide list of scores 
@app.route('/v1/photos/score')
#def get_count():
#	count = Count.
#	return jsonify(count=count)	 

#Delete photos
@app.route('/v1/photos/<photo_id>')
#def get_count():
#	count = Count.
#	return jsonify(count=count)	 

#Submit a rating 
@app.route('/v1/photos/rate/')
#def get_count():
#	count = Count.
#	return jsonify(count=count)	 

#Get list of photos to rate 
@app.route('/v1/photos/rating_list')
#def get_count():
#	count = Count.
#	return jsonify(count=count)	 

#Flagging 
@app.route('/v1/photos/flag')
#def get_count():
#	count = Count.
#	return jsonify(count=count)	 	 	 	 

#Documentation Auto-generator 	
@app.route('/documentation')
def documentation():
    return auto.html()
    
#app.debug = True
#app.run()    	