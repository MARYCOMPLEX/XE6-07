from datetime import UTC, datetime

import pytest

from app.contracts import ArtifactKind, ArtifactRef, JobKind, JobResult, JobState
from app.contracts.workflow import WorkflowEvent, WorkflowEventKind, WorkflowSource
from app.schemas.common import CursorPage


def test_artifact_and_job_enums_cover_printing_contracts() -> None:
    assert ArtifactKind.model_3mf.value == "model_3mf"
    assert JobKind.printability_check.value == "printability_check"


def test_artifact_ref_excludes_transient_storage_details() -> None:
    artifact = ArtifactRef(artifact_id="asset-1", kind=ArtifactKind.model_3mf)

    assert "download_url" not in type(artifact).model_fields
    assert "provider" not in type(artifact).model_fields


def test_contract_payloads_are_deeply_immutable() -> None:
    source = {"nested": {"values": [1, 2]}}
    result = JobResult(
        job_id="job-1",
        kind=JobKind.printability_check,
        status=JobState.succeeded,
        output=source,
    )
    event = WorkflowEvent(
        event_id="event-1",
        kind=WorkflowEventKind.job_succeeded,
        source=WorkflowSource.audit,
        project_id="project-1",
        occurred_at=datetime.now(UTC),
        data=source,
    )

    source["nested"]["values"].append(3)  # type: ignore[index, union-attr]

    assert result.output == {"nested": {"values": (1, 2)}}
    assert event.data == {"nested": {"values": (1, 2)}}
    with pytest.raises(TypeError):
        result.output["new"] = "value"  # type: ignore[index]
    assert '"values":[1,2]' in result.model_dump_json()


def test_contract_rejects_unfreezable_payload_values() -> None:
    # 可变的自定义对象不能潜入契约，否则事后改动它会污染已构造的“不可变”契约。
    class Box:
        def __init__(self) -> None:
            self.items = [1, 2]

    with pytest.raises((TypeError, ValueError)):
        JobResult(
            job_id="job-x",
            kind=JobKind.printability_check,
            status=JobState.succeeded,
            output={"box": Box()},  # type: ignore[dict-item]
        )


def test_contract_preserves_immutable_scalar_and_nested_contract() -> None:
    # datetime 等不可变标量与已冻结的嵌套契约应正常保留，不被冻结逻辑误伤。
    artifact = ArtifactRef(artifact_id="asset-1", kind=ArtifactKind.model_3mf)
    completed = datetime.now(UTC)
    result = JobResult(
        job_id="job-y",
        kind=JobKind.printability_check,
        status=JobState.succeeded,
        artifacts=(artifact,),
        completed_at=completed,
    )

    assert result.completed_at == completed
    assert result.artifacts[0].artifact_id == "asset-1"


def test_cursor_page_serializes_public_cursor_names() -> None:
    page = CursorPage[str](items=["model-1"], next_cursor="cursor", has_more=True)

    assert page.model_dump(by_alias=True) == {
        "items": ["model-1"],
        "nextCursor": "cursor",
        "hasMore": True,
    }
