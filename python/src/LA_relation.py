# -*- encoding: utf-8 -*-
'''
Created on 08/04/2013

@author: Carlos Lallana
'''

import webapp2
import jinja2
import os

import session

from google.appengine.ext import db

from models import WorkerCourseRelation as Relation
from models import Worker
from models import Course
from models import Country


# Initialize Jinja2
jinja_environment = jinja2.Environment(
					loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		
config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': 'ole',
}


class View(session.BaseHandler):
	
	def get(self):
		'''
		Handles GET requests
		'''
		action = self.request.get('action')
		
		if action == 'view_applications':
			self.viewRelations()
			
		elif action == 'view_new_application':
			self.viewRelation(None)
			
		elif action == 'view_edit_application':
			self.viewRelation(self.request.get('k'))
			
		else:
			self.viewRelations()


	def post(self):
		'''Handles POST requests'''
			
		if self.request.get('action') == 'edit_relation':
			self.viewRelation(Relation.get(self.request.get('k')))	


	def viewRelations(self):
		'''
		Loads a number of relations into a Relation list, and renders it 
		to the HTML
		'''
		page 	= self.request.get("p") # current page from the pagination index
		order 	= self.request.get("order") # order to show the relations
		course	= self.request.get("course").capitalize()
		worker	= self.request.get("worker")
		status 	= self.request.get("status").capitalize()
		
		filters = {
			'course'	: course,
			'worker'	: worker,
			'status'	: status
		}
		
		if not page:
			page = '1'
			
		template_data = Controller().loadRelations(self.session, page, order, filters)

		message = self.request.get('m')
		if message == '' or message == None:
			info_tag = ''
			
		elif message == '1':
			info_tag = u'Relación guardada correctamente'
			
		elif message == '2':
			info_tag = u'Relación eliminada correctamente'
			
		elif message == '3':
			info_tag = u'Error al guardar la relación'
			
		elif message == '4':
			info_tag = u'Error al eliminar la relación'
			
		elif message == '5':
			info_tag = u'Se eliminaron todas las relaciones'

		template_data.update({'info_tag': info_tag})
		
		template = jinja_environment.get_template('templates/LA_relation_list.html')
		self.response.out.write(template.render(template_data))


	def viewRelation(self, relation_key):
		'''
		Renders the page to create or edit a new Relation. If there's no key, a
		new relation will be created, else, the selected relation will be modified.
		@param relation_key: The key that references the relation
		'''
		# If there's a key, get the relation that references to it
		if relation_key:
			relation = Relation.get(relation_key)
		else:
			relation = None
		
		template_data = {
			'relation'	: relation
		}
		
		template = jinja_environment.get_template('templates/LA_relation_new_edit.html')
		self.response.out.write(template.render(template_data))


