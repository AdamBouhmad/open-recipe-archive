# Open Recipe Archive

Building the largest open historical recipe corpora on GitHub 

## What This Repo Is
This repo is a public collection of over 54,000 historical recipes from more than thirty countries, built from public domain cookbooks and other copyright-safe sources 

These recipes are available in Markdown and JSONL for humans and agents.

Every recipe includes:

- title
- collection slug
- culture tag
- ingredients and numbered directions in Markdown
- source author
- source title
- source year
- source URL
- license

## Current Corpus

- 54,843 recipes
- 31 historical collections
- Markdown per recipe
- JSONL per collection

Current collections include:

- Argentina
- Australia
- Austria
- Brazil
- Canada
- Chile
- China
- Czechia
- Denmark
- Finland
- France
- Germany
- Greece
- Guatemala
- Hungary
- India
- Indonesia
- Italy
- Japan
- Mexico
- Netherlands
- Norway
- Philippines
- Poland
- Portugal
- Spain
- Sweden
- Turkey
- United Kingdom
- United States
- Jewish diaspora
- Levant
- Louisiana Creole
- West Indies

The project goal is to span every country and diaspora in the world with recipes that have attribution, rather than asking LLMs to infer cultural cooking from a muddied corpus. Some countries have deep pre-1931 cookbook shelves; others have sparse, fragmentary sources.

## Repo Layout

```text
collections/
  <collection-slug>/
    manifest.json
    recipes.jsonl
    recipes/
      <recipe-slug>.md

index/
  collections.json
  countries.json
  cultures.json
  summary.json

scripts/
  export_sqlite.py
```

## Quick Start

Clone the repository:

```sh
git clone https://github.com/adambouhmad/open-recipe-archive.git
cd open-recipe-archive
```

Read a recipe in GitHub or locally:

```sh
open "collections/ye-old-american/recipes/tomato-soup.md"
```

Load one collection as JSONL:

```sh
python3 -c "import json; from pathlib import Path; p=Path('collections/ye-old-american/recipes.jsonl'); print(sum(1 for _ in p.open()))"
```

Inspect the global index:

```sh
python3 -c "import json; print(json.load(open('index/summary.json')))"
```

## For Humans

Each recipe is a normal Markdown file with YAML frontmatter and a provenance
section.

Example:

```text
collections/ye-old-american/recipes/tomato-soup.md
```

## For Scripts And Scrapers

Each collection has a `recipes.jsonl` file with one JSON object per recipe.

Example fields:

```json
{
  "title": "Tomato Soup",
  "slug": "tomato-soup",
  "collection": "ye-old-american",
  "collection_name": "Ye Old American Recipe Book",
  "culture": "american-historical",
  "author": "Fannie Merritt Farmer",
  "body": "## Ingredients\n\n- 1 can tomatoes...",
  "source_title": "The Boston Cooking-School Cook Book",
  "source_url": "https://www.gutenberg.org/ebooks/65061",
  "source_year": "1896",
  "license": "public-domain",
  "tags": ["american-historical", "ye-old-american"],
  "export_date": "1896-01-01"
}
```

Read a collection in Python:

```python
import json
from pathlib import Path

path = Path("collections/ye-old-american/recipes.jsonl")
recipes = [json.loads(line) for line in path.open(encoding="utf-8")]
print(len(recipes), recipes[0]["title"])
```

## For Agents And RAG

Recommended ingestion paths:

- use `recipes.jsonl` for structured bulk loading
- use `recipes/*.md` when you want readable source documents
- use `index/collections.json` to discover available shelves first

Suggested strategy:

1. load `index/collections.json`
2. pick collections relevant to a region, culture, or period
3. ingest `recipes.jsonl` into your vector store or search index
4. retain `source_title`, `source_url`, `source_year`, and `license` in metadata

## Build A Search Site

Treat this repo as content, not infrastructure.

Minimal approach:

1. load all `recipes.jsonl` files
2. index `title`, `body`, `collection_name`, `culture`, and `tags`
3. render the corresponding Markdown file or body text in your UI
4. show provenance fields with every result

Useful stack options:

- static site generator plus prebuilt JSON index
- SQLite FTS
- Meilisearch
- Elasticsearch or OpenSearch
- vector search plus metadata filters

## Provenance And Licensing

All recipes are sourced from public-domain materials or clearly labeled permissive supplements. Every recipe carries source and license metadata. 

Default license status for the exported historical corpus is `public-domain`
unless a recipe is explicitly labeled otherwise.

## Contributing

Good contributions include:

- provenance fixes
- source URL fixes
- license corrections
- collection metadata improvements
- export tooling improvements
- search/demo apps built on top of the corpus

## License

See `LICENSE.md`.
