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
      session: null
    },
    others: [],
    userLookup: {},
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
      send: function(message) {
        // message: {title, data, to: [], prev: ?, public}
        return use($http.post('send-message.php', message, {}));
      }
    }
  };
  use($http.get('/dynamic/users', {}), function(data) {
    var others = data.users, cid = data.me, session_name = data.session;
    User.others.push.apply(User.others, others);
    User.userLookup = {};
    for (var i = 0; i < others.length; i++) {
      User.userLookup[others[i].cid] = others[i];
    }
    User.user.id = cid;
    User.user.name = User.userLookup[cid].name;
    User.user.session = session_name;
  }).then(function(data) {
  }, function(err) {
    throw err;
  });
  return User;
}]);

