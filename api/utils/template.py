import os
from jinja2 import Environment, FileSystemLoader


def render_template(template_path: str, output_path: str, context: dict = None) -> str:
    """Renderiza um arquivo de template Jinja2 e grava o resultado no caminho de saída."""
    template_dir = os.path.dirname(os.path.abspath(template_path))
    template_file = os.path.basename(template_path)

    env = Environment(loader=FileSystemLoader(template_dir), autoescape=False)
    template = env.get_template(template_file)

    ctx = dict(os.environ) if context is None else {**os.environ, **context}
    rendered = template.render(ctx)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered)

    print(f"[Jinja2] Configuracao renderizada com sucesso em: {output_path}")
    return rendered


render = render_template
