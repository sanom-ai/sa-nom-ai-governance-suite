import pytest

from sa_nom_governance.ptag.ptag_ast import PTAGDocument, PTAGBlock
from sa_nom_governance.ptag.ptag_semantic import SemanticAnalyzer
from sa_nom_governance.ptag.ptag_validator import PTAGValidator


def test_validator_requires_headers() -> None:
    document = PTAGDocument(source="", headers={}, blocks=[])
    with pytest.raises(ValueError):
        PTAGValidator().validate(document)


def test_semantic_validator_reports_policy_coverage_gap() -> None:
    document = PTAGDocument(
        source="",
        headers={"language": "PTAG", "module": "TEST", "version": "1.0.0", "owner": "EXEC_OWNER"},
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
