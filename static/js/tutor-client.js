/**
 * Created by admin on 1/27/15.
 */

var appBaseUrl = "https://kx-tutor-hangout-app.appspot.com:";
function launchClientHangout(gid, subject) {
    var url = appBaseUrl + "/hangouts?gid=" + gid + '&subject=' + subject;
    window.open(url, "", "width=1002,height=700,location=0,menubar=0,scrollbars=1,status=1,resizable=0")
}

$(".launch-hangout").click(function () {
    gid = $(this).find(".gid").text();
    subject = $(this).find(".subject").text();
    launchClientHangout(gid, subject);
});

function reload() {
    window.location.reload();
};

$(function () { //reload page every 60 seconds
    reloadId = setInterval(function () {
        reload();
    }, 60000);

    // Stop reloading after 10 minutes
    setTimeout(function () {
        clearInterval(reloadId);
    }, 600000);
});


