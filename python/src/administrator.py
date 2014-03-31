# -*- encoding: utf-8 -*-
'''
Created on 10/04/2013

@author: Carlos Lallana
'''

import webapp2

import jinja2
import os

from google.appengine.ext import db

from models import Administrator
from models import Country

# Initialize Jinja2
jinja_environment = jinja2.Environment(
					loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class View(webapp2.RequestHandler):
	
	def get(self):
		'''Handles GET requests'''

		action = self.request.get('action')
		
		if action == 'view_administrators':
			page = self.request.get("p")
			order = self.request.get("order")
			self.viewAdministrators(page, order)
			
		elif action == 'view_new_administrator':
			self.viewAdministrator(None)
			
		elif action == 'view_edit_administrator':
			self.viewAdministrator(self.request.get('k'))
			
		else:
			self.viewAdministrators('1', '')


	def post(self):
		'''Handles POST requests'''
			
		if self.request.get('action') == 'edit_administrator':
			self.viewAdministrator(Administrator.get(self.request.get('k')))	


	def viewAdministrators(self, page, order):
		'''
		Loads a number of administrators into a Administrator list, and renders it 
		to the HTML
		@param page: The current page from the pagination index.
		@param order: The order defined by the user to show the administrators.
		'''
		template_data = Controller().loadAdministrators(page, order)

		message = self.request.get('m')
		if message == '' or message == None:
			info_tag = ''
			
		elif message == '1':
			info_tag = u'Administrador guardado correctamente'
			
		elif message == '2':
			info_tag = u'Administrador eliminado correctamente'
			
		elif message == '3':
			info_tag = u'Administrador editado correctamente'
			
		elif message == '4':
			info_tag = u'Error al guardar el administrador'
		
		template_data.update({'info_tag': info_tag})
		
		template = jinja_environment.get_template('templates/administrator_list.html')
		self.response.out.write(template.render(template_data))


	def viewAdministrator(self, administrator_key):
		'''
		Renders the page to create or edit a new Administrator. If there's no key, a
		new administrator will be created, else, the selected administrator will be modified.
		@param administrator_key: The key that references the administrator
		'''
		# If there's a key, get the administrator that references to it
		if administrator_key:
			administrator = Administrator.get(administrator_key)
		else:
			administrator = None
		
		# Get all the countries that will match with the administrator
		countries_query	= Country.all()
		#countries_query.ancestor(db.Key.from_path('Country', 'default'))
		
		template_data = {
			'administrator'	: administrator,
			'countries'	: countries_query
		}
		
		template = jinja_environment.get_template('templates/administrator_new_edit.html')
		self.response.out.write(template.render(template_data))


class Controller(webapp2.RequestHandler):
		
	def post(self):
		"""Handles POST requests"""
		
		action = self.request.get('action')
			
		if action == 'save_administrator':
			self.createEditAdministrator(None)
			
		if action == 'edit_administrator':
			self.createEditAdministrator(self.request.get("k"))
			
		if action == 'delete_administrator':
			self.deleteAdministrator(self.request.get("k"))
		

	def createEditAdministrator(self, administrator_key):
		'''
		Calls the function to save the administrator into the datastore and responses 
		the Ajax request.
		
		@param administrator_key: it refers to the Administrator that is going to be 
		edited. If 'None', a new Administrator will be created.
		'''	
		# If everything went ok...
		if self.saveAdministrator(administrator_key): # Returns True if saving was successful
			self.response.out.write('OK')
			return
			
		else:
			self.response.out.write("Error al guardar el administrador. Revise los datos.")
			return


	def saveAdministrator(self, administrator_key):
		'''
		Saves and stores a new Administrator into the Datastore.
		
		@param administrator_key: It refers to the administrator that is going 
			to be edited. If 'None', a new administrator will be created.
		@return: True or False, depending on if the saving was correct.
		'''
		
		# Get the input attributes
		email 	= self.request.get('email')
		c_key 	= self.request.get('c_key') # country key
		
		# Handle exceptions for saving data to the datastore
		try:		
			if not administrator_key:
				# Create a new Administrator
				administrator 	= Administrator(email=email,
												a_country=Country.get(c_key),
												parent=db.Key.from_path('Administrator', 'default'))
				
			else:
				# Get the administrator by its key to edit it
				administrator 			= Administrator.get(administrator_key)
				
				administrator.email		= email
				administrator.a_country	= Country.get(c_key)				
				
			administrator.put()
			return True
		
		except:
			return False
		
		
	def deleteAdministrator(self, administrator_key):
		'''
		Deletes an existing administrator from the datastore.
		
		@param administrator_key: it refers to the Administrator that is going to be 
		deleted.
		'''		
		# Get the administrator by its key
		administrator = Administrator.get(administrator_key)
		
		# Delete administrator
		administrator.delete()

		self.response.out.write("OK")
		return


	def loadAdministrators(self, page, order):
		'''Loads n Customers at a time from the Datastore in order to have a 
		proper pagination index'''
		# Get all the administrators
		administrator_query = Administrator.all()
		administrator_query.ancestor(db.Key.from_path('Administrator', 'default'))
		# If there are any administrators...
		if administrator_query.get():
			# Order depending on the chosen attribute
			if order:
				administrator_query.order(order)
			else:
				administrator_query.order('-updated')
			
			import math
			# Create the pagination elements
			current_page 			= int(page)
			administrators_per_page	= 5
			n_administrators 		= administrator_query.count()
			n_pages 				= int(math.ceil(float(n_administrators) / administrators_per_page))
			administrators 			= administrator_query.run(offset=current_page*administrators_per_page-administrators_per_page, limit=5)

		else:
			n_pages 		= 0
			current_page 	= 1
			administrators 	= None
		
		# Get all the countries (except the Global one) to fill the selectors
		country_query = Country.all()
		country_query.filter('name != ', 'GLOBAL')
		
		template_data = {
			'n_pages'		: n_pages,
			'p'				: current_page,
			'order'			: order,
			'administrators': administrators,
			'countries'		: country_query
		}
		
		return template_data
	

app = webapp2.WSGIApplication([	('/administrators', View),
								('/administrators/save', Controller),
								('/administrators/edit', View),
								('/administrators/delete', Controller)],
								debug=True)