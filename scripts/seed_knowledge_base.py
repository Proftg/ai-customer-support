from pathlib import Path

from app import db

KNOWLEDGE_DIR = Path("knowledge_base")


def parse(path: Path) -> list[tuple[str, str]]:
    """Split a file into (title, content) rows, one per ## heading."""
    entries = []
    for block in path.read_text(encoding="utf-8").split("\n## ")[1:]:
        title, _, content = block.partition("\n")
        entries.append((title.strip(), content.strip()))
    return entries


with db.connect() as conn:
    for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        rows = parse(path)
        for title, content in rows:
            conn.execute(
                """
                insert into knowledge_base (section, title, content) values (%s, %s, %s)
                on conflict (section, title) do update
                  set content = excluded.content, updated_at = now()
                """,
                (path.stem, title, content),
            )
        print(f"{path.stem}: {len(rows)} entries")
