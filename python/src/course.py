# -*- encoding: utf-8 -*-
'''
Created on 08/04/2013

@author: Carlos Lallana
'''

import webapp2

import jinja2
import os

from google.appengine.ext import db
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

from models import Course
from models import Country
from models import Plan
from models import PlanCourseRelation as PCRelation


# Initialize Jinja2
jinja_environment = jinja2.Environment(
					loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class View(webapp2.RequestHandler):
	
	def get(self):
		'''
		Handles GET requests
		'''
		action = self.request.get('action')
		
		if action == 'view_courses':
			self.viewCourses()
			
		elif action == 'view_new_course':
			self.viewCourse(None)
			
		elif action == 'view_edit_course':
			self.viewCourse(self.request.get('k'))
			
		else:
			self.viewCourses()


	def post(self):
		'''Handles POST requests'''
			
		if self.request.get('action') == 'edit_course':
			self.viewCourse(Course.get(self.request.get('k')))	


	def viewCourses(self):
		'''
		Loads a number of courses into a Course list, and renders it 
		to the HTML
		'''
		page 	= self.request.get("p") # current page from the pagination index
		order 	= self.request.get("order") # order to show the courses
		country	= self.request.get("country")
		code	= self.request.get("code")
		c_ok	= self.request.get("ok")
		c_error	= self.request.get("err")
		
		filters = {
			'country'	: country,
			'code'		: code
		}
		
		if not page:
			page = '1'
			
		template_data = Controller().loadCourses(page, order, filters)

		info_tag = ''
		message = self.request.get('m')
			
		if message == '1':
			info_tag = u'Curso guardado correctamente'
			
		elif message == '2':
			info_tag = u'Curso eliminado correctamente'
			
		elif message == '3':
			info_tag = u'Error al guardar el curso'
			
		elif message == '4':
			info_tag = u'Error al eliminar el curso'
			
		elif message == '5':
			info_tag = u'Se eliminaron todos los cursos'
			
		elif message == '6':
			info_tag = u'Carga masiva de cursos completada'
		
		upload_url = blobstore.create_upload_url('/courses/upload')
		template_data.update({	'upload_url'	: upload_url,
								'info_tag'		: info_tag,
								'count_ok'		: c_ok,
								'count_error'	: c_error})
		
		template = jinja_environment.get_template('templates/course_list.html')
		self.response.out.write(template.render(template_data))


	def viewCourse(self, course_key):
		'''
		Renders the page to create or edit a new Course. If there's no key, a
		new course will be created, else, the selected course will be modified.
		
		@param course_key: The key that references the course
		'''
		# If there's a key, get the course that references to it
		if course_key:
			course = Course.get(course_key)
		else:
			course = None
		
		# Get all the countries and plans that will match with the course
		countries	= Country.all()

		plans		= Plan.all()
		plans.ancestor(db.Key.from_path('Plan', 'default'))
		
		template_data = {
			'course'	: course,
			'countries'	: countries,
			'plans'		: plans
		}
		
		template = jinja_environment.get_template('templates/course_new_edit.html')
		self.response.out.write(template.render(template_data))


class Controller(webapp2.RequestHandler):
		
	def post(self):
		"""Handles POST requests"""
		
		action = self.request.get('action')
			
		if action == 'save_course':
			self.createEditCourse(None)
			
		if action == 'edit_course':
			self.createEditCourse(self.request.get("course_key"))
			
		if action == 'delete_course':
			self.deleteSingleCourse(self.request.get("k"))
			
		if action == 'delete_all_courses':
			self.deleteAllCourses()
		
		if action == 'check_code':
			self.checkCode(self.request.get("k"), self.request.get("code"))

	def createEditCourse(self, course_key):
		'''
		Calls the function to save the course into the datastore and responses 
		the Ajax request.
		
		@param course_key: it refers to the Course that is going to be 
		edited. If 'None', a new Course will be created.
		'''	
		# Get the input attributes
		name 	= self.request.get('name').title()
		code 	= self.request.get('code')
		url		= self.request.get('url')
		c_key 	= self.request.get('c_key')
		p_keys 	= self.request.get_all('p_keys[]')
		cost_lc	= int(self.request.get('cost_local_credits'))
		cost_gc	= int(self.request.get('cost_global_credits'))
		
		# If everything went ok...
		if self.saveCourse(	course_key, name, code, url, c_key, p_keys, 
							cost_lc, cost_gc): # Returns True if saving was ok
			self.redirect('/courses?action=view_courses&p=1&m=1')
			return
			
		else:
			self.redirect('/courses?action=view_courses&p=1&m=3')
			return


	def saveCourse(	self, course_key, name, code, url, c_key, p_keys, 
					cost_lc, cost_gc):
		'''
		Saves and stores a new Course into the Datastore.
		
		@param course_key: It refers to the course that is going to be edited.
			If 'None', a new course will be created.
		@param attributes: all the course's attributes.
		@return: True or False, depending on if the saving was correct.
		'''
		# Handle exceptions for saving data to the datastore
		try:		
			if not course_key:
				# Create a new Course
				course 	= Course(	name= name, 
									code=code,
									url=url,
									c_country=Country.get(c_key),
									cost_local_credits=cost_lc,
									cost_global_credits=cost_gc,
									parent=db.Key.from_path('Course', 'default'))
				
			else:
				# Get the course by its key to edit it
				course 				= Course.get(course_key)
				
				course.name 		= name
				course.code			= code
				course.url			= url
				course.c_country	= Country.get(c_key)
				course.cost_local_credits	= cost_lc
				course.cost_global_credits	= cost_gc
				
				plans_relations		= course.pc_relations # Relations with multiple plans
				for p in plans_relations:
					p.delete()
				
				
			course.put()
			
			# Create the plan-course relations
			for k in p_keys:
				r_plan		= Plan.get(k)
				relation 	= PCRelation(	r_course=course,
											r_plan=r_plan,
											parent=db.Key.from_path('PlanCourseRelation', 'default'))
				relation.put()

			return True
			
		except:
			import traceback
			import logging
			stacktrace = traceback.format_exc()
			logging.error("%s", stacktrace)
			return False
		
		
	def deleteCourse(self, course_key):
		'''
		Deletes an existing course from the datastore.
		
		@param course_key: it refers to the Course that is going to be 
		deleted.
		'''
		# Get the course by its key
		course = Course.get(course_key)
		
		# Delete all its plans relations
		for pcr in course.pc_relations:
			pcr.delete()
		
		# Delete all its courses relations
		for wcr in course.wc_relations:
			wcr.delete()
		
		# Delete course		
		course.delete()
		
		return True


	def deleteSingleCourse(self, course_key):
		'''
		Calls the function to delete an existing course from the datastore.
		
		@param course_key: it refers to the Course that is going to be 
		deleted.
		'''		
		if self.deleteCourse(course_key):
			self.redirect('/courses?action=view_courses&p=1&m=2')
			return
		
		else:
			self.redirect('/courses?action=view_courses&p=1&m=4')
			return
		

	def deleteAllCourses(self):
		'''
		Deletes all the existing courses from the datastore.
		'''
		# Get all the courses
		course_query = Course.all()
		course_query.ancestor(db.Key.from_path('Course', 'default'))
		
		for c in course_query:
			self.deleteCourse(c.key())
			
		self.redirect('/courses?action=view_courses&p=1&m=5')
		return


	def loadCourses(self, page, order, filters):
		'''Loads n Customers at a time from the Datastore in order to have a 
		proper pagination index'''
		# Get all the courses
		course_query = Course.all()
		course_query.ancestor(db.Key.from_path('Course', 'default'))
		
		# If there are any courses...
		if course_query.get():
			# Order depending on the chosen attribute
			if order:
				course_query.order(order)

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
						country_query.filter('name >= ', value)
						country_query.filter('name < ', value + u"\ufffd")

						# A query is returned, with zero or one result
						if country_query.get():
							# If there is any country, get its courses
							course_query = country_query[0].courses
							if not course_query.get():
								course_query = None
								break
						else:
							course_query = None
							break
					
					else:
						course_query.filter(key + ' >= ', value)
						course_query.filter(key + ' < ', value + u"\ufffd")
						if not course_query.get():
							course_query = None
							break
			
			if course_query:
				import math
				# Create the pagination elements
				current_page 		= int(page)
				courses_per_page	= 10
				n_courses 			= course_query.count()
				n_pages 			= int(math.ceil(float(n_courses) / courses_per_page))
				courses 			= course_query.run(offset=current_page*courses_per_page-courses_per_page, limit=courses_per_page)

			else:
				n_pages 		= 0
				current_page 	= 1
				courses 		= None

		else:
			n_pages 		= 0
			current_page 	= 1
			courses 		= None
		
		template_data = {
			'n_pages'	: n_pages,
			'p'			: current_page,
			'order'		: order,
			'filters'	: filters,
			'courses'	: courses,
			'countries'	: Country.all()
		}
		
		return template_data


	def checkCode(self, course_key, code):
		'''Checks if the country code already exists'''
		# Get all the plans
		course_query = Course.all()
		course_query.ancestor(db.Key.from_path('Course', 'default'))
		
		# Get the courses with the given code
		course_query.filter('code =', code)
		
		# If a course with that code already exists, notify the user, unless its
		# the actual course code.
		if course_query.get():
			# Check if the user is not changing the code so it remains the same
			if course_key:
				# Get the country that is being edited
				course_edited = Course.get(course_key)
				if course_edited.code == code:
					self.response.out.write("OK")
					return
				
			self.response.out.write("El código ya existe. Introduzca otro nuevo.")

		else:
			self.response.out.write("OK")
			

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

		course_query = Course.all()

		# Loop through the lines, which will be each employer's info
		while not line == '':
			data_ok = True
			line = line.decode("utf-8")
			# Delete the end of line character, and separate by comas
			data = line.rstrip().split(',')
			# Now, we get:
			# data[0]: course code
			# data[1]: course name
			# data[2]: course local credits
			# data[3]: course global credits
			# data[4]: info URL
			# data[5]: country code
			# data[6]: plans codes
			
			# Check if the worker already exists
			# Check if the course already exists
			course_query.filter('code = ', data[0])
			if course_query.get():
				count_error += 1
			else:
				# Get the course's country
				c_query = Country.all()
				c_query.filter('code =', data[5])
				if c_query.get():
					country = c_query.get()
				else:
					data_ok = False
				
				# Get the course-plan relations
				plan_codes = data[6].split('+')
				p_keys = []
				for p in plan_codes:
					p_query = Plan.all()
					p_query.filter('code =', p)
					if p_query.get():
						plan = p_query.get()
						p_keys.append(plan.key())
				
				if data_ok:
					# Save the course
					saved_ok = Controller().saveCourse(	None, 
														data[1],
														data[0],
														data[4],
														country.key(), 
														p_keys, 
														int(data[2]), 
														int(data[3]))
					if saved_ok:
						count_ok += 1
					else:
						count_error += 1
	
				else:
					count_error += 1
				
			line = buf.readline()
		
		
		self.redirect('/courses?action=view_courses&p=1&m=6&ok=' + str(count_ok) 
						+ '&err=' + str(count_error))
		return


app = webapp2.WSGIApplication([	('/courses', View),
								('/courses/new', View),
								('/courses/new/save', Controller),
								('/courses/edit', View),
								('/courses/delete', Controller),
								('/courses/checkcode', Controller),
								('/courses/upload', UploadHandler)],
								debug=True)