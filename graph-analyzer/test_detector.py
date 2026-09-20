"""
test_detector.py - Unit & Integration Tests for Graph Photo Recognition
"""

import unittest
from unittest.mock import patch, MagicMock
import io
from PIL import Image
from vision_detector import detect_graph_from_image, get_gemini_api_key
from app import app


class TestVisionDetector(unittest.TestCase):

    def setUp(self):
        # Create a valid test image in memory
        img = Image.new("RGB", (100, 100), color="white")
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="PNG")
        self.valid_png_bytes = img_byte_arr.getvalue()

    def test_corrupted_image_error(self):
        """Corrupted image bytes should return a clear error."""
        v, e, err = detect_graph_from_image(b"not an image", mime_type="image/png", api_key="dummy_key")
        self.assertEqual(v, "")
        self.assertEqual(e, "")
        self.assertIn("Invalid or corrupted image file", err)

    def test_missing_api_key_error(self):
        """Missing API key should return instructions with Google AI Studio link."""
        with patch.dict("os.environ", {}, clear=True):
            v, e, err = detect_graph_from_image(self.valid_png_bytes, mime_type="image/png", api_key="")
            self.assertEqual(v, "")
            self.assertEqual(e, "")
            self.assertIn("Gemini API key is required", err)
            self.assertIn("https://aistudio.google.com/", err)

    @patch("google.genai.Client")
    def test_mocked_gemini_detection_success(self, mock_client_cls):
        """Verifies that valid JSON response from Gemini Vision is formatted properly."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.text = '{"vertices": ["A", "B", "C", "D"], "edges": ["A-B", "A-C", "B-C", "C-D"]}'
        mock_client.models.generate_content.return_value = mock_response

        v_str, e_str, err = detect_graph_from_image(
            self.valid_png_bytes,
            mime_type="image/png",
            api_key="test_api_key_123"
        )

        self.assertIsNone(err)
        self.assertEqual(v_str, "A,B,C,D")
        self.assertEqual(e_str, "A-B\nA-C\nB-C\nC-D")

    @patch("google.genai.Client")
    def test_coordinate_normalization(self, mock_client_cls):
        """Verifies that coordinate vertices like (0, 3.5) are normalized to (0 3.5) without commas."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.text = '{"vertices": ["(0, 3.5)", "(7, 0)"], "edges": ["(0, 3.5)-(7, 0)"]}'
        mock_client.models.generate_content.return_value = mock_response

        v_str, e_str, err = detect_graph_from_image(
            self.valid_png_bytes,
            mime_type="image/png",
            api_key="test_api_key_123"
        )

        self.assertIsNone(err)
        self.assertEqual(v_str, "(0 3.5),(7 0)")
        self.assertEqual(e_str, "(0 3.5)-(7 0)")

    # -------------------------------------------------------------------------
    # Flask /detect-graph Route Tests
    # -------------------------------------------------------------------------
    def test_flask_detect_graph_no_file(self):
        client = app.test_client()
        response = client.post("/detect-graph", data={})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])
        self.assertIn("No image file provided", data["error"])

    def test_flask_detect_graph_missing_key(self):
        client = app.test_client()
        with patch.dict("os.environ", {}, clear=True):
            data = {
                "image": (io.BytesIO(self.valid_png_bytes), "graph.png")
            }
            response = client.post("/detect-graph", data=data, content_type="multipart/form-data")
            self.assertEqual(response.status_code, 400)
            res_json = response.get_json()
            self.assertFalse(res_json["success"])
            self.assertIn("Gemini API key is required", res_json["error"])

    @patch("app.detect_graph_from_image")
    def test_flask_detect_graph_success(self, mock_detect):
        mock_detect.return_value = ("A,B,C", "A-B\nB-C", None)

        client = app.test_client()
        data = {
            "image": (io.BytesIO(self.valid_png_bytes), "graph.png"),
            "apiKey": "mock_key"
        }
        response = client.post("/detect-graph", data=data, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 200)
        res_json = response.get_json()
        self.assertTrue(res_json["success"])
        self.assertEqual(res_json["vertices"], "A,B,C")
        self.assertEqual(res_json["edges"], "A-B\nB-C")


if __name__ == "__main__":
    unittest.main()
