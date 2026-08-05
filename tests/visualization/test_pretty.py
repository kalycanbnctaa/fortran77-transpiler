from __future__ import annotations

from src.visualization.pretty import print_tree


class Node:
    def __init__(self, label, children=None):
        self.label = label
        self.children = children or []


def label_fn(node):
    return node.label


def children_fn(node):
    return node.children


def render(root):
    lines = []
    print_tree(root, label_fn, children_fn, printer=lines.append)
    return lines


def test_single_node_has_no_children():
    root = Node("Root")
    assert render(root) == ["Root"]


def test_flat_children_use_correct_connectors():
    root = Node("Root", [Node("A"), Node("B"), Node("C")])
    assert render(root) == [
        "Root",
        "├── A",
        "├── B",
        "└── C",
    ]


def test_last_child_uses_elbow_connector():
    root = Node("Root", [Node("Only")])
    assert render(root) == ["Root", "└── Only"]


def test_nested_children_indent_with_pipe_when_not_last():
    root = Node("Root", [Node("A", [Node("A1"), Node("A2")]), Node("B")])
    assert render(root) == [
        "Root",
        "├── A",
        "│   ├── A1",
        "│   └── A2",
        "└── B",
    ]


def test_nested_children_indent_with_blank_when_last():
    root = Node("Root", [Node("A", [Node("A1")])])
    assert render(root) == [
        "Root",
        "└── A",
        "    └── A1",
    ]


def test_deeply_nested_tree():
    root = Node("Root", [Node("A", [Node("B", [Node("C")])])])
    assert render(root) == [
        "Root",
        "└── A",
        "    └── B",
        "        └── C",
    ]