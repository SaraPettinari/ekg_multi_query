var globG = ''
var globSVG = ''
var globSVGroup = ''


function generate_dagre(data) {
  console.log('data', data)
  nodes = []
  const nodeColors = [
    '#87CEFA', // Light sky blue
    '#FFDAB9', // Peach puff
    '#98FB98', // Pale green
    '#E0FFFF',  // Light cyan
    '#ADD8E6', // Light blue
    '#F0E68C', // Khaki
    '#F08080', // Light coral
    '#FFD1DC', // Pastel pink
    '#FFA07A', // Light salmon
    '#FFB6C1', // Light pink
  ];

  var g = new dagre.graphlib.Graph({
    multigraph: true,
    compound: true,
    multiedgesep: 10,
    multiranksep: 50
  });

  console.log(g)

  // Set an object for the graph label
  g.setGraph({ rankdir: 'TB', nodesep: 25 });

  // Default to assigning a new object as a label for each new edge.
  g.setDefaultEdgeLabel(function () { return {}; });

  dagre.layout(g);

  // Function to retrieve unique values associated with the entities
  const uniqueNodesEnt = new Set();
  const uniqueEdgesEnt = new Set();
  const uniqueEnt = new Set();

  // Create entity list
  data.edges.forEach(item => uniqueEdgesEnt.add(item.edge_properties.Type));
  var edges_entities = Array.from(uniqueEdgesEnt);

  data.nodes.forEach(item => {
    edges_entities.forEach(element => {
      if (element in item.e)
        uniqueNodesEnt.add(element);
    });
  });

  var nodes_entities = Array.from(uniqueNodesEnt);
  nodes_entities.forEach(item => {
    data.nodes.forEach(this_item => uniqueEnt.add(this_item.e[item]));
  });

  var entities = Array.from(uniqueEnt)
  
  // Creating a dictionary from unique values mapped to pastel colors
  const colorDict = {};
  nodes_entities.forEach((value, index) => {
    colorDict[value] = nodeColors[index];
  });


  for (n in data.nodes) {
    //node_data.push({ id: in_data.nodes[n]['Event_Id'], properties: in_data.nodes[n] })
    node = data.nodes[n]['e']

    if (node.activity != null) {
      node.label = node.activity.replaceAll("_", " ")
    }

    g.setNode(node.Event_Id, { label: node.label, robot: node.robot, labelStyle: "font-size: 22px" })
  }

  //g.setNode('drone', { type: 'start', label: 'drone' });
  //g.setNode('tractor_1', { type: 'start', label: 'tractor_1' });
  //g.setNode('tractor_2', { type: 'start', label: 'tractor_2' });
  //g.setNode('msg_id', { type: 'start', label: 'msg_id' });


  g.nodes().forEach(function (v) {
    var node = g.node(v);
    var robot = node.robot
    console.log(node)
    if (node.label === 'start') {
      node.shape = 'circle';
      node.r = 15; // Radius of the circle
      node.style = 'fill: white';
    } else if (node.label === 'end') {
      node.shape = 'circle';
      node.r = 15;
      node.style = 'fill: #E55451';
    }
    else {
      node.shape = 'rect';
      node.style = 'fill: ' + colorDict[robot]
    }

    if (node.type) {
      node.shape = 'circle';
      node.r = 15; // Radius of the circle
      node.style = 'fill: white';
    }

    // Round the corners of the nodes
    node.rx = node.ry = 5;
  });

  edges = []
  for (e in data.edges) {
    edge = data.edges[e]
    edge_label = edge.label

    var edge_weight = edge.edge_properties.edge_weight
    var edge_type = edge.edge_properties.Type

    //if (edge_weight > 20) { // filter less frequent behavior
    /*if (edge.from == edge.to && edge_type != 'robot') {
      continue
    }*/

    g.setEdge(edge.from, edge.to, {
      label: edge_type + ' : ' + edge_weight,
      name: edge.from + '-' + edge_label + '-' + edge.to,
      curve: d3.curveBasis,
      labelpos: 'c', // label position to center
      labeloffset: -10, // y offset to decrease edge-label separation
      visible: true,
      type: edge_type
    })
    //}
  }

  /*
    g.setEdge('drone', 'c_takeoff_drone', {
      label: '',
      name: 'START',
      curve: d3.curveLinear,
      class: 'dashed-edge'
    });
  
    g.setEdge('tractor_1', 'c_weed_position?_tractor_1', {
      label: '',
      name: 'START',
      curve: d3.curveLinear,
      class: 'dashed-edge'
    });
  
    g.setEdge('tractor_2', 'c_weed_position?_tractor_2', {
      label: '',
      name: 'START',
      curve: d3.curveLinear,
      class: 'dashed-edge'
    });
  */
  //g.removeEdge('c_land_drone','c_takeoff_drone');
  //g.removeEdge('c_stop_tractor_1','c_weed_position?_tractor_1');
  //g.removeEdge('c_stop_tractor_2','c_weed_position?_tractor_2');

  //g.graph().nodesep = 100;

  console.log(g)

  const svg = d3.select('#graph-container').append('svg');
  const svgGroup = svg.append('g');

  let initialZoomState;

  // Create a zoom behavior
  const zoom = d3.zoom().on('zoom', (event) => {
    svgGroup.attr('transform', event.transform);
  });

  // Apply zoom to the SVG container
  svg.call(zoom);

  initialZoomState = d3.zoomTransform(svg.node());


  // Render the graph
  const render = new dagreD3.render();
  render(svgGroup, g);

  addOnFunctionalities(svgGroup, g)

  globG = g
  globSVGroup = svgGroup
  globSVG = svg


  // Change the graph direction
  d3.select('#toggle-button').on('click', function () {

    const currentDirection = g.graph().rankdir; // Get the current direction

    // Toggle the direction
    const newDirection = currentDirection === 'TB' ? 'LR' : 'TB';

    const currentZoomState = d3.zoomTransform(svg.node());

    // Update the graph with the new direction
    g.setGraph({ rankdir: newDirection, nodesep: 25 });
    dagre.layout(g);


    // Render the updated graph
    svg.selectAll('*').remove(); // Clear the existing SVG content
    const svgGroup = svg.append('g');

    // Create a zoom behavior
    const zoomChange = d3.zoom().on('zoom', (event) => {
      svgGroup.attr('transform', event.transform);
    });

    // Apply zoom to the SVG container
    svg.call(zoomChange);

    const render = new dagreD3.render();

    render(svgGroup, g);
    addOnFunctionalities(svgGroup, g)

  });
}

