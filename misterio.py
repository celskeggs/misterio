import webapp2, os, cgi, datetime, sys, time, logging, json, urllib, jinja2
from google.appengine.api import users
from google.appengine.ext import ndb

with open("avatar-list.txt", "r") as f:
	avatars = list(filter(None, (x.strip() for x in f.readlines())))
avatars.sort()

# TODO: some way to get a report on what hasn't been responded to

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
JINJA_ENVIRONMENT.globals["len"] = len

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
	date = ndb.DateTimeProperty(required=True, auto_now_add=True)
	msg = ndb.TextProperty(required=True, indexed=False)
	needs_reply = ndb.BooleanProperty(required=False)
	response_to = ndb.KeyProperty(required=False, kind="Post")

class VerifyingHandler(webapp2.RequestHandler):
	def get_and_verify_character(self, char=None): # returns (character, session)
		email = users.get_current_user().email()
		if char == None:
			char = self.request.cookies.get("character", None)
		if char == None:
			self.redirect("/select")
			return None, None
		if ":" not in char:
			self.response.delete_cookie("character")
			self.redirect("/select")
			return None, None
		cid, sid = char.split(":", 2)
		if not (cid.isdigit() and sid.isdigit()):
			self.response.delete_cookie("character")
			self.redirect("/select")
			return None, None
		cid, sid = int(cid), int(sid)
		session = ndb.Key(Session, sid).get()
		if session == None:
			self.response.delete_cookie("character")
			self.redirect("/select")
			return None, None
		character = Character.get_by_id(cid, parent=session.template)
		if character == None:
			self.response.delete_cookie("character")
			self.redirect("/select")
			return None, None
		return character, session

class MainPage(VerifyingHandler):
	def get(self):
		character, session = self.get_and_verify_character()
		if character == None:
			return
		with open("static/index.html", "r") as f:
			self.response.headers["Content-Type"] = "text/html"
			data = []
			while True:
				datum = f.read(8192)
				if not datum: break
				data.append(datum)
			self.response.write("".join(data))
class SelectPage(VerifyingHandler):
	def get(self):
		character = self.request.cookies.get('character', None)
		if character != None:
			return self.redirect("/")
		csid = self.request.get("csid", None)
		if csid != None:
			if self.get_and_verify_character(csid) == None:
				return
			else:
				self.response.set_cookie("character", csid)
				return self.redirect("/")
		self.response.headers["Content-Type"] = "text/html"
		jt = JINJA_ENVIRONMENT.get_template('select.html')

		email = users.get_current_user().email()
		sessions = Session.query(Session.assignments.player_email == email).fetch()
		charids = set()
		characters = []
		for session in sessions:
			for assignment in session.assignments:
				if assignment.player_email == email:
					characters.append((assignment.cid, session))
					charids.add(assignment.cid)
		charmap = dict((char.key, char) for char in ndb.get_multi(charids))
		characters = [(charmap[key], session) for key, session in characters]

		self.response.write(jt.render({"username": users.get_current_user().nickname(), "characters": characters, "admin": users.is_current_user_admin()}))
class LogoffPage(webapp2.RequestHandler):
	def get(self):
		self.response.delete_cookie("character")
		if self.request.get("mode", "") == "partial":
			self.redirect("/select")
		else:
			self.redirect(users.create_logout_url('/'))
def get_js_timestamp(x):
	return int(1000 * time.mktime(x.timetuple()))
