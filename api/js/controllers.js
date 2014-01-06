'use strict';

// controllers
var app = angular.module('misterio.controllers', []);

app.controller('Feed', ['$scope', '$location', 'User',
    function Feed($scope, $location, User) {
  $scope.user = function(id) {
    return User.userLookup[id];
  };

  $scope.total = 0;
  $scope.offset = 0;
  $scope.limit = 10;
  $scope.get = function() {
    $scope.messages = [];
    User.messages.all($scope.offset, $scope.limit)
      .then(function(data) {
      $scope.messages = data.data;
      $scope.total = data.total;
    });
  };

  $scope.canNext = function() {
    return $scope.offset + $scope.limit < $scope.total;
  };
  $scope.canPrev = function() {
    return $scope.offset !== 0;
  };

  $scope.next = function() {
    if ($scope.canNext()) {
      $scope.offset += $scope.limit;
      $scope.get();
    }
  };
  $scope.prev = function() {
    if ($scope.canPrev()) {
      if ($scope.offset < $scope.limit) {
        $scope.offset = 0;
      } else {
        $scope.offset -= $scope.limit;
      }
      $scope.get();
    }
  };

  $scope.get();
}]);

app.controller('Inbox', ['$scope', '$location', 'User',
    function Inbox($scope, $location, User) {
  $scope.user = function(id) {
    return User.userLookup[id];
  };

  $scope.total = 0;
  $scope.offset = 0;
  $scope.limit = 10;
  $scope.get = function() {
    $scope.messages = [];
    User.messages.inbox($scope.offset, $scope.limit)
      .then(function(data) {
      $scope.messages = data.data;
      $scope.total = data.total;
    });
  };

  $scope.canNext = function() {
    return $scope.offset + $scope.limit < $scope.total;
  };
  $scope.canPrev = function() {
    return $scope.offset !== 0;
  };

  $scope.next = function() {
    if ($scope.canNext()) {
      $scope.offset += $scope.limit;
      $scope.get();
    }
  };
  $scope.prev = function() {
    if ($scope.canPrev()) {
      if ($scope.offset < $scope.limit) {
        $scope.offset = 0;
      } else {
        $scope.offset -= $scope.limit;
      }
      $scope.get();
    }
  };

  $scope.get();
}]);

app.controller('Compose', ['$scope', '$location', '$routeParams', 'User', 'Storage',
    function Compose($scope, $location, $routeParams, User, Storage) {
  $scope.dirty = 2;
  $scope.message = Storage.get('compose') || ($scope.dirty = 0, $scope.message = {
    public: true, to: ""
  });
  $scope.$watchCollection('message', _.throttle(function(value) {
    Storage.set('compose', value);
    $scope.dirty && ($scope.dirty--);
  }, 100));

  $scope.user = function(uid) {
    return User.userLookup[uid];
  };

  var TO_SPLIT = /\s+,\s+/g;

  function gotPrev(prev) {
    $scope.prev = prev;
    var to = _.compact(($scope.message.to || '').split(TO_SPLIT));
    ~to.indexOf(prev.from+'') || to.push(prev.from);
    $scope.message.to = to.join(', ');
  }

  $scope.getPrev = function() {
    $scope.prev = null;
    User.messages.get(id).then(gotPrev, function(err) {
      $scope.prev = false;
    });
  };

  $scope.reset = function() {
    $scope.message = {
      public: true, to: ""
    };
    $scope.dirty = 0;
    $scope.SendForm.$setPristine();
  };

  $scope.submit = function() {
    var msg = $scope.message;
    User.messages.send({
      title: msg.title,
      data: msg.data,
      to: msg.to.split(TO_SPLIT).map(parseInt).filter(function (e) {return !isNaN(e);}),
      public: msg.public,
      prev: parseInt(msg.prev)
    }).then(function(data) {
      $scope.$emit('flash', 'info', 'Enviado!', 'Tu mensaje ha enviado!', {dismissable: true});
    });
  };

  var id = $scope.message.prev = $routeParams.id || null;
  if (id) {
    var stash = $scope.stash();
    if (stash && stash.id === id) {
      gotPrev(stash);
    } else {
      $scope.getPrev();
    }
  }
}]);