/**
* Graph interactions handler
* @param {*} svgGroup 
* @param {*} g 
*/
function addOnFunctionalities(svgGroup, g) {
  // Add unique IDs to the edge paths during rendering
  svgGroup.selectAll('g.edgePath path')
    .attr('id', (edgeId) => g.edge(edgeId).name);

  // Handle double click on nodes
  svgGroup.selectAll('g.node')
    .on('dblclick', function (event, nodeId) {
      // Reset the style of all edges
      event.stopPropagation(); // Prevent click event from triggering as well

      // Reset the style of all edges
      svgGroup.selectAll('g.edgePath path').style('stroke', '#999');

      // Highlight outgoing edges from the double-clicked node
      g.outEdges(nodeId).forEach(edge => {
        svgGroup.selectAll(`g.edgePath path[id="${g.edge(edge).name}"]`).style('stroke', '#E55451');
      });
      // Highlight incoming edges from the double-clicked node
      g.inEdges(nodeId).forEach(edge => {
        svgGroup.selectAll(`g.edgePath path[id="${g.edge(edge).name}"]`).style('stroke', 'lightgreen');
      });
    });

  const contextMenu = d3.select('#context-menu');
  const contextMenuOptions = contextMenu.selectAll('.context-menu-option');

  // Handle right-click on nodes to show the context menu
  svgGroup.selectAll('g.node')
    .on('contextmenu', function (event, nodeId) {
      document.getElementById("activity_id").setAttribute("value", nodeId)

      event.preventDefault(); // Prevent the default context menu
      event.stopPropagation(); // Stop propagation to prevent triggering other click events

      // Position the context menu next to the node
      contextMenu.style('left', event.layerX + 5 + 'px');
      contextMenu.style('top', event.layerY + 'px');

      // Show the context menu
      contextMenu.style('display', 'block');
      console.log(contextMenu)

      // Handle context menu option clicks
      contextMenuOptions.on('click', function (optionId) {
        // Perform actions based on the selected option
        var option = optionId.srcElement.id

        option = option.replace('-menu', '')

        // Hide the context menu
        contextMenu.style('display', 'none');

        // Trigger the backend
        document.getElementById(option).setAttribute("value", true)
        console.log(document.getElementById(option))
        document.getElementById("see_" + option + "_graph").click();
      });
    });

  // Hide the context menu on document click
  d3.select(document).on('click', function () {
    contextMenu.style('display', 'none');
    svgGroup.selectAll('g.edgePath path').style('stroke', '#999');

  });
}

function downloadGraph() {
  const svg = d3.select('#graph-container svg');

  // Clone the SVG element
  const clonedSvg = svg.node().cloneNode(true);

  // Append the cloned SVG to the document
  document.body.appendChild(clonedSvg);

  // Download SVG
  const svgData = new XMLSerializer().serializeToString(clonedSvg);
  const blob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'graph.svg';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);

  // Remove the cloned SVG from the document
  document.body.removeChild(clonedSvg);
}


/**
 * Hides edges from the graph
 */
function toggleEdgeVisibility() {
  var originalGraph = globG
  var svgGroup = globSVGroup
  var svg = globSVG

  var elements = document.querySelectorAll('[id$="_msg"]');
  var listEdges = []

  // Loop through the elements
  elements.forEach(function (element) {
    if (element.checked) {
      var edge_id = element.id
      var id = edge_id.replace('_msg', '')
      listEdges.push(id)
    }
  });

  var newGraph = new dagreD3.graphlib.Graph().setGraph({});

  // Clone nodes
  originalGraph.nodes().forEach(function (node) {
    newGraph.setNode(node, originalGraph.node(node));
  });

  // Clone edges
  originalGraph.edges().forEach(function (edgeObj) {
    var edge = originalGraph.edge(edgeObj);
    if (!listEdges.includes(edge.type)) {
      newGraph.setEdge(edgeObj.v, edgeObj.w, edge, edgeObj.name);
    }
  });


  console.log(newGraph.edges())

  // Render the updated graph
  svg.selectAll('*').remove(); // Clear the existing SVG content
  svgGroup = svg.append('g');

  // Create a zoom behavior
  const zoomChange = d3.zoom().on('zoom', (event) => {
    svgGroup.attr('transform', event.transform);
  });

  // Apply zoom to the SVG container
  svg.call(zoomChange);

  const render = new dagreD3.render();

  render(svgGroup, newGraph);
  addOnFunctionalities(svgGroup, newGraph)
}