"""
What a source file actually *does*, as opposed to which words it contains.

A word match cannot tell `from deepface import DeepFace` from a comment, a regex or a
sentence of law text that mentions emotions. This module separates them:

  imports      libraries the file really imports            {module: line}
  identifiers  names used in code (never comments/strings)  [(name, line)]
  code_lines   source with comments and string bodies blanked, same line numbering

Python is parsed with `ast`. JavaScript/TypeScript and other C-style or Ruby files use a
small lexer: good enough to drop comments and strings, not a full parser.
Nothing here imports or runs the scanned code.
"""

from __future__ import annotations

import ast
import io
import re
import tokenize
from dataclasses import dataclass, field


@dataclass
class Facts:
    imports: dict[str, int] = field(default_factory=dict)
    identifiers: list[tuple[str, int]] = field(default_factory=list)
    code_lines: list[str] = field(default_factory=list)
    # (assigned name, string value, line) for literals inside e.g. FEATURES = ["gender", ...]
    assigned_strings: list[tuple[str, str, int]] = field(default_factory=list)
    # (first line, last line) of each function, for "is there a human step nearby?"
    functions: list[tuple[int, int]] = field(default_factory=list)


def _blank(lines: list[str], start: tuple[int, int], end: tuple[int, int]) -> None:
    """Replace the (row, col) span with spaces. Rows are 1-based."""
    for row in range(start[0], end[0] + 1):
        if row - 1 >= len(lines):
            return
        s = lines[row - 1]
        a = start[1] if row == start[0] else 0
        b = end[1] if row == end[0] else len(s)
        lines[row - 1] = s[:a] + " " * max(0, min(b, len(s)) - a) + s[b:]


def _python(text: str) -> Facts | None:
    try:
        tree = ast.parse(text)
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (SyntaxError, ValueError, tokenize.TokenError, RecursionError):
        return None
    f = Facts(code_lines=text.split("\n"))
    blank_types = {tokenize.COMMENT, tokenize.STRING, getattr(tokenize, "FSTRING_MIDDLE", None)}
    for t in tokens:
        if t.type in blank_types:
            _blank(f.code_lines, t.start, t.end)

    for node in ast.walk(tree):
        line = getattr(node, "lineno", 0)
        if isinstance(node, ast.Import):
            for a in node.names:
                f.imports.setdefault(a.name, line)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            f.imports.setdefault(node.module, line)
            for a in node.names:  # `from google import genai`
                f.imports.setdefault(f"{node.module}.{a.name}", line)
        elif isinstance(node, ast.Name):
            f.identifiers.append((node.id, line))
        elif isinstance(node, ast.Attribute):
            f.identifiers.append((node.attr, node.end_lineno or line))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            f.identifiers.append((node.name, line))
            if not isinstance(node, ast.ClassDef):
                f.functions.append((line, node.end_lineno or line))
        elif isinstance(node, ast.arg):
            f.identifiers.append((node.arg, line))
        elif isinstance(node, ast.keyword) and node.arg:
            f.identifiers.append((node.arg, line))

        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names = [t.id for t in targets if isinstance(t, ast.Name)]
            if names and isinstance(node.value, (ast.List, ast.Tuple, ast.Set)):
                for el in node.value.elts:
                    if isinstance(el, ast.Constant) and isinstance(el.value, str):
                        f.assigned_strings.append((names[0], el.value, el.lineno))
    f.identifiers.sort(key=lambda x: x[1])
    return f


# One pass over comments and string literals, so "//" inside a string is not a comment.
_C_STYLE = re.compile(
    r"""(?P<comment>//[^\n]*|/\*.*?\*/)|(?P<string>"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*'|`(?:\\.|[^`\\])*`)""",
    re.S,
)
_HASH_STYLE = re.compile(r"""(?P<comment>\#[^\n]*)|(?P<string>"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*')""")
_IMPORT_LINE = re.compile(r"""(?:\bfrom\s*|\brequire\s*\(\s*|\bimport\s*\(?\s*)["']([^"']+)["']""")
_ASSIGNED_LIST = re.compile(r"\b([A-Za-z_]\w*)\s*(?::[^=\n]+)?=\s*\[([^\]]*)\]")


def _spaces(s: str) -> str:
    return re.sub(r"[^\n]", " ", s)


def _lexed(text: str, suffix: str) -> Facts:
    pattern = _HASH_STYLE if suffix in {".rb", ".py"} else _C_STYLE
    no_comments = pattern.sub(lambda m: _spaces(m[0]) if m["comment"] else m[0], text)
    code = pattern.sub(lambda m: _spaces(m[0]), text)
    f = Facts(code_lines=code.split("\n"))
    line_of = lambda i: text.count("\n", 0, i) + 1

    for m in _IMPORT_LINE.finditer(no_comments):
        # Only count it if the `import`/`from`/`require` keyword is code, not inside a string.
        if code[m.start():m.start() + 4].strip():
            f.imports.setdefault(m[1], line_of(m.start()))
    for n, line in enumerate(f.code_lines, 1):
        if re.match(r"\s*(import|require)\b", line):  # Java / Go / Ruby style
            m = re.match(r"""\s*(?:import|require)\s+(?:static\s+)?["']?([\w./@-]+)""", no_comments.split("\n")[n - 1])
            if m:
                f.imports.setdefault(m[1], n)
        f.identifiers += [(w, n) for w in re.findall(r"[A-Za-z_$][\w$]*", line)]
    for m in _ASSIGNED_LIST.finditer(no_comments):
        for s in re.finditer(r"""["']([^"'\n]+)["']""", m[2]):
            f.assigned_strings.append((m[1], s[1], line_of(m.start(2) + s.start())))
    return f


def extract(text: str, suffix: str) -> Facts:
    suffix = suffix.lower()
    if suffix == ".py":
        return _python(text) or _lexed(text, suffix)  # unparsable Python still gets lexed
    return _lexed(text, suffix)


def words(identifier: str) -> list[str]:
    """screenResume / screen_resume / SCREEN_RESUME -> ['screen', 'resume']."""
    spaced = re.sub(r"([a-z0-9])([A-Z])|([A-Z]+)([A-Z][a-z])",
                    lambda m: f"{m[1] or m[3]} {m[2] or m[4]}", identifier)
    return [w.lower() for w in re.split(r"[^A-Za-z0-9]+", spaced) if w]


def imports_any(facts: Facts, libraries: set[str]) -> tuple[str, int] | None:
    """First import that is one of `libraries` or a submodule of one."""
    for module, line in sorted(facts.imports.items(), key=lambda x: x[1]):
        for lib in libraries:
            if module == lib or module.startswith((lib + ".", lib + "/", lib + "-", lib + "_")):
                return module, line
    return None
