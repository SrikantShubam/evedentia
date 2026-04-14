import json
from pathlib import Path


def build_wedge_app(spec: dict, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    package_name = spec["title"].lower().replace(" ", "-")
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
        f"  return <main><h1>{spec['title']}</h1></main>;\n"
        "}\n",
        encoding="utf-8",
    )
    return output_dir


def validate_generated_app(output_dir: Path) -> bool:
    return (output_dir / "package.json").exists() and (output_dir / "app" / "page.tsx").exists()
