'use strict';


// controllers
var app = angular.module('misterio.controllers', []);

app.controller('Feed', ['$scope', '$location', 'User', '$rootScope',
    function Feed($scope, $location, User, $rootScope) {
  $scope.user = function(id) {
    return User.userLookup[id];
  };

  $scope.linkurl = "/";

  $scope.cursor = null;
  $scope.cursor_next = null;
  $scope.limit = 10;

  var handle_messages = function(data) {
    $rootScope.tellFeedListeners(); // TODO: is this in the right spot?
    $scope.loading = false;
    $scope.messages = [];
    for (var i=0; i<data.posts.length; i++) {
      var d = data.posts[i];
      if (d.prev && !d.prevobj) {
        // TODO: have this be sent by the server instead of sending a stampede
        User.messages.get(d.prev).then(function (po) {
          this.prevobj = po;
        }.bind(d));
      }
      $scope.messages.push(d);
    }
  };

  $scope.restart = function() {
    $scope.messages = [];
    $scope.loading = true;
    User.messages.startFeed($scope.limit).then(function(data) {
      handle_messages(data);
      $scope.cursor = null;
      $scope.cursor_next = data.next;
    });
  };

  $scope.canNext = function() {
    return $scope.cursor_next !== null;
  };
  $scope.canPrev = function() {
    return $scope.cursor !== null;
  };

  $scope.next = function() {
    if ($scope.canNext()) {
      $scope.messages = [];
      $scope.loading = true;
      User.messages.continueFeed($scope.cursor_next, $scope.limit).then(function(data) {
        handle_messages(data);
        $scope.cursor = $scope.cursor_next;
        $scope.cursor_next = data.next;
      });
    }
  };
  $scope.prev = function() {
    if ($scope.canPrev()) {
      $scope.messages = [];
      $scope.loading = true;
      User.messages.continueFeed($scope.cursor, $scope.limit, true).then(function(data) {
        handle_messages(data);
        $scope.cursor_next = $scope.cursor;
        $scope.cursor = data.next;
      });
    }
  };

  $scope.restart();
}]);

