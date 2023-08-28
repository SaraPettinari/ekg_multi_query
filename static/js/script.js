/**
 * Supports sugiyama layout
 * Deprecated library
 * @param {*} in_data 
 */
function plot_graph(in_data) {
  var edge_data = in_data.edges
  var node_data = []

  const g = new dagreD3.graphlib.Graph({ multigraph: true }).setGraph({ rankdir: 'LR' })

  for (n in in_data.nodes) {
    //node_data.push({ id: in_data.nodes[n]['Event_Id'], properties: in_data.nodes[n] })
    node = in_data.nodes[n]
    g.setNode(node.Event_Id, { label: node.Activity, class: 'Event', shape: 'rect', data: node })
  }

  for (e in edge_data) {
    edg = edge_data[e]
    g.setEdge(edg.from, edg.to, { label: edg.label }) //d3.curveBasis
  }

  console.log(g)


  const data = {
    nodes: node_data,
    links: edge_data
  };

  var render = new dagreD3.render();


  // Set up an SVG group so that we can translate the final graph.
  var svg = d3.select("svg"),
    svgGroup = svg.append("g"),
    zoom = d3.zoom().on("zoom", function () {
      svgGroup.attr("transform", d3.event.transform);
    });
  svg.call(zoom);

  d3.selectAll('svg g')
    .on('click', function (d) {
      console.log('click on ' + d);
    });
  node = d3.selectAll('svg g')
  node.attr("height", 100)


  // Run the renderer. This is what draws the final graph.
  render(svgGroup, g);
}


/**
 * Does not support sugiyama layout
 * More intuitive library
 * @param {*} data 
 */
function draw(data) {
  nodes = []
  for (n in data.nodes) {
    //node_data.push({ id: in_data.nodes[n]['Event_Id'], properties: in_data.nodes[n] })
    node = data.nodes[n]
    nodes.push({ id: node.Event_Id, label: node.Activity, data: node })
  }

  var container = document.getElementById('networkx');
  var data = {
    nodes: nodes,
    edges: data.edges
  };
  var options = {
    nodes: {
      shape: 'box',
      color: {
        border: '#000000',
        background: '#ffffff'
      },
      shapeProperties: {
        borderRadius: 2
      },
      font: {
        size: 40
      }
    },
    physics: {
      enabled: false,
      hierarchicalRepulsion: {
        avoidOverlap: 1
      },
      stabilization: {
        enabled: true,
      },
    },
    layout: {
      improvedLayout: true,
      hierarchical: {
        enabled: true,
        direction: 'LR',
        sortMethod: "directed",
        nodeSpacing: 500,
        levelSeparation: 500,
        treeSpacing: 500,
      }
    },
    edges: {
      arrows: {
        to: true
      },
      color: {
        color: '#000000'
      },
      font: {
        background: '#ffffff',
        size: 30,
        color: '#000000'
      },
      smooth: {
        enabled: false,
      },
      selfReference: {
        size: 30,
      }
    }
  };

  //console.log(data)

  // initialize your network!
  var network = new vis.Network(container, data, options);
}

function generate_ekg(data) {
  nodes = []
  for (n in data.nodes) {
    //node_data.push({ id: in_data.nodes[n]['Event_Id'], properties: in_data.nodes[n] })
    node = data.nodes[n]
    nodes.push({ data: { id: node.Event_Id, label: node.Activity.replaceAll("_", "\n"), color: node.color, node_data: node, type: node.Type } })
  }

  edges = []
  for (e in data.edges) {
    edge = data.edges[e]
    edge_label = edge.edge_label
    edge_properties = edge.edge_properties
    //"edge_weight": 1,   "CorrelationType": "Message",
    edge_weight = edge_properties.edge_weight
    edge_info = edge_weight + '(' + edge_properties.CorrelationType + ')\n:' + edge_label
    if (edge_weight >= 4) {
      edge_weight = edge_weight / 20
    }
    edges.push({ data: { source: edge.source, target: edge.destination, id: e, label: edge_info, color: edge.color, weight: edge_weight } })
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
          'height': 100,
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
          'curve-style': 'segments',
          // 'curve-style': 'straight',
          //'curve-style': 'unbundled-bezier',
          'text-background-opacity': 1,
          'text-background-color': '#ffffff',
          'text-wrap': 'wrap',
          'loop-sweep': '-45deg',
          'control-point-step-size': 100,
          'segment-distances': "50 -50 20",

        }
      }
    ],
    /*
        layout: {
          name: 'dagre',
          directed: true,
          spacingFactor: 1.0,
          avoidOverlap: true,
          nodeDimensionsIncludeLabels: true,
          multigraph: true,
          nodeSep: 150, // the separation between adjacent nodes in the same rank
          edgeSep: 60, // the separation between adjacent edges in the same rank
          rankSep: 150, // the separation between each rank in the layout
          rankDir: 'LR', // 'TB' for top to bottom flow, 'LR' for left to right,
        }*/

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
      nodeDimensionsIncludeLabels: false, // Excludes the label when calculating node bounding boxes for the layout algorithm
      roots: undefined, // the roots of the trees
      depthSort: undefined, // a sorting function to order nodes at equal depth. e.g. function(a, b){ return a.data('weight') - b.data('weight') }
      animate: false, // whether to transition the node positions
      ready: undefined, // callback on layoutready
      stop: undefined, // callback on layoutstop
      transform: function (node, position) { return position; } // transform a given node position. Useful for changing flow direction in discrete layouts
    }
  });

  /* 
   var svgContent = cy.svg({ full: true })
   var blob = new Blob([svgContent], { type: "image/svg+xml;charset=utf-8" });
   saveAs(blob, "demo.svg");*/
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