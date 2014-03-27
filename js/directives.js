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
app.directive('inboxCounter', function($interval, User) {
  return function(scope, element, attrs) {
    var stopUpdate;
    function updateCount() {
      console.log("update");
      if (User.user.id === null) {
        element.text("");
      } else {
        User.messages.inboxCount().then(function (data) {
          element.text(data.inbox ? data.inbox : "");
        });
      }
    }
    scope.onShouldUpdateInbox(updateCount);
    updateCount();
    stopUpdate = $interval(updateCount, 30000);
    element.bind('$destroy', function() {
      $interval.cancel(stopUpdate);
    });
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
