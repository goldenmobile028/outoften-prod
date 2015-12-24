import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy import literal
from flask.ext.autodoc import Autodoc
from flask import jsonify
from flask import request 
import urlparse
import logging
import logging.handlers
import logging.config
import time
import json

LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
        }
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO'
    }
}

logging.config.dictConfig(LOGGING)



def p(*args):
	#logging.info(args[0] % (len(args) > 1 and args[1:] or []))
	logging.info(*args)
	sys.stdout.flush()
	time.sleep(0.05)	# TODO: make sure this is removed from production / set up environment variables and don't show allow any of this printing on prod instance

#Create App
p("Creating app...")
app = Flask(__name__)
#app.debug = True	# TODO: remove this on prod
auto = Autodoc(app)
db = SQLAlchemy(app)

p("Creating models...")

#Models

FLAG_STATUS_NONE				= 0
FLAG_STATUS_AWAITING_REVIEW		= 1
FLAG_STATUS_APPROVED			= 2
FLAG_STATUS_BANNED				= 3
FLAG_STATUS_AUTOBANNED			= 4

CATEGORY_TYPE_LANDSCAPE			= 0
CATEGORY_TYPE_SELFIE			= 1
CATEGORY_TYPE_RIDES				= 2
CATEGORY_TYPE_RANDOM			= 3

DELETION_STATUS_NONE			= 0
DELETION_STATUS_MARKED			= 1

class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	uuid = db.Column(db.Integer)

	def __init__(self, uuid):
		self.uuid = uuid

