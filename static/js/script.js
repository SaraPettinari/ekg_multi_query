function submit_graph(){
    doAjax("/get_graph", "POST", update_graph);
}

function update_graph(){
    var nodes = new vis.DataSet([
        { id: 1, label: 'Node 1' },
        { id: 2, label: 'Node 2' },
        { id: 3, label: 'Node 3' },
        { id: 4, label: 'Node 4' },
        { id: 5, label: 'Node 5' }
    ]);

    // create an array with edges
    var edges = new vis.DataSet([
        { from: 1, to: 3 },
        { from: 1, to: 2 },
        { from: 2, to: 4 },
        { from: 2, to: 5 }
    ]);

    // create a network
    var container = document.getElementById('result-graph');

    // provide the data in the vis format
    var data = {
        nodes: nodes,
        edges: edges
    };
    var options = {
        edges: {
            arrows: {
                to: true
            },
            color: {
                color: '#919191'
            },
            font: {
                background: '#ffffff',
                size: 20
            },
            smooth: {
                enabled: false,
            },
            selfReference: {
                size: 30,
            }
        },
        nodes: {
            shape: 'circle',
            color: {
                border: '#919191'
            },
            font: {
                size: 20
            }
        }
    }
    // initialize your network!
    var network = new vis.Network(container, data, options);
}


function openLink(e) {
    e.preventDefault()
    var request = { url: e.currentTarget.href }
    doAjax("/open-url", "POST", false, request)
}

// From https://gist.github.com/dharmavir/936328
function getHttpRequestObject() {
    // Define and initialize as false
    var xmlHttpRequst = false;

    // Mozilla/Safari/Non-IE
    if (window.XMLHttpRequest) {
        xmlHttpRequst = new XMLHttpRequest();
    }
    // IE
    else if (window.ActiveXObject) {
        xmlHttpRequst = new ActiveXObject("Microsoft.XMLHTTP");
    }
    return xmlHttpRequst;
}

function doAjax(url, method, responseHandler, data) {
    // Set the variables
    url = url || "";
    method = method || "GET";
    async = true;
    data = data || {};
    data.token = window.token;

    if (url == "") {
        alert("URL can not be null/blank");
        return false;
    }
    var xmlHttpRequest = getHttpRequestObject();

    // If AJAX supported
    if (xmlHttpRequest != false) {
        xmlHttpRequest.open(method, url, async);
        // Set request header (optional if GET method is used)
        if (method == "POST") {
            xmlHttpRequest.setRequestHeader("Content-Type", "application/json");
        }
        // Assign (or define) response-handler/callback when ReadyState is changed.
        xmlHttpRequest.onreadystatechange = responseHandler;
        // Send data
        xmlHttpRequest.send(JSON.stringify(data));
    }
    else {
        alert("Please use browser with Ajax support.!");
    }
}