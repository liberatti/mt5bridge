import os
from jinja2 import Environment, FileSystemLoader


def render_template(template_path: str, output_path: str, context: dict = None) -> str:
    """Renders a Jinja2 template file and writes the output to the destination path."""
    template_dir = os.path.dirname(os.path.abspath(template_path))
    template_file = os.path.basename(template_path)

    env = Environment(loader=FileSystemLoader(template_dir), autoescape=False)
    template = env.get_template(template_file)

    ctx = dict(os.environ) if context is None else {**os.environ, **context}
    rendered = template.render(ctx)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered)

    print(f"[Jinja2] Configuration rendered successfully at: {output_path}")
    return rendered


render = render_template


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python3 template.py <template_path> <output_path>")
        sys.exit(1)

    render_template(sys.argv[1], sys.argv[2])

