from sa_nom_governance.ptag.ptag_parser import PTAGParser
from sa_nom_governance.ptag.ptag_semantic import SemanticAnalyzer


def test_parser_extracts_headers_and_blocks() -> None:
    source = """
language "PTAG"
module "TEST"
version "1.0.0"
owner "EXEC_OWNER"

role GOV {
  title: "GovAI-1"
}
"""
    document = PTAGParser().parse(source)
    assert document.headers["language"] == "PTAG"
    assert document.blocks[0].name == "role GOV"


def test_semantic_parser_extracts_authority_rules() -> None:
    source = """
language "PTAG"
module "TEST"
version "1.0.0"
owner "EXEC_OWNER"

role GOV {
  title: "GovAI-1"
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
  and risk_score <= 0.60
  then approve
  else escalate
}
"""
    document = PTAGParser().parse(source)
    semantic = SemanticAnalyzer().analyze(document)
    policy = semantic.policies["GOV_REVIEW"]

    assert semantic.roles["GOV"].fields["title"] == "GovAI-1"
    assert semantic.roles["GOV"].fields["stratum"] == 0
    assert "review_audit" in semantic.authorities["GOV"].allow
    assert "bypass_ethics" in semantic.authorities["GOV"].deny
    assert semantic.authorities["GOV"].require["approve_group_policy"] == ["human_override"]
    assert "GOV_BOUNDARY" in semantic.constraints
    assert "GOV_REVIEW" in semantic.policies
    assert policy.conditions == ["action == review_audit", "risk_score <= 0.60"]
    assert policy.then_actions == ["approve"]
    assert policy.else_actions == ["escalate"]
    assert policy.action_refs == {"review_audit"}


def test_semantic_parser_supports_case_insensitive_when_then_trigger_grammar() -> None:
    source = """
language "PTAG"
module "TRIGGER_TEST"
version "1.0.0"
owner "EXEC_OWNER"

role GOV {
  title: "GovAI-1"
}

authority GOV {
  allow: review_contract, approve_group_policy
}

policy CULTURAL_FRICTION_GUARD {
  WHEN action in [review_contract, approve_group_policy] AND region == "eu" AND audience == "external"
  THEN apply_policy_pack("EU_PRIVACY"), require_approval("legal"), log_evidence("gdpr_guard")
  ELSE rewrite_tone("diplomatic"), wait_human
}
"""
    document = PTAGParser().parse(source)
    semantic = SemanticAnalyzer().analyze(document)
    policy = semantic.policies["CULTURAL_FRICTION_GUARD"]

    assert policy.conditions == [
        'action in [review_contract, approve_group_policy]',
        'region == "eu"',
        'audience == "external"',
    ]
    assert policy.then_actions == [
        'apply_policy_pack("EU_PRIVACY")',
        'require_approval("legal")',
        'log_evidence("gdpr_guard")',
    ]
    assert policy.else_actions == [
        'rewrite_tone("diplomatic")',
        'wait_human',
    ]
    assert policy.action_refs == {"review_contract", "approve_group_policy"}
