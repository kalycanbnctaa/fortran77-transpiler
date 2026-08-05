from __future__ import annotations

from dataclasses import dataclass, field

from .scope import Scope, SemanticError
from .symbol import ParamInfo, Symbol, SymbolKind


@dataclass(slots=True)
class ProcedureSignature:
    name: str
    kind: SymbolKind
    param_types: list[ParamInfo] = field(default_factory=list)
    return_type: str = ""
    line: int = 0


class SymbolTable:
    def __init__(self) -> None:
        self._scopes: dict[str, Scope] = {}
        self._procedures: dict[str, ProcedureSignature] = {}
        self._common_members: dict[str, dict[str, list[Symbol]]] = {}

    def create_scope(self, name: str) -> Scope:
        scope = Scope(name)
        self._scopes[name.upper()] = scope
        return scope

    def scope_for(self, name: str) -> Scope:
        scope = self._scopes.get(name.upper())
        if scope is None:
            raise SemanticError(f"No scope registered for '{name}'")
        return scope

    def all_scopes(self) -> list[Scope]:
        return list(self._scopes.values())

    def register_procedure(self, signature: ProcedureSignature) -> None:
        key = signature.name.upper()
        if key in self._procedures:
            raise SemanticError(
                f"'{signature.name}' is already declared as a procedure", signature.line
            )
        self._procedures[key] = signature

    def procedure(self, name: str) -> ProcedureSignature | None:
        return self._procedures.get(name.upper())

    def procedures(self) -> list[ProcedureSignature]:
        return list(self._procedures.values())

    def add_common_members(
        self, block_name: str, subprogram_name: str, symbols: list[Symbol]
    ) -> None:
        key = block_name.upper()
        self._common_members.setdefault(key, {})[subprogram_name] = symbols

    def common_blocks(self) -> dict[str, dict[str, list[Symbol]]]:
        return self._common_members