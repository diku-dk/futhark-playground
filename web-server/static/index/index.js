var editor = ace.edit("code");
editor.setTheme("ace/theme/monokai");
editor.session.setMode("ace/mode/haskell");

api_host = "http://127.0.0.1:5000";

document.addEventListener("DOMContentLoaded", function(){
    params = new URLSearchParams(window.location.search);
    if (params.has('backend')) {
        document.getElementById("select_backend").value = params.get("backend");
    }
    if (params.has('version')) {
        document.getElementById("select_version").value = params.get("version");
    }
});

function display_element(id, display) {
    document.getElementById(id).style.display = display ? "block" : "none";
}


async function execute_code() {
    response = await fetch(api_host 
        + "/run?backend="+document.getElementById("select_backend").value
        +"&version="+document.getElementById("select_version").value, {
        method: 'POST',
        body: editor.getValue()
    });

    response_json = await response.json();
    body = response_json["body"]["output"]
    error = response_json["error"]

    if (error) {
        document.getElementById("run_time").innerText = "ERROR: " + error;
        return;
    }

    if (!body.hasOwnProperty("literate")) {
        document.getElementById("run_time").innerText = body["run_time"];
        document.getElementById("compile_time").innerText = body["compile_time"];
        document.getElementById("output").style.flex = 1;

        display_element("literate", false)
        display_element("run_time", true)
        display_element("compile_time", true)
        return;
    }

    display_element("run_time", false)
    display_element("compile_time", false)
    document.getElementById("output").style.flex = 2;
    display_element("literate", true)
    literate_md_url = body["literate"]
    document.getElementById("literate").setAttribute("src", window.location.protocol + "//" + window.location.host + "/" + literate_md_url)
}

async function share_code() {
    response = await fetch(api_host + "/share", {
        method: 'POST',
        body: editor.getValue()
    });

    response_text = await response.text();
    new_url = window.location.protocol + "//" + window.location.host + "/" + response_text + window.location.search;
    window.history.pushState({path: new_url}, '', new_url);
    navigator.clipboard.writeText(window.location.toString());
    alert("Copied shareable URL to clipboard")
}


function addUrlParam(key, val) {
    url = window.location;
    params = new URLSearchParams(url.search);
    params.set(key, val);
    new_url = window.location.protocol + "//" + window.location.host + window.location.pathname + '?' + params.toString();
    window.history.pushState({path: new_url}, '', new_url);
}


function selected_backend() {
    backend = document.getElementById("select_backend").value;
    addUrlParam("backend", backend);
}

function selected_version() {
    version = document.getElementById("select_version").value;
    addUrlParam("version", version);
}