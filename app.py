# -*- coding: utf-8 -*-
"""
Created on Mon Dec  9 21:41:58 2024

@author: aosho
"""

import streamlit as st
import networkx as nx
from pyvis.network import Network
import tempfile
import os
from statistics import mean

st.set_page_config(page_title="Social Capital Assessment Tool", layout="wide")

st.title("Social Capital Assessment Tool")

st.write("""This tool helps you understand the patterns and resources in your personal and professional networks—the “social capital” that can shape your opportunities, influence, and success. By mapping your contacts across various life domains, assessing the nature of those ties, and visualizing how your network is structured, you’ll gain insights into how you can build richer, more effective connections. The goal is to understand not only who you know, but also how well you know them, and how these ties fit together to help you achieve personal and organizational goals.""")

# Define the domains
domains = ["Family/Friends", "Work/Professional", "Education/Alumni",
           "Community/Volunteering", "Hobbies/Recreational Groups"]

st.header("Step 1: Enter Contacts")
st.write("""
Enter at least 3 contacts per domain (ideally 5–10). You can repeat the same individual across multiple domains if applicable—just ensure that you use the exact same spelling and punctuation each time.

**Domains:** These categories represent different spheres of your life (Family/Friends, Work/Professional, Education/Alumni, Community/Volunteering, Hobbies/Recreational Groups). Listing contacts in these domains helps you see where your resources come from.

**Tie Strength:** Indicates how close or frequent your interaction is. Strong ties might be close friends, mentors, or colleagues you speak with daily; weaker ties might be acquaintances or distant connections.

**Valence:** Captures the tone of the relationship. Positive ties offer support or goodwill, neutral ties are neither clearly supportive nor harmful, and negative ties might represent tension or conflict.

Start by selecting how many contacts you will enter for each domain. Then, enter their names and choose the tie strength and valence for each contact.
""")

# We'll store data in session state so it persists as user navigates
if 'contacts' not in st.session_state:
    st.session_state.contacts = []  # will store dicts like {name, domain, tie_strength, valence}

# Input forms for each domain
for d in domains:
    st.subheader(f"Domain: {d}")
    num_contacts = st.number_input(f"How many contacts do you want to add in '{d}'?", min_value=0, value=0, step=1, key=f"num_{d}")
    for i in range(int(num_contacts)):
        col1, col2, col3 = st.columns([3,1,2])
        name = col1.text_input(f"Name for contact #{i+1} in {d}", key=f"name_{d}_{i}")
        strength = col2.slider(f"Tie Strength {d} #{i+1}", 1, 5, 3, key=f"strength_{d}_{i}")
        valence = col3.selectbox(f"Valence {d} #{i+1}", ["Positive", "Neutral", "Negative"], key=f"valence_{d}_{i}")
        # Contacts will be added after pressing "Finalize Contact List"
    st.write("---")

if st.button("Finalize Contact List"):
    # Clear old contacts before adding new
    st.session_state.contacts = []
    for d in domains:
        num = st.session_state.get(f"num_{d}", 0)
        for i in range(int(num)):
            name = st.session_state.get(f"name_{d}_{i}", "").strip()
            if name:
                strength = st.session_state.get(f"strength_{d}_{i}", 3)
                valence = st.session_state.get(f"valence_{d}_{i}", "Neutral")
                st.session_state.contacts.append({
                    'name': name,
                    'domain': d,
                    'tie_strength': strength,
                    'valence': valence
                })
    st.success("Contacts finalized! Move on to next steps.")

if len(st.session_state.contacts) == 0:
    st.stop()

# Convert contacts to a unique set of names and track their attributes
st.header("Step 2: Review and Edit Contacts")
all_names = list({c['name'] for c in st.session_state.contacts})

# Aggregate domain memberships and tie attributes
contact_dict = {}
def most_common(lst):
    return max(set(lst), key=lst.count) if lst else "Neutral"

for c in st.session_state.contacts:
    name = c['name']
    if name not in contact_dict:
        contact_dict[name] = {
            'domains': set(),
            'tie_strengths': [],
            'valences': []
        }
    contact_dict[name]['domains'].add(c['domain'])
    contact_dict[name]['tie_strengths'].append(c['tie_strength'])
    contact_dict[name]['valences'].append(c['valence'])

for name in contact_dict:
    contact_dict[name]['avg_strength'] = round(mean(contact_dict[name]['tie_strengths']),2)
    contact_dict[name]['final_valence'] = most_common(contact_dict[name]['valences'])
    contact_dict[name]['domains'] = list(contact_dict[name]['domains'])

