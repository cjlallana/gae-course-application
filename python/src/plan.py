# -*- encoding: utf-8 -*-
'''
Created on 08/04/2013

@author: Carlos Lallana
'''

import webapp2

import jinja2
import os

from google.appengine.ext import db

from models import Plan

# Initialize Jinja2
jinja_environment = jinja2.Environment(
					loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class View(webapp2.RequestHandler):
	
	def get(self):
		'''Handles GET requests'''

		action = self.request.get('action')
		
		if action == 'view_plans':
			page = self.request.get("p")
			order = self.request.get("order")
			self.viewPlans(page, order)
			
		else:
			self.viewPlans('1', '')


	def viewPlans(self, page, order):
		'''
		Loads a number of plans into a Plan list, and renders it 
		to the HTML
		@param page: The current page from the pagination index.
		@param order: The order defined by the user to show the plans.
		'''
		template_data = Controller().loadPlans(page, order)

		message = self.request.get('m')
		if message == '' or message == None:
			info_tag = ''
			
		elif message == '1':
			info_tag = u'Itinerario guardado correctamente'
			
		elif message == '2':
			info_tag = u'Itinerario eliminado correctamente'
			
		elif message == '3':
			info_tag = u'Itinerario editado correctamente'
		
		template_data.update({'info_tag': info_tag})
		
		template = jinja_environment.get_template('templates/plan_list.html')
		self.response.out.write(template.render(template_data))


class Controller(webapp2.RequestHandler):
		
	def post(self):
		"""Handles POST requests"""
		
		action = self.request.get('action')
			
		if action == 'save_plan':
			self.createEditPlan(None)
			
		if action == 'edit_plan':
			self.createEditPlan(self.request.get("k"))
			
		if action == 'delete_plan':
			self.deletePlan(self.request.get("k"))
			
		if action == 'check_code':
			self.checkCode(self.request.get("k"), self.request.get("code"))
		

	def createEditPlan(self, plan_key):
		'''
		Calls the function to save the plan into the datastore and responses 
		the Ajax request.
		
		@param plan_key: it refers to the Plan that is going to be 
		edited. If 'None', a new Plan will be created.
		'''	
		# If everything went ok...
		if self.savePlan(plan_key): # Returns True if saving was successful
			self.response.out.write('OK')
			return
			
		else:
			self.response.out.write("Error al guardar el itinerario. Revise los datos.")
			return


	def savePlan(self, plan_key):
		'''
		Saves and stores a new Plan into the Datastore.
		
		@param plan_key: It refers to the plan that is going to be edited.
			If 'None', a new plan will be created.
		@return: True or False, depending on if the saving was correct.
		'''
		# Get the input attributes
		name 	= self.request.get('name').capitalize()
		code 	= self.request.get('code')
		
		# Handle exceptions for saving data to the datastore
		try:		
			if not plan_key:
				# Create a new Plan
				plan 	= Plan(	name= name, 
								code=code,
								parent=db.Key.from_path('Plan', 'default'))
				
			else:
				# Get the plan by its key
				plan 			= Plan.get(plan_key)
				
				plan.name 		= name
				plan.code		= code
			
			plan.put()
			return True
			
		except:
			return False
		
		
	def deletePlan(self, plan_key):
		'''
		Deletes an existing plan from the datastore and responses the 
		Ajax request.
		
		@param plan_key: it refers to the Plan that is going to be 
		deleted.
		'''
		# Get the plan by its key
		plan = Plan.get(plan_key)
		
		# Delete all its relations with courses
		for pcr in plan.pc_relations:
			pcr.delete()
		
		# Delete all its related workers
		for w in plan.workers:
			for wcr in w.wc_relations:
				wcr.delete()
			w.delete()
		
		# Delete plan
		plan.delete()

		self.response.out.write('OK')
		return


	def loadPlans(self, page, order):
		'''Loads n Customers at a time from the Datastore in order to have a 
		proper pagination index'''
		# Get all the plans
		plan_query = Plan.all()
		plan_query.ancestor(db.Key.from_path('Plan', 'default'))
		# If there are any plans...
		if plan_query.get():
			# Order depending on the chosen attribute
			if order:
				plan_query.order(order)
			else:
				plan_query.order('name')
			
			import math
			# Create the pagination elements
			current_page 	= int(page)
			plans_per_page 	= 10
			n_plans 		= plan_query.count()
			n_pages 		= int(math.ceil(float(n_plans) / plans_per_page))
			plans 			= plan_query.run(offset=current_page*plans_per_page-plans_per_page, limit=plans_per_page)

		else:
			n_pages 		= 0
			current_page 	= 1
			plans 			= None
		
		template_data = {
			'n_pages'	: n_pages,
			'p'			: current_page,
			'order'		: order,
			'plans'		: plans
		}
		
		return template_data
	
	
	def checkCode(self, plan_key, code):
		'''Checks if the country code already exists'''
		# Get all the plans
		plan_query = Plan.all()
		# Get the plans with the given code
		plan_query.filter('code =', code)
		
		# If a plan with that code already exists, notify the user, unless its
		# the actual plan code.
		if plan_query.get():
			# Check if the user is not changing the code so it remains the same
			if plan_key:
				# Get the country that is being edited
				plan_edited = Plan.get(plan_key)
				if plan_edited.code == code:
					self.response.out.write("OK")
					return
				
			self.response.out.write("El código ya existe. Introduzca otro nuevo.")

		else:
			self.response.out.write("OK")
	

app = webapp2.WSGIApplication([	('/plans', View),
								('/plans/save', Controller),
								('/plans/delete', Controller),
								('/plans/checkcode', Controller)],
								debug=True)