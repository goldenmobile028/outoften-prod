import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy import literal
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref
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

#logging REMOVE FROM PROD


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
	time.sleep(0.05)


#Create App
app = Flask(__name__, static_url_path='')
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)


#Variables

FLAG_STATUS_NONE				= 0
FLAG_STATUS_AWAITING_REVIEW		= 1
FLAG_STATUS_APPROVED			= 2
FLAG_STATUS_BANNED				= 3
FLAG_STATUS_AUTOBANNED			= 4

CATEGORY_TYPE_LANDSCAPE			= 0
CATEGORY_TYPE_FASHION			= 1
CATEGORY_TYPE_RIDES				= 2
CATEGORY_TYPE_RANDOM			= 3

DELETION_STATUS_NONE			= 0
DELETION_STATUS_MARKED			= 1

USERNAME						= "admin"
PASSWORD						= os.environ['ADMIN_PASS']

p("test the logging")

#Models
class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	uuid_string = db.Column(db.String)

	uploaded_photos = db.relationship('Photo', backref='user')
	viewed_photos = db.relationship('Exclude', backref='user')
	blocked_users = db.relationship('Block', backref='blocked_user', primaryjoin='User.id==Block.user_id', lazy='dynamic')

	def __init__(self, uuid_string):
		self.uuid_string = uuid_string

