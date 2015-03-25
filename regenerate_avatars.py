#!/usr/bin/env python2
import os

with open("static/img/notavatar.txt", "r") as f:
	avatars = list(set(os.listdir("static/img")) - set(filter(None, (x.strip() for x in f.readlines()))))
print "Avatar list:", avatars
with open("avatar-list.txt", "w") as f:
	f.write("\n".join(avatars))
print "Wrote", len(avatars), "to file."
