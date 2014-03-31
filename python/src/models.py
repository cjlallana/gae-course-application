'''
Created on 19/04/2013

@author: Developer
'''

from google.appengine.ext import db


class Country(db.Model):
	"""Defines the Country entity or model."""
	name		= db.StringProperty(required=True)
	code		= db.StringProperty()
	created		= db.DateTimeProperty(auto_now_add=True)
	updated		= db.DateTimeProperty(auto_now=True)


class Administrator(db.Model):
	"""Defines the Administrator entity or model."""
	email		= db.StringProperty(required=True)
	a_country	= db.ReferenceProperty(	Country, 
										collection_name='administrators')
	created		= db.DateTimeProperty(auto_now_add=True)
	updated		= db.DateTimeProperty(auto_now=True)
	

class Course(db.Model):
	"""Defines the Course entity or model."""
	name				= db.StringProperty(required=True)
	code				= db.StringProperty()
	url					= db.StringProperty()
	cost_local_credits	= db.IntegerProperty(required=True)
	cost_global_credits	= db.IntegerProperty(required=True)
	c_country			= db.ReferenceProperty(	reference_class=Country, 
												collection_name='courses')
	created				= db.DateTimeProperty(auto_now_add=True)
	updated				= db.DateTimeProperty(auto_now=True)
	
	def __eq__(self, other):
		return self.key() == other.key()


class Plan(db.Model):
	"""Defines the Plan entity or model."""
	name				= db.StringProperty(required=True)
	code				= db.StringProperty(required=True)
	created				= db.DateTimeProperty(auto_now_add=True)
	updated				= db.DateTimeProperty(auto_now=True)

	def __eq__(self, other):
		return self.key() == other.key()
	

class Worker(db.Model):
	"""Defines the Worker entity or model."""
	email			= db.StringProperty(required=True)
	local_credits	= db.IntegerProperty(required=True)
	global_credits	= db.IntegerProperty(required=True)
	w_country		= db.ReferenceProperty(	reference_class=Country, 
											collection_name='workers')
	w_plan			= db.ReferenceProperty(	reference_class=Plan, 
											collection_name='workers')
	created			= db.DateTimeProperty(auto_now_add=True)
	updated			= db.DateTimeProperty(auto_now=True)


class WorkerCourseRelation(db.Model):
	"""Defines the WorkerRelationRelation entity or model."""
	r_worker	= db.ReferenceProperty(	Worker, 
										collection_name='wc_relations',
										required=True)
	r_course	= db.ReferenceProperty(	Course, 
										collection_name='wc_relations',
										required=True)
	r_country	= db.ReferenceProperty(	Country, 
										collection_name='wc_relations',
										required=True)
	status		= db.StringProperty()
	created		= db.DateTimeProperty(auto_now_add=True)
	updated		= db.DateTimeProperty(auto_now=True)


class PlanCourseRelation(db.Model):
	"""Defines the Course entity or model."""
	r_plan		= db.ReferenceProperty(	Plan,
										required=True,
										collection_name='pc_relations')
	r_course	= db.ReferenceProperty(	reference_class=Course, 
										collection_name='pc_relations',
										required=True)
	created		= db.DateTimeProperty(auto_now_add=True)
	updated		= db.DateTimeProperty(auto_now=True)


