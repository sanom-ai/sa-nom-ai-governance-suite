from sa_nom_governance.ptag.ptag_parser import PTAGParser
from sa_nom_governance.ptag.ptag_semantic import SemanticAnalyzer


def test_parser_extracts_headers_and_blocks() -> None:
    source = """
language \"PTAG\"
module \"TEST\"
version \"1.0.0\"
owner \"EXEC_OWNER\"

role GOV {
  title: \"GovAI-1\"
}
"""
    document = PTAGParser().parse(source)
    assert document.headers["language"] == "PTAG"
    assert document.blocks[0].name == "role GOV"


def test_semantic_parser_extracts_authority_rules() -> None:
    source = """
language \"PTAG\"
module \"TEST\"
version \"1.0.0\"
owner \"EXEC_OWNER\"

role GOV {
  title: \"GovAI-1\"
  stratum: 0
}

authority GOV {
  allow: review_audit, emergency_stop
  deny: bypass_ethics
  require human_override for approve_group_policy
}

constraint GOV_BOUNDARY {
  forbid GOV to bypass_ethics
}

policy GOV_REVIEW {
  when action == review_audit
  then approve
}
"""
    document = PTAGParser().parse(source)
    semantic = SemanticAnalyzer().analyze(document)

    assert semantic.roles["GOV"].fields["title"] == "GovAI-1"
    assert semantic.roles["GOV"].fields["stratum"] == 0
    assert "review_audit" in semantic.authorities["GOV"].allow
    assert "bypass_ethics" in semantic.authorities["GOV"].deny
    assert semantic.authorities["GOV"].require["approve_group_policy"] == ["human_override"]
    assert "GOV_BOUNDARY" in semantic.constraints
    assert "GOV_REVIEW" in semantic.policies
