import rdflib
from pyvis.network import Network
import json

# Initialize RDF graph
g = rdflib.Graph()

# Load the RDF data (replace with your actual TTL file)
file = 'bldg1.ttl'
g.parse(file, format="turtle")

g.bind("bldg1", "http://buildsys.org/ontologies/bldg1#")
g.bind("brick", "https://brickschema.org/schema/Brick#")
g.bind("ns4", "http://buildsys.org/ontologies/bldg1#bldg1.CHW.Pump1_Start/")
g.bind("owl", "http://www.w3.org/2002/07/owl#")
g.bind("rdfs", "http://www.w3.org/2000/01/rdf-schema#")
g.bind("ref", "https://brickschema.org/schema/Brick/ref#")
g.bind("unit", "http://qudt.org/vocab/unit/")

# Initialize Pyvis network
net = Network(directed=True)

# SPARQL query to extract main nodes and their relationships
query = """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX brick: <https://brickschema.org/schema/Brick#>
    SELECT DISTINCT ?subject ?predicate ?object
    WHERE {
        ?subject ?predicate ?object . 
        FILTER (?subject != ?object)  # Exclude self-referencing
    }
"""

# Execute the query to get nodes
results = g.query(query)

# Add nodes to the network
visited_nodes = set()

def rename_node(node):
    if isinstance(node, rdflib.term.URIRef):
        return g.qname(node)  # Shorten the URI for display
    elif isinstance(node, rdflib.term.Literal):
        return f"{node} ({node.datatype})"
    else:
        return str(node)

def rename_predicate(predicate):
    if isinstance(predicate, rdflib.term.URIRef):
        return g.qname(predicate)
    else:
        return str(predicate)

# Add initial nodes to the graph
for row in results:
    subject_name = str(row['subject'])
    object_name = str(row['object'])

    subject_label = rename_node(row['subject'])
    object_label = rename_node(row['object'])

    if isinstance(row['subject'], rdflib.term.URIRef) and subject_label not in visited_nodes:
        net.add_node(subject_label, title=subject_name, label=subject_label)
        visited_nodes.add(subject_label)

    if isinstance(row['object'], rdflib.term.URIRef) and object_label not in visited_nodes:
        net.add_node(object_label, title=object_name, label=object_label)
        visited_nodes.add(object_label)

# Add edges between named nodes
for row in results:
    predicate_name = rename_predicate(row['predicate'])
    subject_label = rename_node(row['subject'])
    object_label = rename_node(row['object'])

    if isinstance(row['subject'], rdflib.term.URIRef) and isinstance(row['object'], rdflib.term.URIRef):
        net.add_edge(subject_label, object_label, label=predicate_name)


print(f"Total number of nodes: {len(visited_nodes)}")

net.force_atlas_2based()

network_data = net.get_network_data()
nodes = network_data[0]
edges = network_data[1]

# Convert nodes and edges to JSON strings
nodes_json = json.dumps(nodes)
edges_json = json.dumps(edges)

# Generate and save the graph to an HTML file
net.show('ui3.html', notebook=False)

# HTML content embedding
html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Building Network</title>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        #graph-container {{ height: 800px; }}
        #query-container {{ margin-top: 20px; }}
        
        /* Style for the popup */
        #popup {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background-color: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 20px;
            border-radius: 10px;
            display: none;
            max-width: 80%;
            max-height: 80%;
            overflow: auto;
            z-index: 1000;
        }}
        
        #popup h2 {{
            margin-top: 0;
        }}
        
        #popup .close-btn {{
            position: absolute;
            top: 10px;
            right: 10px;
            color: white;
            font-size: 18px;
            cursor: pointer;
        }}
    </style>
