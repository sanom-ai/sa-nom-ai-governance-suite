from ptag_ast import PTAGBlock, PTAGDocument


class PTAGParser:
    """Minimal parser for the flat development workspace."""

    HEADER_KEYS = {"language", "module", "version", "owner", "context"}

    def parse(self, source: str) -> PTAGDocument:
        source = source.lstrip("\ufeff")
        lines = [line.rstrip() for line in source.splitlines() if line.strip()]
        document = PTAGDocument(source=source)
        current_block_name: str | None = None
        current_body: list[str] = []

        for line in lines:
            line = line.lstrip("\ufeff")
            if current_block_name is None and any(line.startswith(f"{key} ") for key in self.HEADER_KEYS):
                key, value = line.split(" ", 1)
                document.headers[key] = value.strip().strip('"')
                continue

            if line.endswith("{"):
                current_block_name = line[:-1].strip()
                current_body = []
                continue

            if line == "}":
                if current_block_name is not None:
                    document.blocks.append(PTAGBlock(name=current_block_name, body="\n".join(current_body)))
                current_block_name = None
                current_body = []
                continue

            if current_block_name is not None:
                current_body.append(line)

        return document