st.write("### Final Contact List")
for name, info in contact_dict.items():
    st.write(f"**{name}** | Domains: {', '.join(info['domains'])} | Avg Tie Strength: {info['avg_strength']} | Valence: {info['final_valence']}")

# Step 3: Connections between contacts
st.header("Step 3: Specify Connections Between Contacts")
st.write("""
Select pairs of contacts that know each other. This will define the edges in your network.

You can either:
- Add connections one pair at a time using the form below, OR
- Select multiple contacts at once to create all pairwise connections among them.
""")

if 'edges' not in st.session_state:
    st.session_state.edges = set()

# Single pair connection form
with st.form("connections_form"):
    st.write("**Add a Single Connection:**")
    contact_a = st.selectbox("Contact A", all_names)
    contact_b = st.selectbox("Contact B", all_names)
    add_connection = st.form_submit_button("Add Single Connection")
    if add_connection:
        if contact_a != contact_b:
            edge = tuple(sorted([contact_a, contact_b]))
            if edge not in st.session_state.edges:
                st.session_state.edges.add(edge)
                st.success(f"Added connection: {edge[0]} <--> {edge[1]}")
            else:
                st.info("This connection already exists.")
        else:
            st.warning("Cannot connect a contact to themselves.")

st.write("---")

# Multiple connections at once
st.write("**Add Multiple Connections at Once:**")
selected_contacts = st.multiselect(
    "Select multiple contacts to connect them all to each other",
    all_names
)

if st.button("Add Selected Connections"):
    from itertools import combinations
    if len(selected_contacts) < 2:
        st.warning("Select at least two contacts to form connections.")
    else:
        new_edges = 0
        for combo in combinations(selected_contacts, 2):
            edge = tuple(sorted(combo))
            if edge not in st.session_state.edges:
                st.session_state.edges.add(edge)
                new_edges += 1
        if new_edges > 0:
            st.success(f"Added {new_edges} new connections among the selected contacts.")
        else:
            st.info("All these connections already exist.")

st.write("### Current Connections")
if len(st.session_state.edges) == 0:
    st.write("No connections yet.")
else:
    for e in sorted(st.session_state.edges):
        st.write(f"{e[0]} <--> {e[1]}")


