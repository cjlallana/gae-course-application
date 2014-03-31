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

from models import Course
from models import Country
from models import Worker
from models import Plan
from models import WorkerCourseRelation as Application


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
		template_data = Controller().loadCourses(self.session)
		
		template = jinja_environment.get_template('templates/EMP_course_list.html')
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
		countries.ancestor(db.Key.from_path('Country', 'default'))
		plans		= Plan.all()
		plans.ancestor(db.Key.from_path('Plan', 'default'))

		template_data = {
			'course'	: course,
			'countries'	: countries,
			'plans'		: plans
		}
		
		template = jinja_environment.get_template('templates/course_new_edit.html')
		self.response.out.write(template.render(template_data))


class Controller(session.BaseHandler):
		
	def get(self):
		'''
		Handles GET requests
		'''
		action = self.request.get('action')
		
		if action == 'confirm':
			self.confirmApplications()


	def post(self):
		"""Handles POST requests"""
		
		action = self.request.get('action')
			
		if action == 'cancel':
			self.cancelApplication(self.request.get("k"))
			
		if action == 'apply':
			self.applyCourse(self.request.get("k"))


	def cancelApplication(self, application_key):
		'''
		Deletes the given application, and sets the course as free in the HTML.
		
		@param application_key: it refers to the Application that is going to be 
		deleted.
		@return: the key of the course that the application was referencing.
		'''
		# Get the application by its key	
		application = Application.get(application_key)

		# Get the application's course and worker
		worker = application.r_worker
		course = application.r_course
		
		# Add the course's credits to the worker's credits
		worker.local_credits += course.cost_local_credits
		worker.global_credits += course.cost_global_credits
		worker.put()
		
		# Delete application
		application.delete()
		
		# Retun the course key to the ajax call 
		self.response.out.write("OK")
		return


	def applyCourse(self, course_key):
		'''
		Creates a new application taking the selected course and the current
		user.
		
		@param course_key: Course that will be applied.
		@return: the key of the application.
		'''
		# Get the employer
		worker = Worker.get(self.session['worker_key'])
		#Get the course
		course = Course.get(course_key)
		# Get the employer's country
		country = worker.w_country
		
		# Check if the employer has enough credits
		if worker.local_credits < course.cost_local_credits:
			self.response.out.write("ERROR_LC")
			return
		
		if worker.global_credits < course.cost_global_credits:
			self.response.out.write("ERROR_GC")
			return
		
		try:
			# Substract the credit cost from the employer
			worker.local_credits	-= course.cost_local_credits
			worker.global_credits 	-= course.cost_global_credits
			worker.put()
			
			# Save the application
			application = Application(	r_worker=worker, 
										r_course=course,
										r_country=country,
										status='Solicitado',
										parent=db.Key.from_path('WorkerCourseRelation', 'default'))
			
			application.put()
			
			self.response.out.write("OK")
			return
		
		except:
			self.response.out.write("ERROR")
			return


	def confirmApplications(self):
		'''
		Confirms all the courses that the employer applied.
		'''
		# Get the current employer
		worker = Worker.get(self.session['worker_key'])

		# Get all the applications
		applications_query = worker.wc_relations.filter('status', 'Solicitado')

		for a in applications_query:
			a.status = 'Confirmado'
			a.put()

		self.redirect('/employer/courses')
		return


	def loadCourses(self, session):
		'''
		Loads the courses separately
		'''
		# Get the employer
		worker 		= Worker.get(session['worker_key'])
		# Get the employer's country
		country 	= worker.w_country
		# Get the global country
		g_country 	= Country.get(session['g_country_key'])
		
		# Get all the employer's applications
		application_query = worker.wc_relations
		application_query.ancestor(db.Key.from_path('WorkerCourseRelation', 'default'))
								
		applications_list = application_query.run(limit=100)
			
		# Create 2 lists containing the local and global applications, and 
		# another 2 lists containing the courses related to those applications
		l_applications = []
		g_applications = []
		lc_applied_list = []
		gc_applied_list = []
		for a in applications_list:
			if a.r_course.c_country.name == "GLOBAL":
				g_applications.append(a)
				gc_applied_list.append(a.r_course)
			else:
				l_applications.append(a)
				lc_applied_list.append(a.r_course)
			
		# Get all the (local) courses from the worker's country
		local_course_query = country.courses
		lc_list = local_course_query.run(limit=100)
		# Get all the global courses (from the global country)
		global_course_query = g_country.courses
		gc_list = global_course_query.run(limit=100)
		
		# Get all the available local courses
		lc_free_list = []
		for c in lc_list:
			if c not in lc_applied_list:
				# Check if any of the course's plans match with the worker's plan
				relations = c.pc_relations
				for r in relations:
					if worker.w_plan == r.r_plan:
						lc_free_list.append(c)
						break
		
		# Get all the available global courses
		gc_free_list = []
		for c in gc_list:
			if c not in gc_applied_list:
				# Check if any of the course's plans match with the worker's plan
				relations = c.pc_relations
				for r in relations:
					if worker.w_plan == r.r_plan:
						gc_free_list.append(c)
						break

	
		template_data = {
			'worker'			: worker,
			'l_applications'	: l_applications,
			'g_applications'	: g_applications,
			'free_l_courses'	: lc_free_list,
			'free_g_courses'	: gc_free_list
		}
		
		return template_data
			

app = webapp2.WSGIApplication([	('/employer/courses', View),
								('/employer/courses/change', Controller),
								('/employer/courses/confirm', Controller)],
								config=config,
								debug=True)