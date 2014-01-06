'use strict';

// filters

var app = angular.module('misterio.filters', []);

app.filter('interpolate', ['version', function(version) {
  return function(text) {
    return String(text).replace(/\%VERSION\%/mg, version);
  }
}]);
