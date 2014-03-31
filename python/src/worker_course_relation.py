# -*- encoding: utf-8 -*-
'''
Created on 08/04/2013

@author: Carlos Lallana
'''

import webapp2
import jinja2
import os

from google.appengine.ext import db

from models import WorkerCourseRelation as Relation
from models import Worker
from models import Course

# Initialize Jinja2
jinja_environment = jinja2.Environment(
					loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class View(webapp2.RequestHandler):
	
	def get(self):
		'''
		Handles GET requests
		'''
		action = self.request.get('action')
		
		if action == 'view_relations':
			self.viewRelations()
			
		elif action == 'view_new_relation':
			self.viewRelation(None)
			
		elif action == 'view_edit_relation':
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
		course	= self.request.get("course")
		worker	= self.request.get("worker")
		
		filters = {
			'course'	: course,
			'worker'	: worker
		}
		
		if not page:
			page = '1'
			
		template_data = Controller().loadRelations(page, order, filters)

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
		
		template = jinja_environment.get_template('templates/relation_list.html')
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
		
		template = jinja_environment.get_template('templates/relation_new_edit.html')
		self.response.out.write(template.render(template_data))


class Controller(webapp2.RequestHandler):
		
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
		
		worker_query = Worker.all()
		worker = worker_query.ancestor(db.Key.from_path('Worker', 'default')).filter('email = ', w_email)[0]
		w_key = worker.key()
		
		course_query = Course.all()
		course = course_query.ancestor(db.Key.from_path('Course', 'default')).filter('code = ', c_code)[0]
		c_key = course.key()
		
		if self.saveRelation(relation_key, w_key, c_key): # Returns True if saving was successful
			self.redirect('/relations?action=view_relations&p=1&m=1')
			return
			
		else:
			self.redirect('/relations?action=view_relations&p=1&m=3')
			return


	def checkData(self, w_email, c_code):
		'''
		Checks if the email and course are correct and can be selected
		according to each other.
		
		@param w_email: Worker's email
		@param c_code: Course code 
		@return: True or False
		'''
		# Get the worker by its email
		worker_query = Worker.all()
		worker_query.ancestor(db.Key.from_path('Worker', 'default'))
		results = worker_query.filter('email = ', w_email)
		if not results.get():
			self.response.out.write('El email introducido no corresponde a ningún empleado')
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
			r_worker	= Worker.get(w_key)
			r_course	= Course.get(c_key)
			r_country	= r_worker.w_country
			
			if not relation_key:
				# Create a new Relation
				relation 	= Relation(	r_worker=r_worker, 
										r_course=r_course,
										r_country=r_country,
										status=status,
										parent=db.Key.from_path('WorkerCourseRelation', 'default'))
				
			else:
				# Get the relation by its key to edit it
				relation 			= Relation.get(relation_key)
				
				relation.r_worker	= r_worker
				relation.r_course	= r_course
				relation.r_country	= r_country
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
			self.redirect('/relations?action=view_relations&p=1&m=2')
			return
		
		else:
			self.redirect('/relations?action=view_relations&p=1&m=4')
			return
		

	def deleteAllRelations(self):
		'''
		Deletes all the existing relations from the datastore.
		'''
		# Get all the relations
		relation_query = Relation.all()
		relation_query.ancestor(db.Key.from_path('Relation', 'default'))
		
		for r in relation_query:
			self.deleteRelation(r.key())
			
		self.redirect('/relations?action=view_relations&p=1&m=5')
		return


	def loadRelations(self, page, order, filters):
		'''Loads n Customers at a time from the Datastore in order to have a 
		proper pagination index'''
		# Get all the relations
		relation_query = Relation.all()
		relation_query.ancestor(db.Key.from_path('WorkerCourseRelation', 'default'))
		
		# If there are any relations...
		if relation_query.get():
			# Order depending on the chosen attribute
			relation_query.order('-updated')
			
			# Filter depending on the user's choice
			filter_found = False
			course_list = []
			worker_list = []

			for f in filters:	# Get each key of the dictionary
				key = f
				value = filters[f]
				# If the key's value is not empty...
				if value:
					# If we are filtering by worker...
					if key == 'course':
						# Get the all the workers, and filter the worker we
						# are looking for
						courses_query = Course.all()
						courses_query.filter('code >= ', value)
						courses_query.filter('code < ', value + u"\ufffd")
						if courses_query.get():
							filter_found = True
							for w in courses_query:
								for wcr in w.wc_relations:
									course_list.append(wcr)
						else:
							filter_found = False

					# If we are filtering by worker...
					if key == 'worker':
						# Get the all the workers, and filter the worker we
						# are looking for
						workers_query = Worker.all()
						workers_query.filter('email >= ', value)
						workers_query.filter('email < ', value + u"\ufffd")
						if workers_query.get():
							filter_found = True
							for w in workers_query:
								for wcr in w.wc_relations:
									# Check if there is a course_list, and if
									# the relation is already there, so it is
									# a common relation to both filters
									if course_list:
										if wcr in course_list:
											worker_list.append(wcr)
									else:
										worker_list.append(wcr)
						else:
							filter_found = False

			if not filter_found:
				import math
				# Create the pagination elements
				current_page 		= int(page)
				relations_per_page	= 10
				n_relations 		= relation_query.count()
				n_pages 			= int(math.ceil(float(n_relations) / relations_per_page))
				relations 			= relation_query.run(offset=current_page*relations_per_page-relations_per_page, limit=relations_per_page)

			else:
				# If there is a worker list, this is the final list, as we
				# checked before that every element in this list had to be in 
				# both course and worker lists.
				if worker_list:
					wcr_list = worker_list
				# Else, the final list is the course list, as there are no more
				# filtering of workers.
				else:
					wcr_list = course_list
					
				n_pages 		= 0
				current_page 	= 1
				relations = wcr_list
				
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
	

app = webapp2.WSGIApplication([	('/relations', View),
								('/relations/new', View),
								('/relations/new/save', Controller),
								('/relations/edit', View),
								('/relations/delete', Controller),
								('/relations/checkdata', Controller)],
								debug=True)