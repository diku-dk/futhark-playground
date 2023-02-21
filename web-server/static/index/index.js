var editor = ace.edit("code");
editor.setTheme("ace/theme/monokai");
editor.session.setMode("ace/mode/haskell");

api_host = "http://127.0.0.1:5000";


async function execute_code() {
    response = await fetch(api_host + "/run", {
        method: 'POST',
        body: editor.getValue()
    });

    response_json = await response.json();
    body = response_json["body"]["output"]
    error = response_json["error"]

    if (error) {
        document.getElementById("run_time").innerHTML = "<p> ERROR: "+error+"</p>"
        return;
    }
    

    document.getElementById("run_time").innerHTML = "<p>"+body["run_time"]+"</p>";
    document.getElementById("compile_time").innerHTML = "<p>"+body["compile_time"]+"</p>";
}

async function share_code() {
    response = await fetch(api_host + "/share", {
        method: 'POST',
        body: editor.getValue()
    });

    response_text = await response.text();
    window.location.pathname = response_text;
}