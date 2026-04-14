import os

from evidentia.models import DeploymentMetadata, ProductSpec


def can_deploy(spec: ProductSpec | dict) -> bool:
    approved = spec.approved if isinstance(spec, ProductSpec) else spec.get("approved")
    return approved is True


def ensure_live_tests_enabled() -> None:
    if os.getenv("EVIDENTIA_RUN_LIVE_TESTS") != "1":
        raise RuntimeError("live tests are disabled")


def build_deployment_metadata(
    spec: ProductSpec | dict,
    target: str = "vercel",
    deploy_result: dict | None = None,
) -> dict:
    validated_spec = spec if isinstance(spec, ProductSpec) else ProductSpec.model_validate(spec)
    if deploy_result is None:
        metadata = DeploymentMetadata(
            status="dry_run",
            target=target,
            project_id=validated_spec.opportunity_id,
            url=None,
            deployment_id=None,
            proof_level="dry-run",
            detail="No deploy adapter was invoked; this artifact is not live proof.",
        )
        return metadata.model_dump(mode="json")

    metadata = DeploymentMetadata(
        status="deployed",
        target=target,
        project_id=validated_spec.opportunity_id,
        url=deploy_result.get("url"),
        deployment_id=deploy_result.get("deployment_id"),
        proof_level="live",
        detail=deploy_result.get("detail"),
    )
    return metadata.model_dump(mode="json")
