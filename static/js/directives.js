'use strict';

// directives

var app = angular.module('misterio.directives', []);

app.directive('navLink', ['$location', function($location) {
  return {
    restrict: 'A',
    link: function(scope, element, attrs) {
      var parent = element.parent();
      var pattern = null;
      if (attrs.navLink) {
        pattern = new RegExp(attrs.navLink);
      }
      var update = function() {
        if ($location.path() === attrs.href || pattern.test($location.path()))
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

// Added to update globals
app.directive('inboxCounter', function(User) {
  return function(scope, element, attrs) {
    function updateCount(event, data) {
      console.log("GOT NEW DATA 1:", data)
      element.text(data.inbox ? data.inbox : "");
    }
    scope.$on("messageCountUpdate", updateCount);
  }
});

app.directive('feedCounter', function(User) {
  return function(scope, element, attrs) {
    function updateCount(event, data) {
      console.log("GOT NEW DATA 2:", data)
      element.text(data.feed ? data.feed : "");
    }
    scope.$on("messageCountUpdate", updateCount);
  }
});

app.directive('markdownPreview', function() {
  return function(scope, element, attrs) {
    var update = _.throttle(function update(text) {
      var html = (typeof marked === 'function' && text) ? marked(text) : '';
      $(element).html(html);
    }, 500);
    /*function update(text) {
      $(element).is(':visible') && trigger(text);
    }*/
    scope.$watch(attrs.markdownPreview, update);
    update(scope.$eval(attrs.markdownPreview));
  };
});