app.controller('Inbox', ['$scope', '$location', 'User',
    function Inbox($scope, $location, User) {
  $scope.user = function(id) {
    return User.userLookup[id];
  };

  $scope.linkurl = "/inbox";

  $scope.total = 0;
  $scope.offset = 0;
  $scope.limit = 10;

  $scope.get = function() {
    $scope.messages = [];
    User.messages.inbox($scope.offset, $scope.limit)
      .then(function(data) {
      $scope.messages = [];
      for (var i=0; i<data.data.length; i++) {
        var d = data.data[i];
        if (d.prev && !d.prevobj) {
          User.messages.get(d.prev).then(function (po) {
            this.prevobj = po;
          }.bind(d));
        }
        $scope.messages.push(d);
      }
      $scope.total = data.total;
    });
  };

  $scope.canNext = function() {
    return $scope.offset + $scope.limit < $scope.total;
  };

  $scope.showing = -1;
  $scope.show = function(id) {
    if ($scope.showing == id) {
      $scope.showing = -1;
    } else {
      $scope.showing = id;
    }
  };
  $scope.isshowing = function(id) {
    return $scope.showing == id;
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
  $scope.dirty = 0;
  $scope.message = Storage.get('compose') || ($scope.dirty = 0, $scope.message = {
    expect: false, to: null
  });
  $scope.$watchCollection('message', _.throttle(function(value) {
    Storage.set('compose', value);
    $scope.dirty && ($scope.dirty--);
  }, 100));

  $scope.state = {
    write: true
  };

  $scope.showWrite = function() {
    $scope.state.write = true;
  };

  $scope.showPreview = function() {
    $scope.state.write = false;
  };

  $scope.user = function(cid) {
    return User.userLookup[cid];
  };
  $scope.User = User;

  $scope.select = function(id) {
    if ($scope.message.to === id) {
      $scope.message.to = null;
    } else {
      $scope.message.to = id;
    }
    if ($scope.message.to === null) {
      $scope.message.expect = false;
    }
  };
  $scope.selected = function(id) {
    return $scope.message.to === id;
  };
  $scope.toggle_expect = function() {
    $scope.message.expect = !$scope.message.expect;
  };

  function gotPrev(prev) {
    $scope.prev = prev;
    $scope.message.to = [prev.from];
  }

  $scope.getPrev = function() {
    $scope.prev = null;
    User.messages.get(id).then(gotPrev, function(err) {
      $scope.prev = false;
    });
  };

  $scope.reset = function() {
    $scope.message = {
      to: null, expect: false
    };
    $scope.state.write = true;
    $scope.dirty = 0;
    $scope.SendForm.$setPristine();
  };

  $scope.sending = false;

  $scope.submit = function() {
    var msg = $scope.message;
    if (msg.to === null) {
      msg.expect = false;
    }
    $scope.sending = true;
    User.messages.send({
      data: msg.data,
      to: msg.to,
      expect: msg.expect,
      prev: parseInt(msg.prev)
    }).then(function(data) {
      $scope.$emit('flash', 'info', 'Enviado!', 'Tu mensaje ha enviado!', {dismissable: true});
      $scope.reset();
      $scope.sending = false;
    }, function() {
      $scope.sending = false;
    });
  };

  var id = $scope.message.prev = $routeParams.id || null;
  if (id) {
    $scope.getPrev();
  }
}]);

app.controller('Users', ['$scope', '$location', 'User',
    function Users($scope, $location, User) {
  $scope.showCredits = false;

  $scope.User = User;

  $scope.toggleCredits = function() {
    $scope.showCredits = !$scope.showCredits;
  };
}]);

app.controller('Profile', ['$scope', '$location', '$routeParams', 'User',
    function Profile($scope, $location, $routeParams, User) {
  var cid = $scope.cid = $routeParams.cid;
  $scope.user = function(id) {
    return User.userLookup[id];
  };

  $scope.linkurl = "/users/" + cid;

  $scope.total = 0;
  $scope.offset = 0;
  $scope.limit = 10;
  $scope.get = function() {
    $scope.messages = [];
    User.messages.profile(cid, $scope.offset, $scope.limit)
      .then(function(data) {
      $scope.messages = [];
      for (var i=0; i<data.data.length; i++) {
        var d = data.data[i];
        if (d.prev && !d.prevobj) {
          User.messages.get(d.prev).then(function (po) {
            this.prevobj = po;
          }.bind(d));
        }
        $scope.messages.push(d);
      }
      $scope.total = data.total;
    });
  };

  $scope.showing = -1;
  $scope.show = function(id) {
    if ($scope.showing == id) {
      $scope.showing = -1;
    } else {
      $scope.showing = id;
    }
  };
  $scope.isshowing = function(id) {
    return $scope.showing == id;
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

app.controller('Navbar', ['$scope', 'User', function Navbar($scope, User) {
  $scope.User = User;
}]);

app.controller('Flash', ['$scope', '$rootScope',
    function Flash($scope, $rootScope) {
  $scope.flash = [];
  $rootScope.$on('apiError', function(e, status, message) {
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
  $rootScope.$on('$routeChangeSuccess', function() {
    var then = Date.now() - 5000;
    for (var i = 0; i < $scope.flash.length; i++) {
      var elem = $scope.flash[i];
      if (elem.time > then) {
        break;
      }
    }
    if (i >= 1) $scope.flash.splice(0, i);
  });

  $scope.dismiss = function(index) {
    $scope.flash.splice(index, 1);
  };

  function flash(type, info, message, options) {
    options || (options = {});
    var obj = {
      info: info,
      message: message,
      'class': ['alert-' + type],
      dismissable: !!options.dismissable,
      time: Date.now()
    };
    options.dismissable && obj['class'].push('alert-dismissable');
    $scope.flash.push(obj);
  }
}]);
