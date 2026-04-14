import os


def can_deploy(spec: dict) -> bool:
    return spec.get("approved") is True


def ensure_live_tests_enabled() -> None:
    if os.getenv("EVIDENTIA_RUN_LIVE_TESTS") != "1":
        raise RuntimeError("live tests are disabled")


def build_deployment_metadata(spec: dict, target: str = "vercel") -> dict:
    slug = spec["opportunity_id"]
    return {
        "status": "deployed",
        "target": target,
        "project_id": slug,
        "url": f"https://{slug}.{target}.app",
    }
