/**
 * Created by admin on 2/27/15.
 */
function httpRequest(method, server, path, params) {
    console.log('method: ' + method + ' path: ' + path + ' params: ' + params);

    var http = new XMLHttpRequest();

    http.onreadystatechange = function () {
        if (this.readyState == 4 && this.status == 200) {
            var jsonResponse = JSON.parse(http.responseText);
        }
        else {
            console.log("readyState: " + this.readyState);
            console.log("status: " + this.status);
            console.log("statusText: " + http.responseText);
        }
    }
    if (method && method.toUpperCase() == "GET") {
        //e.g. path == "subscribe", params == gid="gasdfsfsfssdfdsfs"
        http.open('GET', server + path + '?' + params);
        http.send();
    }
    else if ((method && method.toUpperCase() == "POST")) {
        http.open('POST', server + path);
        http.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
        http.send(params);
    }
}

function getDate() {
    var today = new Date();
    var dd = today.getDate();
    var mm = today.getMonth() + 1; //January is 0!
    var yyyy = today.getFullYear();

    if (dd < 10) {
        dd = '0' + dd
    }

    if (mm < 10) {
        mm = '0' + mm
    }

    today = mm + '/' + dd + '/' + yyyy;
    return today;
}