</head>
<body>
    <h1>Interactive Building Graph</h1>
    <div id="graph-container"></div>

    <div id="query-container">
        <h2>SPARQL Query</h2>
        <textarea id="query-text" rows="10" cols="50" placeholder="Click a node to build your query..."></textarea><br>
        <button onclick="executeQuery()">Run Query</button>
        <div id="query-results"></div>
    </div>

    <div id="popup">
        <span class="close-btn" onclick="closePopup()">X</span>
        <h2>Node Information</h2>
        <p id="popup-text">Click on a node to view information.</p>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.js"></script>
    <script>
        var container = document.getElementById('graph-container');
        
        // Inject the JSON data for nodes and edges into the graph
        var data = {{
            nodes: {nodes_json},
            edges: {edges_json}
        }};

        data.nodes.forEach(function (node) {{
            node.color = '#6CC2A1';  // Set a base color for nodes
            if (node.label.includes("ZONE")) {{
                node.color = '#FF8C00';  // Highlight specific types of nodes with different colors
            }}
        }});

        data.edges.forEach(function (edge) {{
            edge.color = {{ color: "#848484" }};
            if (edge.label.includes("brick:isPartOf")) {{
                edge.color = {{ color: "#FF0000" }};  // Highlight specific types of nodes with different colors
            }}
        }});
        
        var options = {{
            "clickToUse": true,
            "physics": {{
                "enabled": true,
                "solver": "forceAtlas2Based", // This keeps the force-directed layout
                "timestep": 0.5, // Controls speed of the physics simulation
                "minVelocity": 0.1
            }},
            "interaction": {{
                "dragNodes": true,   // Enable dragging nodes
                "zoomView": true,    // Enable zooming
                "tooltipDelay": 200  // Tooltip delay for hover effect
            }},
            "layout": {{
                "improvedLayout": false
            }}
        }};
        
        var network = new vis.Network(container, data, options);
        
        // Function to display the popup with the node name
        function showPopup(nodeLabel) {{
            var popup = document.getElementById("popup");
            var screenWidth = window.innerWidth;  // Get the width of the screen
            var screenHeight = window.innerHeight; // Get the height of the screen
            var popupWidth = popup.offsetWidth; // Get the width of the popup
            var popupHeight = popup.offsetHeight;

            var left = (screenWidth - popupWidth) / 2;
            var top = (screenHeight - popupHeight) / 2;

            // Position the popup in the center of the screen
            popup.style.left = left + 'px';
            popup.style.top = top + 'px';

            // Set the text content of the popup
            //document.getElementById("popup-text").textContent = "You clicked on: " + nodeLabel;

            var popupText = "You clicked on: " + nodeLabel;

            // Fetch and display neighbors and relationships
            var neighbors = network.getConnectedNodes(nodeLabel);  // Get connected nodes
            //console.log("Neighbors to clicked: " + neighbors); 
            alert("Neighbors to clicked: " + neighbors);
            if (neighbors.length > 0) {{
                popupText += "\\nNeighbors:";
                neighbors.forEach(function(neighborId) {{
                    var neighborLabel = network.body.data.nodes.get(neighborId).label;
                    popupText += "\\n- " + neighborLabel;
            }});
            }} else {{
                popupText += "\\nNo neighbors found.";
            }}

            document.getElementById("popup-text").textContent = popupText;

            // Display the popup
            popup.style.display = "block";
        }}

        // Function to close the popup
        function closePopup() {{
            document.getElementById("popup").style.display = "none";
        }}

        // Add a click event listener for nodes to show their name/label in the popup
        network.on("click", function(event) {{
            var clickedNode = event.nodes[0];
            if (clickedNode) {{
                var nodeLabel = network.body.data.nodes.get(clickedNode).label;

                // Debugging: print node label to the console
                console.log("Node clicked: " + nodeLabel);  // Console log
                alert("Node clicked: " + nodeLabel);  // Alert for debugging

                showPopup(nodeLabel);
            }}
        }});

        document.body.addEventListener('click', function(event) {{
            const popup = document.getElementById('popup');
            if (!popup.contains(event.target)) {{
                closePopup();
            }}
        }});

    </script>
</body>
</html>
"""

# Save the HTML content to a file
with open("ui3.html", "w") as f:
    f.write(html_content)

































# # the actual page embedding 
# html_content = f"""
# <!DOCTYPE html>
# <html lang="en">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <title>Building Network</title>
#     <style>
#         body {{ font-family: Arial, sans-serif; }}
#         #graph-container {{ height: 800px; }}
#         #query-container {{ margin-top: 20px; }}
#     </style>
# </head>
# <body>
#     <h1>Interactive Building Graph</h1>
#     <div id="graph-container"></div>

#     <div id="query-container">
#         <h2>SPARQL Query</h2>
#         <textarea id="query-text" rows="10" cols="50" placeholder="Click a node to build your query..."></textarea><br>
#         <button onclick="executeQuery()">Run Query</button>
#         <div id="query-results"></div>
#     </div>

#     <script src="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.js"></script>
#     <script>
#         var container = document.getElementById('graph-container');
        
#         // Inject the JSON data for nodes and edges into the graph
#         var data = {{
#             nodes: {nodes_json},
#             edges: {edges_json}
#         }};
        
#         var options = {{
#             "clickToUse": true,
#             "physics": {{
#                 "enabled": true
#             }},
#             "layout": {{
#                 "improvedLayout": false  // Disable the improved layout here
#             }}
#         }};
        
#         var network = new vis.Network(container, data, options);

#         // Capture click event on node
#         network.on("click", function(properties) {{
#             var clickedNodeId = properties.nodes[0];
#             var query = buildSPARQLQuery(clickedNodeId);
#             document.getElementById("query-text").value = query;
#         }});

#         // Function to build SPARQL query dynamically based on the clicked node
#         function buildSPARQLQuery(node) {{
#             return `SELECT ?predicate ?object WHERE {{ <${{node}}> ?predicate ?object . }}`;
#         }}

#         function executeQuery() {{
#             var query = document.getElementById("query-text").value;
#             document.getElementById("query-results").innerHTML = "<p>Query executed: " + query + "</p>";
#         }}
#     </script>
# </body>
# </html>
# """

# # Save the HTML content to a file
# with open("ui3.html", "w") as f:
#     f.write(html_content)