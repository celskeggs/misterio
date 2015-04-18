import webapp2, os, cgi, datetime, sys, time, logging, json, urllib, jinja2, random
from google.appengine.api import users, memcache
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

def is_user_admin():
	user = users.get_current_user()
	if not user:
		return False
	return users.is_current_user_admin() or Administrator.get_by_id(user.email()) != None

def notify_update(key, realm):
	return memcache.incr("%s/%d" % (realm, key.id()), initial_value=random.randint(0, 100000000))
def get_update_value(key, realm):
	out = memcache.get("%s/%d" % (realm, key.id()))
	if out != None:
		return out
	out = notify_update(key, realm)
	if out != None:
		return out
	logging.error("could not make a %s!" % realm)
	return -1
def notify_update_template(template_key):
	return notify_update(template_key, "TUN")
def get_template_update_value(template_key):
	return get_update_value(template_key, "TUN")
def notify_update_posts(session_key, update_time): # time is a JS timestamp
	# last post update time
	memcache.set("LPUT/%d" % session_key.id(), update_time)
	return notify_update(session_key, "PUN")
def post_updated_since(session_key, since): # since is a JS timestamp
	tm = memcache.get("LPUT/%d" % session_key.id())
	return tm == None or tm >= since, tm
def get_post_update_value(session_key):
	return get_update_value(session_key, "PUN")
def notify_update_session(session_key):
	return notify_update(session_key, "SUN")
def get_session_update_value(session_key):
	return get_update_value(session_key, "SUN")
def get_session_or_template_update_value(session):
	return "%d&%d" % (get_session_update_value(session.key), get_template_update_value(session.template))
def unwrap_for_update(data, pun_actual):
	if data == None:
		return None
	pun_value, data = data.split("$", 1)
	if pun_value == str(pun_actual):
		return data
	else:
		return None
def wrap_for_update(data, pun_actual):
	if data == None:
		return None
	return "%s$%s" % (pun_actual, data)
def dump_message(message):
	return {"message_set": message.msid, "title": message.title, "body": message.body}
def dump_character(character, messages):
	enc_msgs = [dump_message(msg) for msg in messages if msg.key.parent() == character.key]
	return {"name": character.name, "avatar": character.avatar, "messages": enc_msgs}
def dump_template(template):
	chars = Character.query(ancestor=template.key).fetch()
	messages = Message.query(ancestor=template.key).fetch()
	enc_chars = [dump_character(char, messages) for char in chars]
	enc_global_msgs = [dump_message(msg) for msg in messages if msg.key.parent() == template.key]
	return json.dumps({"name": template.name, "message_sets": template.message_sets, "characters": enc_chars, "global_messages": enc_global_msgs})
def load_template(string):
	try:
		loaded = json.loads(string)
	except ValueError, e:
		return "Failed to decode JSON: %s" % e
	err = verify_template(loaded)
	if err:
		return err
	return load_template_real(loaded)
def verify_type(dicti, key, typ, *args):
	value = dicti.get(key, None)
	if type(typ) == type:
		if type(value) != typ and not (type(value) == unicode and typ == str):
			return "Bad type of field %s: %s instead of %s" % (key, type(value), typ)
	elif type(value) != list:
		return "Bad type of field %s: %s instead of %s" % (key, type(value), list)
	else:
		for elem in value:
			err = typ(elem, *args)
			if err:
				return err
def verify_template(template):
	return verify_type(template, "name", str) or verify_type(template, "message_sets", verify_message_set) or verify_type(template, "characters", verify_character, template["message_sets"]) or verify_type(template, "global_messages", verify_message, template["message_sets"])
def verify_message_set(message_set):
	if type(message_set) not in (str, unicode):
		return "Expected string for message set"
def load_template_real(template):
	tkey = Template(name=template["name"], message_sets=template["message_sets"]).put()
	for char in template["characters"]:
		load_character(char, tkey)
	for msg in template["global_messages"]:
		load_message(msg, tkey)
	return tkey
