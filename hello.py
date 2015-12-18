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
	
#Global photo count 
#@app.route('/v1/photos/count')
#def get_count():
#	count = Count.
#	return jsonify(count=count)	 	 

#Documentation Auto-generator 	
@app.route('/documentation')
def documentation():
    return auto.html()
    
#app.debug = True
#app.run()    	