class DynamicPage(VerifyingHandler):
	def build_post_obj(self, post):
		return {"id": post.key.id(), "data": post.msg, "from": post.cid.id(), "prev": post.response_to and post.response_to.id(), "date": get_js_timestamp(post.date), "to": post.target and post.target.id(), "expect": post.needs_reply}
	def post(self, dynamic_id):
		character, session = self.get_and_verify_character()
		if character == None:
			return
		if dynamic_id == "new-post":
			jo = json.loads(self.request.body)
			if type(jo) != dict:
				return self.abort(400)
			to, prev, data, expect = jo.get("to", None), jo.get("prev", None), jo.get("data", None), jo.get("expect", None)
			print "GOT JSON", jo, type(to), type(prev), type(data), type(expect)
			if not ((type(to) == int or to == None) and (type(prev) == int or prev == None) and (type(data) == str or type(data) == unicode) and type(expect) == bool):
				return self.abort(400)
			if to != None:
				to = Character.get_by_id(to, parent=session.template)
				if to == None: # character is gone
					return self.abort(400)
				to = to.key
			elif expect:
				return self.abort(400) # can't be both expecting a response and not having a target
			if prev != None:
				prev = Post.get_by_id(prev, parent=session.key)
				if prev == None: # post is gone
					return self.abort(400)
				if prev.needs_reply and prev.target == character.key:
					prev.needs_reply = False
					prev.put()
				prev = prev.key
			post = Post(cid=character.key, target=to, msg=data, needs_reply=expect or None, response_to=prev, parent=session.key)
			pkey = post.put()
			o = {"id": pkey.id(), "date": get_js_timestamp(post.date)}
		else:
			return self.abort(404)
		self.response.headers["Content-Type"] = "application/json"
		self.response.write(json.dumps(o))
	def get(self, dynamic_id):
		# TODO: inbox, profile
		character, session = self.get_and_verify_character()
		if character == None:
			return
		if dynamic_id == "users":
			chars = Character.query(ancestor=session.template)
			chard = []
			for char in chars:
				chard.append({"cid": char.key.id(), "avatar": char.avatar, "name": char.name, "session": session.name})
			o = {"me": character.key.id(), "session": session.name, "users": chard}
		elif dynamic_id == "get-post":
			mid = self.request.get("id", None)
			if mid == None or not mid.isdigit():
				return self.abort(400)
			post = Post.get_by_id(int(mid), parent=session.key)
			if post == None:
				return self.abort(404) # gone
			o = self.build_post_obj(post)
		elif dynamic_id == "inbox-count":
			o = {"inbox": 0, "msgs": 0} # TODO: do this properly
		elif dynamic_id == "feed":
			limit = self.request.get("limit", "10")
			if not limit.isdigit():
				return self.abort(400)
			limit = max(1, min(int(limit), 20))

			begin = self.request.get("begin", None)
			if begin != None:
				begin = Cursor(urlsafe=begin)

			direction = self.request.get("direction", "forward")
			reverse = direction == "reverse"

			q = Post.query(ancestor=session.key).order((Post.date) if reverse else (-Post.date))
			posts, cursor, more = q.fetch_page(limit, start_cursor=(begin.reversed() if reverse else begin))
			o = {"posts": [self.build_post_obj(post) for post in posts], "next": (cursor.reversed().urlsafe() if reverse else cursor.urlsafe()) if more else None}
		else:
			return self.abort(404)
		self.response.headers["Content-Type"] = "application/json"
		self.response.write(json.dumps(o))

application = webapp2.WSGIApplication([
	('/logoff', LogoffPage),
	('/select', SelectPage),
	('/dynamic/([-a-z]+)', DynamicPage),
	('/[a-z0-9/]*', MainPage),
])

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
		jt = JINJA_ENVIRONMENT.get_template('static_admin/error.html')
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
			jt = JINJA_ENVIRONMENT.get_template('static_admin/root.html')

			templates = Template.query().fetch()
			sessions = Session.query().fetch()

			self.response.write(jt.render({"templates": templates, "sessions": sessions}))
		elif rel == "template":
			self.response.headers["Content-Type"] = "text/html"
			jt = JINJA_ENVIRONMENT.get_template('static_admin/template.html')

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
			jt = JINJA_ENVIRONMENT.get_template('static_admin/session.html')

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
			jt = JINJA_ENVIRONMENT.get_template('static_admin/posts.html')

			key = self.safe_get_key("Session")
			if key != None:
				session = key.get()
				if session == None:
					return self.display_error("The session that you are trying to view either does not exist or has been deleted.")
				limit = 10
				posts = Post.query(ancestor=session.key).order(Post.date).fetch(limit)
				charids = list(set(post.cid for post in posts).union(set(post.target for post in posts if post.target != None)))
				chars = ndb.get_multi(charids)
				avatarmap = dict((char.key, char.avatar) for char in chars)
				namemap = dict((char.key, char.name) for char in chars)
				self.response.write(jt.render({"session": session, "posts": posts, "limit": limit, "avatars": avatarmap, "names": namemap}))
		elif rel == "character":
			self.response.headers["Content-Type"] = "text/html"
			jt = JINJA_ENVIRONMENT.get_template('static_admin/character.html')

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
			jt = JINJA_ENVIRONMENT.get_template('static_admin/prepare_delete.html')

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
			jt = JINJA_ENVIRONMENT.get_template('static_admin/prepare_delete.html')

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

