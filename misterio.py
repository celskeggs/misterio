import webapp2, os, cgi, datetime, sys, time, logging, json, urllib
from google.appengine.api import users
from google.appengine.ext import ndb

class DataBlock(ndb.Model):
	contents = ndb.BlobProperty(required=True)

class TestPage(webapp2.RequestHandler):
	def get(self):
		character = self.request.cookies.get('character', None)
		if character == None:
			return self.redirect("/select")
		with open("static/index.html", "r") as f:
			self.response.headers["Content-Type"] = "text/html"
			data = []
			while True:
				datum = f.read(8192)
				if not datum: break
				data.append(datum)
			self.response.write("".join(data))
class SelectPage(webapp2.RequestHandler):
	def get(self):
		character = self.request.cookies.get('character', None)
		if character != None:
			return self.redirect("/")
		cid = self.request.get("id", None)
		if cid != None:
			self.response.set_cookie("character", str(cid))
			return self.redirect("/")
		with open("static/select.html", "r") as f:
			self.response.headers["Content-Type"] = "text/html"
			data = []
			while True:
				datum = f.read(8192)
				if not datum: break
				data.append(datum)
			prefix, ifany, rep, nochars, postfix = ''.join(data).split("<? CHARACTERS ?>")
			chars = [(17, "arturo_d_b_a.png", "Sr. Loquacious Verylongname", "2015 Misterio Group 1")]
			prefix = prefix.replace("<? USERNAME ?>", cgi.escape(users.get_current_user().nickname()))
			if chars:
				data = prefix + ifany + "\n".join(rep.replace("<? CID ?>", str(cid)).replace("<? AVATAR ?>", urllib.quote_plus(avatar)).replace("<? NAME ?>", cgi.escape(name)).replace("<? SESSION ?>", cgi.escape(session)) for cid, avatar, name, session in chars) + postfix
			else:
				data = prefix + nochars + postfix
			self.response.write(data)
class LogoffPage(webapp2.RequestHandler):
	def get(self):
		self.response.delete_cookie("character")
		self.redirect(users.create_logout_url('/'))
class TestPage2(webapp2.RequestHandler):
	def get(self):
		self.response.headers["Content-Type"] = "text/plain"
		self.response.write("HELLO WORLD #2\n")

application = webapp2.WSGIApplication([
	('/logoff', LogoffPage),
	('/select', SelectPage),
	('/[a-z]*', TestPage),
	('/dynamic/', TestPage2),
])
