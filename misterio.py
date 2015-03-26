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
	title = ndb.StringProperty(indexed=False, required=True)
	body = ndb.TextProperty(indexed=False, required=True)
	charspec = ndb.ComputedProperty(lambda self: self.key.parent().kind() == "Character")

class Assignment(ndb.Model): # not stored in database - stored in Session entity.
	cid = ndb.KeyProperty(required=True, kind=Character)
	player_email = ndb.StringProperty(indexed=True, required=True)
class Session(ndb.Model):
	template = ndb.KeyProperty(required=True, kind=Template)
	name = ndb.StringProperty(required=True)
	activated = ndb.StringProperty(repeated=True)
	assignments = ndb.StructuredProperty(Assignment, repeated=True)
class Post(ndb.Model):
	cid = ndb.KeyProperty(required=True, kind=Character)
	target = ndb.KeyProperty(required=False, kind=Character)
	msg = ndb.TextProperty(required=True, indexed=False)
	needs_reply = ndb.BooleanProperty(required=True)

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
		# Template-related calls
		if rel == "new_template":
			succ, name = self.get_reqs("name")
			if succ:
				key = Template(name=name).put()
				self.redirect("/administration/template?key=%s" % key.urlsafe())
		elif rel == "set_template_name":
			succ, name, key = self.get_reqs_key("name", "Template")
			if succ:
				templ = key.get()
				templ.name = name
				templ.put()
				self.redirect("/administration/template?key=%s" % key.urlsafe())
		elif rel == "duplicate_template":
			succ, name, key = self.get_reqs_key("name", "Template")
			if succ:
				oldtemplate = key.get()
				oldchars = Character.query(ancestor=key).fetch()
				oldmsgs = Message.query(ancestor=key).fetch()
				newkey = Template(name=name, message_sets=oldtemplate.message_sets).put()
				for char in oldchars:
					newchar = Character(name=char.name, avatar=char.avatar, parent=newkey).put()
					for oldm in oldmsgs:
						if oldm.key.parent() == char.key:
							Message(msid=oldm.msid, title=oldm.title, body=oldm.body, parent=newchar).put()
				for oldm in oldmsgs:
					if oldm.key.parent() == key:
						Message(msid=oldm.msid, title=oldm.title, body=oldm.body, parent=newkey).put()
				self.redirect("/administration/template?key=%s#properties" % newkey.urlsafe())
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
				if templ == None:
					return self.display_error("Specified template does not exist.")
				if message_set not in templ.message_sets:
					return self.display_error("Specified message set does not exist.")
				msg = Message(parent=key, msid=message_set, title=title, body=body)
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
		elif rel == "add_character_message":
			succ, message_set, title, body, key = self.get_reqs_key("message-set", "title", "body", "Template/Character")
			if succ:
				char = key.get()
				if char == None:
					return self.display_error("Specified character does not exist.")
				templ = key.parent().get()
				if templ == None:
					return self.display_error("Specified template does not exist.")
				if message_set not in templ.message_sets:
					return self.display_error("Specified message set does not exist.")
				msg = Message(parent=key, msid=message_set, title=title, body=body)
				msg.put()
				self.redirect("/administration/character?key=%s#global-messages" % key.urlsafe())
		elif rel == "update_character_message":
			mode = self.request.get("mode", "")
			if mode == "":
				return self.display_error("Missing request parameter: mode")
			elif mode not in ("update", "delete"):
				return self.display_error("Invalid mode: must be update or delete.")
			key = self.safe_get_key("Template/Character/Message")
			if key == None: return
			msg = key.get()
			if msg == None:
				return self.display_error("The target message does not exist.")
			if mode == "delete":
				key.delete()
				self.redirect("/administration/character?key=%s#global-messages" % key.parent().urlsafe())
			else:
				succ, message_set, title, body = self.get_reqs("message-set", "title", "body")
				if succ:
					msg.msid = message_set
					msg.title = title
					msg.body = body
					msg.put()
					self.redirect("/administration/character?key=%s#global-messages" % key.parent().urlsafe())
		elif rel == "set_character_name":
			succ, name, key = self.get_reqs_key("name", "Template/Character")
			if succ:
				char = key.get()
				char.name = name
				char.put()
				self.redirect("/administration/character?key=%s#properties" % key.urlsafe())
		elif rel == "set_character_avatar":
			succ, avatar, key = self.get_reqs_key("avatar", "Template/Character")
			if succ:
				char = key.get()
				char.avatar = avatar
				char.put()
				self.redirect("/administration/character?key=%s#properties" % key.urlsafe())
		elif rel == "duplicate_character":
			succ, name, key = self.get_reqs_key("name", "Template/Character")
			if succ:
				old = key.get()
				oldmsgs = Message.query(ancestor=key).fetch()
				newkey = Character(name=name, avatar=old.avatar, parent=key.parent()).put()
				for oldm in oldmsgs:
					Message(msid=oldm.msid, title=oldm.title, body=oldm.body, parent=newkey).put()
				self.redirect("/administration/character?key=%s#properties" % newkey.urlsafe())
		elif rel == "delete_character":
			succ, key = self.get_reqs_key("Template/Character")
			if succ:
				oldkeys = Message.query(ancestor=key).fetch(keys_only=True)
				for mkey in oldkeys:
					mkey.delete()
				key.delete()
				self.redirect("/administration/template?key=%s#characters" % key.parent().urlsafe())
		elif rel == "delete_template":
			succ, key = self.get_reqs_key("Template")
			if succ:
				if Session.query(Session.template == key).get(keys_only=True) != None:
					return self.display_error("Sessions still exist that use this template! Convert them to use different Templates before you can delete this one.")
				oldmsgs = Message.query(ancestor=key).fetch(keys_only=True)
				for mkey in oldmsgs:
					mkey.delete()
				oldchars = Character.query(ancestor=key).fetch(keys_only=True)
				for ckey in oldchars:
					ckey.delete()
				key.delete()
				self.redirect("/administration")
		# Session-related calls
		elif rel == "new_session":
			succ, name, key = self.get_reqs_key("name", "Template")
			if succ:
				template = key.get()
				if template == None:
					return self.display_error("The template that you are trying to use either does not exist or has been deleted.")
				session = Session(template=key, name=name, activated=[], assignments=[]).put()
				self.redirect("/administration/session?key=%s" % session.urlsafe())
		elif rel == "set_session_name":
			succ, name, key = self.get_reqs_key("name", "Session")
			if succ:
				session = key.get()
				session.name = name
				session.put()
				self.redirect("/administration/session?key=%s" % key.urlsafe())
		elif rel == "toggle_message_set":
			succ, name, key = self.get_reqs_key("name", "Session")
			if succ:
				session = key.get()
				if name in session.activated:
					session.activated.remove(name)
				else:
					session.activated.append(name)
				session.put()
				self.redirect("/administration/session?key=%s#message-sets" % key.urlsafe())
		elif rel == "assign_character":
			succ, key = self.get_reqs_key("Session")
			charid = self.safe_get_key("Template/Character", "charid")
			email = self.request.get("email", None)
			if succ and charid != None:
				session = key.get()
				toremove = []
				for assignment in session.assignments:
					if assignment.cid.get() == None or assignment.cid == charid:
						toremove.append(assignment)
				for target in toremove:
					session.assignments.remove(target)
				if email != None and email != "":
					session.assignments.append(Assignment(cid=charid, player_email=email))
				session.put()
				self.redirect("/administration/session?key=%s#characters" % key.urlsafe())
		else:
			self.response.headers["Content-Type"] = "text/plain"
			self.response.write("ADMIN: %s: %s" % (rel, self.request.params))
	def get(self, rel=""):
		if rel == "":
			self.response.headers["Content-Type"] = "text/html"
			jt = JINJA_ENVIRONMENT.get_template('root.html')

			templates = Template.query().fetch()
			sessions = Session.query().fetch()

			self.response.write(jt.render({"templates": templates, "sessions": sessions}))
		elif rel == "template":
			self.response.headers["Content-Type"] = "text/html"
			jt = JINJA_ENVIRONMENT.get_template('template.html')

			key = self.safe_get_key("Template")
			if key != None:
				template = key.get()
				global_messages = Message.query(Message.charspec == False, ancestor=key).fetch()
				characters = Character.query(ancestor=key).fetch()
				if template == None:
					self.display_error("The template that you are trying to view either does not exist or has been deleted.")
				else:
					self.response.write(jt.render({"template": template, "global_messages": global_messages, "characters": characters, "avatars": avatars}))
		elif rel == "session":
			self.response.headers["Content-Type"] = "text/html"
			jt = JINJA_ENVIRONMENT.get_template('session.html')

			key = self.safe_get_key("Session")
			if key != None:
				session = key.get()
				if session == None:
					return self.display_error("The session that you are trying to view either does not exist or has been deleted.")
				template = session.template.get()
				template_names = Template.query(projection=[Template.name]).fetch()
				characters = Character.query(ancestor=session.template).fetch()
				if template == None:
					self.display_error("The template of the session that you are trying to view either does not exist or has been deleted.")
				else:
					template_names = [templ.name for templ in template_names]
					assignment_map = dict((assignment.cid, assignment.player_email) for assignment in session.assignments)
					self.response.write(jt.render({"session": session, "template": template, "characters": characters, "assignment_map": assignment_map, "template_names": template_names}))
		elif rel == "posts":
			self.response.headers["Content-Type"] = "text/html"
			jt = JINJA_ENVIRONMENT.get_template('posts.html')

			key = self.safe_get_key("Session")
			if key != None:
				session = key.get()
				if session == None:
					return self.display_error("The session that you are trying to view either does not exist or has been deleted.")
				limit = 10
				posts = Post.query().fetch(limit)
				charids = list(set(post.cid for post in posts).union(set(post.target for post in posts if post.target != None)))
				chars = ndb.get_multi(charids)
				avatarmap = dict((char.key, char.avatar) for char in chars)
				namemap = dict((char.key, char.name) for char in chars)
				self.response.write(jt.render({"session": session, "posts": posts, "limit": limit, "avatars": avatarmap, "names": namemap}))
		elif rel == "character":
			self.response.headers["Content-Type"] = "text/html"
			jt = JINJA_ENVIRONMENT.get_template('character.html')

			key = self.safe_get_key("Template/Character")
			if key != None:
				character = key.get()
				template = key.parent().get()
				if character == None:
					self.display_error("The character that you are trying to view either does not exist or has been deleted.")
				elif template == None:
					self.display_error("The template of the character that you are trying to view either does not exist or has been deleted.")
				else:
					character_messages = Message.query(ancestor=key).fetch()
					self.response.write(jt.render({"template": template, "character": character, "character_messages": character_messages, "avatars": avatars}))
		elif rel == "prepare_delete_character":
			self.response.headers["Content-Type"] = "text/html"
			jt = JINJA_ENVIRONMENT.get_template('prepare_delete.html')

			key = self.safe_get_key("Template/Character")
			if key != None:
				character = key.get()
				template = key.parent().get()
				if character == None:
					self.display_error("The character that you are trying to delete either does not exist or has been deleted.")
				elif template == None:
					self.display_error("The template of the character that you are trying to delete either does not exist or has been deleted.")
				else:
					self.response.write(jt.render({"target": character, "warning": "You are attempting to delete a character and ALL ATTACHED MESSAGES!", "type": "character", "keep": "/administration/character?key=%s" % key.urlsafe(), "destroy": "/administration/delete_character"}))
		elif rel == "prepare_delete_template":
			self.response.headers["Content-Type"] = "text/html"
			jt = JINJA_ENVIRONMENT.get_template('prepare_delete.html')

			key = self.safe_get_key("Template")
			if key != None:
				if Session.query(Session.template == key).get(keys_only=True) != None:
					return self.display_error("Sessions still exist that use this template! Convert them to use different Templates before you can delete this one.")
				template = key.get()
				if template == None:
					self.display_error("The template that you are trying to delete either does not exist or has been deleted.")
				else:
					self.response.write(jt.render({"target": template, "warning": "You are attempting to delete a template and ALL ATTACHED CHARACTERS and ALL ATTACHED MESSAGES!", "type": "template", "keep": "/administration/template?key=%s" % key.urlsafe(), "destroy": "/administration/delete_template"}))
		else:
			self.response.headers["Content-Type"] = "text/plain"
			self.response.write("ADMIN: %s" % rel)

administration = webapp2.WSGIApplication([
	('/administration', AdminPage),
	('/administration/(.*)', AdminPage),
])

