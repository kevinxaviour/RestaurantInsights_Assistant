from .schemas import QueryPayload


class PayloadFormatter:
    def format(self, payload: QueryPayload) -> str:
        raise NotImplementedError


class JSONPayloadFormatter(PayloadFormatter):
    def format(self, payload: QueryPayload) -> str:
        return payload.model_dump_json(indent=2)


class TOONPayloadFormatter(PayloadFormatter):
    """
    TOON = Token Optimized Object Notation.
    Compact, line-based payload representation.
    """

    def format(self, payload: QueryPayload) -> str:
        lines = [
            "@TOON/v1",
            f"question={payload.question}",
            f"sql={payload.sql}",
            f"columns={'|'.join(payload.columns)}",
            f"row_count={payload.row_count}",
            "rows:",
        ]
        for index, row in enumerate(payload.rows, start=1):
            line = "|".join(str(value) for value in row)
            lines.append(f"r{index}={line}")
        return "\n".join(lines)
