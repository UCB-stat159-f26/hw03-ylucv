"""Assignment function length limits."""

import ast
from pathlib import Path

import pytest

import tennis_career


@pytest.mark.parametrize("path", list(Path(tennis_career.__file__).parent.glob("*.py")))
def test_function_lengths(path):
    source = path.read_text()
    lines = source.splitlines()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            body = lines[node.lineno - 1:node.end_lineno]
            count = sum(bool(line.strip()) and not line.lstrip().startswith("#")
                        for line in body)
            assert count <= 20, f"{path.name}:{node.name}: {count} lines"