app.controller('Users', ['$scope', '$location', 'User',
    function Users($scope, $location, User) {
  $scope.state = {editing: -1, adding: false};
  $scope.editUser = null;

  $scope.User = User;
  /* $scope.count = function() {
    var n = User.others.length;
    return "Hay " + n + " personas.";
  }; */
  $scope.access = function() {
    return User.user.access;
  };

  $scope.disabled = function(index, del) {
    var s = $scope.state, u = User.others[index], m = User.user.id;
    return s.adding || ~s.editing || (del && u.uid === m);
  };

  $scope.add = function() {
    $scope.state.adding = true;
    $scope.editUser = {'access': false, 'email': null};
  };

  $scope.edit = function(index) {
    if (!User.user.access) return;
    var other = User.others[index];
    $scope.state.editing = index;
    $scope.editUser = {};
    for (var key in other) {
      $scope.editUser[key] = other[key];
    }
  };
  $scope.delete = function(index) {
    if (!User.user.access) return;
    var user = User.others[index];
    if (confirm('Are you sure you wish to delete ' + user.name + '?')) {
      User.users.remove(user.uid);
    }
  };

  $scope.save = function() {
    if (!User.user.access) return;
    if ($scope.state.adding) {
      User.users.add($scope.editUser).then($scope.cancel);
    } else {
      User.users.update($scope.editUser.uid, $scope.editUser).then($scope.cancel);
    }
  };
  $scope.cancel = function() {
    if (!User.user.access) return;
    $scope.state.adding = false;
    $scope.state.editing = -1;
    $scope.editUser = null;
  };
}]);

app.controller('AddUser', ['$scope', '$location', 'User',
    function AddUser($scope, $location, User) {
  $scope.user = {};
  $scope.submit = function() {
    User.users.add($scope.user).then(function(data) {
      $location.url('/users/' + data.uid);
    });
  };
}]);

app.controller('Profile', ['$scope', '$location', '$routeParams', 'User',
    function Profile($scope, $location, $routeParams, User) {
  var uid = $scope.uid = $routeParams.uid;
  $scope.user = function(id) {
    return User.userLookup[id];
  };

  $scope.totalFrom = null;

  $scope.total = 0;
  $scope.offset = 0;
  $scope.limit = 10;
  $scope.get = function() {
    $scope.messages = [];
    User.messages.profile(uid, 'all', $scope.offset, $scope.limit)
      .then(function(data) {
      $scope.messages = data.data;
      $scope.total = data.total;
      $scope.totalFrom = data.from;
    });
  };

  $scope.canNext = function() {
    return $scope.offset + $scope.limit < $scope.total;
  };
  $scope.canPrev = function() {
    return $scope.offset !== 0;
  };

  $scope.next = function() {
    if ($scope.canNext()) {
      $scope.offset += $scope.limit;
      $scope.get();
    }
  };
  $scope.prev = function() {
    if ($scope.canPrev()) {
      if ($scope.offset < $scope.limit) {
        $scope.offset = 0;
      } else {
        $scope.offset -= $scope.limit;
      }
      $scope.get();
    }
  };

  $scope.get();
}]);

app.controller('Token', ['$routeParams', '$location', 'User',
    function Token($routeParams, $location, User) {
  if ($routeParams.token && $routeParams.token.length === 40) {
    User.login($routeParams.token).then(function() {
      $location.url('/');
    }, function() {
      $location.url('/forbidden');
    });
  } else {
    // TODO: flash message
    $location.url('/forbidden');
  }
}]);

app.controller('Navbar', ['$scope', 'User', function Navbar($scope, User) {
  $scope.User = User;
  $scope.logout = User.logout;
  /*$scope.unread = function() {
    return 4; //User.messages.inboxCount();
  };*/
}]);

app.controller('Flash', ['$scope', '$rootScope', 'Storage',
    function Flash($scope, $rootScope, Storage) {
  $scope.flash = [];
  $rootScope.$on('apiError', function(e, status, message) {
    console.log(arguments);
    var type;
    if (status >= 400 && status < 500) {
      type = 'App Error!';
    } else if (status >= 500) {
      type = 'Server Error!';
    } else {
      type = 'Network Error!';
      message || (message = 'An unknown error occurred, please check your network connection.');
    }
    flash('danger', type, message, {dismissable: true});
  });
  $rootScope.$on('flash', function(e, type, info, message, options) {
    flash(type, info, message, options);
  });
  Storage.status || flash('warning', 'Cookies Disabled!',
    'This site uses a method similar to cookies to manage your user session, but cannot because your cookies are disabled!');

  $scope.dismiss = function(index) {
    $scope.flash.splice(index, 1);
  };

  function flash(type, info, message, options) {
    options || (options = {});
    var obj = {
      info: info,
      message: message,
      'class': ['alert-' + type],
      dismissable: !!options.dismissable
    };
    options.dismissable && obj['class'].push('alert-dismissable');
    $scope.flash.push(obj);
  }
}]);
