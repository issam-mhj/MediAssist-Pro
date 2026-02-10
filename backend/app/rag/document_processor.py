
from pathlib import Path
from typing import List, Optional
from pypdf import PdfReader
from langchain_core.documents import Document


class DocumentProcessor:

    def __init__(self, documents_dir: Optional[str] = None):
        if documents_dir:
            self.documents_dir = Path(documents_dir)
        else:
            self.documents_dir = Path(__file__).parent
        self.documents_dir.mkdir(parents=True, exist_ok=True)

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

        reader = PdfReader(str(pdf_path))
        documents = []

        for page_num, page in enumerate(reader.pages):
            text = page.extract_text() or ""

            if len(text.strip()) < 50:
                continue

            text = self._preprocess_text(text)

            metadata = {
                "source": pdf_path.name,
                "page": page_num + 1,
                "total_pages": len(reader.pages),
                "file_path": str(pdf_path),
            }
            documents.append(Document(page_content=text, metadata=metadata))

        print(f" {len(documents)} pages extraites de {pdf_path.name}")
        return documents

    def load_all_pdfs(self) -> List[Document]:
        
        all_documents = []
        pdf_files = list(self.documents_dir.glob("*.pdf"))

        if not pdf_files:
            print(f"⚠️ Aucun fichier PDF trouvé dans {self.documents_dir}")
            return all_documents

        print(f" {len(pdf_files)} fichier(s) PDF trouvé(s)")

        for pdf_file in pdf_files:
            try:
                docs = self.load_pdf(str(pdf_file))
                all_documents.extend(docs)
            except Exception as e:
                print(f"❌ Erreur lors du chargement de {pdf_file.name}: {e}")

        print(f"📊 Total: {len(all_documents)} pages extraites de {len(pdf_files)} fichier(s)")
        return all_documents

    def get_page_text(self, page_number: int, file_path: Optional[str] = None) -> str:
        if file_path is None:
            pdf_files = list(self.documents_dir.glob("*.pdf"))
            if not pdf_files:
                raise FileNotFoundError("Aucun fichier PDF trouvé")
            file_path = str(pdf_files[0])

        reader = PdfReader(file_path)

        if page_number < 1 or page_number > len(reader.pages):
            raise ValueError(
                f"Page {page_number} invalide. Le document a {len(reader.pages)} pages."
            )

        text = reader.pages[page_number - 1].extract_text() or ""
        return self._preprocess_text(text)

    def extract_metadata(self, file_path: Optional[str] = None) -> dict:
        if file_path is None:
            pdf_files = list(self.documents_dir.glob("*.pdf"))
            if not pdf_files:
                raise FileNotFoundError("Aucun fichier PDF trouvé")
            file_path = str(pdf_files[0])

        pdf_path = Path(file_path)
        reader = PdfReader(str(pdf_path))
        meta = reader.metadata or {}

        return {
            "file_name": pdf_path.name,
            "file_size_kb": round(pdf_path.stat().st_size / 1024, 2),
            "total_pages": len(reader.pages),
            "title": meta.get("/Title", "N/A"),
            "author": meta.get("/Author", "N/A"),
            "subject": meta.get("/Subject", "N/A"),
            "creator": meta.get("/Creator", "N/A"),
        }

    @staticmethod
    def _preprocess_text(text: str) -> str:

        import re

        text = re.sub(r"[ \t]+", " ", text)

        text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

        text = re.sub(r"\n{3,}", "\n\n", text)

        text = text.strip()

        return text


def load_documents(documents_dir: Optional[str] = None) -> List[Document]:
    processor = DocumentProcessor(documents_dir)
    return processor.load_all_pdfs()


if __name__ == "__main__":

    processor = DocumentProcessor()

    try:
        metadata = processor.extract_metadata()
        print("📋 Métadonnées du document:")
        for key, value in metadata.items():
            print(f"  • {key}: {value}")
    except FileNotFoundError as e:
        print(f"⚠️ {e}")

    documents = processor.load_all_pdfs()
    if documents:
        print(f"\n📄 Aperçu de la première page:")
        print(f"   {documents[0].page_content[:200]}...")
    else:
        print(" Aucun document chargé")