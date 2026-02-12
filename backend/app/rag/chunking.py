import re
from typing import List, Optional

from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from langchain_core.documents import Document


class DocumentChunker:

    def __init__(self, chunk_size: int = 1200, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        self._md_headers = [
            ("#", "heading_1"),
            ("##", "heading_2"),
            ("###", "heading_3"),
        ]


    def create_character_chunks(
        self,
        documents: List[Document],
        separators: Optional[List[str]] = None,
    ) -> List[Document]:
        print("\nCréation de chunks structurés...")

        all_chunks: List[Document] = []

        for doc in documents:
            page_chunks = self._split_single_document(doc, separators)
            all_chunks.extend(page_chunks)

        for i, chunk in enumerate(all_chunks, start=1):
            chunk.metadata["chunk_id"] = i
            chunk.metadata["char_count"] = len(chunk.page_content)

        if all_chunks:
            avg = sum(len(c.page_content) for c in all_chunks) / len(all_chunks)
            print(f"  {len(all_chunks)} chunks créés")
            print(f"     Taille moyenne: {avg:.0f} caractères")
        else:
            print("  Aucun chunk créé")

        return all_chunks

    def get_chunk_stats(self, chunks: List[Document]) -> dict:
        if not chunks:
            return {}
        lengths = [len(c.page_content) for c in chunks]
        return {
            "total_chunks": len(chunks),
            "min_length": min(lengths),
            "max_length": max(lengths),
            "avg_length": round(sum(lengths) / len(lengths)),
            "total_chars": sum(lengths),
            "chunk_size_setting": self.chunk_size,
            "chunk_overlap_setting": self.chunk_overlap,
        }

    def _split_single_document(
        self,
        doc: Document,
        separators: Optional[List[str]] = None,
    ) -> List[Document]:
        text = doc.page_content
        base_meta = dict(doc.metadata)

        tables, text = self._extract_tables(text)

        md_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self._md_headers,
            strip_headers=False,
        )
        md_sections = md_splitter.split_text(text)

        if not md_sections:
            md_sections = [Document(page_content=text, metadata={})]

        sub_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=separators or [
                "\n\n",   
                "\n",     
                ". ",     
                "; ",     
                ", ",     
                " ",     
                "",      
            ],
            length_function=len,
            is_separator_regex=False,
        )

        chunks: List[Document] = []

        for section in md_sections:
            sec_text = section.page_content.strip()
            if not sec_text:
                continue

            ctx_header = self._build_context_header(base_meta, section.metadata)

            if len(sec_text) <= self.chunk_size:
                content = f"{ctx_header}\n\n{sec_text}" if ctx_header else sec_text
                meta = {**base_meta, **section.metadata, "chunk_type": "structured"}
                chunks.append(Document(page_content=content, metadata=meta))
            else:
                sub_docs = sub_splitter.split_text(sec_text)
                for part in sub_docs:
                    content = f"{ctx_header}\n\n{part}" if ctx_header else part
                    meta = {**base_meta, **section.metadata, "chunk_type": "structured"}
                    chunks.append(Document(page_content=content, metadata=meta))

        for table_text in tables:
            ctx = self._build_context_header(base_meta, {})
            content = f"{ctx}\n\n{table_text}" if ctx else table_text
            meta = {**base_meta, "chunk_type": "table"}
            chunks.append(Document(page_content=content, metadata=meta))

        return chunks

    @staticmethod
    def _extract_tables(text: str):
        table_pattern = re.compile(
            r"((?:^\|.+\|\s*$\n?){2,})",
            re.MULTILINE,
        )
        tables: List[str] = []
        for m in table_pattern.finditer(text):
            table = m.group(0).strip()
            if table:
                tables.append(table)

        cleaned = table_pattern.sub("\n\n", text)
        return tables, cleaned

    @staticmethod
    def _build_context_header(base_meta: dict, section_meta: dict) -> str:
        parts: List[str] = []

        chapter = base_meta.get("chapter")
        if chapter:
            parts.append(chapter)

        for key in ("heading_1", "heading_2", "heading_3"):
            val = section_meta.get(key)
            if val:
                parts.append(val)

        section = base_meta.get("section")
        if section and section not in parts:
            parts.append(section)

        if not parts:
            return ""
        return "[" + " > ".join(parts) + "]"
