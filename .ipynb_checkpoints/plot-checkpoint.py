from libraries import *

plt.rcParams['font.family']  = 'DeJavu Serif'
plt.rcParams['font.serif']   = ['Times New Roman']
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype']  = 42

def plot_synth(V_P_S, V_P_R, E_P):
    # Define nodes, labels, and edges
    nodes_nrbs = [idx_q for idx_q,q in enumerate(V_P_R)]
    nodes_ps   = [idx_p+len(V_P_R) for idx_p,p in enumerate(V_P_S)]
    #nodes_hop  = [idx_l+len(V_P_R)+len(V_P_S)+idx_e_p*(len(L_pqi[idx_e_p])) for idx_e_p, e_p in enumerate(E_P) if (len(L_pqi[idx_e_p]) >= 2) for idx_l,l in enumerate(L_pqi[idx_e_p]) if idx_l <= len(L_pqi[idx_e_p])-1 ]
    edges = [(V_P_R.index(e_p.q), V_P_S.index(e_p.p)+len(V_P_R)) for e_p in E_P if (e_p.q in V_P_R) and (e_p.p in V_P_S)]
    edges.extend([(V_P_S.index(e_p.p)+len(V_P_R), V_P_S.index(e_p.q)+len(V_P_R)) for e_p in E_P if (e_p.p in V_P_S) and (e_p.q in V_P_S)])
    edges.extend([(V_P_R.index(e_p.p), V_P_R.index(e_p.q)) for e_p in E_P if (e_p.p in V_P_R) and (e_p.q in V_P_R)])

    # Create a graph
    G = nx.Graph()
    
    # Add nodes
    G.add_nodes_from(nodes_nrbs, bipartite=0)
    G.add_nodes_from(nodes_ps,   bipartite=1)
    
    # Add edges
    G.add_edges_from(edges)
    
    # Define custom labels with multiple numbers
    # Generate labels iteratively
    labels = {}
    for node in G.nodes():
        if node in nodes_nrbs:
            labels[node] = f'{node}'
        else:
            labels[node] = f'{node}'
    
    
    # Define node colors and sizes
    node_colors   = []
    node_sizes    = []
    node_size     = 1000
    border_colors = []
    border_sizes  = []
    border_size   = 1050
    
    for node in G.nodes():
        if node in nodes_nrbs:
            border_colors.append('black')
            border_sizes.append(border_size)
        elif node in nodes_ps:
            border_colors.append('black')
            border_sizes.append(border_size)
        else:
            border_colors.append('black')
            border_sizes.append(border_size)
    
    for node in G.nodes():
        if node in nodes_nrbs:
            node_colors.append('orange')
            node_sizes.append(node_size)
        elif node in nodes_ps:
            node_colors.append('skyblue')
            node_sizes.append(node_size)
        else:
            node_colors.append('black')
            node_sizes.append(node_size)
    
    # Draw the graph
    # Get the positions for the bipartite graph
    plt.figure(figsize=(5, 5))
    pos = nx.bipartite_layout(G, nodes_nrbs)
    
    # Draw the nodes with fill color (smaller size)
    nx.draw_networkx_nodes(
        G, pos,
        node_color=border_colors,
        node_size=border_size
    )
    
    # Draw the nodes with border (larger size)
    nx.draw_networkx_nodes(
        G, pos,
        node_color=node_colors,
        node_size=node_size,
        edgecolors='black'  # Set border color
    )
    
    # Draw the edges
    nx.draw_networkx_edges(G, pos)
    
    #nx.draw(G, pos, with_labels=False, node_color=node_colors, node_size=node_sizes, edge_color='black', linewidths=1, font_size=15)
    nx.draw_networkx_labels(G, pos, labels, font_size=10, font_color='black', verticalalignment='center', horizontalalignment='center')
    
    # Create custom legend
    red_patch = mpatches.Patch(color='orange', label='NR-BS Nodes')
    skyblue_patch = mpatches.Patch(color='skyblue', label='PS Nodes')
    
    plt.legend(handles=[red_patch, skyblue_patch], loc='upper center', fontsize=12)
    
    # Display and save the graph
    plt.savefig("plots/graph.svg", format="svg")
    plt.show()