class Controller(session.BaseHandler):
		
	def post(self):
		"""Handles POST requests"""
		
		action = self.request.get('action')
			
		if action == 'save_relation':
			self.createEditRelation(None)
			
		if action == 'edit_relation':
			self.createEditRelation(self.request.get("relation_key"))
			
		if action == 'delete_relation':
			self.deleteSingleRelation(self.request.get("k"))
			
		if action == 'delete_all_relations':
			self.deleteAllRelations()
			
		if action == 'check_data':
			self.checkData(self.request.get("w_email"), self.request.get("c_code"))
		

	def createEditRelation(self, relation_key):
		'''
		Calls the function to save the relation into the datastore and responses 
		the Ajax request.
		
		@param relation_key: it refers to the Relation that is going to be 
		edited. If 'None', a new Relation will be created.
		'''	
		# Get the user input
		w_email	= self.request.get('w_email')
		c_code	= self.request.get('c_code')
		
		worker_query = Worker.all().ancestor(db.Key.from_path('Worker', 'default'))
		worker = worker_query.filter('email = ', w_email)[0]
		w_key = worker.key()
		
		course_query = Course.all().ancestor(db.Key.from_path('Course', 'default'))
		course = course_query.filter('code = ', c_code)[0]
		c_key = course.key()
		
		if self.saveRelation(relation_key, w_key, c_key): # Returns True if saving was successful
			self.redirect('/localadmin/applications?action=view_applications&p=1&m=1')
			return
			
		else:
			self.redirect('/localadmin/applications?action=view_applications&p=1&m=3')
			return


	def checkData(self, w_email, c_code):
		'''
		Checks if the email and course are correct and can be selected
		according to each other.
		
		@param w_email: Worker's email
		@param c_code: Course code 
		@return: True or False
		'''
		# Get the local admin's country
		country = Country.get(self.session['country_key'])
		# Get the worker by its email
		worker_query = country.workers
		results = worker_query.filter('email = ', w_email)
		if not results.get():
			self.response.out.write('El email introducido es incorrecto o no ' +
								'corresponde a ningún empleado de su país')
			return
		
		worker = results[0]
		
		# Get the worker's country
		country = worker.w_country
		
		# Get all the courses from that country
		course_query = country.courses
		
		# Check if the course is available for that country
		results = course_query.filter('code = ', c_code)
		if not results.get():
			self.response.out.write('El curso indicado no es correcto o aplicable en el país del empleado')
			return
		
		self.response.out.write('OK')
		

	def saveRelation(self, relation_key, w_key, c_key):
		'''
		Saves and stores a new Relation into the Datastore.
		
		@param relation_key: It refers to the relation that is going to be edited.
			If 'None', a new relation will be created.
		@return: True or False, depending on if the saving was correct.
		'''
		status 	= self.request.get('status')
		
		# Handle exceptions for saving data to the datastore
		try:		
			if not relation_key:
				# Create a new Relation
				relation 	= Relation(	r_worker=Worker.get(w_key), 
										r_course=Course.get(c_key),
										r_country=Country.get(self.session['country_key']),
										status=status,
										parent=db.Key.from_path('WorkerCourseRelation', 'default'))
				
			else:
				# Get the relation by its key to edit it
				relation 			= Relation.get(relation_key)
				
				relation.r_worker	= Worker.get(w_key)
				relation.r_course	= Course.get(c_key)
				relation.r_country	= Country.get(self.session['country_key'])
				relation.status		= status
				
			relation.put()

			return True
			
		except:
			return False
		
		
	def deleteRelation(self, relation_key):
		'''
		Deletes an existing relation from the datastore.
		
		@param relation_key: it refers to the Relation that is going to be 
		deleted.
		'''
		try:
			# Get the relation by its key
			relation = Relation.get(relation_key)
		
			# Delete relation		
			relation.delete()
			return True
		
		except:
			return False


	def deleteSingleRelation(self, relation_key):
		'''
		Calls the function to delete an existing relation from the datastore.
		
		@param relation_key: it refers to the Relation that is going to be 
		deleted.
		'''		
		if self.deleteRelation(relation_key):
			self.redirect('/localadmin/applications?action=view_applications&p=1&m=2')
			return
		
		else:
			self.redirect('/localadmin/applications?action=view_applications&p=1&m=4')
			return
		

	def deleteAllRelations(self):
		'''
		Deletes all the existing relations from the datastore.
		'''
		# Get all the relations
		relation_query = Relation.all()
		relation_query.ancestor(db.Key.from_path('WorkerCourseRelation', 'default'))
		
		for r in relation_query:
			self.deleteRelation(r.key())
			
		self.redirect('/localadmin/applications?action=view_applications&p=1&m=5')
		return


	def loadRelations(self, session, page, order, filters):
		'''Loads n Relations at a time from the Datastore in order to have a 
		proper pagination index'''
		# Get the local admin's country
		country = Country.get(session['country_key'])
		# Get the country's relations
		relations_query = country.wc_relations
		relations_query.ancestor(db.Key.from_path('WorkerCourseRelation', 'default'))
		
		if relations_query.get():
			for f in filters:
				key = f
				value = filters[f]
				
				if value:
					if key == 'course':
						course_query = Course.all()
						course_query.ancestor(db.Key.from_path('Course', 'default')).filter('code = ', value)
						if course_query.get():
							course = course_query[0]
							relations_query.filter('r_course = ', course)
						else:
							relations_query = None
						
					if key == 'worker':
						worker_query = Worker.all()
						worker_query.ancestor(db.Key.from_path('Worker', 'default')).filter('email = ', value)
						if worker_query.get():
							worker = worker_query[0]
							relations_query.filter('r_worker = ', worker)
						else:
							relations_query = None
							
					if key == 'status':
						relations_query.filter('status = ', value)
						if not relations_query.get():
							relations_query = None
		
			if relations_query:
				import math
				# Create the pagination elements
				current_page 		= int(page)
				relations_per_page	= 5
				n_relations 		= relations_query.count()
				n_pages 			= int(math.ceil(float(n_relations) / relations_per_page))
				relations 			= relations_query.run(offset=current_page*relations_per_page-relations_per_page, limit=5)
	
			else:
				n_pages 		= 0
				current_page 	= 1
				relations 		= None
		
		else:
			n_pages 		= 0
			current_page 	= 1
			relations 		= None
				
		template_data = {
			'n_pages'	: n_pages,
			'p'			: current_page,
			'order'		: order,
			'filters'	: filters,
			'relations'	: relations
		}
		
		return template_data
	

app = webapp2.WSGIApplication([	('/localadmin/applications', View),
								('/localadmin/applications/new', View),
								('/localadmin/applications/new/save', Controller),
								('/localadmin/applications/edit', View),
								('/localadmin/applications/delete', Controller),
								('/localadmin/applications/checkdata', Controller)],
								config=config,
								debug=True)