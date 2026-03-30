from ptag_parser import PTAGParser
from ptag_semantic import SemanticAnalyzer, ValidationIssue
from ptag_validator import PTAGValidator
from registry import RoleRegistry
from role_compiler import RoleCompiler


class RoleLoader:
    def __init__(self, registry: RoleRegistry) -> None:
        self.registry = registry
        self.parser = PTAGParser()
        self.validator = PTAGValidator()
        self.semantic = SemanticAnalyzer()
        self.compiler = RoleCompiler()

    def load(self, role_id: str):
        trusted_source = self.registry.load_source(role_id)
        parsed = self.parser.parse(trusted_source.source)
        self.validator.validate(parsed)
        semantic_document = self.semantic.analyze(parsed)
        semantic_document.headers["trusted_source_origin"] = trusted_source.source_origin
        semantic_document.headers["trusted_sha256"] = trusted_source.sha256
        semantic_document.headers["trusted_signed_by"] = trusted_source.signed_by
        semantic_document.headers["trusted_signature_mode"] = trusted_source.signature_mode
        semantic_document.headers["trusted_manifest_signature_status"] = trusted_source.manifest_signature_status
        semantic_document.headers["trusted_manifest_key_id"] = trusted_source.manifest_signature_key_id
        semantic_document.validation_issues.extend(self.validator.validate_semantic(semantic_document))
        if trusted_source.source_origin == "last_known_good":
            semantic_document.validation_issues.append(
                ValidationIssue(
                    severity="warning",
                    code="REGISTRY_FALLBACK_USED",
                    message=f"Role {role_id} loaded from last known good trusted cache.",
                    role_id=role_id,
                )
            )
        return self.compiler.compile(semantic_document)
