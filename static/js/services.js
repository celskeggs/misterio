'use strict';

// services

var app = angular.module('misterio.services', []);

app.factory('Storage', ['$window', function Storage($window) {
  var prefix = 'MI-', store, status = true;

  try {
    store = $window.localStorage;
  } catch (e) {
    // probably a user who hates cookies
    if (e && $window.DOMException && e.code === $window.DOMException.SECURITY_ERR) {
      var data = {};
      store = {
        getItem: function(key) {
          return data[key];
        },
        setItem: function(key, value) {
          data[key] = value;
        },
        removeItem: function(key) {
          delete data[key];
        }
      };
      status = false;
    } else {
      throw e;
    }
  }

  var get = function(key) {
    var item = store.getItem(prefix + key);
    try {
      return item && JSON.parse(item);
    } catch (e) {}
    return null;
  };

  var set = function(key, item) {
    store.setItem(prefix + key, JSON.stringify(item));
  };

  var remove = function(key) {
    store.removeItem(prefix + key);
  };

  return {
    get: get,
    set: set,
    remove: remove,
    status: status
  };
}]);

app.factory('User', ['$rootScope', '$location', '$http', '$q', 'Storage',
    function User($rootScope, $location, $http, $q, Storage) {
  function config() {
    return {
      headers: headers()
    };
  }
  function headers() {
    return {
      'X-Session': User.user.session
    };
  }
  function use(req, manipulate) {
    var d = $q.defer();
    req.success(success(d, manipulate)).error(error(d));
    return d.promise;
  }
  function putData(data, d) {
    if (typeof data !== 'object' || data === null) {
      var err = new TypeError('Server response type not valid.');
      err.status = 500;
      bubble(err, 500, res);
      return d.reject(err), false;
    }
    d.resolve(data);
    return true;
  }
  // handle success
  function success(d, manipulate) {
    return function handle(data, status, res) {
      putData(data, d) && manipulate && manipulate(data);
    };
  }
  function bubble(data, status) {
    // let somebody else handle that
    $rootScope.$emit('apiError', status, data.message);
  }
  // handle error
  function error(d) {
    return function handle(data, status, res) {
      var err = new Error(data.message || 'Server error.');
      bubble(err, status, res);
      err.status = status;
      d.reject(err);
    };
  }

  // TODO: pull users on launch ("login"?)

  var User = {
    user: Storage.get('user') || {
      id: null,
      name: null,
      access: null,
      session: null,
      instance: null
    },
    inboxes: function() {
      return use($http.get('get-counts.php', {
        params: {},
        headers: headers()
      }));
    },
    others: [],
    userLookup: {}, // hmmm
    login: function(session) {
      User.user.session = session;
      return User.users.all().then(function(data) {
        return User.user.id;
      }, function(err) {
        if (err.status === 403) {
          User.logout();
        }
        throw err;
      });
    },
    become: function(targetid) {
      return use($http.get('be-user.php', {
        params: {be: targetid},
        headers: headers()
      }));
    },
    logout: function() {
      User.user.id = null;
      User.user.name = null;
      User.user.access = null;
      User.user.session = null;
      User.user.instance = null;
      Storage.set('user', User.user);
      $location.url('/select');
    },
    avatars: {
      get: function() {
        return use($http.get('get-avatars.php', {
          params: {},
          headers: headers()
        }));
      }
    },
    messages: {
      get: function(id) {
        return use($http.get('get-message.php', {
          params: {
            id: id
          },
          headers: headers()
        }));
      },
      all: function(offset, limit) {
        return use($http.get('messages.php', {
          params: {
            offset: offset,
            limit: limit,
            scope: 'all'
          },
          headers: headers()
        }));
      },
      inboxCount: function() {
        return use($http.get('messages.php', {
          params: {
            offset: 0, // ignored on server
            limit: 1, // ignored on server
            scope: 'count'
          },
          headers: headers()
        }));
      },
      inbox: function(offset, limit) {
        return use($http.get('messages.php', {
          params: {
            offset: offset,
            limit: limit,
            scope: 'inbox'
          },
          headers: headers()
        }));
      },
      profile: function(uid, offset, limit) {
        return use($http.get('profile.php', {
          params: {
            uid: uid,
            offset: offset,
            limit: limit
          },
          headers: headers()
        }));
      },
      update: function(id, message) {
        // message: {title, data}
        return use($http.put('update-message.php', message, {
          params: {
            id: id
          },
          headers: headers()
        }));
      },
      toggleFinalize: function(id) {
        return use($http.post('qedit-message.php', {}, {
          params: {
            id: id,
            operation: "finalize"
          },
          headers: headers()
        }));
      },
      send: function(message) {
        // message: {title, data, to: [], prev: ?, public}
        return use($http.post('send-message.php', message, config()));
      },
      remove: function(id) {
        return use($http.delete('remove-message.php', {
          params: {
            id: id
          },
          headers: headers()
        }));
      },
      clear: function() {
        return use($http.delete('clear-messages.php', {
          params: {},
          headers: headers()
        }));
      }
    },
    users: {
      // TODO: enforce access?
      add: function(user) {
        // user: {name, email, access, avatar}
        return use($http.post('add-user.php', user, config()), function(data) {
          user.uid = data.uid;
          User.others.push(user);
          User.userLookup[user.uid] = user;
        });
      },
      move: function(uid, instance) {
        return use($http.post('move-user.php', {instance: instance}, {
          params: {
            uid: uid
          },
          headers: headers()
        }));
      },
      all: function() {
        return use($http.get('get-users.php', config()), function(data) {
          var others = data.data, uid = data.uid, instance = data.instance;
          User.others.length = 0;
          User.others.push.apply(User.others, others);
          User.userLookup = {};
          for (var i = 0; i < others.length; i++) {
            User.userLookup[others[i].uid] = others[i];
          }
          User.user.id = uid;
          User.user.name = User.userLookup[uid].name;
          User.user.access = User.userLookup[uid].access;
          User.user.instance = instance;
          Storage.set('user', User.user);
        });
      },
      // TODO: enforce access?
      reset: function(uid) {
        return use($http.post('reset-user.php', {}, {
          params: {
            uid: uid
          },
          headers: headers()
        }));
      },
      update: function(uid, user) {
        // user: {name, email, access, avatar}
        var d = $q.defer();
        $http.put('update-user.php', user, {
          params: {
            uid: uid
          },
          headers: headers()
        }).success(function(data, status, res) {
          // TODO: update User.others
          var uid = data.uid, user = User.userLookup[uid];
          for (var key in data) {
            user[key] = data[key];
          }
          putData(data, d);
        }).error(error(d));
        return d.promise;
      },
      remove: function(uid) {
        for (var i = 0; i < User.others.length; i++) {
          if (User.others[i].uid === uid) {
            break;
          }
        }
        User.others.splice(i, 1);
        return use($http.delete('remove-user.php', {
          params: {
            uid: uid
          },
          headers: headers()
        })).then(function(data) {
          delete User.userLookup[uid];
          return data;
        }, function(err) {
          User.others.splice(i, 0, User.userLookup[uid]);
          throw err;
        });
      }
    }
  };
  User.user.session && User.login(User.user.session);
  Storage.set('user', User.user);
  return User;
}]);
