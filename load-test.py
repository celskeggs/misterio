#!/usr/bin/env python2
#  Derived from code under the following license.
#  See https://cloud.google.com/appengine/articles/load_test
#
#    Copyright 2009 Google Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import httplib2
import random
import socket
import time
import json
from threading import Event
from threading import Thread
from threading import current_thread
from urllib import urlencode

# Modify these values to control how the testing is done

# How many threads should be running at peak load.
NUM_THREADS = 20

# How many minutes the test should run with all threads active.
TIME_AT_PEAK_QPS = 30 # minutes

# How many seconds to wait between starting threads.
# Shouldn't be set below 30 seconds.
DELAY_BETWEEN_THREAD_START = 5 # seconds

quitevent = Event()

def threadproc():
    """This function is executed by each thread."""
    print "Thread started: %s" % current_thread().getName()
    h = httplib2.Http(timeout=30)

    zero_point = int(time.time() * 1000)
    baseurl = "https://toluca-misterio.appspot.com"
    testpostid = None
    testpostid2 = None
    testuserid = None
    uqid = random.randint(100000, 999999)
    headers = {"X-Bypass-Token": "BPKEY07771"}
    successes = 0

    while not quitevent.is_set():
        # Twenty five events of load-testing per minute.
        # 2.4 seconds on average between load tests
        time.sleep(random.uniform(2.2, 2.6))

        # Six inbox-count requests per minute.
        # One new-post request per NINE minutes.
        # One users request per minute.
        # One predefs request per minute.
        # Five feed requests per minute.
        # Five inbox requests per minute.
        # Refetch all resources once per NINE minutes.
        # One get-post request per minute.
        try:
            resp = None
            rqtype = None
            while rqtype == None:
                rqtype = random.randint(1, 25 if testpostid != None else 24)
                if (rqtype == 11 or rqtype == 24) and random.randint(1, 9) != 1: # do these one ninth of the normal rate
                    rqtype = None
                elif rqtype >= 7 and rqtype <= 10:
                    rqtype = None
            if rqtype >= 1 and rqtype <= 6:
                startAt = int(time.time() * 1000)
                resp, content = h.request("%s/dynamic/inbox-count?since=%d" % (baseurl, zero_point), headers=headers)
                if resp != None and resp.status == 200:
                    ct = json.loads(content)
                    if random.randint(1, 30) == 1:
                        print "Representative inbox:", ct["inbox"]
                    if ct["next_since"] != None:
                        zero_point = ct["next_since"]
                    elif ct["feed"] != 0:
                        zero_point = startAt
            elif rqtype == 11:
                resp, content = h.request("%s/dynamic/new-post" % baseurl, method="POST", body=json.dumps({"to": testuserid, "prev": testpostid2, "data": "autopost by %d" % uqid, "expect": testuserid != None}), headers=headers)
                print "New post!"
            elif rqtype == 12:
                resp, content = h.request("%s/dynamic/users" % baseurl, headers=headers)
                if resp != None and resp.status == 200:
                    testuserid = json.loads(content)["users"][1]["cid"]
            elif rqtype == 13:
                resp, content = h.request("%s/dynamic/predefs" % baseurl, headers=headers)
            elif rqtype >= 14 and rqtype <= 18:
                resp, content = h.request("%s/dynamic/feed?direction=%s" % (baseurl, "forward" if random.randint(0, 1) else "reverse"), headers=headers)
                if resp != None and resp.status == 200:
                    testpostid = json.loads(content)["posts"][0]["id"]
            elif rqtype >= 19 and rqtype <= 23:
                resp, content = h.request("%s/dynamic/inbox?direction=%s" % (baseurl, "forward" if random.randint(0, 1) else "reverse"), headers=headers)
                if resp != None and resp.status == 200:
                    posts = json.loads(content)["posts"]
                    if posts:
                        testpostid2 = random.choice(posts)["id"]
            elif rqtype == 24:
                for req in ["%s/fonts/glyphicons-halflings-regular.woff", "%s/img/game_doctor.png", "%s/img/arturo_d_c_e.png", "%s/partials/feed.html", "%s/js/directives.js", "%s/js/controllers.js", "%s/js/app.js", "%s/js/services.js", "%s/lib/angular/i18n/angular-locale_es-es.js", "%s/lib/angular/angular-route.js", "%s/css/app.css", "%s/css/bootstrap.min.css", "%s/lib/marked/marked.js", "%s/lib/angular/angular.js", "%s/lib/underscore/underscore.js", "%s/lib/jquery/jquery.js", "%s/lib/bootstrap/bootstrap.js", "%s/"]:
                    resp, content = h.request(req % baseurl, headers=headers)
                    if resp == None or resp.status != 200:
                        print "Failed resource request for", req % baseurl
            elif rqtype == 25:
                resp, content = h.request("%s/dynamic/get-post?id=%d" % (baseurl, testpostid), headers=headers)
            else:
                print "Bad rqtype"
            if resp == None or resp.status != 200:
                print "Failed request of type", rqtype, "with", resp
            else:
                successes += 1
        except socket.timeout:
            print "Socket timeout"

    print "Thread finished: %s with %d successes" % (current_thread().getName(), successes)


if __name__ == "__main__":
    runtime = (TIME_AT_PEAK_QPS * 60 + DELAY_BETWEEN_THREAD_START * NUM_THREADS)
    print "Total runtime will be: %d seconds" % runtime
    threads = []
    try:
        for i in range(NUM_THREADS):
            t = Thread(target=threadproc)
            t.start()
            threads.append(t)
            time.sleep(DELAY_BETWEEN_THREAD_START)
        print "All threads running"
        for i in range(TIME_AT_PEAK_QPS):
            print "%d/%d" % (i, TIME_AT_PEAK_QPS)
            time.sleep(60)
        print "%d/%d" % (TIME_AT_PEAK_QPS, TIME_AT_PEAK_QPS)
        print "Completed full time at peak qps, shutting down threads"
    except:
        print "Exception raised, shutting down threads"

    quitevent.set()
    time.sleep(3)
    for t in threads:
        t.join(1.0)
    print "Finished"
