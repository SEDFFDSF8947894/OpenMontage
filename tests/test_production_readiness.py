"""Offline tests for the production readiness checker."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import subprocess

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "production_readiness.py"
spec = importlib.util.spec_from_file_location("production_readiness", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class ReadinessTests(unittest.TestCase):
    def test_missing_project_files_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            checks = module.inspect(Path(directory))
            for filename in module.PROJECT_FILES:
                self.assertFalse(next(c for c in checks if c["name"] == filename)["ok"])

    def test_valid_video_metadata(self):
        payload = {"format": {"duration": "12.5"}, "streams": [{"codec_type": "video", "width": 1920, "height": 1080}, {"codec_type": "audio"}]}
        with patch.object(module.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, json.dumps(payload), "")):
            result = module.validate_video("example.mp4")
        self.assertTrue(result["ok"])
        self.assertTrue(result["has_audio"])
        self.assertEqual(result["width"], 1920)

    def test_no_video_stream_fails(self):
        payload = {"format": {"duration": "12"}, "streams": [{"codec_type": "audio"}]}
        with patch.object(module.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, json.dumps(payload), "")):
            self.assertFalse(module.validate_video("example.mp4")["ok"])

    def test_ffprobe_failure(self):
        with patch.object(module.subprocess, "run", return_value=subprocess.CompletedProcess([], 1, "", "bad file")):
            self.assertFalse(module.validate_video("broken.mp4")["ok"])

if __name__ == "__main__":
    unittest.main()
