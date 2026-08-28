import re
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class Document:
    def __init__(self, doc_id: str, title: str, version: str, effective_date: str, status: str, content: str):
        self.doc_id = doc_id
        self.title = title
        self.version = version
        self.effective_date = effective_date
        self.status = status
        self.content = content

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "version": self.version,
            "effective_date": self.effective_date,
            "status": self.status,
            "content": self.content,
        }


class DocumentLoader:
    @staticmethod
    def load_corpus(corpus_dir: str = "corpus") -> List[Document]:
        corpus_path = Path(corpus_dir)
        documents = []

        if not corpus_path.exists():
            logger.warning(f"Corpus directory not found: {corpus_path}")
            return documents

        for md_file in sorted(corpus_path.glob("*.md")):
            try:
                doc = DocumentLoader._parse_markdown(md_file)
                if doc:
                    documents.append(doc)
            except Exception as e:
                logger.error(f"Failed to load document {md_file}: {e}")

        logger.info(f"Loaded {len(documents)} documents from corpus")
        return documents

    @staticmethod
    def _parse_markdown(file_path: Path) -> Document:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        yaml_match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)

        metadata = {}
        body_content = content

        if yaml_match:
            yaml_block = yaml_match.group(1)
            body_content = content[yaml_match.end() :]

            for line in yaml_block.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    metadata[key.strip()] = value.strip()

        doc_id = metadata.get("document_id", file_path.stem)
        title = metadata.get("title", file_path.stem)
        version = metadata.get("version", "1.0")
        effective_date = metadata.get("effective_date", datetime.now().isoformat())
        status = metadata.get("status", "active")

        return Document(
            doc_id=doc_id,
            title=title,
            version=version,
            effective_date=effective_date,
            status=status,
            content=body_content.strip(),
        )
