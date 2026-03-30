from execution_context import ExecutionContext


class RiskScorer:
    def score(self, context: ExecutionContext) -> float:
        if "amount" in context.payload:
            amount = float(context.payload["amount"])
            return min(amount / 10_000_000, 1.0)
        return 0.1