class Photo(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	image_url = db.Column(db.String(2083))
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
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
	exclusions = db.relationship('Exclude', backref='photo')

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

#Do not show a user a photo more than once.
#Placeholder column
class Exclude(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
	photo_id = db.Column(db.Integer, db.ForeignKey("photo.id"))
	placeholder = db.Column(db.Integer)

	def __init__(self):
		self.placeholder = 0


#Allow a user to block another user.
class Block(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
	blocked_id = db.Column(db.Integer, db.ForeignKey("user.id"))
	placeholder = db.Column(db.Integer)

	user = relationship('User', foreign_keys='Block.user_id')
	blocked = relationship('User', foreign_keys='Block.blocked_id')

	def __init__(self):
		self.placeholder = 0

#Connect to postgres
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['POSTGRES_URL']
# app.config['SQLALCHEMY_DATABASE_URI'] = "postgres://localhost:5432/dckn2j5felndns"
db.create_all()
db.session.commit()


#FUNCTIONS
#Create Photo Record
#OK
def create_photo_record(uuid_string, image_url, category):
	#obtain user
	user = find_or_create_user(uuid_string)

	#create photo record
	photo = Photo(image_url, category)
	photo.user = user
	db.session.add(photo)
	db.session.commit()

	#don't show a user his own photo
	hide = hide_photo(photo, user)

	return photo

#With no user accounts desired, we have to find or create user "A" upon either 1. creating a photo record or 2. blocking another user "B" 3.viewing/rating photos
#OK
def find_or_create_user(uuid_string):

	user = db.session.query(User).filter(User.uuid_string == uuid_string).first()

	if not user:
		#create the user
		user = User(uuid_string = uuid_string)
		db.session.add(user)
		db.session.commit()
	else:
		pass

	return user

#OK
def hide_photo(photo, user):
	p("hide_photo entered")

	hide = Exclude()
	hide.user = user
	hide.photo = photo
	db.session.add(hide)
	db.session.commit()

	#check whether I can return nothing
	return "exclusion stored"

#OK
def hide_photo_list(hide_photo_list, user):
	p("in hide_photo_list")
	for photo in hide_photo_list:
		p(photo)
		hide_photo(photo, user)
		p("hid the photo")

	return "done"

#OK
def block_user(uuid_string, photo_id):
	#call find_or_create_user to find the blocker's user id
	p("in the block user function")
	user = find_or_create_user(uuid_string)

	#use photo_id to look up blocked_user's user id
	photo = Photo.query.get(photo_id)
	blocked = photo.user

	#store in block table
	block = Block()
	block.user = user
	block.blocked_user = blocked

	db.session.add(block)
	db.session.commit()

	return "user blocked"

#OK
def update_flag_status(photo_id, creation_time):
	now = time.time()
	photo = Photo.query.get(photo_id)

	if ((now - creation_time) <= (10*60)):
		photo.flag_status = FLAG_STATUS_AUTOBANNED
	else:
		photo.flag_status = FLAG_STATUS_AWAITING_REVIEW

	db.session.commit()

	return "ok"

#API ENDPOINTS
#OK
@app.route('/')
def hello():
	return 'Welcome to 0ut of 10'

#Provide global photo count
#OK
@app.route('/api/v1/photos/count/')
def get_count():
	count = db.session.query(db.func.count(Photo.id)).scalar()
	return jsonify(count=count)


#Create photo record endpoint
#OK
import logging
@app.route('/api/v1/photos/', methods=['POST'])
def create_photo():
	content = request.get_json(force=True)
        p(content)

	category = content["category"]
	uuid_string = content["uuid"]
	image_url = content["image_url"]
	photo = create_photo_record(uuid_string, image_url, category)

	return jsonify(photo_id=photo.id)


#Get list of scores
#OK
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

#Delete a photo
#OK
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
#OK
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
#OK
@app.route('/api/v1/photos/photo_list/', methods=['GET'])
def get_photo_list():
	uuid_string = request.args.get('uuid')
	category = request.args.get('category')

	#get user.id
	user = find_or_create_user(uuid_string)
	user_id = user.id

	#find which photos the user has already seen
	excluded_photo_id_tuples = db.session.query(Exclude.photo_id).filter(Exclude.user_id == user_id).all()
	excluded_photo_ids = [tuple[0] for tuple in excluded_photo_id_tuples]

	#find photos authors the user has blocked
	blocked_user_id_tuples = db.session.query(Block.blocked_id).filter(Block.user_id == user_id).all()
	blocked_user_ids = [tuple[0] for tuple in blocked_user_id_tuples]

	#get photos
	querySize = 20
	#specify fields to return
	q = db.session.query(Photo.id, Photo.image_url, Photo.category, Photo.rating_sum, Photo.rating_total, Photo.flag_status, Photo.user_id)
	#do not include deleted and banned photos
	q = q.filter(Photo.flag_status != 3 and Photo.flag_status != 4 and Photo.deletion_status == 0)
	#filter by requested category
	q = q.filter(Photo.category == category)
	#do not include photos already seen
	q = q.filter(Photo.id.notin_(excluded_photo_ids))
	#do not include photos uploaded by blocked users
	q = q.filter(Photo.user_id.notin_(blocked_user_ids))
	#return random results
	q = q.order_by(func.random())
	#limit the query size
	q = q.limit(querySize)
	result = q.all()

	#prepare photo_list for json, and photo_ids for exclusion
	photo_ids = []
	photo_list = []
	entry = []
	keys = ["photo_id", "image_url", "category", "rating_sum", "rating_total"]

	for photo in result:
			photo_ids.append(photo[0])
			entry = dict(zip(keys, photo))
			photo_list.append(entry)

	#store these photos in exclusion table
	photos = []
	for photo_id in photo_ids:
		photo = Photo.query.get(photo_id)
		photos.append(photo)
	hide = hide_photo_list(photos, user)

	return json.dumps(photo_list)

#Flagging and Blocking
#OK, but the blocking function called doesn't work
@app.route('/api/v1/photos/flag/', methods=["POST"])
def flag_photo():
	content = request.get_json(force=True)
	photo_id = content['photo_id']
	category = content['flag_category']
	uuid_string = content['uuid']
	now = time.time()

	photo = Photo.query.get(photo_id)
	creation_time = photo.creation_timestamp

	if category == 1:
		photo.flag_count_miscategorized = photo.flag_count_miscategorized + 1
	elif category == 2:
		photo.flag_count_inappropriate = photo.flag_count_inappropriate + 1
	elif category == 3:
		photo.flag_count_spam = photo.flag_count_spam + 1
	else:
		#call blocking function
		block = block_user(uuid_string, photo_id)

	all_flags_count = photo.flag_count_miscategorized + photo.flag_count_inappropriate + photo.flag_count_spam

	if all_flags_count >= 3:
		update_flag_status = update_flag_status(photo_id, creation_time)
	else:
		pass

	db.session.commit()

	return jsonify(status="ok")

#Need to check this one after block is ready
#Delete User Account (hide all photos)
@app.route('/api/v1/delete_account/', methods=["POST"])
def delete_account():
	content = request.get_json(force=True)
	uuid_string = content['uuid']

	user = find_or_create_user(uuid_string)

	#update deletion status for all user's photos
	q = db.session.query(Photo).filter(Photo.user == user).update({'deletion_status': DELETION_STATUS_MARKED})
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


if __name__=='__main__':
    app.run()
