import os
import re
from pathlib import Path
from typing import List, Optional
from llama_parse import LlamaParse
from langchain_core.documents import Document

_PARSING_INSTRUCTIONS = """
This is a French-language technical manual about laboratory equipment maintenance.
The PDF has a complex layout with two-column text, tables, photographs with
captions, footnotes, and structured chapters/sections.

Please follow these rules carefully:

1. **Two-column layout**: Merge both columns into a single continuous text flow.
   Read the LEFT column fully first, then the RIGHT column. Never interleave
   sentences from different columns.

2. **Tables**: Reproduce every table in full Markdown table syntax.
   Include the header row and ALL data rows. Example:
   | GMDN Code | 17489 |
   | ECRI Code | 17-489 |
   | Dénomination | Laveur de microplaques |
   Do NOT skip any row or column.

3. **Chapter and section headings**: Keep them exactly as they appear.
   Use Markdown heading levels:
   - # for chapter titles (e.g., "Chapitre 2")
   - ## for main section titles (e.g., "Laveur de microplaques")
   - ### for sub-sections (e.g., "PRINCIPES DE FONCTIONNEMENT")

4. **Photo captions / figure labels**: Include them as italic text, e.g.:
   *PHOTOGRAPHIE D'UN LAVEUR DE MICROPLAQUES*
   followed by the caption text.

5. **Footnotes**: Place footnotes at the end of the page's text, each on its
   own line, prefixed with the footnote number (e.g., "¹ Voir une explication…").

6. **Bullet / numbered lists**: Preserve the list structure using Markdown
   (- or 1. 2. 3.).

7. **Special characters**: Keep accented French characters intact (é, è, ê, à, ç, etc.).

8. **Completeness**: Extract ALL text on EVERY page. Do not skip or summarize.
   Every sentence must appear in the output.
"""


class DocumentProcessor:
    def __init__(
        self,
        documents_dir: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        if documents_dir:
            self.documents_dir = Path(documents_dir)
        else:
            self.documents_dir = Path(__file__).parent
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 DocumentProcessor scanning: {self.documents_dir}")

        self.api_key = api_key or os.getenv("LLAMA_CLOUD_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "LLAMA_CLOUD_API_KEY is required. Set it as an environment variable."
            )

        self.parser = LlamaParse(
            api_key=self.api_key,
            result_type="markdown",
            language="fr",
            verbose=True,
            premium_mode=True,
            parsing_instruction=_PARSING_INSTRUCTIONS,
            split_by_page=True,
            skip_diagonal_text=False,
            do_not_unroll_columns=False,
        )


    @staticmethod
    def _clean_text(text: str) -> str:
        """Normalise whitespace, fix hyphenation, remove artefacts."""
        text = re.sub(r"-(\n|\r\n?)\s*", "", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[^\S\n]+", " ", text)
        lines = [line.strip() for line in text.splitlines()]
        text = "\n".join(lines)
        text = re.sub(r"^[-_=]{3,}$", "", text, flags=re.MULTILINE)
        return text.strip()

    @staticmethod
    def _detect_chapter(text: str) -> Optional[str]:
        for line in text.split("\n")[:10]:
            line_stripped = line.strip().lstrip("# ").strip()
            if re.match(r"(?i)chapitre\s+\d+", line_stripped):
                return line_stripped
        return None

    @staticmethod
    def _detect_section(text: str) -> Optional[str]:
        for line in text.split("\n")[:15]:
            stripped = line.strip().lstrip("# ").strip()
            if not stripped:
                continue
            if line.strip().startswith("#"):
                return stripped
            if stripped.isupper() and len(stripped) > 5:
                return stripped
        return None


    def load_pdf(self, file_path: Optional[str] = None) -> List[Document]:
        if file_path is None:
            pdf_files = list(self.documents_dir.glob("*.pdf"))
            if not pdf_files:
                raise FileNotFoundError(
                    f"Aucun fichier PDF trouvé dans {self.documents_dir}"
                )
            file_path = str(pdf_files[0])

        pdf_path = Path(file_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"Fichier PDF introuvable: {file_path}")

        parsed_documents = self.parser.load_data(str(pdf_path))

        documents: List[Document] = []
        current_chapter: Optional[str] = None

        for idx, doc in enumerate(parsed_documents):
            text = self._clean_text(doc.text)
            if not text or len(text) < 30:
                continue

            chapter = self._detect_chapter(text)
            if chapter:
                current_chapter = chapter

            section = self._detect_section(text)

            metadata = {
                "source": pdf_path.name,
                "page": idx + 1,
                "total_pages": len(parsed_documents),
                "file_path": str(pdf_path),
                "chapter": current_chapter,
                "section": section,
            }
            documents.append(Document(page_content=text, metadata=metadata))

        print(
            f"📄 {len(documents)} page(s) extraite(s) de {pdf_path.name} "
            f"via LlamaParse (premium)"
        )
        return documents

    def load_all_pdfs(self) -> List[Document]:
        """Load every PDF in the directory."""
        all_documents: List[Document] = []
        pdf_files = list(self.documents_dir.glob("*.pdf"))

        if not pdf_files:
            print(f"⚠️ Aucun fichier PDF trouvé dans {self.documents_dir}")
            return all_documents

        print(f"📂 {len(pdf_files)} fichier(s) PDF trouvé(s)")

        for pdf_file in pdf_files:
            try:
                docs = self.load_pdf(str(pdf_file))
                all_documents.extend(docs)
            except Exception as e:
                print(f"❌ Erreur lors du chargement de {pdf_file.name}: {e}")

        total_chars = sum(len(d.page_content) for d in all_documents)
        print(
            f"📊 Total: {len(all_documents)} page(s) — "
            f"{total_chars:,} caractères extraits"
        )
        return all_documents

    def extract_metadata(self, file_path: Optional[str] = None) -> dict:
        if file_path is None:
            pdf_files = list(self.documents_dir.glob("*.pdf"))
            if not pdf_files:
                raise FileNotFoundError("Aucun fichier PDF trouvé")
            file_path = str(pdf_files[0])

        pdf_path = Path(file_path)

        return {
            "file_name": pdf_path.name,
            "file_size_kb": round(pdf_path.stat().st_size / 1024, 2),
            "parser": "LlamaParse (premium)",
            "result_type": "markdown",
            "language": "fr",
        }


def load_documents(documents_dir: Optional[str] = None) -> List[Document]:
    processor = DocumentProcessor(documents_dir)
    return processor.load_all_pdfs()