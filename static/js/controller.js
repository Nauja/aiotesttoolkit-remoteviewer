$(document).ready(function() {
    var root = $("#messages");
    var socket = new WebSocket("ws://127.0.0.1:8082");
    socket.onopen = function (event) {
    };
    socket.onmessage = function (event) {
        root.append($("<p>", {"text": event.data}));
    }
});