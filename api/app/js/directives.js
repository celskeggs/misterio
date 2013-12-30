'use strict';

// directives

var app = angular.module('misterio.directives', []);

app.directive('navLink', ['$location', function($location) {
  return {
    restrict: 'A',
    link: function(scope, element, attrs) {
      var parent = element.parent();
      var update = function() {
        if ($location.path() === attrs.href)
          parent.addClass('active');
        else
          parent.removeClass('active');
      };
      scope.$on('$locationChangeSuccess', update);
      update();
    }
  };
}]);

app.directive('focusMe', function() {
  return {
    link: function(scope, element, attrs) {
      if (attrs.focusMe) {
        var prev = {};
        scope.$watch(attrs.focusMe, function(value) {
          value && value !== prev && element.focus();
        });
      } else {
        element.focus();
      }
    }
  };
});
