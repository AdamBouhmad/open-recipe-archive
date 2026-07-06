#!/usr/bin/env python3
"""Export harvested recipes from SQLite into a plain public data layout."""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = REPO_ROOT.parent.parent / "recipes.db"
DEFAULT_OUT = REPO_ROOT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--include-collection", action="append", default=[])
    parser.add_argument("--exclude-collection", action="append", default=["everyday"])
    parser.add_argument("--no-clean", action="store_true")
    return parser.parse_args()


def page_date(source_year: str) -> str:
    year = (source_year or "").strip()
    if len(year) == 4 and year.isdigit():
        return f"{year}-01-01"
    return "1900-01-01"


def yaml_scalar(value: str) -> str:
    return json.dumps(value or "", ensure_ascii=False)


def split_tags(raw: str, collection_slug: str, culture: str) -> list[str]:
    tags = []
    for item in (raw or "").split(","):
        tag = item.strip()
        if tag:
            tags.append(tag)
    tags.append(collection_slug)
    if culture:
        tags.append(culture)

    seen = set()
    deduped = []
    for tag in tags:
        key = tag.casefold()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(tag)
    return deduped


def recipe_record(recipe: sqlite3.Row, collection: sqlite3.Row) -> dict:
    source_year = (recipe["source_year"] or "").strip()
    return {
        "title": recipe["title"].strip(),
        "slug": recipe["slug"].strip(),
        "collection": collection["slug"].strip(),
        "collection_name": collection["name"],
        "culture": collection["culture"] or "",
        "author": recipe["author"] or "",
        "body": recipe["body"].strip(),
        "source_title": recipe["source_title"] or "",
        "source_url": recipe["source_url"] or "",
        "source_year": source_year,
        "license": recipe["license"] or "public-domain",
        "tags": split_tags(recipe["tags"], collection["slug"], collection["culture"]),
        "export_date": page_date(source_year),
    }


def recipe_markdown(record: dict) -> str:
    lines = [
        "---",
        f'title: {yaml_scalar(record["title"])}',
        f'slug: {yaml_scalar(record["slug"])}',
        f'collection: {yaml_scalar(record["collection"])}',
        f'collection_name: {yaml_scalar(record["collection_name"])}',
        f'culture: {yaml_scalar(record["culture"])}',
        f'date: {yaml_scalar(record["export_date"])}',
        f'author: {yaml_scalar(record["author"])}',
        f'source_title: {yaml_scalar(record["source_title"])}',
        f'source_url: {yaml_scalar(record["source_url"])}',
        f'source_year: {yaml_scalar(record["source_year"])}',
        f'license: {yaml_scalar(record["license"])}',
        f"tags: {json.dumps(record['tags'], ensure_ascii=False)}",
        "---",
        "",
        record["body"],
        "",
        "## Provenance",
        "",
        f'- Collection: {record["collection_name"]}',
        f'- Culture: {record["culture"] or record["collection"]}',
        f'- Source: [{record["source_title"]}]({record["source_url"]})' if record["source_url"] else f'- Source: {record["source_title"]}',
        f'- Source author: {record["author"] or "Unknown"}',
        f'- Source year: {record["source_year"] or "Unknown"}',
        f'- License: {record["license"]}',
        "",
    ]
    return "\n".join(lines)


def collection_manifest(collection: sqlite3.Row, records: list[dict]) -> dict:
    years = sorted({record["source_year"] for record in records if record["source_year"]})
    return {
        "slug": collection["slug"],
        "name": collection["name"],
        "description": collection["description"] or "",
        "culture": collection["culture"] or "",
        "recipe_count": len(records),
        "source_years": years,
        "formats": {
            "jsonl": "recipes.jsonl",
            "markdown_dir": "recipes/",
        },
    }


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def clean_output(out_dir: Path) -> None:
    for relative in ("collections", "index"):
        path = out_dir / relative
        if path.exists():
            shutil.rmtree(path)


def export(db_path: Path, out_dir: Path, include: set[str], exclude: set[str], clean: bool) -> tuple[int, int]:
    if not db_path.exists():
        raise SystemExit(f"SQLite database not found: {db_path}")

    if clean:
        clean_output(out_dir)

    out_dir.mkdir(parents=True, exist_ok=True)
    collections_dir = out_dir / "collections"
    index_dir = out_dir / "index"
    collections_dir.mkdir(parents=True, exist_ok=True)
    index_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    collections = conn.execute(
        "SELECT slug, name, description, culture FROM collections ORDER BY name"
    ).fetchall()

    exported_collections = 0
    exported_recipes = 0
    collection_index = []
    culture_counts: dict[str, int] = {}
    country_counts: dict[str, int] = {}

    for collection in collections:
        slug = collection["slug"]
        if include and slug not in include:
            continue
        if slug in exclude:
            continue

        recipes = conn.execute(
            """
            SELECT slug, title, tags, author, body, source_title, source_url,
                   source_year, license
            FROM recipes
            WHERE collection = ?
            ORDER BY title COLLATE NOCASE, slug
            """,
            (slug,),
        ).fetchall()
        if not recipes:
            continue

        records = [recipe_record(recipe, collection) for recipe in recipes]
        collection_dir = collections_dir / slug
        recipes_dir = collection_dir / "recipes"
        recipes_dir.mkdir(parents=True, exist_ok=True)

        with (collection_dir / "recipes.jsonl").open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                (recipes_dir / f"{record['slug']}.md").write_text(
                    recipe_markdown(record),
                    encoding="utf-8",
                )

        manifest = collection_manifest(collection, records)
        write_json(collection_dir / "manifest.json", manifest)
        collection_index.append(manifest)

        if manifest["culture"]:
            culture = manifest["culture"]
            culture_counts[culture] = culture_counts.get(culture, 0) + manifest["recipe_count"]
            country_counts[culture] = country_counts.get(culture, 0) + manifest["recipe_count"]

        exported_collections += 1
        exported_recipes += len(records)
        print(f"exported {slug}: {len(records)} recipes")

    write_json(index_dir / "collections.json", collection_index)
    write_json(
        index_dir / "cultures.json",
        [{"culture": key, "recipe_count": value} for key, value in sorted(culture_counts.items())],
    )
    write_json(
        index_dir / "countries.json",
        [{"country": key, "recipe_count": value} for key, value in sorted(country_counts.items())],
    )
    write_json(
        index_dir / "summary.json",
        {
            "collection_count": exported_collections,
            "recipe_count": exported_recipes,
            "excluded_collections": sorted(exclude),
        },
    )

    conn.close()
    return exported_collections, exported_recipes


def main() -> None:
    args = parse_args()
    collections, recipes = export(
        db_path=args.db.resolve(),
        out_dir=args.out.resolve(),
        include=set(args.include_collection),
        exclude=set(args.exclude_collection),
        clean=not args.no_clean,
    )
    print(f"done: {collections} collections, {recipes} recipes")


if __name__ == "__main__":
    main()