class Photo(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	image_url = db.Column(db.String(2083))
	category = db.Column(db.Integer)
	rating_sum = db.Column(db.Integer)
	rating_total = db.Column(db.Integer)
	creation_timestamp = db.Column(db.Float)
	flag_count_inappropriate = db.Column(db.Integer)
	flag_count_miscategorized = db.Column(db.Integer)
	flag_count_spam = db.Column(db.Integer)
	flag_status = db.Column(db.Integer)
	deletion_status = db.Column(db.Integer)
	deletion_timestamp = db.Column(db.Float)

	#default values	    
	def __init__(self, image_url, category):
		self.image_url = image_url
		self.category = category
		self.rating_sum = 0
		self.rating_total = 0
		self.creation_timestamp = time.time()
		self.flag_count_inappropriate = 0
		self.flag_count_miscategorized = 0
		self.flag_count_spam = 0
		self.flag_status = FLAG_STATUS_NONE
		self.deletion_status = DELETION_STATUS_NONE
		self.deletion_timestamp = 0
		
		
#Table that records a uuid associated with a photo id to avoid showing repeat photos 
exclusions = db.Table('exclusions',
	db.Column('uuid', db.Integer),
	db.Column('photo_id', db.Integer))		

#Connect to postgres
p("Connecting to postgres...")
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://mhevgpfchwsopm:Ip8BtqNWSBzqsQralgNCFOm4Um@ec2-75-101-143-150.compute-1.amazonaws.com:5432/dckn2j5felndns'
db.create_all()
db.session.commit()

p("Done! Awaiting connections...")

#ENDPOINTS
#TODO decorate each endpoint with @auto.doc() to generate the docs 

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
@app.route('/api/v1/photos/count/')
@auto.doc()
def get_count():
	count = db.session.query(db.func.count(Photo.id)).scalar()
	return jsonify(count=count)	

#Create photo record
#TODO image_url = get it and do AWS
#We need to store the owner of the photo so that people are not shown their own?
@app.route('/api/v1/photos/', methods=['POST'])
def create_photo():
	content = request.get_json(force=True)
	image_url = "http://i.kinja-img.com/gawker-media/image/upload/s--pEKSmwzm--/c_scale,fl_progressive,q_80,w_800/1414228815325188681.jpg"
	category = content["category"]
	photo = Photo(image_url, category)
	db.session.add(photo)
	db.session.commit()
	return jsonify(photo_id=photo.id)


#Provide list of scores
#TODO: Parse the formatting that comes from getlist 
@app.route('/api/v1/photos/score/', methods=['GET'])
def get_scores():
	scorelist = []
	p("l1")
	photolist = request.values.getlist('photo_id')
	p(photolist)
	for photo_id in photolist:
		photo = Photo.query.get(photo_id)
		p(photo)
		s = photo.rating_sum
		p(s)
		t = photo.rating_total
		p(t)
		if t == 0:
			score = {photo_id:0}
		else:
			score = {photo_id:float(s/t)}
		p(score)
		scorelist.append(score)
		p(scorelist) 	
	json.dumps(scorelist)	
	return "hello"
	 
#Delete photos
#Note: This function currently allows photos to be flagged for deletion more than once.   
@app.route('/api/v1/photos/delete_photo', methods=['POST'])
def delete_photo():
	content = request.get_json(force=True)
	photo_id = content["photo_id"]
	photo = Photo.query.get(photo_id)
	photo.deletion_status = DELETION_STATUS_MARKED
	photo.deletion_timestamp = time.time()
	db.session.commit()
	return jsonify(status=200)

#Submit a rating 
@app.route('/api/v1/photos/rate/', methods=['POST'])
def submit_rating():
	p("0")
	content = request.get_json(force=True)
	p("0.5")
	photo_id = content["photo_id"]
	p("1")
	rating = content["rating"]
	p("1.5")
	photo = Photo.query.get(photo_id)
	p("2")
	photo.rating_sum = photo.rating_sum + rating 
	p("3")
	photo.rating_total = photo.rating_total + 1
	p("4")
	db.session.commit()	
	return jsonify(updated_rating=photo.rating_sum, updated_total=photo.rating_total) 

#Get list of photos to rate 
#TODO: need to get the actual rows of interest for the photo objects
#TODO: handle exclusion when uuid exists 
#TODO: hide deleted photos 
#TOTO: hide users own photos 
@app.route('/api/v1/photos/photo_list/', methods=['GET'])
def get_photo_list():
	photolist = []
	uuid = request.args.get('uuid')
	p(uuid)
	q = db.session.query(User).filter(User.uuid == uuid)
	p("did the query")
	x = db.session.query(literal(True)).filter(q.exists()).scalar()
	p("stored the exists variable")
	p(x)
	if x:
		p("user exists")
		#get exc list
		f = db.session.query(exclusions).filter(exlusions.uuid == uuid)
		#g = db.session.query(literal(True)).filter(f.exists()).scalar() 
		p("did the query")
		p(f)
		#return photos not on list
	else:
		#create user
		p("the user is new")
		user = User(uuid)
		p("made the user object")
		db.session.add(user)
		p("added")
		db.session.commit()
		p("committed")
		#get rando list
		z= db.session.query(Photo.id, Photo.image_url, Photo.category, Photo.rating_sum, Photo.rating_total).order_by(func.random()).limit(2).all()
		p("made query")
		p(z)
		#TODO: make this list of lists of values (no keys) into something I can return with JSON
		#TODO: add the photos in the list to the exclusion for this new user 
		#photolist = photolist.extend()
		#p(photolist) 
	#return jsonify(photolist=photolist)	
	return "hello"

#Flagging 
#TODO: Handle alerting the admin interface 
#TODO: Handle the autobanning  
@app.route('/api/v1/photos/flag/', methods=["POST"])
def flag_photo():
	p("1")
	content = request.get_json(force=True)
	photo_id = content['photo_id']
	p("2")
	category = content['category']
	p("3")
	photo = Photo.query.get(photo_id)
	p("4")
	if category == 1:
		photo.flag_count_miscategorized = photo.flag_count_miscategorized + 1
		p(photo.flag_count_miscategorized)
	elif category == 2:
		photo.flag_count_inappropriate = photo.flag_count_inappropriate + 1
		p(photo.flag_count_inappropriate)
	else:
		photo.flag_count_spam = photo.flag_count_spam + 1
		p(photo.flag_count_spam)
	db.session.commit()
	return jsonify(status=200) 	 

#Documentation Auto-generator 	
@app.route('/documentation')
def documentation():
    return auto.html()
    
	