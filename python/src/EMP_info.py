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

# Initialize Jinja2
jinja_environment = jinja2.Environment(
					loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		
config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': 'ole',
}


class Info(session.BaseHandler):
	
	def get(self):
		'''
		Handles GET requests
		'''
		from models import Worker
		# Get the actual worker/employer
		worker = Worker.get(self.session['worker_key'])
		
		template_data = {
			'worker': worker,
			'url_logout': users.create_logout_url('/')
		}
		
		page = self.request.get('p')
		
		if page == 'intro':
			template = jinja_environment.get_template('templates/EMP_intro.html')
			self.response.out.write(template.render(template_data))
			
		if page == 'goal':
			template = jinja_environment.get_template('templates/EMP_goal.html')
			self.response.out.write(template.render(template_data))
			
		if page == 'structure':
			template = jinja_environment.get_template('templates/EMP_structure.html')
			self.response.out.write(template.render(template_data))



app = webapp2.WSGIApplication([	('/employer/info', Info)],
								config=config,
								debug=True)