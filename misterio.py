import webapp2, os, cgi, datetime, sys, time, logging, json, urllib, jinja2
from google.appengine.api import users
from google.appengine.ext import ndb

class Template(ndb.Model):
	name = ndb.StringProperty(required=True)
class MessageSet(ndb.Model):
	tag = ndb.StringProperty(required=True)
class Character(ndb.Model):
	name = ndb.StringProperty(required=True)
	avatar = ndb.StringProperty(required=True)
class Message(ndb.Model):
	msid = ndb.KeyProperty(required=True, kind=MessageSet)
	cid = ndb.KeyProperty(required=True, kind=Character)
	title = ndb.StringProperty(required=True)
	body = ndb.TextProperty(required=True)

class Session(ndb.Model):
	name = ndb.StringProperty(required=True)
	activated = ndb.KeyProperty(repeated=True, kind=MessageSet)
class Assignment(ndb.Model):
	cid = ndb.KeyProperty(required=True, kind=Character)
	player = ndb.UserProperty(required=True)
class Post(ndb.Model):
	cid = ndb.KeyProperty(required=True, kind=Character)
	target = ndb.KeyProperty(kind=Character)
	msg = ndb.TextProperty(required=True, indexed=False)

class MainPage(webapp2.RequestHandler):
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
class DynamicPage(webapp2.RequestHandler):
	def get(self, dynamic_id):
		self.response.headers["Content-Type"] = "application/json"
		if dynamic_id == "users":
			o = {"me": 17, "session": "2015 Misterio Group 1", "access": False, "users": [{"cid": 17, "avatar": "arturo_d_b_a.png", "name": "Sra. Remota Fletched"}]}
		else:
			return self.abort(404)
		self.response.write(json.dumps(o))

application = webapp2.WSGIApplication([
	('/logoff', LogoffPage),
	('/select', SelectPage),
	('/[a-z]*', MainPage),
	('/dynamic/([a-z]+)', DynamicPage),
])

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), "static_admin")),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class AdminPage(webapp2.RequestHandler):
	def get(self, rel=""):
		if rel == "":
			self.response.headers["Content-Type"] = "text/html"
			with open("static/admin/root.html", "r") as f:
				data = []
				while True:
					datum = f.read(8192)
					if not datum: break
					data.append(datum)
				data = "".join(data)
				self.response.write(data)
		else:
			self.response.headers["Content-Type"] = "text/plain"
			self.response.write("ADMIN WOAH: %s" % rel)

administration = webapp2.WSGIApplication([
	('/administration', AdminPage),
	('/administration/(.*)', AdminPage),
])
