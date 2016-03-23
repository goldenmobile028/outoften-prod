import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy import literal
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

#Create App
app = Flask(__name__, static_url_path='')
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
db = SQLAlchemy(app)

#Variables

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

#Models
class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	uuid_string = db.Column(db.String)

	def __init__(self, uuid_string):
		self.uuid_string = uuid_string

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

class Exclude(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	uuid_string = db.Column(db.String)
	photo_id = db.Column(db.Integer)

	def __init__(self, uuid_string, photo_id):
		self.uuid_string = uuid_string
		self.photo_id = photo_id		

#Connect to postgres
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['POSTGRES_URL']
db.create_all()
db.session.commit()


#Create Record Function
def create_photo_record(uuid_string, image_url, category):
	#create photo record	
	photo = Photo(image_url, category)
	db.session.add(photo)
	db.session.commit()
	photo_id = photo.id
	
	#find or create user 
	user_check = db.session.query(User).filter(User.uuid_string == uuid_string)
	user_exists = db.session.query(literal(True)).filter(user_check.exists()).scalar()
	
	if not user_exists:
		#create user
		user = User(uuid_string)
		db.session.add(user)
		db.session.commit()

	result = store_excluded_photos(photo_id, uuid_string)

	return photo_id

def store_excluded_photos(photo_id, uuid_string):
	exclusion = Exclude(uuid_string, photo_id)
	db.session.add(exclusion)
	db.session.commit()

	return "exclusion stored"


#ENDPOINTS

@app.route('/')
def hello():
	return 'Welcome to 0ut of 10'   
	
#Provide global photo count 
@app.route('/api/v1/photos/count/')
def get_count():
	count = db.session.query(db.func.count(Photo.id)).scalar()
	return jsonify(count=count)	

#Create photo record
@app.route('/api/v1/photos/', methods=['POST'])
def create_photo():
	content = request.get_json(force=True)
	category = content["category"]
	uuid_string = content["uuid"]
	image_url = content["image_url"]
	photo_id = create_photo_record(uuid_string, image_url, category)
	
	return jsonify(photo_id=photo_id)
	

#Get list of scores
@app.route('/api/v1/photos/score/', methods=['GET'])
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
def get_photo_list():
	photo_list = []
	retrieved_photo_ids = []
	entry = []
	keys = ["photo_id", "image_url", "category", "rating_sum", "rating_total"]
	uuid_string = request.args.get('uuid')
	category = request.args.get('category')
	user_check = db.session.query(User).filter(User.uuid_string == uuid_string)
	user_exists = db.session.query(literal(True)).filter(user_check.exists()).scalar()
	querySize = 2
	photos = None

	if user_exists:
		#get exclusion list
		excluded_photo_id_tuples = db.session.query(Exclude.photo_id).filter(Exclude.uuid_string == uuid_string).all()
		excluded_photo_ids = [tuple[0] for tuple in excluded_photo_id_tuples]
		#get photos
		#specify fields to return
		q = db.session.query(Photo.id, Photo.image_url, Photo.category, Photo.rating_sum, Photo.rating_total, Photo.flag_status)
		#do not include deleted and banned photos
		q = q.filter(Photo.flag_status != 3 and Photo.flag_status != 4 and Photo.deletion_status != 1)
		#filter by requested category	
		q = q.filter(Photo.category == category)
		#do not include photos already seen
		q = q.filter(Photo.id.notin_(excluded_photo_ids))
		#return random results 
		q = q.order_by(func.random())
		#limit the query size
		q = q.limit(querySize)
		photos = q.all()
	else:
		#create user
		user = User(uuid_string)
		db.session.add(user)
		db.session.commit()
		#get photos
		q = db.session.query(Photo.id, Photo.image_url, Photo.category, Photo.rating_sum, Photo.rating_total)
		#filter by requested category	
		q = q.filter(Photo.category == category)
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
		new_exclusion = Exclude(uuid_string, photo_id)
		db.session.add(new_exclusion)
		db.session.commit()	
	return json.dumps(photo_list)	

#Flagging 
@app.route('/api/v1/photos/flag/', methods=["POST"])
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
			photo.flag_status = FLAG_STATUS_AUTOBANNED
			#photo.flag_status = FLAG_STATUS_AWAITING_REVIEW
		else:	
			photo.flag_status = FLAG_STATUS_AWAITING_REVIEW
	else:
		pass
	db.session.commit()
	return jsonify(status="ok")
	
#Submit Moderation (Admin Interface) 
@app.route('/api/v1/admin/submit_moderation/', methods=["POST"])
@cross_origin()
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
		else:
			status = "ok"
			output = {"status": status, "photos": flagged_list}
	else:
		output = {"status": "bad credentials"}
	
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

			
	