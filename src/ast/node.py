from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Node:
    line: int = field(default=0, kw_only=True, compare=False)

    def accept(self, visitor):
        method_name = f"visit_{type(self).__name__}"
        visitor_method = getattr(visitor, method_name, None)
        if visitor_method is None:
            return visitor.generic_visit(self)
        return visitor_method(self)