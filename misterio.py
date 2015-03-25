import webapp2, os, cgi, datetime, sys, time, logging, json, urllib, jinja2
from google.appengine.api import users
from google.appengine.ext import ndb

with open("avatar-list.txt", "r") as f:
	avatars = list(filter(None, (x.strip() for x in f.readlines())))
avatars.sort()

class Template(ndb.Model):
	name = ndb.StringProperty(required=True)
	message_sets = ndb.StringProperty(repeated=True)
class Character(ndb.Model):
	name = ndb.StringProperty(required=True)
	avatar = ndb.StringProperty(required=True)
class Message(ndb.Model):
	msid = ndb.StringProperty(indexed=True, required=True)
	cid = ndb.KeyProperty(indexed=True, required=False, kind=Character)
	title = ndb.StringProperty(indexed=False, required=True)
	body = ndb.TextProperty(indexed=False, required=True)

class Session(ndb.Model):
	name = ndb.StringProperty(required=True)
	activated = ndb.StringProperty(repeated=True)
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
JINJA_ENVIRONMENT.globals["len"] = len

def safe_unwrap_key(expected_path, unsafe):
	unsafe_key = ndb.Key(urlsafe=unsafe)
	if len(unsafe_key.pairs()) != len(expected_path):
		return None
	for kind_id, expected in zip(unsafe_key.pairs(), expected_path):
		if kind_id[0] != expected:
			return None
	return unsafe_key

class AdminPage(webapp2.RequestHandler):
	def safe_get_key(self, expected, field="key"):
		rawkey = self.request.get(field, "")
		if rawkey == "":
			self.display_error("Missing request parameter: key")
			return None
		unwrapped = safe_unwrap_key(expected.split("/"), rawkey)
		if unwrapped == None:
			self.display_error("Invalid key.")
			return None
		return unwrapped
	def get_reqs(self, *requests):
		return self.get_reqs_i(requests)
	def get_reqs_key(self, *requests):
		return self.get_reqs_i(requests[:-1], requests[-1])
	def get_reqs_i(self, requests, key=None):
		vals = [True]
		rescount = len(requests) + (1 if key != None else 0)
		for req in requests:
			value = self.request.get(req, "")
			if value == "":
				self.display_error("Missing request parameter: %s" % req)
				return [False] + [None] * rescount
			vals.append(value)
		if key != None:
			kv = self.safe_get_key(key)
			if kv == None:
				return [False] + [None] * rescount
			vals.append(kv)
		return vals
	def display_error(self, error):
		self.response.headers["Content-Type"] = "text/html"
		jt = JINJA_ENVIRONMENT.get_template('error.html')
		self.response.write(jt.render({"error": error}))
	def post(self, rel=""):
		if rel == "new_template":
			succ, name = self.get_reqs("name")
			if succ:
				key = Template(name=name).put()
				self.redirect("/administration/template?key=%s" % key.urlsafe())
		elif rel == "add_message_set":
			succ, name, key = self.get_reqs_key("name", "Template")
			if succ:
				templ = key.get()
				templ.message_sets.append(name)
				templ.put()
				self.redirect("/administration/template?key=%s#message-sets" % key.urlsafe())
		elif rel == "delete_message_set":
			succ, name, key = self.get_reqs_key("name", "Template")
			if succ:
				templ = key.get()
				if name in templ.message_sets:
					templ.message_sets.remove(name)
					templ.put()
					self.redirect("/administration/template?key=%s#message-sets" % key.urlsafe())
				else:
					self.display_error("The specified message set was not found.")
		elif rel == "add_global_message":
			succ, message_set, title, body, key = self.get_reqs_key("message-set", "title", "body", "Template")
			if succ:
				templ = key.get()
				if message_set not in templ.message_sets:
					return self.display_error("Specified message set does not exist.")
				msg = Message(parent=key, msid=message_set, cid=None, title=title, body=body)
				msg.put()
				self.redirect("/administration/template?key=%s#global-messages" % key.urlsafe())
		elif rel == "update_global_message":
			mode = self.request.get("mode", "")
			if mode == "":
				return self.display_error("Missing request parameter: mode")
			elif mode not in ("update", "delete"):
				return self.display_error("Invalid mode: must be update or delete.")
			key = self.safe_get_key("Template/Message")
			if key == None: return
			msg = key.get()
			if msg == None:
				return self.display_error("The target message does not exist.")
			if mode == "delete":
				key.delete()
				self.redirect("/administration/template?key=%s#global-messages" % key.parent().urlsafe())
			else:
				succ, message_set, title, body = self.get_reqs("message-set", "title", "body")
				if succ:
					msg.msid = message_set
					msg.title = title
					msg.body = body
					msg.put()
					self.redirect("/administration/template?key=%s#global-messages" % key.parent().urlsafe())
		elif rel == "new_character":
			succ, name, avatar, key = self.get_reqs_key("name", "avatar", "Template")
			if succ:
				nkey = Character(name=name, avatar=avatar, parent=key).put()
				self.redirect("/administration/character?key=%s" % nkey.urlsafe())
		else:
			self.response.headers["Content-Type"] = "text/plain"
			self.response.write("ADMIN: %s: %s" % (rel, self.request.params))
	def get(self, rel=""):
		if rel == "":
			self.response.headers["Content-Type"] = "text/html"
			jt = JINJA_ENVIRONMENT.get_template('root.html')

			templates = Template.query().fetch()

			self.response.write(jt.render({"templates": templates}))
		elif rel == "template":
			self.response.headers["Content-Type"] = "text/html"
			jt = JINJA_ENVIRONMENT.get_template('template.html')

			key = self.safe_get_key("Template")
			if key != None:
				template = key.get()
				global_messages = Message.query(Message.cid == None, ancestor=key).fetch()
				characters = Character.query(ancestor=key).fetch()
				if template == None:
					self.display_error("The template that you are trying to view either does not exist or has been deleted.")
				else:
					self.response.write(jt.render({"template": template, "global_messages": global_messages, "characters": characters, "avatars": avatars}))
		else:
			self.response.headers["Content-Type"] = "text/plain"
			self.response.write("ADMIN: %s" % rel)

administration = webapp2.WSGIApplication([
	('/administration', AdminPage),
	('/administration/(.*)', AdminPage),
])

