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
      element.text(data.inbox ? data.inbox : "");
    }
    scope.$on("messageCountUpdate", updateCount);
  }
});

app.directive('feedCounter', function(User) {
  return function(scope, element, attrs) {
    function updateCount(event, data) {
      element.text(data.feed ? data.feed : "");
    }
    scope.$on("messageCountUpdate", updateCount);
  }
});

app.directive('markdownPreview', function() {
  return function(scope, element, attrs) {
    var renderer = new marked.Renderer();

    renderer.table = function(header, body) {
      return '<table class="table"><thead>' + header + '</thead><tbody>' + body + '</tbody></table>';
    };
    renderer.image = function(href, title, text) {
      var spt = href.split("@");
      if (spt.length >= 3) {
        href = href.substring(spt[0].length + spt[1].length + 2);
      }
      var out = '<img src="/img/' + href + '" alt="' + text + '"';
      if (spt.length >= 3) {
        out += ' width="' + parseInt(spt[0]) + '"';
        out += ' height="' + parseInt(spt[1]) + '"';
      }
      if (title) {
        out += ' title="' + title + '"';
      }
      out += this.options.xhtml ? '/>' : '>';
      return out;
    };

    var opts = { renderer: renderer };

    var update = _.throttle(function update(text) {
      var html = (typeof marked === 'function' && text) ? marked(text, opts) : '';
      $(element).html(html);
    }, 500);
    scope.$watch(attrs.markdownPreview, update);
    update(scope.$eval(attrs.markdownPreview));
  };
});
