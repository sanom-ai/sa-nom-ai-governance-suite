import pytest

from sa_nom_governance.ptag.ptag_ast import PTAGDocument, PTAGBlock
from sa_nom_governance.ptag.ptag_semantic import SemanticAnalyzer, SemanticDocument, RoleDefinition, AuthorityDefinition
from sa_nom_governance.ptag.ptag_validator import PTAGValidator


VALID_HEADERS = {
    "language": "PTAG",
    "module": "TEST",
    "version": "1.0.0",
    "owner": "EXEC_OWNER",
}


def test_validator_requires_headers() -> None:
    document = PTAGDocument(source="", headers={}, blocks=[])
    with pytest.raises(ValueError):
        PTAGValidator().validate(document)


def test_validator_requires_at_least_one_block() -> None:
    document = PTAGDocument(source="", headers=dict(VALID_HEADERS), blocks=[])
    with pytest.raises(ValueError, match="contains no blocks"):
        PTAGValidator().validate(document)


def test_validator_rejects_unsupported_block_types() -> None:
    document = PTAGDocument(
        source="",
        headers=dict(VALID_HEADERS),
        blocks=[PTAGBlock(name="unknown SAMPLE", body='title: "Bad"')],
    )

    with pytest.raises(ValueError, match="unsupported block types"):
        PTAGValidator().validate(document)


def test_semantic_validator_reports_policy_coverage_gap() -> None:
    document = PTAGDocument(
        source="",
        headers=dict(VALID_HEADERS),
        blocks=[
            PTAGBlock(name="role OPS", body='title: "Ops-AI"'),
            PTAGBlock(name="authority OPS", body='allow: restart_runtime'),
        ],
    )
    semantic = SemanticAnalyzer().analyze(document)
    issues = PTAGValidator().validate_semantic(semantic)
    assert len(issues) == 1
    assert issues[0].code == "POLICY_COVERAGE_GAP"
    assert issues[0].action == "restart_runtime"


def test_semantic_validator_accepts_constraint_action_coverage() -> None:
    document = PTAGDocument(
        source="",
        headers=dict(VALID_HEADERS),
        blocks=[
            PTAGBlock(name="role GOV", body='title: "Gov-AI"'),
            PTAGBlock(name="authority GOV", body='require human_override for approve_group_policy'),
            PTAGBlock(name="constraint GOV_BOUNDARY", body='require human_override for approve_group_policy'),
        ],
    )

    semantic = SemanticAnalyzer().analyze(document)
    issues = PTAGValidator().validate_semantic(semantic)

    assert issues == []


def test_semantic_validator_requires_authority_for_each_role() -> None:
    document = PTAGDocument(
        source="",
        headers=dict(VALID_HEADERS),
        blocks=[PTAGBlock(name="role GOV", body='title: "Gov-AI"')],
    )

    semantic = SemanticAnalyzer().analyze(document)

    with pytest.raises(ValueError, match="missing an authority block"):
        PTAGValidator().validate_semantic(semantic)


def test_semantic_validator_rejects_authority_for_unknown_role() -> None:
    semantic = SemanticDocument(
        headers=dict(VALID_HEADERS),
        roles={"GOV": RoleDefinition(role_id="GOV", fields={"title": "Gov-AI"})},
        authorities={
            "GOV": AuthorityDefinition(role_id="GOV", allow={"approve_policy"}),
            "OPS": AuthorityDefinition(role_id="OPS", allow={"review_audit"}),
        },
    )

    with pytest.raises(ValueError, match="unknown role"):
        PTAGValidator().validate_semantic(semantic)