def plot_brain(V_P_S, V_P_R, E_P):
    # Define nodes, labels, and edges
    nodes_nrbs = [idx_q for idx_q,q in enumerate(V_P_R)]
    nodes_ps   = [idx_p+len(V_P_R) for idx_p,p in enumerate(V_P_S)]
    #nodes_hop  = [idx_l+len(V_P_R)+len(V_P_S)+idx_e_p*(len(L_pqi[idx_e_p])) for idx_e_p, e_p in enumerate(E_P) if (len(L_pqi[idx_e_p]) >= 2) for idx_l,l in enumerate(L_pqi[idx_e_p]) if idx_l <= len(L_pqi[idx_e_p])-1 ]
    edges = [(V_P_R.index(e_p.q), V_P_S.index(e_p.p)+len(V_P_R)) for e_p in E_P if (e_p.q in V_P_R) and (e_p.p in V_P_S)]
    edges.extend([(V_P_S.index(e_p.p)+len(V_P_R), V_P_S.index(e_p.q)+len(V_P_R)) for e_p in E_P if (e_p.p in V_P_S) and (e_p.q in V_P_S)])
    edges.extend([(V_P_R.index(e_p.p), V_P_R.index(e_p.q)) for e_p in E_P if (e_p.p in V_P_R) and (e_p.q in V_P_R)])
    
    # Create a graph
    G = nx.Graph()
    
    # Add nodes
    #G.add_nodes_from(nodes_nrbs, bipartite=0)
    #G.add_nodes_from(nodes_ps,   bipartite=1)
    G.add_nodes_from(nodes_nrbs)
    G.add_nodes_from(nodes_ps)
    
    # Add edges
    G.add_edges_from(edges)
    
    # Define custom labels with multiple numbers
    # Generate labels iteratively
    labels = {}
    
    # Define node colors and sizes
    node_colors   = []
    node_sizes    = []
    node_size     = 60
    border_colors = []
    border_sizes  = []
    border_size   = 70
    
    for node in G.nodes():
        if node in nodes_nrbs:
            border_colors.append('black')
            border_sizes.append(border_size)
        elif node in nodes_ps:
            border_colors.append('black')
            border_sizes.append(border_size)
    
    for node in G.nodes():
        if node in nodes_nrbs:
            node_colors.append('#FF0000')
            node_sizes.append(node_size)
        elif node in nodes_ps:
            node_colors.append('skyblue')
            node_sizes.append(node_size)
            
    
    
    # Draw the graph
    # Get the positions for the bipartite graph
    plt.figure(figsize=(4, 4))
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)  # Adjust margins
    
    # Alternative layouts:
    pos = nx.kamada_kawai_layout(G)
    
    # Draw the nodes with border (larger size)
    nx.draw_networkx_nodes(
        G, pos,
        node_color=border_colors,
        node_size=25,
        edgecolors='black'  # Set border color
    )
    
    # Draw the nodes with fill color (smaller size)
    nx.draw_networkx_nodes(
        G, pos,
        node_color=node_colors,
        node_size=20
    )
    
    # Draw the edges
    nx.draw_networkx_edges(G, pos)
    nx.draw_networkx_labels(G, pos, labels, font_size=15, font_color='red', verticalalignment='center', horizontalalignment='center')
    
    # Create custom legend
    red_patch = mpatches.Patch(color='#FF0000', label='NR-BS')
    skyblue_patch = mpatches.Patch(color='skyblue', label='PS')
    
    plt.legend(handles=[red_patch, skyblue_patch], loc='upper left', fontsize=14)
    
    # Display and save the graph
    plt.savefig("plots/graph_large.svg", format="svg", bbox_inches='tight', pad_inches=0)
    plt.show()
    
    print(len(nodes_nrbs))
    print(len(nodes_ps))
    print(len(edges))