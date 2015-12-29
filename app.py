import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy import literal
from flask.ext.autodoc import Autodoc
from flask import jsonify
from flask import request
from flask import send_from_directory 
import urlparse
import logging
import logging.handlers
import logging.config
import time
import json
from flask.ext.cors import CORS, cross_origin
import random

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
	#return
	#logging.info(args[0] % (len(args) > 1 and args[1:] or []))
	logging.info(*args)
	sys.stdout.flush()
	time.sleep(0.05)	# TODO: make sure this is removed from production / set up environment variables and don't show allow any of this printing on prod instance

#Create App
p("Creating app...")
app = Flask(__name__, static_url_path='')
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
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

USERNAME						= "admin"
PASSWORD						= os.environ['ADMIN_PASS']

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
	
#Testing this new table
class Exclude(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	uuid = db.Column(db.Integer)
	photo_id = db.Column(db.Integer)

	def __init__(self, uuid, photo_id):
		self.uuid = uuid
		self.photo_id = photo_id		

#Connect to postgres
p("Connecting to postgres...")
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['POSTGRES_URL']
db.create_all()
db.session.commit()

p("Done! Awaiting connections...")

def create_photo_record(uuid, image_url, category):
	#create photo record	
	photo = Photo(image_url, category)
	db.session.add(photo)
	db.session.commit()
	photo_id = photo.id
	
	#find or create user 
	user_check = db.session.query(User).filter(User.uuid == uuid)
	user_exists = db.session.query(literal(True)).filter(user_check.exists()).scalar()
	
	if not user_exists:
		#create user
		user = User(uuid)
		db.session.add(user)
		db.session.commit()
			
	#store photos in exclusion table
	exclusion = Exclude(photo_id, uuid)
	db.session.add(exclusion)
	db.session.commit()

	return photo_id
 
'''
def populateDatabase():
	for i in range(0,50):
		uuid = "00001"
		category = random.randint(0, 3)
		image_url = "https://placekitten.com/200/" + str(random.randint(350,450))
		photo_id = create_photo_record(uuid, image_url, category)
		
		photo = Photo.query.get(photo_id)

		photo.flag_count_miscategorized = 0
		photo.flag_count_inappropriate = 0
		photo.flag_count_spam = 0
		photo.flag_status = FLAG_STATUS_NONE
		db.session.commit()

	for i in range(0,50):
		uuid = "00001"
		category = random.randint(0, 3)
		image_url = "https://placekitten.com/200/" + str(random.randint(350,450))
		photo_id = create_photo_record(uuid, image_url, category)
		
		photo = Photo.query.get(photo_id)

		photo.flag_count_miscategorized = random.randint(3,20)
		photo.flag_count_inappropriate = random.randint(0,5)
		photo.flag_count_spam = random.randint(0,5)
		photo.flag_status = FLAG_STATUS_AWAITING_REVIEW
		db.session.commit()

	for i in range(0,50):
		uuid = "00001"
		category = random.randint(0, 3)
		image_url = "https://placekitten.com/200/" + str(random.randint(350,450))
		photo_id = create_photo_record(uuid, image_url, category)
		
		photo = Photo.query.get(photo_id)

		photo.flag_count_miscategorized = random.randint(0,5)
		photo.flag_count_inappropriate = random.randint(3,20)
		photo.flag_count_spam = random.randint(0,5)
		photo.flag_status = FLAG_STATUS_AWAITING_REVIEW
		db.session.commit()

	for i in range(0,50):
		uuid = "00001"
		category = random.randint(0, 3)
		image_url = "https://placekitten.com/200/" + str(random.randint(350,450))
		photo_id = create_photo_record(uuid, image_url, category)
		
		photo = Photo.query.get(photo_id)

		photo.flag_count_miscategorized = random.randint(0,5)
		photo.flag_count_inappropriate = random.randint(0,5)
		photo.flag_count_spam = random.randint(3,20)
		photo.flag_status = FLAG_STATUS_AWAITING_REVIEW
		db.session.commit()

#populateDatabase()
'''

#ENDPOINTS
#TODO: Handle the autobanning

@app.route('/')
def hello():
	return 'Welcome to 0ut of 10'   
	
#Provide global photo count 
@app.route('/api/v1/photos/count/')
@auto.doc()
def get_count():
	count = db.session.query(db.func.count(Photo.id)).scalar()
	return jsonify(count=count)	

#Create photo record
#TODO AWS integration
@app.route('/api/v1/photos/', methods=['POST'])
@auto.doc()
def create_photo():
	content = request.get_json(force=True)
	category = content["category"]
	uuid = content["uuid"]
	if content["image_url"] == "":
		image_url = "https://placekitten.com/200/400"	
	else:
		image_url = content["image_url"]
		
	photo_id = create_photo_record(uuid, image_url, category)
	
	return jsonify(photo_id=photo_id)
	

#Get list of scores
@app.route('/api/v1/photos/score/', methods=['GET'])
@auto.doc()
def get_scores():
	scorelist = []
	photolist = request.values.getlist('photo_id')
	for photo_id in photolist:
		photo = Photo.query.get(photo_id)
		total = photo.rating_total
		if total == 0:
			score = {photo_id:0}
		else:
			sum = photo.rating_sum
			score = {photo_id:float(sum/total)}
		scorelist.append(score) 	
	return json.dumps(scorelist)	
	 
#Delete photos
@app.route('/api/v1/photos/delete_photo', methods=['POST'])
@auto.doc()
def delete_photo():
	content = request.get_json(force=True)
	photo_id = content["photo_id"]
	photo = Photo.query.get(photo_id)
	photo.deletion_status = DELETION_STATUS_MARKED
	photo.deletion_timestamp = time.time()
	db.session.commit()
	return jsonify(status="ok")

#Submit a rating 
@app.route('/api/v1/photos/rate/', methods=['POST'])
@auto.doc()
def submit_rating():
	content = request.get_json(force=True)
	photo_id = content["photo_id"]
	rating = content["rating"]
	photo = Photo.query.get(photo_id)
	photo.rating_sum = photo.rating_sum + rating 
	photo.rating_total = photo.rating_total + 1
	db.session.commit()	
	return jsonify(updated_rating=photo.rating_sum, updated_total=photo.rating_total) 

#Gets list of photos to rate with exclusion filter 
@app.route('/api/v1/photos/photo_list/', methods=['GET'])
@auto.doc()
def get_photo_list():
	photo_list = []
	retrieved_photo_ids = []
	entry = []
	keys = ["photo_id", "image_url", "category", "rating_sum", "rating_total"]
	uuid = request.args.get('uuid')
	user_check = db.session.query(User).filter(User.uuid == uuid)
	user_exists = db.session.query(literal(True)).filter(user_check.exists()).scalar()
	querySize = 2
	photos = None

	if user_exists:
		#get exc list
		excluded_photo_id_tuples = db.session.query(Exclude.photo_id).filter(Exclude.uuid == uuid).all()
		excluded_photo_ids = [tuple[0] for tuple in excluded_photo_id_tuples]
		#get photos
		q = db.session.query(Photo.id, Photo.image_url, Photo.category, Photo.rating_sum, Photo.rating_total, Photo.flag_status)
		q = q.filter(Photo.flag_status != 3 and Photo.flag_status != 4 and Photo.deletion_status != 1)
		q = q.filter(Photo.id.notin_(excluded_photo_ids))
		q = q.order_by(func.random())
		q = q.limit(querySize)
		photos = q.all()
	else:
		#create user
		user = User(uuid)
		db.session.add(user)
		db.session.commit()
		#get photos
		q = db.session.query(Photo.id, Photo.image_url, Photo.category, Photo.rating_sum, Photo.rating_total)
		q = q.order_by(func.random())
		q = q.limit(querySize)
		photos = q.all()
	
	#make list of photos and save them for exclusion list
	for photo in photos:
			retrieved_photo_ids.append(photo[0])
			entry = dict(zip(keys, photo))
			photo_list.append(entry)
	
	#store photos in exclusion table
	for photo_id in retrieved_photo_ids:
		new_exclusion = Exclude(uuid, photo_id)
		db.session.add(new_exclusion)
		db.session.commit()	
	return json.dumps(photo_list)	

#Flagging 
@app.route('/api/v1/photos/flag/', methods=["POST"])
@auto.doc()
def flag_photo():
	content = request.get_json(force=True)
	photo_id = content['photo_id']
	category = content['flag_category']
	now = time.time()
	
	photo = Photo.query.get(photo_id)
	creation_time = photo.creation_timestamp
	
	if category == 1:
		photo.flag_count_miscategorized = photo.flag_count_miscategorized + 1
	elif category == 2:
		photo.flag_count_inappropriate = photo.flag_count_inappropriate + 1
	else:
		photo.flag_count_spam = photo.flag_count_spam + 1
	
	all_flags_count = photo.flag_count_miscategorized + photo.flag_count_inappropriate + photo.flag_count_spam
	
	if all_flags_count >= 3:
		if ((now - creation_time) <= (10*60)):
			#photo.flag_status = FLAG_STATUS_AUTOBANNED
			photo.flag_status = FLAG_STATUS_AWAITING_REVIEW
		else:	
			photo.flag_status = FLAG_STATUS_AWAITING_REVIEW
	else:
		pass
		#photo.flag_status = FLAG_STATUS_NONE
	db.session.commit()
	return jsonify(status="ok")
	
#Submit Moderation (Admin Interface) 
@app.route('/api/v1/admin/submit_moderation/', methods=["POST"])
@cross_origin()
@auto.doc()
def submit_moderation():
	content = request.get_json(force=True)
	username = content["username"]
	password = content["password"]
	if username == USERNAME and password == PASSWORD:
		photo_id = content["photo_id"]
		flag_status = content ["flag_status"]
		photo = Photo.query.get(photo_id)
		photo.flag_status = flag_status
		db.session.commit()
		status = "ok"
	else:
		status = "bad credentials"		
	return jsonify(status=status) 
	
#Log In (Admin Interface) 
@app.route('/api/v1/admin/login/', methods=["POST"])
@cross_origin()
@auto.doc()
def login():
	content = request.get_json(force=True)
	username = content["username"]
	password = content["password"]
	if username == USERNAME and password == PASSWORD:
		status = "ok"
	else:
		status = "bad credentials"	
	return jsonify(status=status)
	
#Gets list of photos to moderate (Admin Interface)
@app.route('/api/v1/admin/flagged_list/', methods=['POST'])
@cross_origin()
@auto.doc()
def get_flagged_list():
	flagged_list = []
	entry = []
	output = {}
	keys = ["photo_id", "image_url", "category", "flag_count_inappropriate", "flag_count_miscategorized", "flag_count_spam"]
	querySize = 30
	
	content = request.get_json(force=True)
	username = content["username"]
	password = content["password"]
	
	if username == USERNAME and password == PASSWORD:
		q = db.session.query(Photo.id, Photo.image_url, Photo.category, Photo.flag_count_inappropriate, Photo.flag_count_miscategorized, Photo.flag_count_spam).filter_by(flag_status=FLAG_STATUS_AWAITING_REVIEW)
		q = q.limit(querySize)
		flagged_items_result = q.all()
		
		for flagged_item in flagged_items_result:
			entry = dict(zip(keys, flagged_item))
			flagged_list.append(entry)
		
		if len(flagged_list) == 0:
			status = "ok"
			output = {"status": status, "photos": flagged_list} 
			#output = dict([("status" : status), ("photos" : flagged_list)])
		else:
			status = "ok"
			output = {"status": status, "photos": flagged_list} 
			#output = dict([("status" : status), ("photos" : flagged_list)])
	else:
		output = {"status": "bad credentials"}
		#output = dict("status" : "bad credentials")
	
	return json.dumps(output)
	

	 	
@app.route('/admin/')	 	 
@app.route('/admin/index.html')
def send_admin():
	return send_from_directory("admin", "index.html")
	
@app.route('/admin/css/<css>')
def send_admin_css(css):
	return send_from_directory("admin/css", css)
	
@app.route('/admin/img/<img>')
def send_admin_img(img):
	return send_from_directory("admin/img", img)	

@app.route('/admin/src/<src>')
def send_admin_src(src):
	return send_from_directory("admin/src", src)				

#TODO: Add descriptions and arguments to the generated html (not happening automatically)
#Documentation Auto-generator 	
@app.route('/api/v1/documentation')
def documentation():
    return auto.html()

   
	