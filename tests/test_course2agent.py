import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from course2agent.builder import build_course
from course2agent.runtime import CourseIndex


class Course2AgentTest(unittest.TestCase):
    def test_build_search_and_generated_server(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            materials = temp_path / "materials"
            materials.mkdir()
            (materials / "syllabus.md").write_text(
                "# BIO101\nLearning objective: explain selective permeability.\n",
                encoding="utf-8",
            )
            (materials / "lecture-01.md").write_text(
                "# Membranes\nPhospholipids form a bilayer. Cholesterol changes membrane fluidity.\n",
                encoding="utf-8",
            )
            output = build_course([materials], temp_path / "bio101-agent", "BIO101")
            index = CourseIndex(output)
            results = index.search("cholesterol membrane fluidity")
            self.assertTrue(results)
            self.assertIn("Lecture 01", results[0]["citation"])
            self.assertEqual(index.overview()["source_count"], 2)

            completed = subprocess.run(
                [sys.executable, str(output / "mcp" / "server.py"), "--self-test"],
                check=True,
                capture_output=True,
                text=True,
            )
            report = json.loads(completed.stdout)
            self.assertTrue(report["ok"])

    def test_notebook_cells_keep_locators(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            notebook = temp_path / "week-2.ipynb"
            notebook.write_text(
                json.dumps(
                    {
                        "cells": [
                            {"cell_type": "markdown", "source": ["# Gradient descent\n", "Choose a learning rate."]},
                            {"cell_type": "code", "source": ["theta = theta - alpha * gradient"]},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            output = build_course([notebook], temp_path / "ml-agent", "ML101")
            index = CourseIndex(output)
            results = index.search("learning rate")
            self.assertEqual(results[0]["citation"], "[Week 2, markdown cell 1]")
            self.assertEqual(index.overview()["sources"][0]["role"], "notebook")

    def test_chinese_query_uses_cjk_tokens(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            lecture = temp_path / "lecture-中文.md"
            lecture.write_text(
                "胆固醇可以缓冲细胞膜流动性，在高温时限制磷脂运动。",
                encoding="utf-8",
            )
            output = build_course([lecture], temp_path / "cn-agent", "细胞生物学")
            results = CourseIndex(output).search("细胞膜流动性")
            self.assertTrue(results)
            self.assertIn("Lecture 中文", results[0]["citation"])


if __name__ == "__main__":
    unittest.main()
