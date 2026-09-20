"""
analyzer.py - Graph Analysis Module

This module is responsible for:
1. Parsing raw text inputs for vertices and edges (including coordinate points like (0 9) or (0, 3.5)).
2. Validating the input data (checking for empty inputs, bad formats, missing vertices,
   duplicate edges, and self-loops).
3. Constructing an undirected simple graph using NetworkX.
4. Calculating core graph-theory properties.

Author: Graph Analyzer Team
"""

import networkx as nx


def split_outside_brackets(text: str, delimiter: str) -> list[str]:
    """
    Splits `text` by `delimiter` only when the delimiter is NOT enclosed
    inside brackets (parentheses `()`, square brackets `[]`, or curly braces `{}`).

    Examples:
        split_outside_brackets('(0, 3.5), (7, 0)', ',')
        -> ['(0, 3.5)', '(7, 0)']

        split_outside_brackets('(0, 3.5)-(7, 0)', '-')
        -> ['(0, 3.5)', '(7, 0)']

        split_outside_brackets('(-1, 2)-(-3, 4)', '-')
        -> ['(-1, 2)', '(-3, 4)']
    """
    items = []
    current = []
    depth = 0
    i = 0
    n = len(text)
    delim_len = len(delimiter)

    while i < n:
        char = text[i]
        if char in "([{":
            depth += 1
            current.append(char)
            i += 1
        elif char in ")]}":
            if depth > 0:
                depth -= 1
            current.append(char)
            i += 1
        elif depth == 0 and text[i:i + delim_len] == delimiter:
            val = "".join(current).strip()
            if val:
                items.append(val)
            current = []
            i += delim_len
        else:
            current.append(char)
            i += 1

    val = "".join(current).strip()
    if val:
        items.append(val)

    return items


def parse_edge_endpoints(line: str) -> tuple[str, str] | None:
    """
    Extracts two vertex endpoints from an edge line.
    Handles:
    - Standard hyphen format: 'A-B', 'A - B', '0-1'
    - Coordinate points: '(0, 3.5)-(7, 0)', '(0 3.5)-(7 0)'
    - Negative coordinates: '(-1, 2)-(3, 4)'
    - Fallback comma/space format: '(0 3.5), (7 0)'
    """
    # 1. Try splitting on hyphen '-' outside brackets
    hyphen_parts = split_outside_brackets(line, "-")
    if len(hyphen_parts) == 2 and hyphen_parts[0] and hyphen_parts[1]:
        return hyphen_parts[0], hyphen_parts[1]

    # 2. Try splitting on double hyphen '--' outside brackets
    double_hyphen = split_outside_brackets(line, "--")
    if len(double_hyphen) == 2 and double_hyphen[0] and double_hyphen[1]:
        return double_hyphen[0], double_hyphen[1]

    # 3. Try splitting on comma ',' outside brackets (e.g. '(0 3.5), (7 0)')
    comma_parts = split_outside_brackets(line, ",")
    if len(comma_parts) == 2 and comma_parts[0] and comma_parts[1]:
        return comma_parts[0], comma_parts[1]

    return None


