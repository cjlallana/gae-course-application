# -*- encoding: utf-8 -*-
'''
Created on 11/04/2013

@author: Carlos Lallana
'''

import webapp2

import jinja2
import os

from google.appengine.ext import db
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

from models import Worker
from models import Plan
from models import Country

# Initialize Jinja2
jinja_environment = jinja2.Environment(
					loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class View(webapp2.RequestHandler):
	
	def get(self):
		'''
		Handles GET requests
		'''
		action = self.request.get('action')
		
		if action == 'view_workers':
			self.viewWorkers()
			
		elif action == 'view_new_worker':
			self.viewWorker(None)
			
		elif action == 'view_edit_worker':
			self.viewWorker(self.request.get('k'))
			
		else:
			self.viewWorkers()


	def post(self):
		'''
		Handles POST requests
		'''
		action = self.request.get('action')
		
		if action == 'edit_worker':
			self.viewWorker(Worker.get(self.request.get('k')))	
			
		elif action == 'mass_load':
			self.massLoad()

	def viewWorkers(self):
		'''
		Loads a number of workers into a Worker list, and renders it 
		to the HTML.
		'''
		page 	= self.request.get("p") # current page from the pagination index
		order 	= self.request.get("order") # order to show the courses
		country	= self.request.get("country").capitalize()
		email	= self.request.get("email")
		c_ok	= self.request.get("ok")
		c_error	= self.request.get("err")
		
		filters = {
			'country'	: country,
			'email'		: email
		}
		
		if not page:
			page = '1'
		
		template_data = Controller().loadWorkers(page, order, filters)

		message = self.request.get('m')
		if message == '' or message == None:
			info_tag = ''
			
		elif message == '1':
			info_tag = u'Empleado guardado correctamente'
			
		elif message == '2':
			info_tag = u'Empleado eliminado correctamente'
			
		elif message == '3':
			info_tag = u'Error al guardar el empleado'
			
		elif message == '4':
			info_tag = u'Error al eliminar el empleado'
			
		elif message == '5':
			info_tag = u'Se eliminaron todos los empleados'
			
		elif message == '6':
			info_tag = u'Carga masiva de empleados completada'
		
		upload_url = blobstore.create_upload_url('/workers/upload')
		template_data.update({	'upload_url'	: upload_url,
								'info_tag'		: info_tag,
								'count_ok'		: c_ok,
								'count_error'	: c_error})
		
		template = jinja_environment.get_template('templates/worker_list.html')
		self.response.out.write(template.render(template_data))


	def viewWorker(self, worker_key):
		'''
		Renders the page to create or edit a new Worker. If there's no key, a
		new worker will be created, else, the selected worker will be modified.
		@param worker_key: The key that references the worker
		'''
		# If there's a key, get the worker that references to it
		if worker_key:
			worker = Worker.get(worker_key)
		else:
			worker = None
		
		# Get all the countries and plans that will match with the worker
		countries_query = Country.all()
		countries_query.filter('name != ', 'GLOBAL')
		plans_query		= Plan.all()
		plans_query.ancestor(db.Key.from_path('Plan', 'default')).order('name')
		
		template_data = {
			'worker'	: worker,
			'countries'	: countries_query,
			'plans'		: plans_query
		}
		
		template = jinja_environment.get_template('templates/worker_new_edit.html')
		self.response.out.write(template.render(template_data))


class Controller(webapp2.RequestHandler):
		
	def post(self):
		'''
		Handles POST requests
		'''
		action = self.request.get('action')
			
		if action == 'save_worker':
			self.createEditWorker(None)
			
		if action == 'edit_worker':
			self.createEditWorker(self.request.get("worker_key"))
			
		if action == 'delete_worker':
			self.deleteSingleWorker(self.request.get("k"))
			
		if action == 'delete_all_workers':
			self.deleteAllWorkers()
		

	def createEditWorker(self, worker_key):
		'''
		Calls the function to save the worker into the datastore and responses 
		the Ajax request.
		
		@param worker_key: it refers to the Worker that is going to be 
		edited. If 'None', a new Worker will be created.
		'''	
		# Get the input attributes
		email 	= self.request.get('email')
		c_key 	= self.request.get('c_key') #country_key
		p_key 	= self.request.get('p_key') #plan_key
		lc		= int(self.request.get('local_credits'))
		gc		= int(self.request.get('global_credits'))
		
		# If everything went ok...
		if self.saveWorker(worker_key, email, c_key, p_key, lc, gc): # Returns True if saving was successful
			self.redirect('/workers?action=view_workers&p=1&m=1')
			return
			
		else:
			self.redirect('/workers?action=view_workers&p=1&m=3')
			return


	def saveWorker(self, worker_key, email, c_key, p_key, lc, gc):
		'''
		Saves and stores a new Worker into the Datastore.
		
		@param worker_key: It refers to the worker that is going to be edited.
			If 'None', a new worker will be created.
		@param attributes: all the worker's attributes.
		@return: True or False, depending on if the saving was correct.
		'''		
		# Handle exceptions for saving data to the datastore
		try:		
			if not worker_key: # Create a new Worker
				# Check if the worker already exists
				worker_query = Worker.all()
				worker_query.filter('email = ', email)
				if worker_query.get():
					return False
				else:
					worker = Worker(email			= email,
									w_country		= Country.get(c_key),
									w_plan			= Plan.get(p_key),
									local_credits	= lc,
									global_credits	= gc,
									parent			= db.Key.from_path('Worker', 'default'))
				
			else:
				# Get the worker by its key to edit it
				worker 					= Worker.get(worker_key)
				
				worker.email			= email
				worker.w_country		= Country.get(c_key)
				worker.w_plan			= Plan.get(p_key)
				worker.local_credits	= lc
				worker.global_credits	= gc
				
			worker.put()

			return True
			
		except:
			return False
		
		
	def deleteWorker(self, worker_key):
		'''
		Deletes an existing worker from the datastore.
		
		@param worker_key: it refers to the Worker that is going to be 
		deleted.
		'''
		try:			
			# Get the worker by its key
			worker = Worker.get(worker_key)
			
			# Delete all its relations with the courses.
			for wcr in worker.wc_relations:
				wcr.delete()
			
			# Delete worker
			worker.delete()
			return True
		
		except:
			return False


	def deleteSingleWorker(self, worker_key):
		'''
		Calls the function to delete an existing worker from the datastore.
		
		@param worker_key: it refers to the Course that is going to be 
		deleted.
		'''		
		if self.deleteWorker(worker_key):
			self.redirect('/workers?action=view_workers&p=1&m=2')
			return
		
		else:
			self.redirect('/workers?action=view_courses&p=1&m=4')
			return
		
		
	def deleteAllWorkers(self):
		'''
		Deletes all the existing workers from the datastore.
		'''
		# Get all the courses
		worker_query = Worker.all()
		worker_query.ancestor(db.Key.from_path('Worker', 'default'))
		
		for w in worker_query:
			self.deleteWorker(w.key())
			
		self.redirect('/workers?action=view_courses&p=1&m=5')
		return
	

	def loadWorkers(self, page, order, filters):
		'''Loads n Customers at a time from the Datastore in order to have a 
		proper pagination index'''
		# Get all the workers
		worker_query = Worker.all()
		worker_query.ancestor(db.Key.from_path('Worker', 'default'))
		
		# If there are any workers...
		if worker_query.get():
			# Order depending on the chosen attribute
			if order:
				worker_query.order(order)
			else:
				worker_query.order('email')
			
			# Filter depending on the user's choice
			for f in filters:	# Get each key of the dictionary
				key = f
				value = filters[f]
				# If the key's value is nor empty...
				if value:
					# If we are filtering by country...
					if key == 'country':
						# Get the all the countries, and filter the country we
						# are looking for
						country_query = Country.all()
						country_query.ancestor(db.Key.from_path('Country', 'default'))
						country_query.filter('name >= ', value)
						country_query.filter('name < ', value + u"\ufffd")

						# A query is returned, with none or one result
						if country_query.get():
							# If there is any country, get its workers
							worker_query = country_query[0].workers
							if not worker_query.get():
								worker_query = None
								break
						else:
							worker_query = None
							break
					
					else:
						worker_query.filter(key + ' >= ', value)
						worker_query.filter(key + ' < ', value + u"\ufffd")
						if not worker_query.get():
							worker_query = None
							break
						
			if worker_query:
				import math
				# Create the pagination elements
				current_page 		= int(page)
				workers_per_page	= 10
				n_workers			= worker_query.count()
				n_pages 			= int(math.ceil(float(n_workers) / workers_per_page))
				workers 			= worker_query.run(offset=current_page*workers_per_page-workers_per_page, limit=workers_per_page)
			
			else:
				n_pages 		= 0
				current_page 	= 1
				workers 		= None
				
		else:
			n_pages 		= 0
			current_page 	= 1
			workers 		= None
		
		# Get all the countries (except Global) to fill the selectors
		country_query = Country.all()
		country_query.filter('name != ', 'GLOBAL')
		
		template_data = {
			'n_pages'	: n_pages,
			'p'			: current_page,
			'order'		: order,
			'filters'	: filters,
			'workers'	: workers,
			'countries'	: country_query
		}
		
		return template_data
	
	
class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
	
	def post(self):
		'''
		Handles POST requests
		'''
		upload_files = self.get_uploads('file')
		blob_info = upload_files[0]
		
		blob_reader = blobstore.BlobReader(blob_info.key(), buffer_size=1048576)
		csv_data = blob_reader.read()
		
		import StringIO
		buf = StringIO.StringIO(csv_data)
		buf.readline() # Avoid first line
		line = buf.readline()
		
		count_ok = 0
		count_error = 0
		
		# Loop through the lines, which will be each employer's info
		while not line == '':
			try:
				data_ok = True
				# Delete the end of line character, and separate by comas
				data = line.rstrip().split(',')
				# Now, we get:
				# data[0]: email/ID
				# data[1]: country code
				# data[2]: plan code
				# data[3]: plan's local credits
				# data[4]: plan's global credits
				# Check if the worker already exists
				worker_query = Worker.all()
				worker_query.filter('email = ', data[0])
				if worker_query.get():
					count_error += 1
				else:
					# Get the worker's country
					c_query = Country.all()
					c_query.filter('code =', data[1])
					if c_query.get():
						country = c_query.get()
					else:
						data_ok = False
					# Get the worker's plan
					p_query = Plan.all()
					p_query.filter('code =', data[2])
					if p_query.get():
						plan = p_query.get()
					else:
						data_ok = False
					
					if data_ok:
						# Save the worker
						saved_ok = Controller().saveWorker(	None, 
															data[0], 
															country.key(), 
															plan.key(), 
															int(data[3]), 
															int(data[4]))
						if saved_ok:
							count_ok += 1
						else:
							count_error += 1
		
					else:
						count_error += 1
			except:
				count_error += 1
			
			# Get the next line	
			line = buf.readline()
		
		
		self.redirect('/workers?action=view_workers&p=1&m=6&ok=' + str(count_ok) 
						+ '&err=' + str(count_error))
		return
			

app = webapp2.WSGIApplication([	('/workers', View),
								('/workers/new', View),
								('/workers/new/save', Controller),
								('/workers/edit', View),
								('/workers/delete', Controller),
								('/workers/upload', UploadHandler)],
								debug=True)