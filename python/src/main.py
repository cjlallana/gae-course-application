# -*- encoding: utf-8 -*-
'''
Created on 03/04/2013

@author: Carlos Lallana
'''

import webapp2
import jinja2
import os
from google.appengine.api import users

# Initialize Jinja2
jinja_environment = jinja2.Environment(
					loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
		
config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': 'ole',
}


class MainPage(webapp2.RequestHandler):
	
	def get(self):
		'''Handles GET requests'''
		
		user = users.get_current_user()
		
		if user:
			google_link = users.create_logout_url('/')
			str_link	= u'Cerrar sesión'
		else:
			google_link = users.create_login_url('/')
			str_link	= u'Iniciar sesión'
		
		
		info_tag 	= ''
		error 		= self.request.get('e')
		
		if error == '1':
			info_tag = u'La dirección de email no corresponde a ningún super admin'
		elif error == '2':
			info_tag = u'La dirección de email no corresponde a ningún admin local'
		elif error == '3':
			info_tag = u'La dirección de email no corresponde a ningún empleado'
		
		template_data = {
			'google_link'	: google_link,
			'str_link'		: str_link,
			'info_tag'		: info_tag,
			'user'			: user
		}
		
		template = jinja_environment.get_template('templates/welcome.html')
		self.response.out.write(template.render(template_data))
		

app = webapp2.WSGIApplication([	('/', MainPage)],
								debug=True)