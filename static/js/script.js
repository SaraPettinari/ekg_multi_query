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
    //node_data.push({ id: in_data.nodes[n]['EventID'], properties: in_data.nodes[n] })
    node = in_data.nodes[n]
    g.setNode(node.EventID, { label: node.Activity, class: 'Event', shape: 'rect', data: node })
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
    //node_data.push({ id: in_data.nodes[n]['EventID'], properties: in_data.nodes[n] })
    node = data.nodes[n]
    nodes.push({ id: node.EventID, label: node.Activity, data: node })
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
    //node_data.push({ id: in_data.nodes[n]['EventID'], properties: in_data.nodes[n] })
    node = data.nodes[n]
    nodes.push({ data: { id: node.EventID, label: node.Activity.replaceAll("_", "\n"), color: node.color, node_data: node } })
  }

  edges = []
  for (e in data.edges) {
    edge = data.edges[e]
    edge_label = edge.edge_label
    edge_properties = edge.edge_properties
    //"edge_weight": 1,   "CorrelationType": "Message",
    edge_weight = edge_properties.edge_weight
    if(edge_weight > 1){
      edge_weight = edge_weight/2
    }
    edge_info = edge_weight + '(' + edge_properties.CorrelationType + ')\n:' + edge_label
    edges.push({ data: { source: edge.source, target: edge.destination, id: e, label: edge_info, color: edge.color, weight: edge_weight } })
  }

  elements = nodes.concat(edges)


  var cy = cytoscape({
    container: document.getElementById('cyto'), // container to render in
    elements: elements,
    style: [ // the stylesheet for the graph
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