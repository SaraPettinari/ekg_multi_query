var globcy = ''; // to store the cytoscape object

/**
 * Generation of the layout for showing the Event Knowledge Graph
 * @param {*} data : dictionary with nodes and edges
 */
function generate_ekg(data) {
  // creation of nodes list
  nodes = []
  for (n in data.nodes) {
    node = data.nodes[n]
    nodes.push({
      data: {
        id: node.Event_Id,
        label: node.Activity.replaceAll("_", "\n"),
        color: node.color,
        node_data: node,
        type: node.Type
      }
    })
  }

  // creation of edges list
  edges = []
  for (e in data.edges) {
    edge = data.edges[e]
    edge_label = edge.edge_label
    edge_properties = edge.edge_properties
    edge_weight = edge_properties.edge_weight
    edge_info = edge_weight + '(' + edge_properties.CorrelationType + ')\n:' + edge_label
    if (edge_weight >= 4) {
      edge_weight = 4 // to avoid edges too thick
    }
    else if (edge_weight == undefined) {
      continue
    }
    edges.push({
      data: {
        source: edge.source,
        target: edge.destination,
        id: e,
        label: edge_info,
        color: edge.color,
        weight: edge_weight
      }
    })
  }

  elements = nodes.concat(edges)

  /* FIND FIRST PROCESS NODE
  const incomingEdges = {};

  edges.forEach(edge => {
    const targetNode = edge.data.target;
    if (!incomingEdges[targetNode]) {
      incomingEdges[targetNode] = [];
    }
    incomingEdges[targetNode].push(edge.data.source);
  });

  console.log(incomingEdges)

  const nodesWithNoIncomingEdges = [];

  edges.forEach(edge => {
    const sourceNode = edge.data.source;
    if (!incomingEdges[sourceNode]) {
      nodesWithNoIncomingEdges.push(sourceNode);
    }
  });

  console.log(nodesWithNoIncomingEdges)
*/
  var cy = cytoscape({
    container: document.getElementById('cyto'), // container to render in
    elements: elements,
    style: [ // the stylesheet for the graph
      {
        selector: 'node[type="HiddenNode"]',
        style: {
          'shape': 'round-tag',
        }
      },
      {
        selector: 'node',
        style: {
          'height': 80,
          'width': 100,
          'background-color': 'data(color)' || '#666666',
          'label': 'data(label)',
          'font-size': 20,
          'color': '#ffffff',
          'text-wrap': 'wrap',
          'text-halign': 'center',
          'text-valign': 'center'
        }
      },

      {
        selector: 'edge',
        style: {
          'label': 'data(label)',
          'width': 'data(weight)' || 1,
          'line-color': 'data(color)',
          'target-arrow-color': 'data(color)',
          'target-arrow-shape': 'triangle',
          //'curve-style': 'segments',
          'curve-style': 'bezier',
          'text-background-opacity': 1,
          'text-background-color': '#ffffff',
          'text-wrap': 'wrap',
          'loop-sweep': '-45deg',
          'control-point-step-size': 100,
          'segment-distances': "50 -50 20",

        }
      }
    ],
    layout: {
      name: 'breadthfirst',
      fit: true, // whether to fit the viewport to the graph
      directed: true, // whether the tree is directed downwards (or edges can point in any direction if false)
      padding: 30, // padding on fit
      circle: false, // put depths in concentric circles if true, put depths top down if false
      grid: false, // whether to create an even grid into which the DAG is placed (circle:false only)
      spacingFactor: 3, // positive spacing factor, larger => more space between nodes (N.B. n/a if causes overlap)
      boundingBox: undefined, // constrain layout bounds; { x1, y1, x2, y2 } or { x1, y1, w, h }
      avoidOverlap: true, // prevents node overlap, may overflow boundingBox if not enough space
      nodeDimensionsIncludeLabels: true, // Excludes the label when calculating node bounding boxes for the layout algorithm
    }
  });

  globcy = cy;
}

/**
 * Download the EKG as svg image
 */
function downloadEKG() {
  var svgContent = globcy.svg({ full: true })
  var blob = new Blob([svgContent], { type: "image/svg+xml;charset=utf-8" });
  let datetime = new Date().toJSON();
  saveAs(blob, datetime + "_ekg.svg");
}


function showOptions() {
  var checkBox = document.getElementById("communication_link");
  var slider = document.getElementById("msg_slider_div");
  if (checkBox.checked == true) {
    slider.style.display = "block";
  } else {
    slider.style.display = "none";
  }
}

function showNav() {
  var x = document.getElementById("sliders");
  if (x.style.display === "none") {
    x.style.display = "block";
  } else {
    x.style.display = "none";
  }

  var x = document.getElementById("analysis");
  if (x.style.display === "none") {
    x.style.display = "block";
  } else {
    x.style.display = "none";
  }
}