def parse_and_validate_graph(vertices_text: str, edges_text: str):
    """
    Parses and validates vertices and edges from user input.

    Parameters:
        vertices_text (str): Comma-separated list of vertices (e.g., "A, B, C, D" or "(0 3.5), (7 0)").
        edges_text (str): Line-separated list of edges (e.g., "A-B\nA-C" or "(0 3.5)-(7 0)").

    Returns:
        tuple: (vertices_list, edges_list, error_message)
    """
    # -------------------------------------------------------------------------
    # 1. Validate Vertices Input
    # -------------------------------------------------------------------------
    if not vertices_text or not vertices_text.strip():
        return [], [], "Vertices input cannot be empty. Please enter at least one vertex (e.g., A, B, C or (0 3.5), (7 0))."

    # Split by commas outside brackets (protects coordinates like (0, 3.5))
    raw_vertices = split_outside_brackets(vertices_text, ",")
    
    # Filter out empty entries
    vertices = [v.strip() for v in raw_vertices if v.strip()]

    if not vertices:
        return [], [], "No valid vertices found. Please provide vertex names (e.g., A, B, C)."

    # Check for duplicate vertices in the list
    seen_vertices = set()
    for v in vertices:
        if v in seen_vertices:
            return [], [], f"Duplicate vertex detected in vertex list: '{v}'."
        seen_vertices.add(v)

    # -------------------------------------------------------------------------
    # 2. Validate Edges Input
    # -------------------------------------------------------------------------
    if not edges_text or not edges_text.strip():
        return [], [], "Edges input cannot be empty. Please enter at least one edge (e.g., A-B)."

    edge_lines = [line.strip() for line in edges_text.splitlines() if line.strip()]

    if not edge_lines:
        return [], [], "No valid edges found. Please enter edges in the format 'Vertex1-Vertex2' (one per line)."

    edges = []
    seen_edges = set()

    for line_num, line in enumerate(edge_lines, start=1):
        endpoints = parse_edge_endpoints(line)

        if not endpoints:
            return [], [], (
                f"Invalid edge format on line {line_num}: '{line}'. "
                "Expected format is 'Vertex1-Vertex2' (e.g., A-B or (0 3.5)-(7 0))."
            )

        u, v = endpoints[0].strip(), endpoints[1].strip()

        # In a simple graph, self-loops are not allowed
        if u == v:
            return [], [], (
                f"Self-loop detected on line {line_num}: '{u}-{v}'. "
                "Self-loops are not allowed in a simple undirected graph."
            )

        # Ensure both vertices exist in the provided vertex list
        if u not in seen_vertices:
            return [], [], (
                f"Edge error on line {line_num}: Vertex '{u}' in edge '{u}-{v}' "
                "does not exist in the vertices list."
            )
        if v not in seen_vertices:
            return [], [], (
                f"Edge error on line {line_num}: Vertex '{v}' in edge '{u}-{v}' "
                "does not exist in the vertices list."
            )

        # In an undirected graph, (u, v) and (v, u) represent the same edge
        edge_key = tuple(sorted([u, v]))
        if edge_key in seen_edges:
            return [], [], (
                f"Duplicate edge detected on line {line_num}: '{u}-{v}'. "
                "Duplicate edges between the same pair of vertices are not allowed in a simple graph."
            )

        seen_edges.add(edge_key)
        edges.append((u, v))

    return vertices, edges, None


def analyze_graph(vertices: list, edges: list) -> dict:
    """
    Creates an undirected simple graph using NetworkX and computes its
    fundamental graph-theory properties.
    """
    G = nx.Graph()

    G.add_nodes_from(vertices)
    G.add_edges_from(edges)

    num_vertices = G.number_of_nodes()
    num_edges = G.number_of_edges()

    degree_dict = {node: G.degree(node) for node in vertices}
    degree_values = list(degree_dict.values())

    min_degree = min(degree_values) if degree_values else 0
    max_degree = max(degree_values) if degree_values else 0
    avg_degree = round(sum(degree_values) / num_vertices, 2) if num_vertices > 0 else 0

    is_connected = nx.is_connected(G) if num_vertices > 0 else False

    max_possible_edges = (num_vertices * (num_vertices - 1)) // 2
    is_complete = (num_edges == max_possible_edges)

    is_regular = (min_degree == max_degree)
    is_bipartite = nx.is_bipartite(G)

    cycle_basis = nx.cycle_basis(G)
    has_cycle = len(cycle_basis) > 0

    return {
        "num_vertices": num_vertices,
        "num_edges": num_edges,
        "degrees": degree_dict,
        "min_degree": min_degree,
        "max_degree": max_degree,
        "avg_degree": avg_degree,
        "is_connected": is_connected,
        "is_complete": is_complete,
        "is_regular": is_regular,
        "is_bipartite": is_bipartite,
        "has_cycle": has_cycle
    }
