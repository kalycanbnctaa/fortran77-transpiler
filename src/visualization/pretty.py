from __future__ import annotations

from typing import Any, Callable, Iterable

LabelFn = Callable[[Any], str]
ChildrenFn = Callable[[Any], Iterable[Any]]


def print_tree(
    root: Any,
    label_fn: LabelFn,
    children_fn: ChildrenFn,
    printer: Callable[[str], None] = print,
) -> None:
    printer(label_fn(root))
    _print_children(list(children_fn(root)), label_fn, children_fn, "", printer)


def _print_children(
    nodes: list[Any],
    label_fn: LabelFn,
    children_fn: ChildrenFn,
    prefix: str,
    printer: Callable[[str], None],
) -> None:
    count = len(nodes)
    for index, node in enumerate(nodes):
        is_last = index == count - 1
        connector = "└── " if is_last else "├── "
        printer(f"{prefix}{connector}{label_fn(node)}")
        extension = "    " if is_last else "│   "
        _print_children(list(children_fn(node)), label_fn, children_fn, prefix + extension, printer)