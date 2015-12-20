from app import db 

#MODELS

#FLAG_STATUS_NONE			= 0
#FLAG_STATUS_AWAITING_REVIEW	= 1
#FLAG_STATUS_APPROVED		= 2
#FLAG_STATUS_BANNED			= 3
#FLAG_STATUS_AUTOBANNED		= 4

#CATEGORY_TYPE_LANDSCAPE		= 0
#CATEGORY_TYPE_SELFIE		= 1
#CATEGORY_TYPE_RIDES			= 3
#CATEGORY_TYPE_RANDOM		= 4


#User object (device id)
#class User(db.Model):
#    id = db.Column(db.Integer, primary_key=True)
#   uuid = db.Column(db.Integer)

#	def __init__(self, uuid):
#		self.uuid = uuid
	
#	def __repr__(self):
#        return self.uuid	 

#db.create_all()

#Table that records a uuid associated with a photo id to avoid showing repeat photos 
#exclusions = db.Table('exclusions',
#	db.Column('uuid', db.Integer),
#	db.Column('photo_id', db.Integer))

#Photo object
#class Photo(db.Model):
#    id = db.Column(db.Integer, primary_key=True)
#    image_url = db.Column(db.Text)
#    category = db.Column(db.Integer)
#	rating_sum = db.Column(db.Integer)
#    rating_total = db.Column(db.Integer)
#    creation_date = db.Column(db.DateTime)
#    flag_count_inappropriate = db.Column(db.Integer)
#    flag_count_miscategorized = db.Column(db.Integer)
#    flag_status = db.Column(db.Integer)
    	   
