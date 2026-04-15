from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from hierarchical.postprocessor import ResultPostprocessor
from docling_core.transforms.chunker import HierarchicalChunker
from langchain_core.documents import Document
import os
import logging

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

    def process_file(self, file_path: str, collection: str, explicit_roles: list[str] = None) -> list[Document]:
        filename = os.path.basename(file_path)
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        
        # 1. Proactive Memory Safety Check
        # User requested to remove 1MB safety catch
        is_large_pdf = False
        
        result = None
        current_pipeline = "Primary"
        
        try:
            if is_large_pdf:
                logger.info(f"[FORCE ULTRA-LITE] Document '{filename}' ({file_size_mb:.2f}MB) is too large for 8GB RAM Hierarchical parse. Bypassing ML models to prevent crash.")
                current_pipeline = "Ultra-Lite"
                result = self.ultra_lite_converter.convert(file_path)
            else:
                logger.info(f"Attempting Primary Hierarchical conversion for: {filename} ({file_size_mb:.2f}MB)")
                result = self.primary_converter.convert(file_path)
                
            # If the process didn't crash but return FAILURE (managed memory limit)
            if hasattr(result, "status") and str(result.status) == "ConversionStatus.FAILURE":
                logger.warning(f"Managed Memory Failure for {filename}. Retrying with Ultra-Lite safety net.")
                current_pipeline = "Ultra-Lite"
                result = self.ultra_lite_converter.convert(file_path)
                
        except Exception as e:
            logger.error(f"Ingestion attempt failed for {filename}: {str(e)}. Attempting Ultra-Lite safety net.")
            current_pipeline = "Ultra-Lite"
            result = self.ultra_lite_converter.convert(file_path)

        # 2. Safety Check: If results are missing entirely
        if not result or not result.document:
             raise Exception(f"CRITICAL: Resource Failure for {filename}. All Docling paths failed.")

        # 3. Apply Postprocessor (Only if we used high-fidelity Primary)
        if filename.lower().endswith(".pdf") and current_pipeline != "Ultra-Lite":
            try:
                ResultPostprocessor(result, source=os.path.abspath(file_path)).process()
            except Exception:
                pass
        
        # 4. Chunking
        chunks = self.chunker.chunk(result.document)
        
        # 5. Metadata Enrichment
        if explicit_roles and len(explicit_roles) > 0:
            access_roles = explicit_roles
        else:
            access_roles = self.role_mapping.get(collection, ["c_level"])
        
        langchain_docs = []
        
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
                "page_number": 0, # Standard default for Ultra-Lite
                "chunk_type": "text",
                "parent_chunk_id": f"parent_{i}"
            }
            
            # Try to get page number if available (might be present in some Docling doc items)
            try:
                if chunk.meta.doc_items and hasattr(chunk.meta.doc_items[0], "prov"):
                    metadata["page_number"] = chunk.meta.doc_items[0].prov[0].page_no
            except Exception:
                pass
            
            doc = Document(page_content=content, metadata=metadata)
            langchain_docs.append(doc)
            
        return langchain_docs

parsing_service = ParsingService()
