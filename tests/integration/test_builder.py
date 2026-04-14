from evidentia.builder import build_wedge_app, validate_generated_app


def test_build_creates_app_manifest(tmp_path):
    spec = {"opportunity_id": "opp_001", "title": "Invoice chase automation", "approved": True}

    output_dir = build_wedge_app(spec, tmp_path)

    assert (output_dir / "package.json").exists()
    assert (output_dir / "app" / "page.tsx").exists()
    assert validate_generated_app(output_dir) is True
