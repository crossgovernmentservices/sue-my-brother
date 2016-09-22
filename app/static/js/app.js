(function ($, window) {
  "use strict"

  // AUTH_MAX_AGE comes from flask config
  // change these to change max
  // auth time for UI
  var AUTH_MAX_AGE = AUTH_MAX_AGE || 300,
      passed_allowed_time_str = "over the maximum 5 minutes";

  function isNearlyPastAuthTime( secs ) {
    return secs > (AUTH_MAX_AGE / 2);
  }

  function isPastAuthTime( secs ) {
    return secs > AUTH_MAX_AGE;
  }

  $(function() {
    var last_auth_time = $(".auth-time").data("last-auth-time"),
        $auth_time = $(".auth-time");

    // check if passed auth time
    (function checkAuthStatus() {
      var now_in_secs = Math.round(Date.now() / 1000);
      var last_auth_str = moment(last_auth_time*1000).fromNow();

      // update friendly date text 
      $auth_time.text(last_auth_str);

      // check against configured max auth time
      // set classes depending on result
      if(isPastAuthTime(now_in_secs - last_auth_time)) {
        $(".user-auth-status")
          .removeClass("user-auth-status--warning")
          .addClass("user-auth-status--reauth");
        $(".auth-time").text(passed_allowed_time_str);
        // if passed max auth time stop running
        return;
      } else if (isNearlyPastAuthTime(now_in_secs - last_auth_time)) {
        $(".user-auth-status")
          .removeClass("user-auth-status--reauth")
          .addClass("user-auth-status--warning");
      }
      // keep checking every 5s
      setTimeout(checkAuthStatus, 5000);
    })();

  });

}).call(this, jQuery, window);