# Step 4: Compute Network Metrics
st.header("Step 4: Compute Network Measures")
if st.button("Compute Metrics"):
    G = nx.Graph()
    # Add nodes
    for name, info in contact_dict.items():
        G.add_node(name, domains=info['domains'], avg_strength=info['avg_strength'], valence=info['final_valence'])
    # Add edges
    for e in st.session_state.edges:
        G.add_edge(*e)

    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()
    max_edges = num_nodes*(num_nodes-1)/2 if num_nodes > 1 else 1
    density = num_edges / max_edges if max_edges > 0 else 0
    
    degree_dict = dict(G.degree())
    # Domain composition
    domain_counts = {}
    for _, data in G.nodes(data=True):
        for d in data['domains']:
            domain_counts[d] = domain_counts.get(d, 0) + 1

    st.subheader("Basic Metrics")
    st.write(f"**Size (Number of Contacts):** {num_nodes}")
    st.write(f"**Number of Connections:** {num_edges}")
    st.write(f"**Density:** {round(density,3)}")

    if num_nodes > 0:
        sorted_by_degree = sorted(degree_dict.items(), key=lambda x: x[1], reverse=True)
        st.write(f"**Most Connected Contact:** {sorted_by_degree[0][0]} with {sorted_by_degree[0][1]} connections")

    st.subheader("Domain Composition")
    total_contacts = sum(domain_counts.values()) if domain_counts else 1
    for d in domains:
        count = domain_counts.get(d, 0)
        pct = (count/total_contacts)*100
        st.write(f"{d}: {count} contacts ({round(pct,2)}%)")

    valence_counts = {"Positive":0, "Neutral":0, "Negative":0}
    for n in G.nodes:
        val = G.nodes[n]['valence']
        valence_counts[val] = valence_counts.get(val,0)+1

    st.subheader("Valence Distribution")
    for k,v in valence_counts.items():
        pct = (v/num_nodes)*100 if num_nodes>0 else 0
        st.write(f"{k}: {v} contacts ({round(pct,2)}%)")
        
    # Connectivity and Closure (Clustering)
    st.subheader("Connectivity")
    if num_nodes > 0:
        connected = nx.is_connected(G)
        num_components = nx.number_connected_components(G)
        if connected:
            st.write("Your network is fully connected (only one connected component).")
        else:
            st.write(f"Your network is not fully connected. It has {num_components} connected components.")
            components = list(nx.connected_components(G))
            largest_component = max(components, key=len) if components else set()
            st.write(f"The largest connected component has {len(largest_component)} contacts.")

        # Closure via average clustering coefficient
        avg_clustering = nx.average_clustering(G)
        st.subheader("Closure (Approx. via Clustering Coefficient)")
        st.write(f"The average clustering coefficient is {avg_clustering:.3f} (max = 1.0). Higher values suggest your contacts tend to know each other, indicating greater closure.")

    # Attempt Eigenvector Centrality, fallback to PageRank if AmbiguousSolution occurs
    if num_nodes > 0 and num_edges > 0:
        try:
            eigen_centrality = nx.eigenvector_centrality_numpy(G)
            closeness = nx.closeness_centrality(G)
            # Find node with highest eigenvector centrality
            top_eigen_node, _ = max(eigen_centrality.items(), key=lambda x: x[1])
            # Find node with lowest closeness centrality (furthest from everyone)
            furthest_node, _ = min(closeness.items(), key=lambda x: x[1])

            st.subheader("Additional Insights")
            st.write(f"**Central Influence:** {top_eigen_node} appears to be particularly well-connected to other well-connected individuals, suggesting a central position of influence in your network.")
            st.write(f"**Most Distant Contact:** {furthest_node} seems to be relatively far from most others, possibly on the periphery of your network.")
        
        except nx.AmbiguousSolution:
            # Fallback to PageRank if eigenvector centrality is ambiguous
            st.warning("Your network is disconnected in a way that eigenvector centrality is not uniquely defined. We'll use an alternative measure (PageRank) to identify a central contact.")
            page_rank = nx.pagerank(G)
            top_pr_node, _ = max(page_rank.items(), key=lambda x: x[1])

            st.subheader("Additional Insights (PageRank Fallback)")
            st.write(f"**Central Influence (Based on PageRank):** {top_pr_node} appears central when considering how influence might flow through the network.")
            # Distance measure isn't as directly interpreted from PageRank, so we can omit the "furthest" measure here
            # or just rely on closeness even if eigenvector failed:
            closeness = nx.closeness_centrality(G)
            furthest_node, _ = min(closeness.items(), key=lambda x: x[1])
            st.write(f"**Most Distant Contact:** {furthest_node} seems to be relatively far from most others, possibly on the periphery of your network.")

    # Step 5: Visualization
    st.header("Network Visualization")
    nt = Network(height="600px", width="100%", bgcolor="#FFFFFF", font_color="black", notebook=True)
    nt.force_atlas_2based()

    # Add nodes and edges to PyVis
    color_map = {
        "Positive":"#76c893",
        "Neutral":"#ffdd94",
        "Negative":"#ff6b6b"
    }

    for n,data in G.nodes(data=True):
        title = f"Name: {n}<br>Domains: {', '.join(data['domains'])}<br>Avg Strength: {data['avg_strength']}<br>Valence: {data['valence']}"
        node_color = color_map.get(data['valence'], "#d3d3d3")
        nt.add_node(n, label=n, title=title, color=node_color)
    for u,v in G.edges():
        nt.add_edge(u,v)
    
    # Generate and load the graph
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
        nt.save_graph(tmp_file.name)
        html_file = tmp_file.name

    # Display within Streamlit
    with open(html_file, 'r', encoding='utf-8') as f:
        html_data = f.read()
    st.components.v1.html(html_data, height=600, scrolling=True)

    # Cleanup temp file
    os.remove(html_file)

    st.header("Reflection Guidelines")
    st.markdown("""
**1. Shape of your network:**  
Look at the visualization. Are there clusters or is it fairly interconnected? Is this what you expected?

**2. Dimensions of your network:**  
Consider structure (e.g., density), composition (domain breakdown), and your main focus (which domain is largest?). Which dimension do you rely on most/least?

**3. Antecedents of your network:**  
Think about why it looks like this. Were some domains influenced by your job, school, family environment?

**4. Constraints of your network:**  
Identify areas with few connections, low valence, or low tie strength.

**5. Opportunities in your network:**  
Identify strong, positive clusters that might offer support or bridging opportunities.
""")
else:
    st.info("Click 'Compute Metrics' to see analysis and visualization.")
