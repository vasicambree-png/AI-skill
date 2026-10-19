"""Dependency-free packaging checks, not a general YAML or secret scanner."""
import ast
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ("github-sync", "ch584-ui-tuning", "embedded-link-debug")
IGNORED = {".git", ".local", "__pycache__", ".venv"}


def verify():
    errors = []
    files = []

    def walk(directory):
        for path in directory.iterdir():
            if path.name in IGNORED:
                continue
            if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
                errors.append(f"{path.relative_to(ROOT)}: linked entries are not allowed")
            elif path.is_dir():
                walk(path)
            else:
                files.append(path)

    walk(ROOT)
    for skill in SKILLS:
        entry = ROOT / "skills" / skill / "SKILL.md"
        if not entry.is_file():
            errors.append(f"Missing skill: {skill}")
            continue
        text = entry.read_text(encoding="utf-8-sig")
        match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
        if not match:
            errors.append(f"{skill}: missing YAML frontmatter")
            continue
        fields = {}
        for line in match[1].splitlines():
            field = re.fullmatch(r"(name|description): (.+)", line)
            if not field or field[1] in fields:
                errors.append(f"{skill}: unsupported or duplicate frontmatter field")
            else:
                fields[field[1]] = field[2]
        if fields.get("name") != skill or not fields.get("description", "").strip():
            errors.append(f"{skill}: invalid name/description")

    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        if path.suffix.lower() not in {".md", ".py", ".ps1", ".yaml", ".yml", ""}:
            errors.append(f"{relative}: unexpected artifact type")
            continue
        try:
            text = path.read_text(encoding="utf-8-sig")
        except (UnicodeError, OSError) as exc:
            errors.append(f"{relative}: cannot read as UTF-8: {exc}")
            continue
        if path.suffix == ".py":
            try:
                ast.parse(text, filename=relative)
            except SyntaxError as exc:
                errors.append(f"{relative}: {exc}")
        if path.suffix in {".yaml", ".yml"}:
            # The published agent files use only these mappings and scalars.
            seen = set()
            section = None
            for line in text.splitlines():
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                if line in {"interface:", "policy:"}:
                    section = line[:-1]
                    if section in seen:
                        errors.append(f"{relative}: duplicate section")
                    seen.add(section)
                    continue
                scalar = re.fullmatch(r'  ([a-z_]+): ("[^"\r\n]*"|true|false)', line)
                if not scalar or section is None:
                    errors.append(f"{relative}: unsupported YAML structure")
                    continue
                key = (section, scalar[1])
                if key in seen:
                    errors.append(f"{relative}: duplicate YAML field")
                seen.add(key)
            for field in ("display_name", "short_description"):
                if ("interface", field) not in seen:
                    errors.append(f"{relative}: missing interface.{field}")
        if path.suffix == ".md":
            for target in re.findall(r"\[[^\]\n]*\]\(([^)\n]+)\)", text):
                target = target.strip().strip("<>")
                parts = urlsplit(target)
                if parts.scheme or target.startswith(("#", "//")):
                    continue
                resolved = (path.parent / unquote(parts.path)).resolve()
                if not resolved.is_relative_to(ROOT) or not resolved.exists():
                    errors.append(f"{relative}: broken/outside relative link: {target}")
        # Deliberately narrow patterns avoid claiming comprehensive secret detection.
        patterns = (
            r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----",
            r"\bgh[pousr]_[A-Za-z0-9]{30,}\b",
            r"\bgithub_pat_[A-Za-z0-9_]{40,}\b",
            r"\bsk-(?:proj-)?[A-Za-z0-9_-]{30,}\b",
        )
        if any(re.search(pattern, text) for pattern in patterns):
            errors.append(f"{relative}: possible credential")
        if path.name.lower() in {"auth.json", "config.toml", "history.jsonl", "memory.md"} or path.suffix == ".jsonl":
            errors.append(f"{relative}: private configuration/history artifact")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Repository checks passed: {len(files)} files; {len(SKILLS)} skills.")
    print("Checks cover packaging only; historical firmware/hardware evidence was not rerun.")
    return 0


if __name__ == "__main__":
    raise SystemExit(verify())
