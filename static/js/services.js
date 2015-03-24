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

app.factory('User', ['$rootScope', '$location', '$http', '$q',
    function User($rootScope, $location, $http, $q) {
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

  var User = {
    user: {
      id: null,
      name: null,
      access: null
    },
    inboxes: function() {
      return use($http.get('get-counts.php', {
        params: {}
      }));
    },
    others: [],
    userLookup: {}, // hmmm
    fetch: function() {
      return User.users.all().then(function(data) {
        return User.user.id;
      }, function(err) {
        if (err.status === 403) {
          User.logout();
        }
        throw err;
      });
    },
    logout: function() {
      window.location = '/logoff';
    },
    avatars: {
      get: function() {
        return use($http.get('get-avatars.php', {
          params: {}
        }));
      }
    },
    messages: {
      get: function(id) {
        return use($http.get('get-message.php', {
          params: {
            id: id
          }
        }));
      },
      all: function(offset, limit) {
        return use($http.get('messages.php', {
          params: {
            offset: offset,
            limit: limit,
            scope: 'all'
          }
        }));
      },
      inboxCount: function() {
        return use($http.get('messages.php', {
          params: {
            offset: 0, // ignored on server
            limit: 1, // ignored on server
            scope: 'count'
          }
        }));
      },
      inbox: function(offset, limit) {
        return use($http.get('messages.php', {
          params: {
            offset: offset,
            limit: limit,
            scope: 'inbox'
          }
        }));
      },
      profile: function(cid, offset, limit) {
        return use($http.get('profile.php', {
          params: {
            cid: cid,
            offset: offset,
            limit: limit
          }
        }));
      },
      update: function(id, message) {
        // message: {title, data}
        return use($http.put('update-message.php', message, {
          params: {
            id: id
          }
        }));
      },
      toggleFinalize: function(id) {
        return use($http.post('qedit-message.php', {}, {
          params: {
            id: id,
            operation: "finalize"
          }
        }));
      },
      send: function(message) {
        // message: {title, data, to: [], prev: ?, public}
        return use($http.post('send-message.php', message, {}));
      },
      remove: function(id) {
        return use($http.delete('remove-message.php', {
          params: {
            id: id
          }
        }));
      },
      clear: function() {
        return use($http.delete('clear-messages.php', {
          params: {}
        }));
      }
    },
    users: {
      // TODO: enforce access?
      add: function(user) {
        // user: {name, email, access, avatar}
        return use($http.post('add-user.php', user, {}), function(data) {
          user.cid = data.cid;
          User.others.push(user);
          User.userLookup[user.cid] = user;
        });
      },
      move: function(cid, instance) {
        return use($http.post('move-user.php', {instance: instance}, {
          params: {
            cid: cid
          }
        }));
      },
      all: function() {
        return use($http.get('/dynamic/users', {}), function(data) {
          var others = data.users, cid = data.cid, access = data.access;
          User.others.length = 0;
          User.others.push.apply(User.others, others);
          User.userLookup = {};
          for (var i = 0; i < others.length; i++) {
            User.userLookup[others[i].cid] = others[i];
          }
          User.user.id = cid;
          User.user.name = User.userLookup[cid].name;
          User.user.access = access;
        });
      },
      // TODO: enforce access?
      reset: function(cid) {
        return use($http.post('reset-user.php', {}, {
          params: {
            cid: cid
          }
        }));
      },
      update: function(cid, user) {
        // user: {name, email, access, avatar}
        var d = $q.defer();
        $http.put('update-user.php', user, {
          params: {
            cid: cid
          }
        }).success(function(data, status, res) {
          // TODO: update User.others
          var cid = data.cid, user = User.userLookup[cid];
          for (var key in data) {
            user[key] = data[key];
          }
          putData(data, d);
        }).error(error(d));
        return d.promise;
      },
      remove: function(cid) {
        for (var i = 0; i < User.others.length; i++) {
          if (User.others[i].cid === cid) {
            break;
          }
        }
        User.others.splice(i, 1);
        return use($http.delete('remove-user.php', {
          params: {
            cid: cid
          }
        })).then(function(data) {
          delete User.userLookup[cid];
          return data;
        }, function(err) {
          User.others.splice(i, 0, User.userLookup[cid]);
          throw err;
        });
      }
    }
  };
  User.fetch();
  return User;
}]);
