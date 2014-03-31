# -*- encoding: utf-8 -*-
'''
Created on 14/01/2013

@author: Carlos Lallana
'''

import webapp2
import jinja2
import os

import session

from google.appengine.api import users
from google.appengine.ext import db

# Initialize Jinja2
jinja_environment = jinja2.Environment(
					loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		
config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': 'ole',
}


class SuperAdmin(webapp2.RequestHandler):
	
	def get(self):
		'''
		Handles GET requests
		'''
		self.checkLogin()

	
	def checkLogin(self):
		'''
		Renders the index HTML page
		'''
		# Get the current Google user
		user = users.get_current_user()
		
		# If there is no user, redirect to the Google login page
		if not user:
			self.redirect(users.create_login_url(self.request.uri))
			return
		
		# If the current user is super-admin, redirect to the proper page
		if users.is_current_user_admin():
			self.firstConfiguration()
			self.redirect('/countries')
			return
		
		# Else, redirect to the welcome page
		self.redirect('/?e=1')


	def firstConfiguration(self):
		'''
		Sets the database with some defaults values, in order to have a bugless
		experience.
		'''
		from models import Country

		# Get all the countries
		country_query = Country.all()
		country_query.ancestor(db.Key.from_path('Country', 'default'))
		results = country_query.filter('code =', '0')
		
		# If there is no country with code '0'...
		if not results.get():
			# Create the global 'country'
			default_country = Country(	name='GLOBAL', 
										code='0',
										parent=db.Key.from_path('Country', 'default'))
			default_country.put()


class LocalAdmin(session.BaseHandler):
	
	def get(self):
		'''Handles GET requests'''
		self.checkLogin()


	def checkLogin(self):
		'''Renders the index HTML page'''
		# Get the current Google user
		user = users.get_current_user()
		
		# If there is no user, redirect to the Google login page
		if not user:
			self.redirect(users.create_login_url(self.request.uri))
			return
		
		from models import Administrator
		# Else, check if the user is a local admin
		administrator_query = Administrator.all()
		administrator_query.ancestor(db.Key.from_path('Administrator', 'default'))
		la_results = administrator_query.filter("email = ", user.nickname())
		# If there is a local administrator that matches with the email...
		if la_results.get():
			local_admin = la_results[0]
			c_key = str(local_admin.a_country.key())
			self.session['profile'] = 'local_admin'
			self.session['email'] = local_admin.email
			self.session['country_key'] = c_key
			self.redirect('/localadmin/applications')
		
		else:
			# Else, redirect to the welcome page
			self.redirect('/?e=2')
		
		
class Employer(session.BaseHandler):
	
	def get(self):
		"""Handles GET requests"""
		self.checkLogin()
	
	
	def checkLogin(self):
		"""Renders the index HTML page"""
		# Get the current Google user
		user = users.get_current_user()
		
		# If there is no user, redirect to the Google login page
		if not user:
			self.redirect(users.create_login_url(self.request.uri))
			return
	
		from models import Worker
		worker_query = Worker.all()
		worker_query.ancestor(db.Key.from_path('Worker', 'default'))
		w_results = worker_query.filter("email = ", user.nickname())
		# If there is a worker that matches with the email...
		if w_results.get():
			worker = w_results[0]
			# Save the employer info into the session
			self.session['profile'] 	= 'employer'
			self.session['worker_key'] 	= str(worker.key())
			self.session['country_key'] = str(worker.w_country.key())
			
			# Save the global country key into the session
			from models import Country
			country_query = Country.all()
			country_query.ancestor(db.Key.from_path('Country', 'default'))
			global_country = country_query.filter('name', 'GLOBAL')[0]
			self.session['g_country_key'] = str(global_country.key())
			
			self.redirect('/employer/info?p=intro')
		else:
			# Else, redirect to the welcome page
			self.redirect('/?e=3')

app = webapp2.WSGIApplication([	('/superadmin', SuperAdmin),
								('/localadmin', LocalAdmin),
								('/employer', Employer)],
								config=config,
								debug=True)