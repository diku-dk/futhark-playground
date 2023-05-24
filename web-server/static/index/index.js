var editor = ace.edit("code");
editor.setShowPrintMargin(false);
editor.setTheme("ace/theme/monokai");
editor.session.setMode("ace/mode/futhark");

api_host = "http://playground.futhark-lang.org";

document.addEventListener("DOMContentLoaded", function(){
    params = new URLSearchParams(window.location.search);
    if (params.has('backend')) {
        document.getElementById("select_backend").value = params.get("backend");
    }
    if (params.has('version')) {
        document.getElementById("select_version").value = params.get("version");
    }

    currentCache = localStorage.getItem(window.location.pathname);
    if (currentCache == null) {
        document.getElementById("reset_button").disabled = true;
        return;
    }
    editor.setValue(currentCache);
    document.getElementById("reset_button").disabled = false;
});

editor.session.on('change', function(delta) {
    localStorage.setItem(window.location.pathname, editor.getValue());
    document.getElementById("reset_button").disabled = false;
});

function update_view_link(hash) {
    document.getElementById("expand_button").setAttribute("href", "./view/"+hash);
}

function update_url_uuid(uuid) {
    new_url = window.location.protocol + "//" + window.location.host + "/" + uuid + window.location.search;
    update_view_link(uuid);
    window.history.pushState({path: new_url}, '', new_url);
}

async function execute_code() {
    document.getElementById("literate").innerText = "Loading...";
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
        document.getElementById("literate").innerText = "ERROR: " + error;
        return;
    }

    document.getElementById("compile_time").innerText = body["compile_time"];
    literate_md_url = body["literate"];
    document.getElementById("literate").setAttribute("src", window.location.protocol + "//" + window.location.host + "/" + literate_md_url);
    uuid = response_json["body"]["uuid"];
    update_url_uuid(uuid);
    document.getElementById("reset_button").disabled = true;
}

async function share_code() {
    response = await fetch(api_host + "/share", {
        method: 'POST',
        body: editor.getValue()
    });

    response_text = await response.text();
    
    update_url_uuid(response_text);
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

function reset_code() {
    localStorage.removeItem(window.location.pathname);
    document.getElementById("reset_button").disabled = true;
    location.reload();
}