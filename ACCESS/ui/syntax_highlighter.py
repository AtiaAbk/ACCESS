"""Language detection and syntax tokenization for ACCESS code responses."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


CODE_EXTENSIONS = {
    ".c", ".h", ".cc", ".cpp", ".cxx", ".hpp", ".cs", ".java",
    ".py", ".pyw", ".js", ".jsx", ".ts", ".tsx", ".json", ".html",
    ".htm", ".css", ".scss", ".sql", ".sh", ".bash", ".ps1", ".rb",
    ".rs", ".go", ".php", ".swift", ".kt", ".kts", ".xml", ".yaml",
    ".yml", ".toml", ".ini", ".md",
}

KEYWORDS = {
    "abstract", "and", "as", "async", "await", "auto", "bool", "break",
    "case", "catch", "char", "class", "const", "continue", "def", "default",
    "delete", "do", "double", "else", "enum", "except", "export", "extends",
    "false", "final", "finally", "float", "for", "foreach", "from", "function",
    "if", "implements", "import", "in", "include", "instanceof", "int",
    "interface", "lambda", "let", "long", "namespace", "new", "none", "not",
    "null", "of", "or", "package", "pass", "private", "protected", "public",
    "raise", "return", "short", "signed", "static", "struct", "super", "switch",
    "this", "throw", "true", "try", "typedef", "typeof", "union", "unsigned",
    "using", "var", "virtual", "void", "volatile", "while", "with", "yield",
}


@dataclass(frozen=True)
class HighlightedCode:
    code: str
    language: str
    segments: list[tuple[str, str]]


def _filename_from_context(context: str) -> str:
    match = re.search(r"\b(?:read|open|show|display)\s+(?:file\s+)?(.+)$", context, re.I)
    if not match:
        return ""
    value = match.group(1).strip().strip("\"'")
    return Path(value).name


def _unfence(text: str) -> tuple[str, str]:
    match = re.fullmatch(r"\s*```([\w+#.-]*)\s*\n(.*?)\n?```\s*", text, re.S)
    if not match:
        return text, ""
    return match.group(2), match.group(1).strip().lower()


def looks_like_code(text: str, context: str = "") -> bool:
    """Use command filename and conservative content signals to detect code."""

    if re.search(r"```[\w+#.-]*\s*\n", text):
        return True
    filename = _filename_from_context(context)
    if Path(filename).suffix.lower() in CODE_EXTENSIONS and "\n" in text:
        return True
    signals = (
        r"^\s*#\s*(?:include|define|pragma)",
        r"\b(?:def|class|function|interface|struct)\s+\w+",
        r"\b(?:const|let|var|int|void|public|private)\s+\w+",
        r"(?:=>|</?\w+[^>]*>|\{\s*$|;\s*$)",
    )
    return "\n" in text and sum(bool(re.search(pattern, text, re.I | re.M)) for pattern in signals) >= 2


def _fallback_segments(code: str, language: str) -> list[tuple[str, str]]:
    """Small built-in lexer used when Pygments has not been installed yet."""

    python_like = language in {"python", "py", "ruby", "rb", "shell", "bash", "sh"}
    comment = r"\#[^\n]*" if python_like else r"//[^\n]*|/\*[\s\S]*?\*/"
    keyword_pattern = "|".join(sorted((re.escape(word) for word in KEYWORDS), key=len, reverse=True))
    pattern = re.compile(
        rf"(?P<comment>{comment})"
        r"|(?P<preprocessor>^[ \t]*#[ \t]*[A-Za-z_]+[^\n]*)"
        r"|(?P<string>\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*')"
        r"|(?P<number>\b(?:0x[\dA-Fa-f]+|\d+(?:\.\d+)?)\b)"
        rf"|(?P<keyword>\b(?:{keyword_pattern})\b)"
        r"|(?P<function>\b[A-Za-z_]\w*(?=\s*\())",
        re.M,
    )
    segments: list[tuple[str, str]] = []
    position = 0
    for match in pattern.finditer(code):
        if match.start() > position:
            segments.append((code[position:match.start()], "code"))
        segments.append((match.group(0), match.lastgroup or "code"))
        position = match.end()
    if position < len(code):
        segments.append((code[position:], "code"))
    return segments


def highlight_code(text: str, context: str = "") -> HighlightedCode | None:
    """Return highlighted segments when *text* appears to be source code."""

    if not looks_like_code(text, context):
        return None

    code, fence_language = _unfence(text)
    filename = _filename_from_context(context)
    language = fence_language or Path(filename).suffix.lstrip(".").lower() or "code"

    try:
        from pygments import lex
        from pygments.lexers import get_lexer_by_name, get_lexer_for_filename, guess_lexer
        from pygments.token import Token

        if fence_language:
            lexer = get_lexer_by_name(fence_language)
        elif filename:
            lexer = get_lexer_for_filename(filename, code)
        else:
            lexer = guess_lexer(code)
        language = lexer.name

        def tag_for(token_type) -> str:
            if token_type in Token.Comment.Preproc:
                return "preprocessor"
            if token_type in Token.Comment:
                return "comment"
            if token_type in Token.Keyword:
                return "keyword"
            if token_type in Token.String:
                return "string"
            if token_type in Token.Number:
                return "number"
            if token_type in Token.Name.Function:
                return "function"
            if token_type in Token.Name.Class or token_type in Token.Name.Builtin:
                return "type"
            if token_type in Token.Operator:
                return "operator"
            return "code"

        segments = [(piece, tag_for(token)) for token, piece in lex(code, lexer)]
        return HighlightedCode(code, language, segments)
    except (ImportError, ValueError):
        return HighlightedCode(code, language, _fallback_segments(code, language))
