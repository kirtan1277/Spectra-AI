"""
test_analyzer.py - Comprehensive Unit & Integration Tests for Graph Analyzer
"""

import unittest
from analyzer import parse_and_validate_graph, analyze_graph
from app import app


class TestGraphAnalyzer(unittest.TestCase):

    def test_example_graph(self):
        """Test the exact example from the user prompt."""
        vertices_text = "A,B,C,D"
        edges_text = "A-B\nA-C\nB-C\nC-D"

        vertices, edges, error = parse_and_validate_graph(vertices_text, edges_text)
        self.assertIsNone(error)
        self.assertEqual(vertices, ["A", "B", "C", "D"])
        self.assertEqual(len(edges), 4)

        result = analyze_graph(vertices, edges)
        self.assertEqual(result["num_vertices"], 4)
        self.assertEqual(result["num_edges"], 4)
        self.assertEqual(result["degrees"], {"A": 2, "B": 2, "C": 3, "D": 1})
        self.assertEqual(result["min_degree"], 1)
        self.assertEqual(result["max_degree"], 3)
        self.assertEqual(result["avg_degree"], 2.0)
        self.assertTrue(result["is_connected"])
        self.assertFalse(result["is_complete"])
        self.assertFalse(result["is_regular"])
        self.assertFalse(result["is_bipartite"])  # A-B-C forms a triangle (odd cycle)
        self.assertTrue(result["has_cycle"])

    def test_complete_graph(self):
        """Test a complete graph K_3."""
        v, e, err = parse_and_validate_graph("1, 2, 3", "1-2\n2-3\n1-3")
        self.assertIsNone(err)
        result = analyze_graph(v, e)
        self.assertTrue(result["is_complete"])
        self.assertTrue(result["is_regular"])
        self.assertTrue(result["is_connected"])
        self.assertTrue(result["has_cycle"])

    def test_bipartite_and_regular_graph(self):
        """Test C_4 (4-cycle), which is bipartite and 2-regular."""
        v, e, err = parse_and_validate_graph("A, B, C, D", "A-B\nB-C\nC-D\nD-A")
        self.assertIsNone(err)
        result = analyze_graph(v, e)
        self.assertTrue(result["is_bipartite"])
        self.assertTrue(result["is_regular"])
        self.assertTrue(result["has_cycle"])

    def test_coordinate_vertices_with_space(self):
        """Test coordinate vertices without commas, e.g. (0 9), (7 0)."""
        v, e, err = parse_and_validate_graph("(0 9), (7 0)", "(0 9)-(7 0)")
        self.assertIsNone(err)
        self.assertEqual(v, ["(0 9)", "(7 0)"])
        self.assertEqual(e, [("(0 9)", "(7 0)")])
        result = analyze_graph(v, e)
        self.assertEqual(result["num_vertices"], 2)
        self.assertEqual(result["num_edges"], 1)
        self.assertTrue(result["is_connected"])

    def test_coordinate_vertices_with_comma(self):
        """Test coordinate vertices with commas, e.g. (0, 3.5), (7, 0)."""
        v, e, err = parse_and_validate_graph("(0, 3.5), (7, 0)", "(0, 3.5)-(7, 0)")
        self.assertIsNone(err)
        self.assertEqual(v, ["(0, 3.5)", "(7, 0)"])
        self.assertEqual(e, [("(0, 3.5)", "(7, 0)")])
        result = analyze_graph(v, e)
        self.assertEqual(result["num_vertices"], 2)
        self.assertEqual(result["num_edges"], 1)
        self.assertTrue(result["is_connected"])

    # -------------------------------------------------------------------------
    # Validation & Error Handling Tests
    # -------------------------------------------------------------------------
    def test_empty_vertices(self):
        v, e, err = parse_and_validate_graph("", "A-B")
        self.assertIsNotNone(err)
        self.assertIn("Vertices input cannot be empty", err)

    def test_empty_edges(self):
        v, e, err = parse_and_validate_graph("A, B", "")
        self.assertIsNotNone(err)
        self.assertIn("Edges input cannot be empty", err)

    def test_invalid_edge_format_no_hyphen(self):
        v, e, err = parse_and_validate_graph("A, B", "AB")
        self.assertIsNotNone(err)
        self.assertIn("Invalid edge format", err)

    def test_invalid_edge_format_multiple_hyphens(self):
        v, e, err = parse_and_validate_graph("A, B, C", "A-B-C")
        self.assertIsNotNone(err)
        self.assertIn("Invalid edge format", err)

    def test_vertex_not_found(self):
        v, e, err = parse_and_validate_graph("A, B, C", "A-D")
        self.assertIsNotNone(err)
        self.assertIn("does not exist in the vertices list", err)

    def test_self_loop(self):
        v, e, err = parse_and_validate_graph("A, B", "A-A")
        self.assertIsNotNone(err)
        self.assertIn("Self-loop detected", err)

    def test_duplicate_edge_direct(self):
        v, e, err = parse_and_validate_graph("A, B", "A-B\nA-B")
        self.assertIsNotNone(err)
        self.assertIn("Duplicate edge detected", err)

    def test_duplicate_edge_reversed(self):
        v, e, err = parse_and_validate_graph("A, B", "A-B\nB-A")
        self.assertIsNotNone(err)
        self.assertIn("Duplicate edge detected", err)

    def test_duplicate_vertex_in_list(self):
        v, e, err = parse_and_validate_graph("A, B, A", "A-B")
        self.assertIsNotNone(err)
        self.assertIn("Duplicate vertex detected", err)

    # -------------------------------------------------------------------------
    # Flask Web Routes Tests
    # -------------------------------------------------------------------------
    def test_flask_index_route(self):
        client = app.test_client()
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Graph Analyzer", response.data)

    def test_flask_analyze_api_success(self):
        client = app.test_client()
        payload = {
            "vertices": "A,B,C,D",
            "edges": "A-B\nA-C\nB-C\nC-D"
        }
        response = client.post("/analyze", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["num_vertices"], 4)
        self.assertEqual(data["data"]["num_edges"], 4)

    def test_flask_analyze_api_error(self):
        client = app.test_client()
        payload = {
            "vertices": "A,B",
            "edges": "A-Z"
        }
        response = client.post("/analyze", json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])
        self.assertIn("does not exist", data["error"])


if __name__ == "__main__":
    unittest.main()
