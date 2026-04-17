from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from hierarchical.postprocessor import ResultPostprocessor
from docling_core.transforms.chunker import HierarchicalChunker
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import logging

try:
    from pypdf import PdfReader as _PdfReader
    _PYPDF_AVAILABLE = True
except ImportError:
    try:
        from PyPDF2 import PdfReader as _PdfReader
        _PYPDF_AVAILABLE = True
    except ImportError:
        _PYPDF_AVAILABLE = False

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ParsingService:
    def __init__(self):
        # We delay initialization of the heavy Primary converter to avoid crashing startup
        self._primary_converter = None
        self._ultra_lite_converter = None
        self.chunker = HierarchicalChunker()
        
        self.role_mapping = {
            "general": ["employee", "finance", "engineering", "marketing", "c_level"],
            "finance": ["finance", "c_level"],
            "engineering": ["engineering", "c_level"],
            "marketing": ["marketing", "c_level"]
        }

    @property
    def primary_converter(self):
        if self._primary_converter is None:
            # Hierarchical structure for small/medium files
            params = {
                "do_ocr": False,
                "do_table_structure": True,
                "images_scale": 1.0,
                "generate_page_images": False
            }
            primary_options = PdfPipelineOptions.model_validate(params)
            self._primary_converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=primary_options)
                }
            )
        return self._primary_converter

    @property
    def ultra_lite_converter(self):
        if self._ultra_lite_converter is None:
            # ZERO-ML Path (Bypasses layout analyze stage)
            # We use model_validate to handle the version-specific 'pipeline_id' field correctly
            params = {
                "pipeline_id": "SimplePdfPipeline",
                "do_ocr": False,
                "do_table_structure": False,
                "images_scale": 0.5,
                "generate_page_images": False
            }
            try:
                # Try with SimplePdfPipeline string
                lite_options = PdfPipelineOptions.model_validate(params)
            except Exception:
                # If pipeline_id is truly unknown to this Pydantic model version, 
                # we just use the most minimal Standard settings possible
                lite_options = PdfPipelineOptions.model_validate({k: v for k, v in params.items() if k != "pipeline_id"})
                
            self._ultra_lite_converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=lite_options)
                }
            )
        return self._ultra_lite_converter

    def _extract_text_pypdf(self, file_path: str) -> str:
        """True Zero-ML text extraction fallback using pypdf."""
        if not _PYPDF_AVAILABLE:
            return ""
        try:
            reader = _PdfReader(file_path)
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"pypdf extraction failed: {str(e)}")
            return ""

    def process_file(self, file_path: str, collection: str, explicit_roles: list[str] = None) -> list[Document]:
        filename = os.path.basename(file_path)
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        
        # 1. Pipeline Selection & Execution
        is_large_pdf = False
        result = None
        current_pipeline = "Primary"
        use_pypdf_fallback = False
        
        try:
            if is_large_pdf:
                logger.info(f"[FORCE ULTRA-LITE] Document '{filename}' ({file_size_mb:.2f}MB) bypassing ML models.")
                current_pipeline = "Ultra-Lite"
                result = self.ultra_lite_converter.convert(file_path)
            else:
                logger.info(f"Attempting Primary Hierarchical conversion for: {filename} ({file_size_mb:.2f}MB)")
                result = self.primary_converter.convert(file_path)
                
            # Check for total failure
            if hasattr(result, "status") and str(result.status) == "ConversionStatus.FAILURE":
                logger.warning(f"Managed Memory Failure for {filename}. Retrying with Ultra-Lite safety net.")
                current_pipeline = "Ultra-Lite"
                result = self.ultra_lite_converter.convert(file_path)
            
            # Detect partial failures (std::bad_alloc on specific pages)
            if result and hasattr(result, "errors"):
                failed_pages = result.errors
                if len(failed_pages) > 1: # Be more aggressive with fallback if pages fail
                    logger.warning(f"Docling pipeline had {len(failed_pages)} page failures on '{filename}'. Retrying with Ultra-Lite.")
                    current_pipeline = "Ultra-Lite"
                    result = self.ultra_lite_converter.convert(file_path)
            
            # If Ultra-Lite also has many errors, we MUST use PyPDF
            if current_pipeline == "Ultra-Lite" and result and hasattr(result, "errors"):
                if len(result.errors) > 1:
                    logger.warning(f"Ultra-Lite also failed on {len(result.errors)} pages. Switching to Absolute Zero-ML PyPDF fallback.")
                    use_pypdf_fallback = True

        except Exception as e:
            if "bad_alloc" in str(e).lower() or "memory" in str(e).lower():
                logger.error(f"Memory exhaustion during Docling parse for {filename}. Switching to PyPDF fallback.")
                use_pypdf_fallback = True
            else:
                logger.error(f"Ingestion attempt failed for {filename}: {str(e)}. Attempting Ultra-Lite.")
                current_pipeline = "Ultra-Lite"
                try:
                    result = self.ultra_lite_converter.convert(file_path)
                    if hasattr(result, "errors") and len(result.errors) > 0:
                        use_pypdf_fallback = True
                except Exception:
                    use_pypdf_fallback = True

        # 2. PyPDF Extraction (If triggered)
        if use_pypdf_fallback:
            current_pipeline = "PyPDF"
            full_text = self._extract_text_pypdf(file_path)
            if not full_text:
                 raise Exception(f"CRITICAL: Resource Failure for {filename}. All extraction paths (Docling & PyPDF) failed.")
        else:
            # 3. Safety Check: If results are missing entirely
            if not result or not result.document:
                 raise Exception(f"CRITICAL: Resource Failure for {filename}. All Docling paths failed.")
            
            # 4. Apply Postprocessor (Only if we used high-fidelity Primary)
            if filename.lower().endswith(".pdf") and current_pipeline == "Primary":
                try:
                    ResultPostprocessor(result, source=os.path.abspath(file_path)).process()
                except Exception:
                    pass

        # 5. Chunking Strategy
        text_chunks = None
        if current_pipeline == "PyPDF":
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=700,
                chunk_overlap=150,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            text_chunks = splitter.split_text(full_text)
        else:
            chunks = list(self.chunker.chunk(result.document))
            # If Hierarchical produced way too few chunks, use Recursive Splitter on the Docling text export
            if len(chunks) < 10 and file_size_mb > 0.1:
                logger.warning(f"HierarchicalChunker produced only {len(chunks)} chunks. Falling back to Recursive Splitter.")
                full_text = result.document.export_to_text()
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=700,
                    chunk_overlap=150,
                    separators=["\n\n", "\n", ". ", " ", ""]
                )
                text_chunks = splitter.split_text(full_text)
                current_pipeline = "Hybrid-Split"

        # 6. Metadata & Document Creation
        if explicit_roles and len(explicit_roles) > 0:
            access_roles = explicit_roles
        else:
            access_roles = self.role_mapping.get(collection, ["c_level"])
        
        langchain_docs = []
        
        if text_chunks is not None:
            # Recursive Splitter Path (PyPDF or Hybrid)
            for i, chunk_text in enumerate(text_chunks):
                metadata = {
                    "source_document": filename,
                    "collection": collection,
                    "access_roles": access_roles,
                    "section_title": "N/A",
                    "page_number": 0,
                    "chunk_type": f"split_{current_pipeline.lower().replace('-', '_')}",
                    "parent_chunk_id": f"split_{i}"
                }
                langchain_docs.append(Document(page_content=chunk_text, metadata=metadata))
        else:
            # Hierarchical Chunker Path
            for i, chunk in enumerate(chunks):
                content = chunk.text
                section_title = "N/A"
                if hasattr(chunk, "meta") and chunk.meta and hasattr(chunk.meta, "headings") and chunk.meta.headings:
                    section_title = " | ".join(chunk.meta.headings)
                    
                metadata = {
                    "source_document": filename,
                    "collection": collection,
                    "access_roles": access_roles,
                    "section_title": section_title,
                    "page_number": 0,
                    "chunk_type": "hierarchical",
                    "parent_chunk_id": f"parent_{i}"
                }
                
                try:
                    if chunk.meta.doc_items and hasattr(chunk.meta.doc_items[0], "prov"):
                        metadata["page_number"] = chunk.meta.doc_items[0].prov[0].page_no
                except Exception: pass
                
                langchain_docs.append(Document(page_content=content, metadata=metadata))
            
        logger.info(f"Ingestion complete for '{filename}' using {current_pipeline} pipeline. Total chunks: {len(langchain_docs)}")
        return langchain_docs

parsing_service = ParsingService()