def verify_character(character, message_sets):
	return verify_type(character, "name", str) or verify_type(character, "avatar", str) or verify_type(character, "messages", verify_message, message_sets)
def load_character(character, tkey):
	ckey = Character(name=character["name"], avatar=character["avatar"], parent=tkey).put()
	for msg in character["messages"]:
		load_message(msg, ckey)
def verify_message(message, message_sets):
	err = verify_type(message, "message_set", str) or verify_type(message, "title", str) or verify_type(message, "body", str)
	if err == None and message["message_set"] not in message_sets:
		err = "Invalid message set (not in defined list): %s" % message["message_set"]
	return err
def load_message(message, pkey):
	Message(msid=message["message_set"], title=message["title"], body=message["body"], parent=pkey).put()

class Administrator(ndb.Model): # key is email
	name = ndb.StringProperty(required=True, indexed=False)
	added = ndb.DateTimeProperty(required=True, auto_now_add=True)

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

LOAD_TESTING_TOKEN, LT_SESS, LT_CHAR = None, 5720147234914304, 5066549580791808

class VerifyingHandler(webapp2.RequestHandler):
	def get_and_verify_character(self, char=None): # returns (character, session)
		if LOAD_TESTING_TOKEN != None and self.request.headers.get("X-Bypass-Token", None) == LOAD_TESTING_TOKEN:
			session = Session.get_by_id(LT_SESS)
			if session == None: return None, None
			character = Character.get_by_id(LT_CHAR, parent=session.template)
			if character == None: return None, None
			return character, session
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
		cid, sid = char.split(":", 1)
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
		found = False
		for assignment in session.assignments:
			if assignment.cid.id() == cid and assignment.player_email == email:
				found = True
		if not found:
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

		self.response.write(jt.render({"username": users.get_current_user().nickname(), "characters": characters, "admin": is_user_admin()}))
class LogoffPage(webapp2.RequestHandler):
	def get(self):
		self.response.delete_cookie("character")
		if self.request.get("mode", "") == "partial":
			self.redirect("/select")
		else:
			self.redirect(users.create_logout_url('/'))
def get_js_timestamp(x):
	return int(1000 * time.mktime(x.timetuple()) + x.microsecond / 1000)
