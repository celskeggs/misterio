'use strict';

// declare app level module which depends on filters, and services
var app = angular.module('misterio', [
  'ngRoute',
  'misterio.filters',
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
  r('/inbox', 'inbox', 'Inbox');
  r('/compose', 'compose', 'Compose');
  r('/compose/:id', 'compose', 'Compose');
  r('/users', 'users', 'Users');
  r('/users/add', 'add-user', 'AddUser');
  r('/users/:uid', 'profile', 'Profile');

  r('/token/:token', 'loading', 'Token');

  r('/forbidden', 'forbidden');

  $routeProvider.otherwise({
    templateUrl: 'partials/not-found.html'
  });
}]);

app.config(['$locationProvider', function($locationProvider) {
  $locationProvider.html5Mode(true);
}]);

app.run(function($rootScope, $location, User) {
  $rootScope.page = {
    title: 'Un Misterio en Cuzco',
    fullTitle: function() {
      var ctx = $rootScope.page.context;
      return $rootScope.page.title + (ctx ? ' - ' + ctx : '');
    },
    active: function(route) {
      return route === $location.path();
    }
  };

  $rootScope.ternary = function(cond, a, b) {
    return cond ? a : b;
  };

  $rootScope.blocks = function(text) {
    return text ? text.split(/\n+/g) : [];
  };

  $rootScope.$on('$routeChangeStart', function(event, next, current) {
    if (next.controller !== 'Token' && !User.user.session) {
      $location.url('/forbidden'); // ?proceed=' + encodeURIComponent($location.path())
    }
  });

  $rootScope.onShouldUpdateInbox = function(call) { // I don't know what I'm doing.
    $rootScope.$on('$routeChangeStart', function(event, next, current) {
      call();
    });
  };

  var stashed = null;
  $rootScope.stash = function(value) {
    if (value === undefined) {
      value = stashed;
      stashed = null;
      return value;
    }
    stashed = value;
  };
});

app.run(function($locale) {
  $locale.id = 'es-es';
});
