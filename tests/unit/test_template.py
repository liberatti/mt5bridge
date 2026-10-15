import os
import tempfile
import pytest

from utils.template import render_template


@pytest.mark.unit
class TestTemplateRendering:
    def test_render_template_basic(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            template_path = os.path.join(tmpdir, "test.j2")
            output_path = os.path.join(tmpdir, "output.ini")

            with open(template_path, "w", encoding="utf-8") as f:
                f.write("Server={{ SERVER }}\nPort={{ PORT }}\n")

            rendered = render_template(
                template_path, output_path, context={"SERVER": "TestBroker", "PORT": 5000}
            )

            assert "Server=TestBroker" in rendered
            assert "Port=5000" in rendered
            assert os.path.exists(output_path)

            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert content == rendered
