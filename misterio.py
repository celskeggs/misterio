import webapp2, os, cgi, datetime, sys, time, logging, json
from google.appengine.api import users
from google.appengine.ext import ndb

class DataBlock(ndb.Model):
	contents = ndb.BlobProperty(required=True)

class TestPage(webapp2.RequestHandler):
	def get(self):
		with open("static/select.html", "r") as f:
			self.response.headers["Content-Type"] = "text/html"
			while True:
				data = f.read(8192)
				if not data: break
				self.response.write(data)
class TestPage2(webapp2.RequestHandler):
	def get(self):
		self.response.headers["Content-Type"] = "text/plain"
		self.response.write("HELLO WORLD #2\n")

application = webapp2.WSGIApplication([
	('/[a-z]*', TestPage),
	('/dynamic/', TestPage2),
])
