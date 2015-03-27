'use strict';

// declare app level module which depends on filters, and services
var app = angular.module('misterio', [
  'ngRoute',
  'misterio.services',
  'misterio.directives',
  'misterio.controllers'
]);

app.config(['$routeProvider', function($routeProvider) {
  function r(path, template, controller) {
    $routeProvider.when(path, {
      templateUrl: template ? ('partials/' + template + '.html') : undefined,
      controller: controller || undefined
    });
  }

  r('/', 'feed', 'Feed');
  r('/inbox', 'feed', 'Feed');
  r('/compose', 'compose', 'Compose');
  r('/compose/:id', 'compose', 'Compose');
  r('/users', 'users', 'Users');
  r('/users/:cid', 'feed', 'Feed');
  r('/messages', 'predefs', 'Predefs');

  $routeProvider.otherwise({
    templateUrl: 'partials/not-found.html'
  });
}]);

app.config(['$locationProvider', function($locationProvider) {
  $locationProvider.html5Mode(true);
}]);

app.run(function($rootScope, $interval, $location, User) {
  $rootScope.city = "Toluca";

  $rootScope.messagesSince = Date.now() - 2000;

  function updateCount() {
    User.messages.inboxCount($rootScope.messagesSince).then(function (data) {
      $rootScope.$broadcast("messageCountUpdate", data);
    });
  }
  $rootScope.clearFeed = function() {
    $rootScope.messagesSince = Date.now() - 2000; // keep five seconds of messages
    updateCount();
  };
  $rootScope.$on('$routeChangeSuccess', function(event, next, current) {
    if (next.originalPath == "/") {
      $rootScope.clearFeed();
    } else {
      updateCount();
    }
  });
  updateCount();
  var stopCount = $interval(updateCount, 10000);
  // stopCount not currently used.

  $rootScope.page = {
    title: 'Un Misterio en ' + $rootScope.city,
    fullTitle: function() {
      var ctx = $rootScope.page.context;
      return $rootScope.page.title + (ctx ? ' - ' + ctx : '');
    },
    active: function(route) {
      return route === $location.path();
    }
  };

  $rootScope.username = function() {
    return User.user.name;
  };

  $rootScope.sessionname = function() {
    return User.user.session;
  };

  $rootScope.ternary = function(cond, a, b) {
    return cond ? a : b;
  };

  $rootScope.blocks = function(text) {
    return text ? text.split(/\n+/g) : [];
  };
});

app.run(function($locale) {
  $locale.id = 'es-es';
});
