from sa_nom_governance.ptag.ptag_semantic import SemanticDocument


class RoleCompiler:
    """Adapts PTAG semantic documents into runtime-friendly role documents."""

    def compile(self, semantic_document: SemanticDocument) -> SemanticDocument:
        return semantic_document
