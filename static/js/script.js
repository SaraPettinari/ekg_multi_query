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
        border: '#919191',
        background: '#00ccff'
      },
      font: {
        size: 20
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
      improvedLayout: false,
      hierarchical: {
        enabled: true,
        direction: 'LR',
        sortMethod: "directed",
        nodeSpacing: 200,
        levelSeparation: 500,
        treeSpacing: 500,
      }
    },
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
    }
  };

  //console.log(data)

  // initialize your network!
  var network = new vis.Network(container, data, options);
}
