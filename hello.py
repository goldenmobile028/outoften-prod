import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello World!'
    
@app.route('/endpointone')
def dummy1():
	return 'Endpoint 1'
	
@app.route('/endpointtwo')
def dummy2():
	return 'Endpoint 2' 	    