class DynamicPage(VerifyingHandler):
	def build_post_obj(self, post, include_prev=False):
		out = {"id": post.key.id(), "data": post.msg, "from": post.cid.id(), "prev": post.response_to and post.response_to.id(), "date": get_js_timestamp(post.date), "to": post.target and post.target.id(), "expect": post.needs_reply}
		if include_prev:
			if post.response_to:
				out["prevobj"] = self.build_post_obj(post.response_to.get(), include_prev=False)
			else:
				out["prevobj"] = None
		return out
	def post(self, dynamic_id):
		character, session = self.get_and_verify_character()
		if character == None:
			return
		if dynamic_id == "new-post":
			jo = json.loads(self.request.body)
			if type(jo) != dict:
				logging.info('client provided a non-object over JSON!')
				return self.abort(400)
			to, prev, data, expect = jo.get("to", None), jo.get("prev", None), jo.get("data", None), jo.get("expect", None)
			if not ((type(to) == int or type(to) == long or to == None) and (type(prev) == int or type(prev) == long or prev == None) and (type(data) == str or type(data) == unicode) and type(expect) == bool):
				logging.info('client provided bad data: %s/%s/%s/%s!' % (type(to), type(prev), type(data), type(expect)))
				return self.abort(400)
			if to != None:
				to = Character.get_by_id(to, parent=session.template)
				if to == None: # character is gone
					logging.info('client tried to access a character that doesn\'t exist!')
					return self.abort(400)
				to = to.key
			elif expect:
				logging.info('client expected a response but had no target!')
				return self.abort(400) # can't be both expecting a response and not having a target
			if prev != None:
				prev = Post.get_by_id(prev, parent=session.key)
				if prev == None: # post is gone
					logging.info('client tried to access a post that doesn\'t exist!')
					return self.abort(400)
				if prev.needs_reply and prev.target == character.key:
					prev.needs_reply = False
					prev.put()
					# invalidation for inbox check below
					memcache.delete("IBQ/%d/%d" % (character.key.id(), session.key.id()))
				prev = prev.key
			post = Post(cid=character.key, target=to, msg=data, needs_reply=expect or None, response_to=prev, parent=session.key)
			pkey = post.put()
			notify_update_posts(session.key, get_js_timestamp(post.date))
			if to != None:
				# invalidation for inbox check below
				memcache.delete("IBQ/%d/%d" % (to.id(), session.key.id()))
			o = {"id": pkey.id(), "date": get_js_timestamp(post.date)}
		else:
			return self.abort(404)
		self.response.headers["Content-Type"] = "application/json"
		self.response.write(json.dumps(o))
	def get_inbox_query(self, character_key, session_key):
		return Post.query(Post.target == character_key, Post.needs_reply == True, ancestor=session_key)
	def get(self, dynamic_id):
		character, session = self.get_and_verify_character()
		if character == None:
			return
		if dynamic_id == "users":
			tun_value = get_template_update_value(session.template)

			mcid = "USR/%d" % session.template.id()
			chardo = memcache.get(mcid)
			chard = unwrap_for_update(chardo, tun_value)
			if chard == None:
				logging.debug("missed users cache (%s)" % chardo)
				chars = Character.query(ancestor=session.template)
				chard = []
				for char in chars:
					chard.append({"cid": char.key.id(), "avatar": char.avatar, "name": char.name, "session": session.name})
				memcache.set(mcid, wrap_for_update(json.dumps(chard), tun_value))
			else:
				chard = json.loads(chard)
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
			rsince = self.request.get("since", None)
			if rsince == None or not rsince.isdigit():
				return self.abort(400)
			since = int(rsince) / 1000.0

			pun_value = get_post_update_value(session.key)
			recent_update, recent_update_time = post_updated_since(session.key, int(rsince))

			# invalidated above in special cases
			mcid = "IBQ/%d/%d" % (character.key.id(), session.key.id())
			qc = memcache.get(mcid)
			if qc == None:
				logging.debug("missed qc cache")
				qc = self.get_inbox_query(character.key, session.key).count()
				memcache.set(mcid, str(qc))
			else:
				qc = int(qc)

			if recent_update:
				mcid = "FDQ/%d/%d" % (session.key.id(), since)
				qpo = memcache.get(mcid)
				qp = unwrap_for_update(memcache.get(mcid), pun_value)
				if qp == None:
					qp = Post.query(Post.date > datetime.datetime.fromtimestamp(since), ancestor=session.key).count()
					logging.debug("missed qp cache (%s): messages since (%s) are %d" % (qpo, since, qp))
					memcache.set(mcid, wrap_for_update(qp, pun_value))
				else:
					qp = int(qp)
			else:
				qp = 0

			o = {"inbox": qc, "feed": qp, "next_since": recent_update_time + 1 if recent_update_time != None else None}
		elif dynamic_id == "predefs":
			sets = session.activated
			msgout = []

			if sets: # if no sets, no messages!
				stun_value = get_session_or_template_update_value(session)

				mcid = "PDM/%d/%d" % (session.key.id(), character.key.id())
				msgo = memcache.get(mcid)
				messages = unwrap_for_update(msgo, stun_value)
				if messages == None:
					logging.debug("missed predefs cache (%s)" % msgo)
					glob_ms = Message.query(Message.charspec == False, Message.msid.IN(sets), ancestor=session.template).fetch()
					char_ms = Message.query(Message.msid.IN(sets), ancestor=character.key).fetch()
					messages = glob_ms + char_ms
					messages.sort(key=lambda x: sets.index(x.msid))
					for msg in messages:
						msgout.append({"mid": msg.key.id(), "body": msg.body, "charspec": msg.charspec, "msid": msg.msid, "title": msg.title})
					memcache.set(mcid, wrap_for_update(json.dumps(msgout), stun_value))
				else:
					msgout = json.loads(messages)
			msgout.reverse()
			o = {"messages": msgout}
		elif dynamic_id in ("feed", "inbox"):
			limit = 10

			begin = self.request.get("begin", None)
			cid = self.request.get("cid", None)
			direction = self.request.get("direction", "forward")

			pun_value = get_post_update_value(session.key)

			mcid = "%s/%d/%s/%s/%s" % ("FED" if dynamic_id == "feed" else "IBX", session.key.id(), begin, cid, direction)
			ptso = memcache.get(mcid)
			pts = unwrap_for_update(ptso, pun_value)
			if pts == None:
				logging.debug("missed pts cache (%s)" % ptso)

				if begin != None:
					begin = ndb.Cursor(urlsafe=begin)
				# for quota reasons, we are not verifying the character id
				if cid != None:
					if not cid.isdigit():
						return self.abort(400)
					cid = ndb.Key(Character, int(cid), parent=session.template)

				reverse = direction == "reverse"

				if dynamic_id == "inbox":
					if cid != None:
						return self.abort(400)
					q = self.get_inbox_query(character.key, session.key)
					q = q.order((Post.date) if reverse else (-Post.date))
				elif cid != None: # profile feed
					q = Post.query(ndb.OR(Post.cid == cid, Post.target == cid), ancestor=session.key)
					q = q.order((Post.date) if reverse else (-Post.date), Post.key)
				else: # normal feed
					q = Post.query(ancestor=session.key)
					q = q.order((Post.date) if reverse else (-Post.date))
				posts, cursor, more = q.fetch_page(limit, start_cursor=(begin.reversed() if reverse and begin != None else begin))
				if reverse:
					posts.reverse()
				o = {"posts": [self.build_post_obj(post, include_prev=True) for post in posts], "next": (cursor.reversed().urlsafe() if reverse else cursor.urlsafe()) if more else None}

				memcache.set(mcid, wrap_for_update(json.dumps(o), pun_value))
			else:
				o = json.loads(pts)
		else:
			return self.abort(404)
		self.response.headers["Content-Type"] = "application/json"
		self.response.write(json.dumps(o) if type(o) != str else o)

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
	def check_access(self):
		if not is_user_admin():
			self.abort(403)
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
		self.check_access()
		# Global calls
		if rel == "delete_administrator":
			succ, key = self.get_reqs_key("Administrator")
			if succ:
				if key.id() == users.get_current_user().email():
					self.display_error("You cannot remove yourself as an administrator! Sign into a different administrator account to do so.")
				elif key.get() != None:
					key.delete()
					self.redirect("/administration/#administrators")
				else:
					self.display_error("The specified message set was not found.")
		elif rel == "add_administrator":
			succ, email, name = self.get_reqs("email", "name")
			if succ:
				key = ndb.Key(Administrator, email)
				if key.get() != None:
					self.display_error("An administrator already exists with that email!")
				else:
					Administrator(key=key, name=name).put()
					self.redirect("/administration/#administrators")
		# Template-related calls
		elif rel == "load_template":
			succ, template_data = self.get_reqs("template")
			if succ:
				loaded = load_template(template_data)
				if type(loaded) != str:
					self.redirect("/administration/template?key=%s" % loaded.urlsafe())
				else:
					self.display_error("The specified template is invalid: %s" % loaded)
		elif rel == "new_template":
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
			# Template notification not included because NO ONE CARES ABOUT THE NAME.
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
				notify_update_template(key)
				self.redirect("/administration/template?key=%s#message-sets" % key.urlsafe())
		elif rel == "delete_message_set":
			succ, name, key = self.get_reqs_key("name", "Template")
			if succ:
				templ = key.get()
				if name in templ.message_sets:
					templ.message_sets.remove(name)
					templ.put()
					notify_update_template(key)
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
				notify_update_template(key)
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
					notify_update_template(key.parent())
					self.redirect("/administration/template?key=%s#global-messages" % key.parent().urlsafe())
		elif rel == "new_character":
			succ, name, avatar, key = self.get_reqs_key("name", "avatar", "Template")
			if succ:
				nkey = Character(name=name, avatar=avatar, parent=key).put()
				notify_update_template(key)
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
				notify_update_template(key.parent())
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
					notify_update_template(key.parent().parent())
					self.redirect("/administration/character?key=%s#global-messages" % key.parent().urlsafe())
		elif rel == "set_character_name":
			succ, name, key = self.get_reqs_key("name", "Template/Character")
			if succ:
				char = key.get()
				char.name = name
				char.put()
				notify_update_template(key.parent())
				self.redirect("/administration/character?key=%s#properties" % key.urlsafe())
		elif rel == "set_character_avatar":
			succ, avatar, key = self.get_reqs_key("avatar", "Template/Character")
			if succ:
				char = key.get()
				char.avatar = avatar
				char.put()
				notify_update_template(key.parent())
				self.redirect("/administration/character?key=%s#properties" % key.urlsafe())
		elif rel == "duplicate_character":
			succ, name, key = self.get_reqs_key("name", "Template/Character")
			if succ:
				old = key.get()
				oldmsgs = Message.query(ancestor=key).fetch()
				newkey = Character(name=name, avatar=old.avatar, parent=key.parent()).put()
				for oldm in oldmsgs:
					Message(msid=oldm.msid, title=oldm.title, body=oldm.body, parent=newkey).put()
				notify_update_template(key.parent())
				self.redirect("/administration/character?key=%s#properties" % newkey.urlsafe())
		elif rel == "delete_character":
			succ, key = self.get_reqs_key("Template/Character")
			if succ:
				oldkeys = Message.query(ancestor=key).fetch(keys_only=True)
				for mkey in oldkeys:
					mkey.delete()
				key.delete()
				notify_update_template(key.parent())
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
				notify_update_template(key)
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
		elif rel == "delete_session":
			succ, key = self.get_reqs_key("Session")
			if succ:
				oldposts = Post.query(ancestor=key).fetch(keys_only=True)
				for pkey in oldposts:
					pkey.delete()
				key.delete()
				notify_update_session(key)
				self.redirect("/administration")
		elif rel == "set_session_name":
			succ, name, key = self.get_reqs_key("name", "Session")
			if succ:
				session = key.get()
				session.name = name
				session.put()
				notify_update_session(key)
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
				notify_update_session(key)
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
				notify_update_session(key)
				self.redirect("/administration/session?key=%s#characters" % key.urlsafe())
		else:
			self.abort(404)
	def get(self, rel=""):
		self.check_access()
		if rel == "":
			self.response.headers["Content-Type"] = "text/html"
			jt = JINJA_ENVIRONMENT.get_template('static_admin/root.html')

			templates = Template.query().fetch()
			sessions = Session.query().fetch()
			administrators = Administrator.query().fetch()

			self.response.write(jt.render({"templates": templates, "sessions": sessions, "administrators": administrators}))
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
		elif rel == "prepare_delete_session":
			self.response.headers["Content-Type"] = "text/html"
			jt = JINJA_ENVIRONMENT.get_template('static_admin/prepare_delete.html')

			key = self.safe_get_key("Session")
			if key != None:
				session = key.get()
				if session == None:
					self.display_error("The session that you are trying to delete either does not exist or has been deleted.")
				else:
					self.response.write(jt.render({"target": session, "warning": "You are attempting to delete a session and ALL PLAYER ASSIGNMENT and ALL POSTS!", "type": "session", "keep": "/administration/session?key=%s" % key.urlsafe(), "destroy": "/administration/delete_session"}))
		elif rel == "download_template":
			succ, key = self.get_reqs_key("Template")
			if succ:
				self.response.headers["Content-Type"] = "text/plain"
				self.response.write(dump_template(key.get()))
		else:
			self.abort(404)

administration = webapp2.WSGIApplication([
	('/administration', AdminPage),
	('/administration/(.*)', AdminPage),
])

