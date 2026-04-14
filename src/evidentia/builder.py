import json
from pathlib import Path

from evidentia.models import ProductSpec


def _resolve_spec_title(spec: ProductSpec | dict) -> str:
    if isinstance(spec, ProductSpec):
        return spec.title
    title = spec.get("title") if isinstance(spec, dict) else None
    if not isinstance(title, str) or not title.strip():
        raise ValueError("spec title is required")
    return title


def build_wedge_app(spec: ProductSpec | dict, output_dir: Path) -> Path:
    title = _resolve_spec_title(spec)
    output_dir.mkdir(parents=True, exist_ok=True)
    package_name = title.lower().replace(" ", "-")
    package_json = {
        "name": package_name,
        "version": "0.1.0",
        "private": True,
        "scripts": {
            "dev": "next dev",
            "build": "next build",
            "start": "next start",
        },
    }
    (output_dir / "package.json").write_text(json.dumps(package_json, indent=2), encoding="utf-8")
    app_dir = output_dir / "app"
    app_dir.mkdir(exist_ok=True)
    (app_dir / "page.tsx").write_text(
        "export default function Page() {\n"
        f"  return <main><h1>{title}</h1></main>;\n"
        "}\n",
        encoding="utf-8",
    )
    return output_dir


def validate_generated_app(output_dir: Path) -> bool:
    return (output_dir / "package.json").exists() and (output_dir / "app" / "page.tsx").exists()
