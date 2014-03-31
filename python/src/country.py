# -*- encoding: utf-8 -*-
'''
Created on 03/04/2013

@author: Carlos Lallana
'''

import webapp2

import jinja2
import os

from google.appengine.ext import db

from models import Country

# Initialize Jinja2
jinja_environment = jinja2.Environment(
					loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class View(webapp2.RequestHandler):
	
	def get(self):
		'''Handles GET requests'''

		action = self.request.get('action')
		
		if action == 'view_countries':
			page = self.request.get("p")
			self.viewCountries(page)
			
		else:
			self.viewCountries('1')	


	def viewCountries(self, page):
		'''
		Loads a number of countries into a Country list, and renders it 
		to the HTML
		@param page: The current page from the pagination index.
		@param order: The order defined by the user to show the countries.
		'''
		template_data = Controller().loadCountries(page)

		message = self.request.get('m')
		if message == '' or message == None:
			info_tag = ''
			
		elif message == '1':
			info_tag = u'País guardado correctamente'
			
		elif message == '2':
			info_tag = u'País eliminado correctamente'
		
		elif message == '3':
			info_tag = u'País editado correctamente'
			
		template_data.update({'info_tag': info_tag})
		
		template = jinja_environment.get_template('templates/country_list.html')
		self.response.out.write(template.render(template_data))


class Controller(webapp2.RequestHandler):
		
	def post(self):
		"""Handles POST requests"""
		
		action = self.request.get('action')
			
		if action == 'save_country':
			self.createEditCountry(None)
			
		if action == 'edit_country':
			self.createEditCountry(self.request.get("k"))
			
		if action == 'delete_country':
			self.deleteCountry(self.request.get("k"))
			
		if action == 'check_code':
			self.checkCode(self.request.get("k"), self.request.get("code"))
					

	def createEditCountry(self, country_key):
		'''
		Calls the function to save the country into the datastore and responses 
		the Ajax request.
		
		@param country_key: it refers to the Country that is going to be 
		edited. If 'None', a new Country will be created.
		'''	
		# If everything went ok...
		if self.saveCountry(country_key): # Returns True if saving was successful
			self.response.out.write('OK')
			return
			
		else:
			self.response.out.write("Error al guardar el país. Revise los datos.")
			return
		
	def saveCountry(self, country_key):
		'''
		Saves and stores a new Country into the Datastore.
		
		@param country_key: It refers to the country that is going to be edited.
			If 'None', a new country will be created.
		@return: True or False, depending on if the saving was correct.
		'''
		# Handle exceptions for saving data to the datastore
		try:		
			if not country_key:
				# Create a new Country
				name 	= self.request.get('name').capitalize()
				code 	= self.request.get('code').capitalize()
				
				country = Country(	name= name, 
									code=code,
									parent=db.Key.from_path('Country', 'default'))
				
			else:
				# Get the country by its key
				country 	= Country.get(country_key)
				
			country.name 	= self.request.get('name').capitalize()
			country.code	= self.request.get('code')
			
			country.put()
			return True
			
		except:
			return False
		
		
	def deleteCountry(self, country_key):
		'''
		Deletes an existing country from the datastore and responses the 
		Ajax request.
		
		@param country_key: it refers to the Country that is going to be 
		deleted.
		'''		
		# Get the country by its key
		country = Country.get(country_key)

		# Delete all the workers, and each worker/course relation, from the 
		# country.
		for w in country.workers:
			for wcr in w.wc_relations:
				wcr.delete()
			w.delete()
		
		# Delete all the courses, and each plan/course relation, from the 
		# country.
		for c in country.courses:
			for pcr in c.pc_relations:
				pcr.delete()
			c.delete()
		
		# Delete all the administrators from the country.
		for a in country.administrators:
			a.delete()
		
		# Delete the country
		country.delete()
		
		self.response.out.write('OK')
		return


	def loadCountries(self, page):
		'''Loads n Customers at a time from the Datastore in order to have a 
		proper pagination index'''
		# Get all the countries
		country_query = Country.all()
		country_query.ancestor(db.Key.from_path('Country', 'default'))
		country_query.filter('name != ', 'GLOBAL')
		# If there are any countries...
		if country_query.get():
			# Order by name
			country_query.order('name')
			
			import math
			# Create the pagination elements
			current_page 		= int(page)
			countries_per_page 	= 10
			n_countries 		= country_query.count()
			n_pages 			= int(math.ceil(float(n_countries) / countries_per_page))
			countries 			= country_query.run(offset=current_page*countries_per_page-countries_per_page, limit=countries_per_page)

		else:
			n_pages 		= 0
			current_page 	= 1
			countries 		= None
		
		template_data = {
			'n_pages'	: n_pages,
			'p'			: current_page,
			'countries'	: countries
		}
		
		return template_data
	

	def checkCode(self, country_key, code):
		'''Checks if the country code already exists'''
		# Get all the countries
		country_query = Country.all()
		
		# Get the countries with the given code
		country_query.filter('code =', code)
		
		# If a country with that code already exists, notify the user
		if country_query.get():
			# Check if the user is not changing the code so it remains the same
			if country_key:
				# Get the country that is being edited
				country_edited = Country.get(country_key)
				if country_edited.code == code:
					self.response.out.write("OK")
					return
				
			self.response.out.write("El código ya existe. Introduzca otro nuevo.")

		else:
			self.response.out.write("OK")


app = webapp2.WSGIApplication([('/countries', View),
								('/countries/save', Controller),
								('/countries/delete', Controller),
								('/countries/checkcode', Controller)],
								debug=True)