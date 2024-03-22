var globG = ''
var globSVG = ''
var globSVGroup = ''


function generate_dagre(data) {
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

  const edgeColors = [
    '#1A1A1A', '#4B0082', '#8B0000', '#222222', '#800000', '#191970', '#333333', '#5C0120', '#444444', '#555555'
  ]

  var g = new dagre.graphlib.Graph({
    multigraph: true,
    compound: true,
    multiedgesep: 10,
    multiranksep: 50
  });

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

  // Get all the entities used in the aggregation
  let start_nodes = (nodes) => {
    let unique_values = [
      ...new Set(nodes
        .map((item) => item.e)
        .filter(
          (value) => value.Event_Id === value.activity
        )
        .map((item) => item.Type))
    ]
    return unique_values;
  };

  let entity_start_nodes = (nodes) => {
    let unique_values = [
      ...new Set(nodes
        .map((item) => item.e)
        .filter(
          (value) => value.Event_Id === value.activity
        )
        .map((item) => item.Event_Id)
      )
    ]
    return unique_values;
  };

  var uniqueEntityTypes = start_nodes(data.nodes);
  var uniqueEntities = entity_start_nodes(data.nodes);

  // Creating a dictionary from unique values mapped to colors
  const colorDictNodes = {};

  uniqueEntities.forEach((value, index) => {
    colorDictNodes[value] = nodeColors[index];
    if (index >= uniqueEntities.length) {
      colorDictNodes[value] = generateRandomHexColor()
    }
  });

  let entity_edges = (edge) => {
    let unique_values = [
      ...new Set(edge
        .map((item) => item.edge_properties.Type)
      )
    ]
    return unique_values;
  };

  var uniqueEntEdge = entity_edges(data.edges)
  const colorDictEdges = {};

  uniqueEntEdge.forEach((value, index) => {
    colorDictEdges[value] = edgeColors[index];
    if (index >= uniqueEntEdge.length) {
      colorDictEdges[value] = generateRandomHexColor()
    }
  });


  for (n in data.nodes) {
    node = data.nodes[n]['e']
    var entity = ''
    // check if it is a start node
    if (node.Event_Id == node.activity) {
      entity = node.Event_Id
      g.setNode(entity, { label: entity, type: 'start', labelStyle: "font-size: 22px", shape: 'circle', r: 15, style: 'fill: white' })
    }
    else {
      if (node.activity != null) {
        node.label = node.activity.replaceAll("_", " ")
      }

      // create dynamic event node variables 
      var nodeProps = { label: node.label, labelStyle: "font-size: 22px", shape: 'rect' }
      uniqueEntityTypes.forEach(entity => {
        nodeProps[entity] = node[entity]
        var this_ent = node[entity]
        nodeProps.style = 'fill: ' + colorDictNodes[this_ent]
        nodeProps.rx = nodeProps.ry = 5;
      });

      g.setNode(node.Event_Id, nodeProps)
    }
  }

  edges = []
  for (e in data.edges) {
    edge = data.edges[e]
    edge_label = edge.label

    var edge_weight = edge.edge_properties.edge_weight
    var edge_type = edge.edge_properties.Type


    if (edge_label == 'start') {
      g.setEdge(edge.from, edge.to, {
        label: '',
        name: 'start',
        curve: d3.curveLinear,
        class: 'dashed-edge'
      });
    } else {
      if (edge_weight > 20) { // filter less frequent behavior
        if (edge.from == edge.to && edge_type != 'robot') {
          continue
        }
        else if(edge.from.includes('weed_position?') && edge.to.includes('weed_position?')){
          continue
        }
        else if(edge.from.includes('tractor_position!') && edge.to.includes('tractor_position!')){
          continue
        }
        else if(edge.from.includes('closest_tractor?') && edge.to.includes('closest_tractor?')){
          continue
        }
        else {
        g.setEdge(edge.from, edge.to, {
          label: edge_type + ' : ' + edge_weight,
          name: edge.from + '-' + edge_label + '-' + edge.to,
          curve: d3.curveBasis,
          labelpos: 'c', // label position to center
          labeloffset: -10, // y offset to decrease edge-label separation
          visible: true,
          type: edge_type,
          style: 'stroke: ' + colorDictEdges[edge_type] + '; fill:none'
        })
      }}
    }
  }

  const svg = d3.select('#graph-container').append('svg');
  const svgGroup = svg.append('g');

  let initialZoomState;

  svg.selectAll("g.edgeLabel").select("rect")
    .style("fill", "yellow"); // Change this to the desired background color
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


function generateRandomHexColor() {
  // Generate random R, G, and B values
  var r = Math.floor(Math.random() * 256);
  var g = Math.floor(Math.random() * 256);
  var b = Math.floor(Math.random() * 256);

  // Convert decimal to hexadecimal
  var rHex = r.toString(16).padStart(2, '0');
  var gHex = g.toString(16).padStart(2, '0');
  var bHex = b.toString(16).padStart(2, '0');

  // Concatenate R, G, and B values to form a hex color
  var hexColor = '#' + rHex + gHex + bHex;

  return hexColor;
}
