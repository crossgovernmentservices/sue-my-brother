(function ($, window) {
  "use strict"

  function isNearlyPastAuthTime( secs ) {
    return secs > (AUTH_MAX_AGE / 2);
  }

  function isPastAuthTime( secs ) {
    return secs > AUTH_MAX_AGE;
  }

  $(function() {
    var last_auth_time = $(".auth-time").data("last-auth-time");

    // check if passed auth time
    (function checkAuthStatus() {
      var now_in_secs = Math.round(Date.now() / 1000);
      if(isPastAuthTime(now_in_secs - last_auth_time)) {
        $(".user-auth-status")
          .removeClass("user-auth-status--warning")
          .addClass("user-auth-status--reauth");
        return;
      } else if (isNearlyPastAuthTime(now_in_secs - last_auth_time)) {
        $(".user-auth-status")
          .removeClass("user-auth-status--reauth")
          .addClass("user-auth-status--warning");
      }
      setTimeout(checkAuthStatus, 5000);
    })();

  });

}).call(this, jQuery, window);
