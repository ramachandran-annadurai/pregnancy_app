from flask import Flask, request, jsonify
from flask_cors import CORS
import pymongo
import bcrypt
import os
import uuid
import json
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string
import re
import jwt
from functools import wraps
from bson import ObjectId
import asyncio
import base64
import tempfile
# OCR and Document Processing imports
try:
    import fitz  # PyMuPDF for PDF processing
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("⚠️ PyMuPDF not available. Install with: pip install PyMuPDF")

try:
    from PIL import Image  # PIL for image processing
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️ PIL not available. Install with: pip install Pillow")

# Quantum and LLM imports
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("⚠️ SentenceTransformers not available. Install with: pip install sentence-transformers")

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue, PayloadSchemaType
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    print("⚠️ Qdrant client not available. Install with: pip install qdrant-client")

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI client not available. Install with: pip install openai")

# Load environment variables
load_dotenv()

# Type hints for Python 3.9+ compatibility
from typing import List, Dict, Any, Optional

# Import the complete PaddleOCR service from medication folder
import sys
import os

# Add medication folder to Python path
medication_path = os.path.join(os.path.dirname(__file__), 'medication', 'medication')
sys.path.insert(0, medication_path)

try:
    # Try to import the webhook services first (these don't require heavy dependencies)
    from app.services.webhook_service import WebhookService
    from app.services.webhook_config_service import WebhookConfigService
    from app.models.webhook_config import WebhookConfig
    
    # Try to import OCR services (these might require paddlepaddle)
    try:
        from app.services.enhanced_ocr_service import EnhancedOCRService
        from app.services.ocr_service import OCRService
        OCR_SERVICES_AVAILABLE = True
        print("✅ All PaddleOCR services imported successfully")
    except ImportError as ocr_error:
        print(f"⚠️ OCR services not available (likely missing paddlepaddle): {ocr_error}")
        print("💡 This is normal if paddlepaddle is not installed")
        OCR_SERVICES_AVAILABLE = False
        EnhancedOCRService = None
        OCRService = None
    
    PADDLE_OCR_AVAILABLE = True
    print(f"✅ Webhook services imported successfully from medication folder")
    print(f"🔍 Medication path: {medication_path}")
    print(f"🔍 Python path includes: {medication_path in sys.path}")
    
except ImportError as e:
    print(f"⚠️ Webhook services not available: {e}")
    print(f"🔍 Medication path: {medication_path}")
    print(f"🔍 Python path: {sys.path[:3]}...")  # Show first 3 paths
    PADDLE_OCR_AVAILABLE = False
    OCR_SERVICES_AVAILABLE = False
    WebhookService = None
    WebhookConfigService = None
    WebhookConfig = None
    EnhancedOCRService = None
    OCRService = None

# ==================== QUANTUM & LLM CONFIGURATION ====================

# Qdrant Vector Database Configuration
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "pregnancy_knowledge")
QDRANT_TIMEOUT_SEC = float(os.getenv("QDRANT_TIMEOUT_SEC", "60"))
QDRANT_BATCH_SIZE = int(os.getenv("QDRANT_BATCH_SIZE", "64"))

# Embeddings Configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
VECTOR_SIZE = int(os.getenv("VECTOR_SIZE", "384"))

# LLM Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# Retrieval Configuration
TOP_K = int(os.getenv("TOP_K", "5"))
RETRIEVAL_MIN_SCORE = float(os.getenv("RETRIEVAL_MIN_SCORE", "0.70"))

# User-visible text and prompts (dynamic via env)
DISCLAIMER_TEXT = os.getenv(
    "DISCLAIMER_TEXT",
    "This information is educational and not a medical diagnosis. If you have red-flag symptoms such as heavy bleeding, severe pain, high fever, severe headache with vision changes, reduced fetal movement, or feeling very unwell, seek urgent care immediately."
)

FALLBACK_STATIC_TEXT = os.getenv(
    "FALLBACK_STATIC_TEXT",
    "General guidance: rest, hydrate, track symptoms, avoid triggers, and contact your prenatal provider for advice."
)

FALLBACK_SYSTEM_PROMPT = os.getenv(
    "FALLBACK_SYSTEM_PROMPT",
    "You are a cautious pregnancy symptom assistant. Provide 3-5 concise, trimester-aware self-care suggestions, avoid medications/doses, include when to seek urgent care, and always add a medical disclaimer."
)

SUMMARY_SYSTEM_PROMPT = os.getenv(
    "SUMMARY_SYSTEM_PROMPT",
    "You are a cautious medical assistant supporting an obstetrician. Your ONLY knowledge source is the evidence bullets provided in the user message. Do NOT use outside knowledge. Primary task: Based on the evidence, determine the overall urgency level (mild, moderate, urgent) for the patient's symptoms. Provide a concise, trimester-specific guidance summary for a pregnant patient. Instructions: Use 3–5 short bullets. Include one bullet explicitly stating when to seek urgent care, based on evidence triage tags. Be clear, factual, and non-alarmist. If evidence is conflicting or insufficient, state that clearly. Do NOT invent facts not present in evidence. Do NOT recommend medications, dosages, diagnostic codes, or brand names. Do NOT make definitive diagnoses; frame as possible concerns and next steps. Keep lay-friendly tone; avoid jargon where possible. Assume this is general guidance, not a substitute for clinical judgment. Output format: Start with: 'Urgency level: <mild/moderate/urgent/uncertain>' Then list plain text bullets (no numbering, no markdown headings). Each bullet ≤ 25 words."
)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Database connection
class Database:
    def __init__(self):
        self.client = None
        self.patients_collection = None
        self.connect()
    
    def connect(self):
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
                db_name = os.getenv("DB_NAME", "patients_db")
                
                print(f"🔍 Attempting to connect to MongoDB (attempt {retry_count + 1}/{max_retries})...")
                print(f"🔍 URI: {mongo_uri}")
                print(f"🔍 Database: {db_name}")
                
                # Close existing connection if any
                if self.client:
                    try:
                        self.client.close()
                    except:
                        pass
                
                self.client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=10000)
                
                # Test the connection
                print("🔍 Testing connection with ping...")
                self.client.admin.command('ping')
                print("✅ MongoDB connection test successful")
                
                # Get database
                db = self.client[db_name]
                print(f"✅ Database '{db_name}' accessed successfully")
                
                # Initialize collections
                self.patients_collection = db["patients_v2"]
                self.mental_health_collection = db["mental_health_logs"]
                
                # Test collections exist and are accessible
                print(f"🔍 Testing collections...")
                print(f"🔍 Patients collection: {self.patients_collection.name}")
                print(f"🔍 Mental health collection: {self.mental_health_collection.name}")
                
                # Create indexes with error handling
                print("🔍 Creating indexes...")
                try:
                    self.patients_collection.create_index("patient_id", unique=True, sparse=True)
                    print("✅ patient_id index created")
                except Exception as e:
                    print(f"⚠️ patient_id index creation failed: {e}")
                
                try:
                    self.patients_collection.create_index("email", unique=True, sparse=True)
                    print("✅ email index created")
                except Exception as e:
                    print(f"⚠️ email index creation failed: {e}")
                
                try:
                    self.patients_collection.create_index("mobile", unique=True, sparse=True)
                    print("✅ mobile index created")
                except Exception as e:
                    print(f"⚠️ mobile index creation failed: {e}")
                
                # Mental health collection indexes - Drop old indexes first
                try:
                    print("🔍 Dropping old mental health indexes...")
                    self.mental_health_collection.drop_indexes()
                    print("✅ Old indexes dropped")
                except Exception as e:
                    print(f"⚠️ Index drop failed (may not exist): {e}")
                
                # Create new indexes
                try:
                    self.mental_health_collection.create_index("patient_id")
                    print("✅ mental_health patient_id index created")
                except Exception as e:
                    print(f"⚠️ mental_health patient_id index creation failed: {e}")
                
                try:
                    self.mental_health_collection.create_index("date")
                    print("✅ mental_health date index created")
                except Exception as e:
                    print(f"⚠️ mental_health date index creation failed: {e}")
                
                try:
                    # Create compound index WITHOUT unique constraint
                    self.mental_health_collection.create_index([("patient_id", 1), ("date", 1), ("type", 1)])
                    print("✅ mental_health compound index created (non-unique)")
                except Exception as e:
                    print(f"⚠️ mental_health compound index creation failed: {e}")
                
                print("✅ Connected to MongoDB successfully")
                print(f"✅ Database: {db_name}")
                print(f"✅ Collections: patients_v2, mental_health_logs")
                return  # Success, exit the retry loop
                
            except Exception as e:
                retry_count += 1
                print(f"❌ Database connection attempt {retry_count} failed: {e}")
                print(f"🔍 Error type: {type(e).__name__}")
                print(f"🔍 Full error: {str(e)}")
                
                if retry_count >= max_retries:
                    print(f"❌ All {max_retries} connection attempts failed")
                    self.patients_collection = None
                    self.mental_health_collection = None
                else:
                    print(f"🔄 Retrying in 2 seconds...")
                    import time
                    time.sleep(2)
    
    def close(self):
        if self.client:
            self.client.close()
    
    def is_connected(self):
        """Check if database is connected and accessible"""
        try:
            if self.client is None or self.patients_collection is None:
                return False
            
            # Test connection with a simple command
            self.client.admin.command('ping')
            return True
        except Exception as e:
            print(f"❌ Database connection check failed: {e}")
            return False
    
    def reconnect(self):
        """Attempt to reconnect to the database"""
        print("🔄 Attempting to reconnect to database...")
        self.connect()
        return self.is_connected()

# Initialize database
db = Database()

# ==================== MOCK N8N WEBHOOK SERVICE ====================

class MockN8NService:
    """Mock N8N service for testing webhook integration"""
    
    def process_prescription_webhook(self, webhook_data):
        """Simulate N8N workflow processing"""
        try:
            # Extract key information from webhook data
            patient_id = webhook_data.get('patient_id', 'unknown')
            medication_name = webhook_data.get('medication_name', 'unknown')
            extracted_text = webhook_data.get('extracted_text', '')
            filename = webhook_data.get('filename', 'unknown')
            
            # Simulate AI processing of prescription text
            processed_result = self._simulate_ai_processing(extracted_text)
            
            # Return structured N8N response
            return {
                'success': True,
                'message': 'Prescription processed by Mock N8N workflow',
                'workflow_id': 'mock_prescription_processor_001',
                'processing_time': '1.2s',
                'patient_id': patient_id,
                'filename': filename,
                'extracted_fields': processed_result['extracted_fields'],
                'confidence_score': processed_result['confidence'],
                'recommendations': processed_result['recommendations'],
                'ai_analysis': processed_result['ai_analysis'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Mock N8N processing failed: {str(e)}',
                'step': 'mock_processing_error'
            }
    
    def _simulate_ai_processing(self, text):
        """Simulate AI extraction of prescription fields"""
        text_lower = text.lower()
        
        # Extract medication information using pattern matching
        extracted_fields = {}
        
        # Medication name patterns
        if 'amoxicillin' in text_lower:
            extracted_fields['medication_name'] = 'Amoxicillin'
            extracted_fields['dosage'] = '500mg'
            extracted_fields['frequency'] = 'Three times daily'
            extracted_fields['duration'] = '7 days'
        elif 'paracetamol' in text_lower:
            extracted_fields['medication_name'] = 'Paracetamol'
            extracted_fields['dosage'] = '500mg'
            extracted_fields['frequency'] = 'Every 4-6 hours'
            extracted_fields['duration'] = 'As needed'
        elif 'vitamin' in text_lower:
            extracted_fields['medication_name'] = 'Vitamin Supplement'
            extracted_fields['dosage'] = '1 tablet'
            extracted_fields['frequency'] = 'Once daily'
            extracted_fields['duration'] = 'Ongoing'
        else:
            extracted_fields['medication_name'] = 'Unknown Medication'
            extracted_fields['dosage'] = 'As prescribed'
            extracted_fields['frequency'] = 'As prescribed'
            extracted_fields['duration'] = 'As prescribed'
        
        # Extract doctor information
        if 'dr.' in text_lower or 'doctor' in text_lower:
            extracted_fields['prescribed_by'] = 'Dr. Smith'
        else:
            extracted_fields['prescribed_by'] = 'Unknown'
        
        # Extract patient information
        if 'patient:' in text_lower:
            extracted_fields['patient_name'] = 'Jane Doe'
        
        # Generate AI analysis
        ai_analysis = {
            'text_complexity': 'medium',
            'extraction_confidence': 0.85,
            'key_phrases_found': len(extracted_fields),
            'processing_notes': 'Successfully extracted prescription details using pattern matching'
        }
        
        # Generate recommendations
        recommendations = [
            'Take medication as prescribed by your doctor',
            'Complete the full course of treatment',
            'Store in a cool, dry place',
            'Contact your doctor if you experience side effects'
        ]
        
        return {
            'extracted_fields': extracted_fields,
            'confidence': 0.85,
            'recommendations': recommendations,
            'ai_analysis': ai_analysis
        }

# ==================== OCR AND DOCUMENT PROCESSING SERVICE ====================

class OCRService:
    """OCR service for processing prescription documents, PDFs, and images"""
    
    def __init__(self):
        self.supported_formats = {
            'pdf': ['.pdf'],
            'text': ['.txt', '.doc', '.docx'],
            'image': ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
        }
        self.allowed_types = [
            'application/pdf',
            'text/plain',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'image/jpeg',
            'image/png',
            'image/bmp',
            'image/tiff'
        ]
    
    def get_file_type(self, filename: str) -> str:
        """Determine file type based on extension"""
        ext = os.path.splitext(filename.lower())[1]
        
        for file_type, extensions in self.supported_formats.items():
            if ext in extensions:
                return file_type
        
        return 'unknown'
    
    def validate_file_type(self, content_type: str, filename: str) -> bool:
        """Validate if file type is supported for processing"""
        # Handle missing or generic content types
        if not content_type or content_type == "":
            # Fallback to filename extension check
            file_type = self.get_file_type(filename)
            return file_type != 'unknown'
        
        # Check content type first
        if content_type in self.allowed_types:
            return True
        
        # Handle content types with parameters
        base_content_type = content_type.split(';')[0].strip()
        if base_content_type in self.allowed_types:
            return True
        
        # Handle generic binary types that might be PDFs
        if content_type in ["application/octet-stream", "binary/octet-stream", "application/binary"]:
            file_type = self.get_file_type(filename)
            return file_type != 'unknown'
        
        # Final fallback to filename extension check
        file_type = self.get_file_type(filename)
        return file_type != 'unknown'
    
    def process_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Process any supported file type and return unified results"""
        try:
            file_type = self.get_file_type(filename)
            
            if file_type == 'pdf':
                return self._process_pdf(file_content, filename)
            elif file_type == 'text':
                return self._process_text_file(file_content, filename)
            elif file_type == 'image':
                return self._process_image(file_content, filename)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported file type: {filename}",
                    "supported_types": list(self.supported_formats.keys())
                }
                
        except Exception as e:
            print(f"❌ Error processing file {filename}: {e}")
            return {
                "success": False,
                "error": f"Processing error: {str(e)}",
                "filename": filename
            }
    
    def _process_pdf(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Process PDF file (both native text and scanned pages)"""
        if not PYMUPDF_AVAILABLE:
            return {
                "success": False,
                "error": "PDF processing not available. Install PyMuPDF: pip install PyMuPDF"
            }
        
        try:
            # Open PDF with PyMuPDF
            pdf_document = fitz.open(stream=file_content, filetype="pdf")
            
            results = []
            total_pages = len(pdf_document)
            native_text_pages = 0
            ocr_pages = 0
            
            for page_num in range(total_pages):
                page = pdf_document[page_num]
                
                # Try to extract native text first
                text = page.get_text()
                
                if text.strip():
                    # Native text available
                    results.append({
                        "page": page_num + 1,
                        "text": text.strip(),
                        "confidence": 1.0,
                        "method": "native_text"
                    })
                    native_text_pages += 1
                else:
                    # No native text, might be scanned image
                    results.append({
                        "page": page_num + 1,
                        "text": "[Scanned page - text extraction not available]",
                        "confidence": 0.0,
                        "method": "scanned_page"
                    })
                    ocr_pages += 1
            
            pdf_document.close()
            
            # Extract full text for prescription processing
            full_text = "\n".join([result["text"] for result in results if result["method"] == "native_text"])
            
            return {
                "success": True,
                "filename": filename,
                "file_type": "pdf",
                "total_pages": total_pages,
                "native_text_pages": native_text_pages,
                "ocr_pages": ocr_pages,
                "results": results,
                "full_text": full_text,
                "extracted_text": full_text if full_text else "No extractable text found"
            }
            
        except Exception as e:
            print(f"❌ Error processing PDF {filename}: {e}")
            return {
                "success": False,
                "error": f"PDF processing error: {str(e)}",
                "filename": filename
            }
    
    def _process_text_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Process text files (TXT, DOC, DOCX)"""
        try:
            # Try to decode as UTF-8 first
            try:
                text = file_content.decode('utf-8')
            except UnicodeDecodeError:
                # Try other encodings
                text = file_content.decode('latin-1')
            
            return {
                "success": True,
                "filename": filename,
                "file_type": "text",
                "total_pages": 1,
                "native_text_pages": 1,
                "ocr_pages": 0,
                "results": [{
                    "page": 1,
                    "text": text,
                    "confidence": 1.0,
                    "method": "text_file"
                }],
                "full_text": text,
                "extracted_text": text
            }
            
        except Exception as e:
            print(f"❌ Error processing text file {filename}: {e}")
            return {
                "success": False,
                "error": f"Text file processing error: {str(e)}",
                "filename": filename
            }
    
    def _process_image(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Process image files (basic text extraction placeholder)"""
        if not PIL_AVAILABLE:
            return {
                "success": False,
                "error": "Image processing not available. Install Pillow: pip install Pillow"
            }
        
        try:
            # For now, return a placeholder since full OCR requires additional libraries
            # In a production system, you'd integrate with Tesseract OCR or cloud OCR services
            return {
                "success": True,
                "filename": filename,
                "file_type": "image",
                "total_pages": 1,
                "native_text_pages": 0,
                "ocr_pages": 1,
                "results": [{
                    "page": 1,
                    "text": "[Image file - OCR text extraction requires Tesseract or cloud OCR service]",
                    "confidence": 0.0,
                    "method": "image_placeholder"
                }],
                "full_text": "",
                "extracted_text": "Image processing available but OCR text extraction requires additional setup"
            }
            
        except Exception as e:
            print(f"❌ Error processing image {filename}: {e}")
            return {
                "success": False,
                "error": f"Image processing error: {str(e)}",
                "filename": filename
            }

# Initialize services
ocr_service = OCRService()
mock_n8n_service = MockN8NService()

# ==================== QUANTUM & LLM SERVICES ====================

class QuantumVectorService:
    """Quantum-inspired vector database service using Qdrant"""
    
    def __init__(self):
        self.client = None
        self.embedding_model = None
        self.initialize_services()
    
    def initialize_services(self):
        """Initialize Qdrant client and embedding model"""
        if QDRANT_AVAILABLE:
            try:
                self.client = QdrantClient(
                    url=QDRANT_URL,
                    api_key=QDRANT_API_KEY,
                    timeout=QDRANT_TIMEOUT_SEC,
                )
                print("✅ Qdrant client initialized successfully")
            except Exception as e:
                print(f"❌ Qdrant client initialization failed: {e}")
                self.client = None
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
                print("✅ Embedding model initialized successfully")
            except Exception as e:
                print(f"❌ Embedding model initialization failed: {e}")
                self.embedding_model = None
    
    def ensure_collection(self):
        """Ensure Qdrant collection exists with proper configuration"""
        if not self.client:
            return False
        
        try:
            collections = self.client.get_collections().collections
            names = {c.name for c in collections}
            
            if QDRANT_COLLECTION not in names:
                self.client.create_collection(
                    collection_name=QDRANT_COLLECTION,
                    vectors_config=VectorParams(
                        size=VECTOR_SIZE,
                        distance=Distance.COSINE,
                    ),
                )
                print(f"✅ Created Qdrant collection: {QDRANT_COLLECTION}")
            
            # Ensure payload indexes
            try:
                self.client.create_payload_index(
                    collection_name=QDRANT_COLLECTION,
                    field_name="trimester",
                    field_schema=PayloadSchemaType.KEYWORD,
                )
            except Exception:
                pass  # Index might already exist
            
            return True
        except Exception as e:
            print(f"❌ Collection setup failed: {e}")
            return False
    
    def embed_text(self, text: str) -> list:
        """Generate embeddings for text using sentence transformers"""
        if not self.embedding_model:
            return []
        
        try:
            vector = self.embedding_model.encode([text], normalize_embeddings=True)
            return vector[0].tolist()
        except Exception as e:
            print(f"❌ Text embedding failed: {e}")
            return []
    
    def build_trimester_filter(self, weeks_pregnant: int) -> Filter:
        """Build trimester filter for vector search"""
        if not self.client:
            return None
        
        if weeks_pregnant <= 0:
            return None
        
        trimester = "first" if weeks_pregnant <= 13 else ("second" if weeks_pregnant <= 27 else "third")
        
        return Filter(
            should=[
                FieldCondition(key="trimester", match=MatchValue(value=trimester)),
                FieldCondition(key="trimester", match=MatchValue(value="all")),
            ]
        )
    
    def search_knowledge(self, query_text: str, weeks_pregnant: int) -> list:
        """Search pregnancy knowledge base using vector similarity"""
        if not self.client or not self.embedding_model:
            return []
        
        try:
            # Generate query embedding
            query_vector = self.embed_text(query_text)
            if not query_vector:
                return []
            
            # Build trimester filter
            trimester_filter = self.build_trimester_filter(weeks_pregnant)
            
            # Search Qdrant
            results = self.client.search(
                collection_name=QDRANT_COLLECTION,
                query_vector=query_vector,
                limit=TOP_K,
                query_filter=trimester_filter,
                with_payload=True,
                score_threshold=RETRIEVAL_MIN_SCORE
            )
            
            # Format results
            suggestions = []
            for hit in results:
                payload = hit.payload or {}
                suggestions.append({
                    "id": str(hit.id),
                    "text": payload.get("text", ""),
                    "metadata": {
                        "source": payload.get("source", ""),
                        "tags": payload.get("tags", []),
                        "triage": payload.get("triage", ""),
                        "trimester": payload.get("trimester", ""),
                    },
                    "score": float(hit.score) if hit.score is not None else None,
                })
            
            return suggestions
        except Exception as e:
            print(f"❌ Knowledge search failed: {e}")
            return []

class LLMService:
    """LLM service for symptom analysis and recommendations"""
    
    def __init__(self):
        self.client = None
        self.initialize_client()
    
    def initialize_client(self):
        """Initialize OpenAI client"""
        if OPENAI_AVAILABLE and OPENAI_API_KEY:
            try:
                self.client = OpenAI(api_key=OPENAI_API_KEY)
                print("✅ OpenAI client initialized successfully")
            except Exception as e:
                print(f"❌ OpenAI client initialization failed: {e}")
                self.client = None
        else:
            print("⚠️ OpenAI not available - using fallback responses")
    
    def detect_red_flags(self, text: str) -> list:
        """Detect red flag symptoms in text"""
        flags = []
        lower_text = text.lower()
        
        if any(k in lower_text for k in ["bleeding", "spotting", "blood"]):
            flags.append("vaginal bleeding")
        if any(k in lower_text for k in ["severe pain", "sharp pain", "worst pain"]):
            flags.append("severe pain")
        if any(k in lower_text for k in ["vision", "blurry", "flashing lights"]):
            flags.append("vision changes")
        if any(k in lower_text for k in ["fever", "temperature", "high temp"]):
            flags.append("fever")
        if any(k in lower_text for k in ["reduced movement", "less movement", "not moving"]):
            flags.append("reduced fetal movement")
        
        return flags
    
    def generate_llm_fallback(self, symptom_text: str, weeks_pregnant: int) -> dict:
        """Generate LLM-powered fallback response"""
        red_flags = self.detect_red_flags(symptom_text)
        
        if self.client:
            try:
                trimester = "first" if weeks_pregnant <= 13 else ("second" if weeks_pregnant <= 27 else "third")
                
                response = self.client.chat.completions.create(
                    model=LLM_MODEL,
                    messages=[
                        {"role": "system", "content": FALLBACK_SYSTEM_PROMPT},
                        {"role": "user", "content": f"User symptom text: '{symptom_text}'. Weeks pregnant: {weeks_pregnant} (trimester: {trimester}). If any red flags, state them and advise urgent care."}
                    ],
                    temperature=0.2,
                )
                content = response.choices[0].message.content.strip()
            except Exception as e:
                print(f"⚠️ LLM fallback failed: {e}")
                content = FALLBACK_STATIC_TEXT
        else:
            content = FALLBACK_STATIC_TEXT
        
        suggestions = [
            {
                "id": "fallback-1",
                "text": content,
                "metadata": {
                    "triage": "use clinical judgment; follow red-flag guidance",
                    "source": "LLM-fallback" if self.client else "static-fallback",
                },
                "score": None,
            }
        ]
        
        if red_flags:
            suggestions.insert(0, {
                "id": "fallback-urgent",
                "text": f"Your description suggests potential red flags ({', '.join(red_flags)}) — please seek urgent care or contact your provider immediately.",
                "metadata": {"triage": "urgent", "source": "safety-check"},
                "score": None,
            })
        
        return {
            "suggestions": suggestions,
            "disclaimers": DISCLAIMER_TEXT,
            "red_flags": red_flags
        }
    
    def summarize_retrieval(self, symptom_text: str, weeks_pregnant: int, suggestions: list) -> dict:
        """Summarize retrieved suggestions using LLM"""
        if not suggestions or not self.client:
            return None
        
        try:
            trimester = "first" if weeks_pregnant <= 13 else ("second" if weeks_pregnant <= 27 else "third")
            
            # Build evidence from top suggestions
            top_suggestions = suggestions[:3]
            evidence = "\n".join(
                f"- [triage: {s.get('metadata', {}).get('triage', 'unspecified')}] {s.get('text', '')}"
                for s in top_suggestions
            )
            
            response = self.client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                    {"role": "user", "content": f"User symptom text: '{symptom_text}'. Weeks pregnant: {weeks_pregnant} (trimester: {trimester}). Evidence bullets (use ONLY these):\n{evidence}"}
                ],
                temperature=0.2,
            )
            content = response.choices[0].message.content.strip()
            
            return {
                "id": "synthesis-1",
                "text": content,
                "metadata": {
                    "source": "LLM-summary",
                    "evidence_ids": [s.get("id") for s in top_suggestions],
                    "triage": "summary",
                },
                "score": None,
            }
        except Exception as e:
            print(f"⚠️ LLM summarization failed: {e}")
            return None

# Initialize quantum and LLM services
quantum_service = QuantumVectorService()
llm_service = LLMService()

# User Activity Tracking System
class UserActivityTracker:
    """Track all user activities from login to logout"""
    
    def __init__(self, db):
        self.db = db
        self.activities_collection = db.client[os.getenv("DB_NAME", "patients_db")]["user_activities"]
        
        # Create indexes for efficient querying
        self.activities_collection.create_index("user_email")
        self.activities_collection.create_index("session_id")
        self.activities_collection.create_index("timestamp")
        self.activities_collection.create_index("activity_type")
        print("✅ User Activity Tracker initialized")
    
    def start_user_session(self, user_email, user_role, username, user_id):
        """Start tracking a new user session"""
        session_id = str(uuid.uuid4())
        session_start = datetime.now()
        
        session_data = {
            "session_id": session_id,
            "user_email": user_email,
            "user_role": user_role,
            "username": username,
            "user_id": user_id,
            "session_start": session_start,
            "session_end": None,
            "is_active": True,
            "activities": [],
            "created_at": session_start
        }
        
        result = self.activities_collection.insert_one(session_data)
        print(f"🔍 Started tracking session {session_id} for user {user_email}")
        return session_id
    
    def end_user_session(self, user_email, session_id=None):
        """End a user session"""
        if session_id:
            # End specific session
            result = self.activities_collection.update_one(
                {"session_id": session_id, "is_active": True},
                {
                    "$set": {
                        "session_end": datetime.now(),
                        "is_active": False
                    }
                }
            )
        else:
            # End all active sessions for user
            result = self.activities_collection.update_many(
                {"user_email": user_email, "is_active": True},
                {
                    "$set": {
                        "session_end": datetime.now(),
                        "is_active": False
                    }
                }
            )
        
        print(f"🔍 Ended session(s) for user {user_email}")
        return result.modified_count
    
    def log_activity(self, user_email, activity_type, activity_data, session_id=None):
        """Log a user activity"""
        if not session_id:
            # Find active session for user
            active_session = self.activities_collection.find_one(
                {"user_email": user_email, "is_active": True}
            )
            if active_session:
                session_id = active_session["session_id"]
            else:
                print(f"⚠️ No active session found for user {user_email}")
                return None
        
        activity_entry = {
            "activity_id": str(uuid.uuid4()),
            "timestamp": datetime.now(),
            "activity_type": activity_type,
            "activity_data": activity_data,
            "ip_address": request.remote_addr if request else "unknown"
        }
        
        # Add activity to session
        result = self.activities_collection.update_one(
            {"session_id": session_id},
            {"$push": {"activities": activity_entry}}
        )
        
        print(f"🔍 Logged activity: {activity_type} for user {user_email}")
        return activity_entry["activity_id"]
    
    def get_user_activities(self, user_email, limit=100):
        """Get all activities for a user"""
        sessions = list(self.activities_collection.find(
            {"user_email": user_email},
            {"_id": 0}
        ).sort("created_at", -1).limit(limit))
        
        return sessions
    
    def get_session_activities(self, session_id):
        """Get all activities for a specific session"""
        session = self.activities_collection.find_one(
            {"session_id": session_id},
            {"_id": 0}
        )
        return session
    
    def get_activity_summary(self, user_email):
        """Get summary of user activities"""
        pipeline = [
            {"$match": {"user_email": user_email}},
            {"$unwind": "$activities"},
            {"$group": {
                "_id": "$activities.activity_type",
                "count": {"$sum": 1},
                "last_activity": {"$max": "$activities.timestamp"}
            }},
            {"$sort": {"count": -1}}
        ]
        
        summary = list(self.activities_collection.aggregate(pipeline))
        return summary

# Initialize activity tracker
activity_tracker = UserActivityTracker(db)

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24  # Token expires in 24 hours

def generate_jwt_token(user_data):
    """Generate JWT token for user"""
    payload = {
        "user_id": str(user_data.get("_id")) if user_data.get("_id") else None,
        "patient_id": user_data.get("patient_id"),
        "email": user_data.get("email"),
        "username": user_data.get("username"),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token):
    """Verify JWT token and return user data"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    """Decorator to require JWT token for protected routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({"error": "Invalid token format"}), 401
        
        if not token:
            return jsonify({"error": "Token is missing"}), 401
        
        # Verify token
        payload = verify_jwt_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        # Add user data to request
        request.user_data = payload
        return f(*args, **kwargs)
    
    return decorated

# Utility functions
def generate_patient_id():
    """Generate unique patient ID with timestamp and random component"""
    import time
    timestamp = int(time.time())
    random_component = uuid.uuid4().hex[:6].upper()
    return f"PAT{timestamp}{random_component}"

def generate_unique_patient_id():
    """Generate a unique patient ID that doesn't exist in database"""
    max_attempts = 10
    for attempt in range(max_attempts):
        patient_id = generate_patient_id()
        
        # Check if this patient ID already exists
        if db.patients_collection is not None:
            existing_patient = db.patients_collection.find_one({"patient_id": patient_id})
            if existing_patient is None:
                return patient_id
        
        # If we've tried too many times, add a random suffix
        if attempt == max_attempts - 1:
            extra_random = uuid.uuid4().hex[:4].upper()
            patient_id = f"{patient_id}{extra_random}"
            return patient_id
    
    # Fallback: use timestamp with more random components
    timestamp = int(time.time() * 1000)  # Use milliseconds
    random_component = uuid.uuid4().hex[:8].upper()
    return f"PAT{timestamp}{random_component}"

def generate_otp():
    """Generate 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def send_email(to_email: str, subject: str, body: str) -> bool:
    """Send email using Gmail SMTP"""
    try:
        sender_email = os.getenv("SENDER_EMAIL")
        sender_password = os.getenv("SENDER_PASSWORD")
        
        if not sender_email or not sender_password:
            print("Email configuration missing - using mock email")
            return True  # Mock success for testing
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return True  # Mock success for testing

def send_otp_email(email: str, otp: str) -> bool:
    """Send OTP email"""
    subject = "Patient Alert System - OTP Verification"
    body = f"""
    Hello!
    
    Your OTP for Patient Alert System is: {otp}
    
    This OTP is valid for 10 minutes.
    
    If you didn't request this, please ignore this email.
    
    Best regards,
    Patient Alert System Team
    """
    return send_email(email, subject, body)

def send_patient_id_email(email: str, patient_id: str, username: str) -> bool:
    """Send Patient ID to user's email"""
    try:
        subject = "Your Patient ID - Patient Alert System"
        body = f"""
Hello {username},

Your Patient ID has been generated successfully.

Patient ID: {patient_id}

Please keep this ID safe and use it to log in to your account.

Best regards,
Patient Alert System Team
        """
        
        return send_email(email, subject, body)
    except Exception as e:
        print(f"Error sending Patient ID email: {e}")
        return False

def send_medication_reminder_email(email: str, username: str, medication_name: str, dosage: str, time: str, frequency: str, special_instructions: str = "") -> bool:
    """Send medication reminder email to user"""
    try:
        subject = f"Medication Reminder: {medication_name}"
        body = f"""
Hello {username},

It's time to take your medication!

Medication: {medication_name}
Dosage: {dosage}
Time: {time}
Frequency: {frequency}
{f"Special Instructions: {special_instructions}" if special_instructions else ""}

Please take your medication as prescribed by your doctor.

Best regards,
Patient Alert System Team
        """
        
        return send_email(email, subject, body)
    except Exception as e:
        print(f"Error sending medication reminder email: {e}")
        return False

def check_and_send_medication_reminders():
    """Check all patients for upcoming medication dosages and send email reminders"""
    try:
        print("🔍 Checking for medication reminders...")
        
        # Get all patients
        patients = db.patients_collection.find({})
        current_time = datetime.now()
        
        reminders_sent = 0
        
        for patient in patients:
            try:
                patient_id = patient.get('patient_id')
                email = patient.get('email')
                username = patient.get('username')
                
                if not all([patient_id, email, username]):
                    continue
                
                # Get medication logs for this patient
                medication_logs = patient.get('medication_logs', [])
                
                for log in medication_logs:
                    if not log.get('is_prescription_mode', False):
                        # Handle multiple dosages
                        dosages = log.get('dosages', [])
                        for dosage in dosages:
                            if dosage.get('reminder_enabled', False):
                                try:
                                    time_str = dosage.get('time', '')
                                    if time_str:
                                        hour, minute = map(int, time_str.split(':'))
                                        dose_time = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
                                        
                                        # Check if it's time to send reminder (within 15 minutes of dose time)
                                        time_diff = abs((current_time - dose_time).total_seconds() / 60)
                                        
                                        if time_diff <= 15:  # Within 15 minutes
                                            # Check if we already sent a reminder for this dose today
                                            reminder_key = f"reminder_{patient_id}_{log['medication_name']}_{time_str}_{current_time.strftime('%Y-%m-%d')}"
                                            
                                            # For now, we'll send reminders every time (you can implement reminder tracking later)
                                            if send_medication_reminder_email(
                                                email=email,
                                                username=username,
                                                medication_name=log.get('medication_name', 'Unknown'),
                                                dosage=dosage.get('dosage', ''),
                                                time=time_str,
                                                frequency=dosage.get('frequency', ''),
                                                special_instructions=dosage.get('special_instructions', '')
                                            ):
                                                reminders_sent += 1
                                                print(f"✅ Medication reminder sent to {email} for {log.get('medication_name')} at {time_str}")
                                            else:
                                                print(f"❌ Failed to send medication reminder to {email}")
                                                
                                except Exception as e:
                                    print(f"⚠️ Error processing dosage reminder for patient {patient_id}: {e}")
                                    continue
                                    
            except Exception as e:
                print(f"⚠️ Error processing patient {patient.get('patient_id', 'unknown')}: {e}")
                continue
        
        print(f"✅ Medication reminder check completed. {reminders_sent} reminders sent.")
        return reminders_sent
        
    except Exception as e:
        print(f"❌ Error in medication reminder service: {e}")
        return 0

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    try:
        # Ensure password is string and encode it
        if isinstance(password, bytes):
            password = password.decode('utf-8')
        password_bytes = password.encode('utf-8')
        
        # Ensure hashed is string and encode it
        if isinstance(hashed, bytes):
            hashed = hashed.decode('utf-8')
        hashed_bytes = hashed.encode('utf-8')
        
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

def validate_email(email: str) -> bool:
    """Validate email format"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

def validate_mobile(mobile: str) -> bool:
    """Validate mobile number"""
    return mobile.isdigit() and len(mobile) >= 10

def is_profile_complete(patient_doc: dict) -> bool:
    """Check if patient profile is complete"""
    required_fields = ['first_name', 'last_name', 'date_of_birth', 'blood_type']
    return all(field in patient_doc for field in required_fields)

# API Routes
@app.route('/')
def root():
    """Root endpoint"""
    return jsonify({
        "message": "Patient Alert System API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "POST /signup - Register new patient",
            "POST /send-otp - Send OTP to email",
            "POST /verify-otp - Verify OTP and activate account",
            "POST /login - Login with Patient ID/Email",
            "POST /forgot-password - Send password reset OTP",
            "POST /reset-password - Reset password with OTP",
            "POST /complete-profile - Complete patient profile",
            "GET /profile/<patient_id> - Get patient profile",
            "POST /symptoms/assist - Get pregnancy symptom assistance (Quantum+LLM)",
            "POST /symptoms/save-symptom-log - Save symptom log",
            "POST /symptoms/save-analysis-report - Save symptom analysis report",
            "GET /symptoms/get-symptom-history/<patient_id> - Get symptom history",
            "GET /symptoms/get-analysis-reports/<patient_id> - Get AI analysis reports",
            "POST /medication/save-medication-log - Save medication log",
            "GET /medication/get-medication-history/<patient_id> - Get medication history",
            "POST /medication/process-prescription-document - Process prescription document with PaddleOCR",
            "POST /medication/process-with-paddleocr - Process prescription with medication folder PaddleOCR service",
            "POST /medication/process-prescription-text - Process prescription text for structured extraction",
            "POST /medication/save-tablet-tracking - Save tablet tracking in medication_daily_tracking array",
            "GET /medication/get-tablet-tracking-history/<patient_id> - Get tablet tracking history from medication_daily_tracking array",
            "GET /symptoms/health - Symptom service health check",
            "GET /quantum/health - Quantum vector service health",
            "GET /quantum/collections - Get Qdrant collections",
            "GET /quantum/collection-status/<name> - Get collection status",
            "POST /quantum/add-knowledge - Add knowledge to vector DB",
            "POST /quantum/search-knowledge - Search knowledge base",
            "GET /llm/health - LLM service health",
            "POST /llm/test - Test LLM functionality",
            "GET / - API information",
            "POST /medication/send-reminders - Manually trigger medication reminder check and send emails",
            "POST /medication/test-reminder/<patient_id> - Test medication reminder email for a specific patient",
            "GET /nutrition/health - Nutrition service health check",
            "POST /nutrition/transcribe - Transcribe audio using Whisper AI",
            "POST /nutrition/analyze-with-gpt4 - Analyze food using GPT-4",
            "POST /nutrition/save-food-entry - Save basic food entry",
            "GET /nutrition/get-food-entries/<user_id> - Get food entries from patient's food_data array",
            "GET /nutrition/debug-food-data/<user_id> - Debug food data structure"
        ]
    })

@app.route('/signup', methods=['POST'])
def signup():
    """Register a new patient - Step 1: Collect data and send OTP"""
    try:
        if db.patients_collection is None:
            return jsonify({"error": "Database not connected"}), 500
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'mobile', 'password']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        username = data['username'].strip()
        email = data['email'].strip()
        mobile = data['mobile'].strip()
        password = data['password']
        
        # Validate email and mobile
        if not validate_email(email):
            return jsonify({"error": "Invalid email format"}), 400
        
        if not validate_mobile(mobile):
            return jsonify({"error": "Invalid mobile number"}), 400
        
        # Check if username exists
        if db.patients_collection.find_one({"username": username}):
            return jsonify({"error": "Username already exists"}), 400
        
        # Check if email exists
        if db.patients_collection.find_one({"email": email}):
            return jsonify({"error": "Email already exists"}), 400
        
        # Check if mobile exists
        if db.patients_collection.find_one({"mobile": mobile}):
            return jsonify({"error": "Mobile number already exists"}), 400
        
        # Generate OTP
        otp = generate_otp()
        
        # Store temporary signup data (not a real account yet)
        temp_signup_data = {
            "username": username,
            "email": email,
            "mobile": mobile,
            "password_hash": hash_password(password),
            "otp": otp,
            "otp_created_at": datetime.now(),
            "otp_expires_at": datetime.now() + timedelta(minutes=10),
            "status": "temp_signup",
            "created_at": datetime.now()
        }
        
        # Store in temporary collection or with temp status
        db.patients_collection.insert_one(temp_signup_data)
        
        # Send OTP email
        if send_otp_email(email, otp):
            return jsonify({
                "email": email,
                "status": "otp_sent",
                "message": "Please check your email for OTP verification."
            }), 200
        else:
            # Remove temporary data if email failed
            db.patients_collection.delete_one({"email": email, "status": "temp_signup"})
            return jsonify({"error": "Failed to send OTP email"}), 500
    
    except Exception as e:
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500

@app.route('/send-otp', methods=['POST'])
def send_otp():
    """Send OTP to email for verification"""
    try:
        if db.patients_collection is None:
            return jsonify({"error": "Database not connected"}), 500
        
        data = request.get_json()
        email = data.get('email', '').strip()
        
        if not email:
            return jsonify({"error": "Email is required"}), 400
        
        # Check if user exists
        user = db.patients_collection.find_one({"email": email})
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Generate OTP
        otp = generate_otp()
        
        # Store OTP in database (with expiration)
        db.patients_collection.update_one(
            {"email": email},
            {
                "$set": {
                    "otp": otp,
                    "otp_created_at": datetime.now(),
                    "otp_expires_at": datetime.now() + timedelta(minutes=10)
                }
            }
        )
        
        # Send OTP email
        if send_otp_email(email, otp):
            return jsonify({
                "message": "OTP sent successfully",
                "email": email
            }), 200
        else:
            return jsonify({"error": "Failed to send OTP email"}), 500
    
    except Exception as e:
        return jsonify({"error": f"OTP sending failed: {str(e)}"}), 500

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    """Verify OTP and create actual account"""
    try:
        if db.patients_collection is None:
            return jsonify({"error": "Database not connected"}), 500
        
        data = request.get_json()
        email = data.get('email', '').strip()
        otp = data.get('otp', '').strip()
        
        if not email or not otp:
            return jsonify({"error": "Email and OTP are required"}), 400
        
        # Find temporary signup data by email
        temp_user = db.patients_collection.find_one({"email": email, "status": "temp_signup"})
        if not temp_user:
            return jsonify({"error": "No pending signup found for this email"}), 404
        
        # Check OTP
        if temp_user.get("otp") != otp:
            return jsonify({"error": "Invalid OTP"}), 400
        
        # Check if OTP expired
        if temp_user.get("otp_expires_at") < datetime.now():
            return jsonify({"error": "OTP has expired"}), 400
        
        # Generate unique patient ID for actual account
        patient_id = generate_unique_patient_id()
        
        # Create actual account by updating the temporary data
        db.patients_collection.update_one(
            {"email": email, "status": "temp_signup"},
            {
                "$set": {
                    "patient_id": patient_id,
                    "status": "active",
                    "email_verified": True,
                    "verified_at": datetime.now()
                },
                "$unset": {
                    "otp": "",
                    "otp_created_at": "",
                    "otp_expires_at": ""
                }
            }
        )
        
        # Send Patient ID email
        send_patient_id_email(email, patient_id, temp_user["username"])
        
        # Get the updated user data
        updated_user = db.patients_collection.find_one({"patient_id": patient_id})
        
        # Generate JWT token
        token = generate_jwt_token(updated_user)
        
        return jsonify({
            "patient_id": patient_id,
            "username": temp_user["username"],
            "email": temp_user["email"],
            "mobile": temp_user["mobile"],
            "status": "active",
            "token": token,
            "message": "Account created and verified successfully! Your Patient ID has been sent to your email."
        }), 200
    
    except Exception as e:
        return jsonify({"error": f"OTP verification failed: {str(e)}"}), 500

@app.route('/login', methods=['POST'])
def login():
    """Login patient with Patient ID/Email and password"""
    try:
        # Check database connection and attempt reconnection if needed
        if not db.is_connected():
            print("⚠️ Database not connected during login, attempting reconnection...")
            if not db.reconnect():
                return jsonify({"error": "Database connection error - unable to reconnect"}), 503
        
        if db.patients_collection is None:
            return jsonify({"error": "Database not connected"}), 500
        
        data = request.get_json()
        login_identifier = data.get('login_identifier', '').strip()
        password = data.get('password', '')
        
        if not login_identifier or not password:
            return jsonify({"error": "Login identifier and password are required"}), 400
        
        # Find user by Patient ID or Email
        user = db.patients_collection.find_one({"patient_id": login_identifier})
        if not user:
            user = db.patients_collection.find_one({"email": login_identifier})
        
        if not user:
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Check if account is active
        if user.get("status") != "active":
            return jsonify({"error": "Account not activated. Please verify your email."}), 401
        
        # Verify password
        if not verify_password(password, user["password_hash"]):
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Check profile completion
        profile_complete = is_profile_complete(user)
        
        # Debug logging to identify null values
        print(f"🔍 Login Debug - User Data:")
        print(f"  patient_id: {user.get('patient_id')}")
        print(f"  username: {user.get('username')}")
        print(f"  email: {user.get('email')}")
        print(f"  _id: {user.get('_id')}")
        print(f"  status: {user.get('status')}")
        print(f"  profile_complete: {profile_complete}")
        
        # Generate JWT token
        token = generate_jwt_token(user)
        
        # Start tracking user session
        session_id = activity_tracker.start_user_session(
            user_email=user["email"],
            user_role="patient",
            username=user["username"],
            user_id=user["patient_id"]
        )
        
        # Log login activity
        activity_tracker.log_activity(
            user_email=user["email"],
            activity_type="login",
            activity_data={
                "login_method": "email" if "@" in login_identifier else "patient_id",
                "profile_complete": profile_complete,
                "session_id": session_id
            },
            session_id=session_id
        )
        
        return jsonify({
            "patient_id": user.get("patient_id", ""),
            "username": user.get("username", ""),
            "email": user.get("email", ""),
            "object_id": str(user.get("_id", "")) if user.get("_id") else "",  # Handle null Object ID
            "is_profile_complete": profile_complete,
            "token": token,
            "session_id": session_id,  # Include session ID for tracking
            "message": "Login successful" if profile_complete else "Login successful. Please complete your profile."
        }), 200
    
    except Exception as e:
        return jsonify({"error": f"Login failed: {str(e)}"}), 500

@app.route('/logout', methods=['POST'])
def logout():
    """Logout user and end session tracking"""
    try:
        data = request.get_json()
        user_email = data.get('email')
        session_id = data.get('session_id')
        
        if not user_email:
            return jsonify({"error": "User email is required"}), 400
        
        # Log logout activity before ending session
        activity_tracker.log_activity(
            user_email=user_email,
            activity_type="logout",
            activity_data={
                "logout_time": datetime.now().isoformat(),
                "session_id": session_id
            },
            session_id=session_id
        )
        
        # End user session
        ended_sessions = activity_tracker.end_user_session(user_email, session_id)
        
        return jsonify({
            "success": True,
            "message": "Logout successful",
            "ended_sessions": ended_sessions
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Logout failed: {str(e)}"}), 500

@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Send password reset OTP"""
    try:
        if db.patients_collection is None:
            return jsonify({"error": "Database not connected"}), 500
        
        data = request.get_json()
        login_identifier = data.get('login_identifier', '').strip()
        
        if not login_identifier:
            return jsonify({"error": "Login identifier is required"}), 400
        
        # Find user by Patient ID or Email
        user = db.patients_collection.find_one({"patient_id": login_identifier})
        if not user:
            user = db.patients_collection.find_one({"email": login_identifier})
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        email = user["email"]
        
        # Generate OTP
        otp = generate_otp()
        
        # Store OTP
        db.patients_collection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "reset_otp": otp,
                    "reset_otp_created_at": datetime.now(),
                    "reset_otp_expires_at": datetime.now() + timedelta(minutes=10)
                }
            }
        )
        
        # Send OTP email
        if send_otp_email(email, otp):
            return jsonify({
                "message": "Password reset OTP sent successfully",
                "email": email
            }), 200
        else:
            return jsonify({"error": "Failed to send OTP email"}), 500
    
    except Exception as e:
        return jsonify({"error": f"Password reset failed: {str(e)}"}), 500

@app.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password with OTP"""
    try:
        if db.patients_collection is None:
            return jsonify({"error": "Database not connected"}), 500
        
        data = request.get_json()
        email = data.get('email', '').strip()
        otp = data.get('otp', '').strip()
        new_password = data.get('new_password', '')
        
        if not email or not otp or not new_password:
            return jsonify({"error": "Email, OTP, and new password are required"}), 400
        
        # Find user by email
        user = db.patients_collection.find_one({"email": email})
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Check OTP
        if user.get("reset_otp") != otp:
            return jsonify({"error": "Invalid OTP"}), 400
        
        # Check if OTP expired
        if user.get("reset_otp_expires_at") < datetime.now():
            return jsonify({"error": "OTP has expired"}), 400
        
        # Hash new password
        new_hashed_password = hash_password(new_password)
        
        # Update password
        db.patients_collection.update_one(
            {"email": email},
            {
                "$set": {
                    "password_hash": new_hashed_password,
                    "password_updated_at": datetime.now()
                },
                "$unset": {
                    "reset_otp": "",
                    "reset_otp_created_at": "",
                    "reset_otp_expires_at": ""
                }
            }
        )
        
        return jsonify({
            "patient_id": user.get("patient_id", ""),
            "username": user.get("username", ""),
            "email": user["email"],
            "mobile": user.get("mobile", ""),
            "status": "active",
            "message": "Password reset successfully"
        }), 200
    
    except Exception as e:
        return jsonify({"error": f"Password reset failed: {str(e)}"}), 500

@app.route('/complete-profile', methods=['POST'])
@token_required
def complete_profile():
    """Complete patient profile information"""
    try:
        if db.patients_collection is None:
            return jsonify({"error": "Database not connected"}), 500
        
        # Get patient_id from JWT token
        patient_id = request.user_data.get('patient_id')
        
        if not patient_id:
            return jsonify({"error": "Patient ID not found in token"}), 400
        
        # Find user by Patient ID
        user = db.patients_collection.find_one({"patient_id": patient_id})
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Extract profile data with safe handling of null values
        first_name = request.json.get('first_name', '').strip() if request.json.get('first_name') else ''
        last_name = request.json.get('last_name', '').strip() if request.json.get('last_name') else ''
        date_of_birth = request.json.get('date_of_birth', '').strip() if request.json.get('date_of_birth') else ''
        blood_type = request.json.get('blood_type', '').strip() if request.json.get('blood_type') else ''
        is_pregnant = request.json.get('is_pregnant', False)
        last_period_date = request.json.get('last_period_date', '').strip() if request.json.get('last_period_date') else ''
        weight = request.json.get('weight', '').strip() if request.json.get('weight') else ''
        height = request.json.get('height', '').strip() if request.json.get('height') else ''
        
        # Emergency contact
        emergency_contact = {
            "name": request.json.get('emergency_name', '').strip() if request.json.get('emergency_name') else '',
            "relationship": request.json.get('emergency_relationship', '').strip() if request.json.get('emergency_relationship') else '',
            "phone": request.json.get('emergency_phone', '').strip() if request.json.get('emergency_phone') else ''
        }
        
        # Calculate age
        age = None
        if date_of_birth:
            try:
                from datetime import datetime
                birth_date = datetime.strptime(date_of_birth, '%Y-%m-%d')
                today = datetime.now()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            except:
                age = None
        
        # Calculate pregnancy information if pregnant
        calculated_pregnancy_week = None
        calculated_expected_delivery = None
        
        if is_pregnant and last_period_date:
            try:
                from datetime import datetime, timedelta
                last_period = datetime.strptime(last_period_date, '%Y-%m-%d')
                today = datetime.now()
                
                # Calculate pregnancy week (gestational age)
                days_diff = (today - last_period).days
                calculated_pregnancy_week = max(1, min(42, days_diff // 7))
                
                # Calculate expected delivery date (40 weeks from last period)
                calculated_expected_delivery = last_period + timedelta(weeks=40)
                calculated_expected_delivery = calculated_expected_delivery.strftime('%Y-%m-%d')
                
            except Exception as e:
                print(f"Error calculating pregnancy dates: {e}")
        
        # Update profile
        update_data = {
            "first_name": first_name,
            "last_name": last_name,
            "date_of_birth": date_of_birth,
            "age": age,
            "blood_type": blood_type,
            "weight": weight,
            "height": height,
            "is_pregnant": is_pregnant,
            "last_period_date": last_period_date if is_pregnant else None,
            "pregnancy_week": calculated_pregnancy_week if is_pregnant else None,
            "expected_delivery_date": calculated_expected_delivery if is_pregnant else None,
            "emergency_contact": emergency_contact,
            "profile_completed_at": datetime.now()
        }
        
        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        db.patients_collection.update_one(
            {"patient_id": patient_id},
            {"$set": update_data}
        )
        
        return jsonify({
            "patient_id": patient_id,
            "message": "Profile completed successfully",
            "is_profile_complete": True
        }), 200
    
    except Exception as e:
        return jsonify({"error": f"Profile completion failed: {str(e)}"}), 500

@app.route('/verify-token', methods=['POST'])
def verify_token():
    """Verify JWT token and return user data"""
    try:
        data = request.get_json()
        token = data.get('token', '').strip()
        
        if not token:
            return jsonify({"error": "Token is required"}), 400
        
        # Verify token
        payload = verify_jwt_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        return jsonify({
            "valid": True,
            "user_data": payload,
            "message": "Token is valid"
        }), 200
    
    except Exception as e:
        return jsonify({"error": f"Token verification failed: {str(e)}"}), 500

@app.route('/profile/<patient_id>', methods=['GET'])
def get_profile(patient_id):
    """Get patient profile information"""
    try:
        if db.patients_collection is None:
            return jsonify({"error": "Database not connected"}), 500
        
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({"error": "Patient not found"}), 404
        
        return jsonify({
            "patient_id": patient["patient_id"],
            "username": patient["username"],
            "email": patient["email"],
            "mobile": patient["mobile"],
            "first_name": patient.get("first_name"),
            "last_name": patient.get("last_name"),
            "age": patient.get("age"),
            "blood_type": patient.get("blood_type"),
            "is_pregnant": patient.get("is_pregnant"),
            "last_period_date": patient.get("last_period_date"),
            "pregnancy_week": patient.get("pregnancy_week"),
            "expected_delivery_date": patient.get("expected_delivery_date"),
            "emergency_contact": patient.get("emergency_contact"),
            "preferences": patient.get("preferences")
        }), 200
    
    except Exception as e:
        return jsonify({"error": f"Failed to get profile: {str(e)}"}), 500

@app.route('/save-sleep-log', methods=['POST'])
def save_sleep_log():
    """Save sleep log data to MongoDB"""
    try:
        data = request.get_json()
        
        # Debug logging
        print(f"🔍 Received sleep log data: {json.dumps(data, indent=2)}")
        
        # Validate required fields
        required_fields = ['userId', 'userRole', 'startTime', 'endTime', 'totalSleep', 'sleepRating']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400
        
        # Check if we have Patient ID for precise linking
        patient_id = data.get('userId')
        if not patient_id:
            return jsonify({
                'success': False, 
                'message': 'Patient ID is required for precise patient linking. Please ensure you are logged in.',
                'debug_info': {
                    'received_userId': data.get('userId'),
                    'received_data': data
                }
            }), 400
        
        # Create sleep log document
        sleep_log = {
            'userId': data['userId'],
            'userRole': data['userRole'],
            'username': data.get('username', 'unknown'),
            'email': data.get('email', 'unknown'),  # Add email for better user linking
            'startTime': data['startTime'],
            'endTime': data['endTime'],
            'totalSleep': data['totalSleep'],
            'smartAlarmEnabled': data.get('smartAlarmEnabled', False),
            'optimalWakeUpTime': data.get('optimalWakeUpTime', ''),
            'sleepRating': data['sleepRating'],
            'notes': data.get('notes', ''),
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'createdAt': datetime.now(),
        }
        
        # Store sleep log within the patient's document
        if data['userRole'] == 'doctor':
            # For doctors, store in separate collection (as before)
            collection = db.doctors_collection
            result = collection.insert_one(sleep_log)
            
            if result.inserted_id:
                return jsonify({
                    'success': True,
                    'message': 'Sleep log saved successfully',
                    'sleepLogId': str(result.inserted_id)
                }), 200
            else:
                return jsonify({'success': False, 'message': 'Failed to save sleep log'}), 500
        else:
            # For patients, store within their patient document using Patient ID
            patient_id = data.get('userId')
            if not patient_id:
                return jsonify({
                    'success': False, 
                    'message': 'Patient ID is required. Please ensure you are logged in.',
                    'debug_info': {
                        'received_userId': data.get('userId'),
                        'received_data': data
                    }
                }), 400
            
            print(f"🔍 Looking for patient with ID: {patient_id}")
            
            # Find patient by Patient ID (more reliable than email)
            patient = db.patients_collection.find_one({"patient_id": patient_id})
            if not patient:
                return jsonify({'success': False, 'message': f'Patient not found with ID: {patient_id}'}), 404
            
            print(f"🔍 Found patient: {patient.get('username')} ({patient.get('email')})")
            
            # Create sleep log entry (without MongoDB _id)
            sleep_log_entry = {
                'startTime': data['startTime'],
                'endTime': data['endTime'],
                'totalSleep': data['totalSleep'],
                'smartAlarmEnabled': data.get('smartAlarmEnabled', False),
                'optimalWakeUpTime': data.get('optimalWakeUpTime', ''),
                'sleepRating': data['sleepRating'],
                'notes': data.get('notes', ''),
                'timestamp': data.get('timestamp', datetime.now().isoformat()),
                'createdAt': datetime.now(),
            }
            
            # Add sleep log to patient's sleep_logs array using Patient ID
            result = db.patients_collection.update_one(
                {"patient_id": patient_id},
                {
                    "$push": {"sleep_logs": sleep_log_entry},
                    "$set": {"last_updated": datetime.now()}
                }
            )
            
            if result.modified_count > 0:
                # Log the sleep log activity
                activity_tracker.log_activity(
                    user_email=patient.get('email'),
                    activity_type="sleep_log_created",
                    activity_data={
                        "sleep_log_id": "embedded_in_patient_doc",
                        "sleep_data": sleep_log_entry,
                        "patient_id": patient_id,
                        "total_sleep_logs": len(patient.get('sleep_logs', [])) + 1
                    }
                )
                
                return jsonify({
                    'success': True,
                    'message': 'Sleep log saved successfully to patient profile',
                    'patientId': patient_id,
                    'patientEmail': patient.get('email'),
                    'sleepLogsCount': len(patient.get('sleep_logs', [])) + 1
                }), 200
            else:
                return jsonify({'success': False, 'message': 'Failed to save sleep log to patient profile'}), 500
            
    except Exception as e:
        print(f"Error saving sleep log: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/get-sleep-logs/<username>', methods=['GET'])
def get_sleep_logs(username):
    """Get sleep logs for a specific user"""
    try:
        # Get user role from the username
        user_doc = db.patients_collection.find_one({"username": username})
        if not user_doc:
            # Try doctors collection
            user_doc = db.doctors_collection.find_one({"username": username})
            if not user_doc:
                return jsonify({'success': False, 'message': 'User not found'}), 404
        
        user_role = user_doc.get('role', 'patient')
        
        # Get sleep logs for this user
        if user_role == 'doctor':
            collection = db.doctors_collection
        else:
            collection = db.patients_collection
        
        # Find all sleep logs for this user
        sleep_logs = list(collection.find(
            {"username": username, "startTime": {"$exists": True}},
            {"_id": 0}  # Exclude MongoDB _id
        ))
        
        return jsonify({
            'success': True,
            'username': username,
            'userRole': user_role,
            'sleepLogs': sleep_logs,
            'count': len(sleep_logs)
        }), 200
        
    except Exception as e:
        print(f"Error retrieving sleep logs: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/get-sleep-logs-by-email/<email>', methods=['GET'])
def get_sleep_logs_by_email(email):
    """Get sleep logs for a specific user by email"""
    try:
        # Get user role from the email
        user_doc = db.patients_collection.find_one({"email": email})
        if not user_doc:
            # Try doctors collection
            user_doc = db.doctors_collection.find_one({"email": email})
            if not user_doc:
                return jsonify({'success': False, 'message': 'User not found with this email'}), 404
        
        user_role = user_doc.get('role', 'patient')
        username = user_doc.get('username', 'unknown')
        
        # Get sleep logs for this user by email
        if user_role == 'doctor':
            # For doctors, get from separate collection
            collection = db.doctors_collection
            sleep_logs = list(collection.find(
                {"email": email, "startTime": {"$exists": True}},
                {"_id": 0}  # Exclude MongoDB _id
            ))
        else:
            # For patients, get from their document's sleep_logs array
            sleep_logs = user_doc.get('sleep_logs', [])
        
        return jsonify({
            'success': True,
            'email': email,
            'username': username,
            'userRole': user_role,
            'sleepLogs': sleep_logs,
            'count': len(sleep_logs)
        }), 200
        
    except Exception as e:
        print(f"Error retrieving sleep logs by email: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/patient-complete-profile/<email>', methods=['GET'])
def get_patient_complete_profile(email):
    """Get complete patient profile including all health data"""
    try:
        # Find patient by email
        patient = db.patients_collection.find_one({"email": email})
        if not patient:
            return jsonify({'success': False, 'message': 'Patient not found with this email'}), 404
        
        # Return complete patient profile with all data
        complete_profile = {
            'success': True,
            'patient_id': patient.get('patient_id'),
            'username': patient.get('username'),
            'email': patient.get('email'),
            'mobile': patient.get('mobile'),
            'first_name': patient.get('first_name'),
            'last_name': patient.get('last_name'),
            'age': patient.get('age'),
            'blood_type': patient.get('blood_type'),
            'weight': patient.get('weight'),
            'height': patient.get('height'),
            'is_pregnant': patient.get('is_pregnant'),
            'last_period_date': patient.get('last_period_date'),
            'pregnancy_week': patient.get('pregnancy_week'),
            'expected_delivery_date': patient.get('expected_delivery_date'),
            'emergency_contact': patient.get('emergency_contact'),
            'preferences': patient.get('preferences'),
            'profile_completed_at': patient.get('profile_completed_at'),
            'last_updated': patient.get('last_updated'),
            'health_data': {
                'sleep_logs': patient.get('sleep_logs', []),
                'sleep_logs_count': len(patient.get('sleep_logs', [])),
                'food_logs': patient.get('food_logs', []),
                'food_logs_count': len(patient.get('food_logs', [])),
                'medication_logs': patient.get('medication_logs', []),
                'medication_logs_count': len(patient.get('medication_logs', [])),
                'symptom_logs': patient.get('symptom_logs', []),
                'symptom_logs_count': len(patient.get('symptom_logs', [])),
                'mental_health_logs': patient.get('mental_health_logs', []),
                'mental_health_logs_count': len(patient.get('mental_health_logs', [])),
                'kick_count_logs': patient.get('kick_count_logs', []),
                'kick_count_logs_count': len(patient.get('kick_count_logs', [])),
            }
        }
        
        return jsonify(complete_profile), 200
        
    except Exception as e:
        print(f"Error retrieving complete patient profile: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

# User Activity Management Endpoints
@app.route('/user-activities/<email>', methods=['GET'])
def get_user_activities(email):
    """Get all activities for a specific user"""
    try:
        activities = activity_tracker.get_user_activities(email)
        return jsonify({
            'success': True,
            'user_email': email,
            'activities': activities,
            'total_sessions': len(activities)
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/session-activities/<session_id>', methods=['GET'])
def get_session_activities(session_id):
    """Get all activities for a specific session"""
    try:
        session = activity_tracker.get_session_activities(session_id)
        if session:
            return jsonify({
                'success': True,
                'session': session
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/activity-summary/<email>', methods=['GET'])
def get_activity_summary(email):
    """Get summary of user activities"""
    try:
        summary = activity_tracker.get_activity_summary(email)
        return jsonify({
            'success': True,
            'user_email': email,
            'summary': summary,
            'total_activities': sum(item['count'] for item in summary)
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/track-activity', methods=['POST'])
def track_activity():
    """Manually track a user activity"""
    try:
        data = request.get_json()
        user_email = data.get('email')
        activity_type = data.get('activity_type')
        activity_data = data.get('activity_data', {})
        session_id = data.get('session_id')
        
        if not user_email or not activity_type:
            return jsonify({'success': False, 'message': 'Email and activity_type are required'}), 400
        
        # Log the activity
        activity_id = activity_tracker.log_activity(
            user_email=user_email,
            activity_type=activity_type,
            activity_data=activity_data,
            session_id=session_id
        )
        
        if activity_id:
            return jsonify({
                'success': True,
                'message': 'Activity tracked successfully',
                'activity_id': activity_id
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Failed to track activity'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/active-sessions/<email>', methods=['GET'])
def get_active_sessions(email):
    """Get all active sessions for a user"""
    try:
        active_sessions = list(activity_tracker.activities_collection.find(
            {"user_email": email, "is_active": True},
            {"_id": 0}
        ))
        
        return jsonify({
            'success': True,
            'user_email': email,
            'active_sessions': active_sessions,
            'count': len(active_sessions)
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/save-kick-session', methods=['POST'])
def save_kick_session():
    """Save kick session data to MongoDB"""
    try:
        data = request.get_json()
        
        # Debug logging
        print(f"🔍 Received kick session data: {json.dumps(data, indent=2)}")
        
        # Validate required fields
        required_fields = ['userId', 'userRole', 'kickCount', 'sessionDuration']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400
        
        # Check if we have Patient ID for precise linking
        patient_id = data.get('userId')
        if not patient_id:
            return jsonify({
                'success': False, 
                'message': 'Patient ID is required for precise patient linking. Please ensure you are logged in.',
                'debug_info': {
                    'received_userId': data.get('userId'),
                    'received_data': data
                }
            }), 400
        
        print(f"🔍 Looking for patient with ID: {patient_id}")
        
        # Find patient by Patient ID (more reliable than email)
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({'success': False, 'message': f'Patient not found with ID: {patient_id}'}), 404
        
        print(f"🔍 Found patient: {patient.get('username')} ({patient.get('email')})")
        
        # Create kick session entry
        kick_session_entry = {
            'kickCount': data['kickCount'],
            'sessionDuration': data['sessionDuration'],
            'sessionStartTime': data.get('sessionStartTime'),
            'sessionEndTime': data.get('sessionEndTime'),
            'averageKicksPerMinute': data.get('averageKicksPerMinute', 0),
            'notes': data.get('notes', ''),
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'createdAt': datetime.now(),
        }
        
        # Add kick session to patient's kick_count_logs array using Patient ID
        result = db.patients_collection.update_one(
            {"patient_id": patient_id},
            {
                "$push": {"kick_count_logs": kick_session_entry},
                "$set": {"last_updated": datetime.now()}
            }
        )
        
        if result.modified_count > 0:
            # Log the kick session activity
            activity_tracker.log_activity(
                user_email=patient.get('email'),
                activity_type="kick_session_created",
                activity_data={
                    "kick_session_id": "embedded_in_patient_doc",
                    "kick_data": kick_session_entry,
                    "patient_id": patient_id,
                    "total_kick_sessions": len(patient.get('kick_count_logs', [])) + 1
                }
            )
            
            return jsonify({
                'success': True,
                'message': 'Kick session saved successfully to patient profile',
                'patientId': patient_id,
                'patientEmail': patient.get('email'),
                'kickSessionsCount': len(patient.get('kick_count_logs', [])) + 1
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Failed to save kick session to patient profile'}), 500
            
    except Exception as e:
        print(f"Error saving kick session: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/get-kick-history/<patient_id>', methods=['GET'])
def get_kick_history(patient_id):
    """Get kick history for a specific patient"""
    try:
        # Find patient by Patient ID
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({'success': False, 'message': f'Patient not found with ID: {patient_id}'}), 404
        
        # Get kick count logs
        kick_logs = patient.get('health_data', {}).get('kick_count_logs', [])
        
        return jsonify({
            'success': True,
            'patientId': patient_id,
            'kick_logs': kick_logs,
            'totalSessions': len(kick_logs)
        }), 200
        
    except Exception as e:
        print(f"Error getting kick history: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/get-food-history/<patient_id>', methods=['GET'])
def get_food_history(patient_id):
    """Get food history for a specific patient"""
    try:
        print(f"🔍 Getting food history for patient ID: {patient_id}")
        
        # Find patient by Patient ID
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({'success': False, 'message': f'Patient not found with ID: {patient_id}'}), 404
        
        # Get food logs from patient document
        food_logs = patient.get('food_logs', [])
        
        # Sort by newest first
        food_logs.sort(key=lambda x: x.get('createdAt', datetime.min), reverse=True)
        
        # Convert datetime objects to strings for JSON serialization
        for entry in food_logs:
            if 'createdAt' in entry:
                entry['createdAt'] = entry['createdAt'].isoformat()
        
        print(f"✅ Retrieved {len(food_logs)} food entries for patient: {patient_id}")
        
        return jsonify({
            'success': True,
            'patientId': patient_id,
            'food_logs': food_logs,
            'totalEntries': len(food_logs)
        }), 200
        
    except Exception as e:
        print(f"Error getting food history: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/get-current-pregnancy-week/<patient_id>', methods=['GET'])
def get_current_pregnancy_week(patient_id):
    """Get current pregnancy week for a specific patient"""
    try:
        print(f"🔍 Getting current pregnancy week for patient ID: {patient_id}")
        
        # Find patient by Patient ID
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({'success': False, 'message': f'Patient not found with ID: {patient_id}'}), 404
        
        # Try to get pregnancy week from patient's health data
        pregnancy_week = 1  # Default fallback
        pregnancy_info = {}
        auto_fetched = False
        
        try:
            # First try to get pregnancy week directly from patient document (your current structure)
            if 'pregnancy_week' in patient:
                pregnancy_week = patient['pregnancy_week']
                auto_fetched = True
                print(f"✅ Found pregnancy week in patient document: {pregnancy_week}")
            else:
                # Try to get from patient's health data
                health_data = patient.get('health_data', {})
                if 'pregnancy_week' in health_data:
                    pregnancy_week = health_data['pregnancy_week']
                    auto_fetched = True
                    print(f"✅ Found pregnancy week in health data: {pregnancy_week}")
                else:
                    # Try to get from pregnancy info
                    pregnancy_info = health_data.get('pregnancy_info', {})
                    if pregnancy_info and 'current_week' in pregnancy_info:
                        pregnancy_week = pregnancy_info['current_week']
                        auto_fetched = True
                        print(f"✅ Found pregnancy week in pregnancy info: {pregnancy_week}")
                    else:
                        print(f"⚠️ No pregnancy week found, using default: {pregnancy_week}")
        except Exception as e:
            print(f"⚠️ Error fetching pregnancy week: {e}, using default: {pregnancy_week}")
        
        print(f"✅ Retrieved pregnancy week: {pregnancy_week} for patient: {patient_id}")
        
        return jsonify({
            'success': True,
            'patientId': patient_id,
            'patientEmail': patient.get('email'),
            'current_pregnancy_week': pregnancy_week,
            'pregnancy_info': pregnancy_info,
            'auto_fetched': auto_fetched,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"Error getting current pregnancy week: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

# ==================== SYMPTOM ASSISTANCE ENDPOINTS ====================

@app.route('/symptoms/health', methods=['GET'])
def symptoms_health_check():
    """Health check endpoint for symptoms service"""
    return jsonify({
        'success': True,
        'message': 'Pregnancy Symptom Assistant is running',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/symptoms/assist', methods=['POST'])
def get_symptom_assistance():
    """Get pregnancy symptom assistance using quantum vector search and LLM analysis"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        symptom_text = data.get('text', '').strip()
        weeks_pregnant = data.get('weeks_pregnant', 1)
        patient_id = data.get('patient_id')
        
        if not symptom_text:
            return jsonify({
                'success': False,
                'message': 'Symptom description is required'
            }), 400
        
        # Auto-fetch pregnancy week from patient profile if not provided
        if not weeks_pregnant and patient_id:
            try:
                patient = db.patients_collection.find_one({"patient_id": patient_id})
                if patient and patient.get('pregnancy_week'):
                    weeks_pregnant = patient['pregnancy_week']
                    print(f"✅ Auto-fetched pregnancy week: {weeks_pregnant}")
            except Exception as e:
                print(f"⚠️ Error fetching pregnancy week: {e}")
        
        # Determine trimester
        if weeks_pregnant <= 12:
            trimester = "First Trimester"
        elif weeks_pregnant <= 26:
            trimester = "Second Trimester"
        else:
            trimester = "Third Trimester"
        
        print(f"🔍 Analyzing symptoms: '{symptom_text}' for week {weeks_pregnant} ({trimester})")
        
        # Step 1: Try quantum vector search for knowledge base retrieval
        suggestions = []
        if quantum_service.client and quantum_service.embedding_model:
            print("🔬 Using quantum vector search...")
            suggestions = quantum_service.search_knowledge(symptom_text, weeks_pregnant)
            print(f"✅ Found {len(suggestions)} suggestions from knowledge base")
        else:
            print("⚠️ Quantum vector search not available")
        
        # Step 2: Generate response based on search results
        if suggestions:
            # Use LLM to synthesize a summary from retrieved suggestions
            print("🤖 Using LLM to synthesize recommendations...")
            summary = llm_service.summarize_retrieval(symptom_text, weeks_pregnant, suggestions)
            
            if summary:
                # Return synthesized summary
                response_text = summary.get("text", "")
                response_source = "quantum_llm_synthesis"
                print("✅ LLM synthesis successful")
            else:
                # Fallback to safe guidance
                print("⚠️ LLM synthesis failed, using safe fallback")
                fallback = llm_service.generate_llm_fallback(symptom_text, weeks_pregnant)
                response_text = fallback.get("suggestions", [{}])[0].get("text", "")
                response_source = "quantum_safe_fallback"
        else:
            # No suggestions found, use LLM fallback
            print("⚠️ No knowledge base suggestions, using LLM fallback")
            fallback = llm_service.generate_llm_fallback(symptom_text, weeks_pregnant)
            response_text = fallback.get("suggestions", [{}])[0].get("text", "")
            response_source = "llm_fallback"
        
        # Step 3: Detect red flags for safety
        red_flags = llm_service.detect_red_flags(symptom_text)
        
        # Step 4: Generate additional recommendations
        additional_recommendations = generate_symptom_recommendations(symptom_text, weeks_pregnant, trimester)
        
        # Log the symptom consultation
        if patient_id:
            try:
                activity_tracker.log_activity(
                    user_email=patient.get('email') if patient else None,
                    activity_type="symptom_consultation",
                    activity_data={
                        "symptom_text": symptom_text,
                        "pregnancy_week": weeks_pregnant,
                        "trimester": trimester,
                        "patient_id": patient_id,
                        "analysis_method": response_source,
                        "red_flags_detected": red_flags,
                        "suggestions_count": len(suggestions)
                    }
                )
            except Exception as e:
                print(f"⚠️ Warning: Could not log symptom consultation activity: {e}")
        
        return jsonify({
            'success': True,
            'symptom_text': symptom_text,
            'pregnancy_week': weeks_pregnant,
            'trimester': trimester,
            'analysis_method': response_source,
            'primary_recommendation': response_text,
            'additional_recommendations': additional_recommendations,
            'red_flags_detected': red_flags,
            'knowledge_base_suggestions': len(suggestions),
            'disclaimer': DISCLAIMER_TEXT,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"Error getting symptom assistance: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

def generate_symptom_recommendations(symptom_text, weeks_pregnant, trimester):
    """Generate symptom-specific recommendations based on pregnancy week and trimester"""
    symptom_lower = symptom_text.lower()
    recommendations = []
    
    # Common pregnancy symptoms and recommendations
    if any(word in symptom_lower for word in ['nausea', 'morning sickness', 'vomiting']):
        recommendations.extend([
            "Eat small, frequent meals throughout the day",
            "Avoid spicy, greasy, or strong-smelling foods",
            "Try ginger tea or ginger candies",
            "Stay hydrated with small sips of water",
            "Eat crackers or dry toast before getting out of bed"
        ])
    
    if any(word in symptom_lower for word in ['fatigue', 'tired', 'exhausted']):
        recommendations.extend([
            "Get plenty of rest and sleep",
            "Take short naps during the day",
            "Maintain a regular sleep schedule",
            "Stay hydrated and eat nutritious foods",
            "Listen to your body and rest when needed"
        ])
    
    if any(word in symptom_lower for word in ['back pain', 'backache', 'lower back']):
        recommendations.extend([
            "Practice good posture",
            "Use proper body mechanics when lifting",
            "Try gentle stretching exercises",
            "Consider prenatal yoga or swimming",
            "Use a pregnancy pillow for support while sleeping"
        ])
    
    if any(word in symptom_lower for word in ['heartburn', 'acid reflux', 'indigestion']):
        recommendations.extend([
            "Eat smaller, more frequent meals",
            "Avoid lying down immediately after eating",
            "Limit spicy, acidic, or fatty foods",
            "Try eating yogurt or drinking milk",
            "Elevate your head while sleeping"
        ])
    
    if any(word in symptom_lower for word in ['swelling', 'edema', 'water retention']):
        recommendations.extend([
            "Elevate your feet when possible",
            "Avoid standing for long periods",
            "Stay hydrated and limit salt intake",
            "Wear comfortable, supportive shoes",
            "Consider compression stockings if recommended by your doctor"
        ])
    
    if any(word in symptom_lower for word in ['constipation', 'bowel', 'digestive']):
        recommendations.extend([
            "Increase fiber intake with fruits, vegetables, and whole grains",
            "Stay hydrated by drinking plenty of water",
            "Exercise regularly with your doctor's approval",
            "Consider natural laxatives like prunes or prune juice",
            "Don't ignore the urge to have a bowel movement"
        ])
    
    # Trimester-specific advice
    if trimester == "First Trimester":
        recommendations.extend([
            "Take prenatal vitamins as prescribed",
            "Avoid alcohol, smoking, and recreational drugs",
            "Get plenty of rest - your body is working hard",
            "Eat a balanced diet rich in folic acid"
        ])
    elif trimester == "Second Trimester":
        recommendations.extend([
            "Continue with regular prenatal care",
            "Start or continue gentle exercise routines",
            "Focus on good nutrition and hydration",
            "Consider childbirth education classes"
        ])
    else:  # Third Trimester
        recommendations.extend([
            "Prepare for labor and delivery",
            "Practice relaxation and breathing techniques",
            "Get plenty of rest and conserve energy",
            "Have your hospital bag ready",
            "Know the signs of labor"
        ])
    
    # General pregnancy wellness advice
    general_advice = [
        "Always consult your healthcare provider for persistent or severe symptoms",
        "Keep a symptom diary to track patterns",
        "Stay hydrated and maintain a healthy diet",
        "Get regular prenatal care and follow your doctor's recommendations",
        "Trust your instincts - you know your body best"
    ]
    
    # Combine specific and general recommendations
    all_recommendations = recommendations + general_advice
    
    # Remove duplicates while preserving order
    seen = set()
    unique_recommendations = []
    for rec in all_recommendations:
        if rec not in seen:
            seen.add(rec)
            unique_recommendations.append(rec)
    
    return unique_recommendations

@app.route('/symptoms/save-symptom-log', methods=['POST'])
def save_symptom_log():
    """Save symptom log to patient profile"""
    try:
        data = request.get_json()
        
        # Debug logging
        print(f"🔍 Received symptom log data: {json.dumps(data, indent=2)}")
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['patient_id', 'symptom_text', 'severity', 'category']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        patient_id = data.get('patient_id')
        symptom_text = data.get('symptom_text', '').strip()
        severity = data.get('severity', 5)
        category = data.get('category', 'General')
        notes = data.get('notes', '')
        
        if not symptom_text:
            return jsonify({
                'success': False,
                'message': 'Symptom description is required'
            }), 400
        
        print(f"🔍 Looking for patient with ID: {patient_id}")
        
        # Find patient by Patient ID
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({'success': False, 'message': f'Patient not found with ID: {patient_id}'}), 404
        
        print(f"🔍 Found patient: {patient.get('username')} ({patient.get('email')})")
        
        # Create symptom log entry
        symptom_log_entry = {
            'symptom_text': symptom_text,
            'severity': severity,
            'category': category,
            'notes': notes,
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'createdAt': datetime.now(),
            'pregnancy_week': patient.get('pregnancy_week', 1),
            'trimester': 'First' if patient.get('pregnancy_week', 1) <= 12 else 'Second' if patient.get('pregnancy_week', 1) <= 26 else 'Third'
        }
        
        # Add symptom log to patient's symptom_logs array
        result = db.patients_collection.update_one(
            {"patient_id": patient_id},
            {
                "$push": {"symptom_logs": symptom_log_entry},
                "$set": {"last_updated": datetime.now()}
            }
        )
        
        if result.modified_count > 0:
            # Log the symptom log activity
            activity_tracker.log_activity(
                user_email=patient.get('email'),
                activity_type="symptom_log_created",
                activity_data={
                    "symptom_log_id": "embedded_in_patient_doc",
                    "symptom_data": symptom_log_entry,
                    "patient_id": patient_id,
                    "total_symptom_logs": len(patient.get('symptom_logs', [])) + 1
                }
            )
            
            return jsonify({
                'success': True,
                'message': 'Symptom log saved successfully to patient profile',
                'patientId': patient_id,
                'patientEmail': patient.get('email'),
                'symptomLogsCount': len(patient.get('symptom_logs', [])) + 1
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Failed to save symptom log to patient profile'}), 500
            
    except Exception as e:
        print(f"Error saving symptom log: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/symptoms/save-analysis-report', methods=['POST'])
def save_symptom_analysis_report():
    """Save complete symptom analysis report including AI recommendations"""
    try:
        data = request.get_json()
        
        # Debug logging
        print(f"🔍 Received symptom analysis report data: {json.dumps(data, indent=2)}")
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['patient_id', 'symptom_text', 'weeks_pregnant']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        patient_id = data.get('patient_id')
        symptom_text = data.get('symptom_text', '').strip()
        weeks_pregnant = data.get('weeks_pregnant', 1)
        
        if not symptom_text:
            return jsonify({
                'success': False,
                'message': 'Symptom description is required'
            }), 400
        
        print(f"🔍 Looking for patient with ID: {patient_id}")
        
        # Find patient by Patient ID
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({'success': False, 'message': f'Patient not found with ID: {patient_id}'}), 404
        
        print(f"🔍 Found patient: {patient.get('username')} ({patient.get('email')})")
        
        # Create comprehensive symptom analysis report
        analysis_report = {
            'symptom_text': symptom_text,
            'weeks_pregnant': weeks_pregnant,
            'trimester': 'First' if weeks_pregnant <= 12 else 'Second' if weeks_pregnant <= 26 else 'Third',
            'severity': data.get('severity', 'Not specified'),
            'notes': data.get('notes', ''),
            'analysis_date': data.get('date', datetime.now().strftime('%d/%m/%Y')),
            'timestamp': datetime.now().isoformat(),
            'createdAt': datetime.now(),
            
            # AI Analysis Results
            'ai_analysis': {
                'analysis_method': data.get('analysis_method', 'quantum_llm'),
                'primary_recommendation': data.get('primary_recommendation', ''),
                'additional_recommendations': data.get('additional_recommendations', []),
                'red_flags_detected': data.get('red_flags_detected', []),
                'disclaimer': data.get('disclaimer', ''),
                'urgency_level': data.get('urgency_level', 'moderate'),
                'knowledge_base_suggestions_count': data.get('knowledge_base_suggestions_count', 0)
            },
            
            # Patient Context
            'patient_context': data.get('patient_context', {}),
            
            # Metadata
            'report_id': str(ObjectId()),
            'version': '1.0',
            'source': 'flutter_app_quantum_llm'
        }
        
        # Add analysis report to patient's symptom_analysis_reports array
        result = db.patients_collection.update_one(
            {"patient_id": patient_id},
            {
                "$push": {"symptom_analysis_reports": analysis_report},
                "$set": {"last_updated": datetime.now()}
            }
        )
        
        if result.modified_count > 0:
            # Log the symptom analysis activity
            activity_tracker.log_activity(
                user_email=patient.get('email'),
                activity_type="symptom_analysis_report_created",
                activity_data={
                    "report_id": analysis_report['report_id'],
                    "symptom_text": symptom_text,
                    "pregnancy_week": weeks_pregnant,
                    "trimester": analysis_report['trimester'],
                    "red_flags_count": len(analysis_report['ai_analysis']['red_flags_detected']),
                    "patient_id": patient_id,
                    "total_analysis_reports": len(patient.get('symptom_analysis_reports', [])) + 1
                }
            )
            
            return jsonify({
                'success': True,
                'message': 'Symptom analysis report saved successfully',
                'report_id': analysis_report['report_id'],
                'patientId': patient_id,
                'patientEmail': patient.get('email'),
                'analysisReportsCount': len(patient.get('symptom_analysis_reports', [])) + 1,
                'timestamp': analysis_report['timestamp']
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Failed to save analysis report'}), 500
            
    except Exception as e:
        print(f"Error saving symptom analysis report: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/symptoms/get-symptom-history/<patient_id>', methods=['GET'])
def get_symptom_history(patient_id):
    """Get symptom history for a specific patient"""
    try:
        print(f"🔍 Getting symptom history for patient ID: {patient_id}")
        
        # Find patient by Patient ID
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({'success': False, 'message': f'Patient not found with ID: {patient_id}'}), 404
        
        # Get symptom logs from patient document
        symptom_logs = patient.get('symptom_logs', [])
        
        # Sort by newest first
        symptom_logs.sort(key=lambda x: x.get('createdAt', datetime.min), reverse=True)
        
        # Convert datetime objects to strings for JSON serialization
        for entry in symptom_logs:
            if 'createdAt' in entry:
                entry['createdAt'] = entry['createdAt'].isoformat()
        
        print(f"✅ Retrieved {len(symptom_logs)} symptom logs for patient: {patient_id}")
        
        return jsonify({
            'success': True,
            'patientId': patient_id,
            'symptom_logs': symptom_logs,
            'totalEntries': len(symptom_logs)
        }), 200
        
    except Exception as e:
        print(f"Error getting symptom history: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/symptoms/get-analysis-reports/<patient_id>', methods=['GET'])
def get_analysis_reports(patient_id):
    """Get only the AI analysis reports for a patient"""
    try:
        print(f"🔍 Getting analysis reports for patient ID: {patient_id}")
        
        # Find patient by Patient ID
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({'success': False, 'message': f'Patient not found with ID: {patient_id}'}), 404
        
        # Get only analysis reports
        analysis_reports = patient.get('symptom_analysis_reports', [])
        
        # Sort by timestamp (newest first)
        analysis_reports.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Format reports for display (remove sensitive fields)
        formatted_reports = []
        for report in analysis_reports:
            formatted_report = {
                'report_id': report.get('report_id'),
                'symptom_text': report.get('symptom_text'),
                'weeks_pregnant': report.get('weeks_pregnant'),
                'trimester': report.get('trimester'),
                'severity': report.get('severity'),
                'analysis_date': report.get('analysis_date'),
                'timestamp': report.get('timestamp'),
                'ai_analysis': {
                    'primary_recommendation': report.get('ai_analysis', {}).get('primary_recommendation'),
                    'red_flags_detected': report.get('ai_analysis', {}).get('red_flags_detected', []),
                    'urgency_level': report.get('ai_analysis', {}).get('urgency_level'),
                    'analysis_method': report.get('ai_analysis', {}).get('analysis_method')
                }
            }
            formatted_reports.append(formatted_report)
        
        print(f"✅ Retrieved {len(formatted_reports)} analysis reports for patient: {patient_id}")
        
        return jsonify({
            'success': True,
            'patientId': patient_id,
            'patientName': patient.get('username', 'Unknown'),
            'analysisReports': formatted_reports,
            'totalAnalysisReports': len(formatted_reports)
        }), 200
        
    except Exception as e:
        print(f"Error getting analysis reports: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

# ==================== MEDICATION TRACKING ENDPOINTS ====================

@app.route('/medication/save-medication-log', methods=['POST'])
def save_medication_log():
    """Save medication log to patient profile"""
    try:
        data = request.get_json()
        
        # Debug logging
        print(f"🔍 Received medication log data: {json.dumps(data, indent=2)}")
        print(f"🔍 Data keys: {list(data.keys())}")
        print(f"🔍 Dosages field: {data.get('dosages', 'NOT_FOUND')}")
        print(f"🔍 Is prescription mode: {data.get('is_prescription_mode', 'NOT_FOUND')}")
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['patient_id', 'medication_name']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        patient_id = data.get('patient_id')
        medication_name = data.get('medication_name', '').strip()
        
        if not medication_name:
            return jsonify({
                'success': False,
                'message': 'Medication name is required'
            }), 400
        
        # Check if it's prescription mode or multiple dosages mode
        is_prescription_mode = data.get('is_prescription_mode', False)
        dosages = data.get('dosages', [])
        prescription_details = data.get('prescription_details', '').strip()
        
        # Ensure dosages is always a list
        if not isinstance(dosages, list):
            print(f"⚠️ Warning: dosages is not a list, converting from {type(dosages)}")
            dosages = []
        
        print(f"🔍 Validation Debug:")
        print(f"🔍 - Is prescription mode: {is_prescription_mode}")
        print(f"🔍 - Dosages type: {type(dosages)}")
        print(f"🔍 - Dosages length: {len(dosages) if isinstance(dosages, list) else 'NOT_A_LIST'}")
        print(f"🔍 - Dosages content: {dosages}")
        print(f"🔍 - Prescription details: '{prescription_details}'")
        
        # Handle backward compatibility with old format
        if not is_prescription_mode and len(dosages) == 0:
            # Check for old format fields
            old_dosage = data.get('dosage', '').strip()
            old_time_taken = data.get('time_taken', '').strip()
            
            if old_dosage and old_time_taken:
                # Convert old format to new format
                dosages = [{
                    'dosage': old_dosage,
                    'time': old_time_taken,
                    'frequency': 'As prescribed',
                    'reminder_enabled': False,
                    'next_dose_time': None,
                    'special_instructions': ''
                }]
                print(f"🔍 Converted old format to new format: {dosages}")
            else:
                return jsonify({
                    'success': False,
                    'message': 'At least one dosage is required when not in prescription mode'
                }), 400
        
        if is_prescription_mode:
            if not prescription_details:
                return jsonify({
                    'success': False,
                    'message': 'Prescription details are required in prescription mode'
                }), 400
        elif len(dosages) == 0:
            return jsonify({
                'success': False,
                'message': 'At least one dosage is required when not in prescription mode'
            }), 400
        
        print(f"🔍 Looking for patient with ID: {patient_id}")
        
        # Find patient by Patient ID
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({'success': False, 'message': f'Patient not found with ID: {patient_id}'}), 404
        
        print(f"🔍 Found patient: {patient.get('username')} ({patient.get('email')})")
        
        # Create medication log entry
        medication_log_entry = {
            'medication_name': medication_name,
            'date_taken': data.get('date_taken', datetime.now().strftime('%d/%m/%Y')),
            'timestamp': datetime.now().isoformat(),
            'createdAt': datetime.now(),
            'pregnancy_week': patient.get('pregnancy_week', 1),
            'trimester': 'First' if patient.get('pregnancy_week', 1) <= 12 else 'Second' if patient.get('pregnancy_week', 1) <= 26 else 'Third',
            'notes': data.get('notes', ''),
            'prescribed_by': data.get('prescribed_by', ''),
            'medication_type': data.get('medication_type', 'prescription'),
            'side_effects': data.get('side_effects', []),
            'is_prescription_mode': is_prescription_mode,
            'prescription_details': prescription_details,
            'dosages': dosages,
            'total_dosages': len(dosages) if not is_prescription_mode else 0
        }
        
        # Add medication log to patient's medication_logs array
        result = db.patients_collection.update_one(
            {"patient_id": patient_id},
            {
                "$push": {"medication_logs": medication_log_entry},
                "$set": {"last_updated": datetime.now()}
            }
        )
        
        if result.modified_count > 0:
            # Log the medication activity
            activity_tracker.log_activity(
                user_email=patient.get('email'),
                activity_type="medication_log_created",
                activity_data={
                    "medication_log_id": "embedded_in_patient_doc",
                    "medication_data": medication_log_entry,
                    "patient_id": patient_id,
                    "total_medication_logs": len(patient.get('medication_logs', [])) + 1,
                    "is_prescription_mode": is_prescription_mode,
                    "total_dosages": len(dosages) if not is_prescription_mode else 0
                }
            )
            
            return jsonify({
                'success': True,
                'message': 'Medication log saved successfully',
                'patientId': patient_id,
                'patientEmail': patient.get('email'),
                'medicationLogsCount': len(patient.get('medication_logs', [])) + 1,
                'timestamp': medication_log_entry['timestamp']
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Failed to save medication log'}), 500
            
    except Exception as e:
        print(f"Error saving medication log: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/medication/get-medication-history/<patient_id>', methods=['GET'])
def get_medication_history(patient_id):
    """Get medication history for a patient"""
    try:
        print(f"🔍 Getting medication history for patient ID: {patient_id}")
        
        # Find patient by Patient ID
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({'success': False, 'message': f'Patient not found with ID: {patient_id}'}), 404
        
        # Get medication logs from patient document
        medication_logs = patient.get('medication_logs', [])
        
        # Sort by newest first
        medication_logs.sort(key=lambda x: x.get('createdAt', datetime.min), reverse=True)
        
        # Convert datetime objects to strings for JSON serialization
        for entry in medication_logs:
            if 'createdAt' in entry:
                entry['createdAt'] = entry['createdAt'].isoformat()
        
        print(f"✅ Retrieved {len(medication_logs)} medication logs for patient: {patient_id}")
        
        return jsonify({
            'success': True,
            'patientId': patient_id,
            'medication_logs': medication_logs,
            'totalEntries': len(medication_logs)
        }), 200
        
    except Exception as e:
        print(f"Error getting medication history: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/medication/get-upcoming-dosages/<patient_id>', methods=['GET'])
def get_upcoming_dosages(patient_id):
    """Get upcoming dosages and alerts for a patient"""
    try:
        print(f"🔍 Getting upcoming dosages for patient ID: {patient_id}")
        
        # Find patient by Patient ID
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({'success': False, 'message': f'Patient not found with ID: {patient_id}'}), 404
        
        # Get medication logs from patient document
        medication_logs = patient.get('medication_logs', [])
        
        # Process dosages and create upcoming schedule
        upcoming_dosages = []
        today = datetime.now()
        
        for log in medication_logs:
            if not log.get('is_prescription_mode', False):
                # Handle multiple dosages
                dosages = log.get('dosages', [])
                for dosage in dosages:
                    if dosage.get('reminder_enabled', False):
                        # Parse time and create schedule
                        try:
                            time_str = dosage.get('time', '')
                            if time_str:
                                hour, minute = map(int, time_str.split(':'))
                                next_dose = today.replace(hour=hour, minute=minute, second=0, microsecond=0)
                                
                                # If time has passed today, schedule for tomorrow
                                if next_dose < today:
                                    next_dose += timedelta(days=1)
                                
                                upcoming_dosages.append({
                                    'medication_name': log.get('medication_name', 'Unknown'),
                                    'dosage': dosage.get('dosage', ''),
                                    'time': time_str,
                                    'frequency': dosage.get('frequency', ''),
                                    'next_dose_time': next_dose.isoformat(),
                                    'special_instructions': dosage.get('special_instructions', ''),
                                    'medication_type': log.get('medication_type', 'prescription'),
                                    'prescribed_by': log.get('prescribed_by', ''),
                                    'notes': log.get('notes', ''),
                                    'urgency_level': 'normal'
                                })
                        except Exception as e:
                            print(f"⚠️ Error parsing dosage time: {e}")
                            continue
        
        # Sort by next dose time
        upcoming_dosages.sort(key=lambda x: x.get('next_dose_time', ''))
        
        # Add prescription mode medications as general reminders
        prescription_medications = []
        for log in medication_logs:
            if log.get('is_prescription_mode', False):
                prescription_medications.append({
                    'medication_name': log.get('medication_name', 'Unknown'),
                    'type': 'prescription',
                    'details': log.get('prescription_details', ''),
                    'prescribed_by': log.get('prescribed_by', ''),
                    'notes': log.get('notes', ''),
                    'urgency_level': 'normal'
                })
        
        print(f"✅ Retrieved {len(upcoming_dosages)} upcoming dosages and {len(prescription_medications)} prescription medications for patient: {patient_id}")
        
        return jsonify({
            'success': True,
            'patientId': patient_id,
            'upcoming_dosages': upcoming_dosages,
            'prescription_medications': prescription_medications,
            'total_upcoming': len(upcoming_dosages),
            'total_prescriptions': len(prescription_medications),
            'current_time': today.isoformat()
        }), 200
        
    except Exception as e:
        print(f"Error getting upcoming dosages: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/medication/save-tablet-taken', methods=['POST'])
def save_tablet_taken():
    """Save daily tablet tracking for a patient"""
    try:
        data = request.get_json()
        print(f"🔍 Saving tablet taken: {data}")
        
        # Validate required fields
        required_fields = ['patient_id', 'tablet_name', 'date_taken']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400
        
        patient_id = data['patient_id']
        tablet_name = data['tablet_name']
        notes = data.get('notes', '')
        date_taken = data['date_taken']
        time_taken = data.get('time_taken', datetime.now().isoformat())
        tracking_type = data.get('type', 'daily_tracking')
        
        # Find patient by Patient ID
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({'success': False, 'message': f'Patient not found with ID: {patient_id}'}), 404
        
        # Create tablet tracking entry
        tablet_entry = {
            'tablet_name': tablet_name,
            'notes': notes,
            'date_taken': date_taken,
            'time_taken': time_taken,
            'type': tracking_type,
            'timestamp': datetime.now().isoformat()
        }
        
        # Add to patient's tablet tracking history
        if 'tablet_tracking' not in patient:
            patient['tablet_tracking'] = []
        
        patient['tablet_tracking'].append(tablet_entry)
        
        # Update patient document
        result = db.patients_collection.update_one(
            {"patient_id": patient_id},
            {"$set": {"tablet_tracking": patient['tablet_tracking']}}
        )
        
        if result.modified_count > 0:
            print(f"✅ Tablet tracking saved successfully for patient: {patient_id}")
            return jsonify({
                'success': True,
                'message': f'Tablet "{tablet_name}" tracking saved successfully',
                'tablet_entry': tablet_entry
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Failed to save tablet tracking'}), 500
            
    except Exception as e:
        print(f"Error saving tablet tracking: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/medication/get-tablet-history/<patient_id>', methods=['GET'])
def get_tablet_history(patient_id):
    """Get tablet tracking history for a patient"""
    try:
        print(f"🔍 Getting tablet history for patient ID: {patient_id}")
        
        # Find patient by Patient ID
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({'success': False, 'message': f'Patient not found with ID: {patient_id}'}), 404
        
        # Get tablet tracking history
        tablet_history = patient.get('tablet_tracking', [])
        
        # Sort by timestamp (most recent first)
        tablet_history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        print(f"✅ Retrieved {len(tablet_history)} tablet tracking entries for patient: {patient_id}")
        
        return jsonify({
            'success': True,
            'patientId': patient_id,
            'tablet_history': tablet_history,
            'totalEntries': len(tablet_history)
        }), 200
        
    except Exception as e:
        print(f"Error getting tablet history: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/medication/upload-prescription', methods=['POST'])
def upload_prescription():
    """Upload prescription details and dosage information"""
    try:
        print("🔍 Uploading prescription details...")
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['patient_id', 'medication_name', 'prescription_details']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400
        
        patient_id = data['patient_id']
        medication_name = data['medication_name']
        prescription_details = data['prescription_details']
        prescribed_by = data.get('prescribed_by', '')
        medication_type = data.get('medication_type', 'prescription')
        dosage_instructions = data.get('dosage_instructions', '')
        frequency = data.get('frequency', '')
        duration = data.get('duration', '')
        special_instructions = data.get('special_instructions', '')
        pregnancy_week = data.get('pregnancy_week', 0)
        
        # Find patient by Patient ID
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({'success': False, 'message': f'Patient not found with ID: {patient_id}'}), 404
        
        # Create prescription entry
        prescription_entry = {
            'medication_name': medication_name,
            'prescription_details': prescription_details,
            'prescribed_by': prescribed_by,
            'medication_type': medication_type,
            'dosage_instructions': dosage_instructions,
            'frequency': frequency,
            'duration': duration,
            'special_instructions': special_instructions,
            'pregnancy_week': pregnancy_week,
            'upload_date': datetime.now().isoformat(),
            'status': 'active'
        }
        
        # Add to patient's prescription history
        if 'prescriptions' not in patient:
            patient['prescriptions'] = []
        
        patient['prescriptions'].append(prescription_entry)
        
        # Update patient document
        result = db.patients_collection.update_one(
            {"patient_id": patient_id},
            {"$set": {"prescriptions": patient['prescriptions']}}
        )
        
        if result.modified_count > 0:
            print(f"✅ Prescription uploaded successfully for patient: {patient_id}")
            return jsonify({
                'success': True,
                'message': f'Prescription for "{medication_name}" uploaded successfully',
                'prescription_entry': prescription_entry
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Failed to upload prescription'}), 500
            
    except Exception as e:
        print(f"Error uploading prescription: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/medication/get-prescription-details/<patient_id>', methods=['GET'])
def get_prescription_details(patient_id):
    """Get prescription details and dosage information for a patient"""
    try:
        print(f"🔍 Getting prescription details for patient ID: {patient_id}")
        
        # Find patient by Patient ID
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({'success': False, 'message': f'Patient not found with ID: {patient_id}'}), 404
        
        # Get prescription details
        prescriptions = patient.get('prescriptions', [])
        
        # Sort by upload date (most recent first)
        prescriptions.sort(key=lambda x: x.get('upload_date', ''), reverse=True)
        
        # Get active prescriptions only
        active_prescriptions = [p for p in prescriptions if p.get('status') == 'active']
        
        print(f"✅ Retrieved {len(active_prescriptions)} active prescriptions for patient: {patient_id}")
        
        return jsonify({
            'success': True,
            'patientId': patient_id,
            'prescriptions': active_prescriptions,
            'totalPrescriptions': len(active_prescriptions),
            'allPrescriptions': prescriptions
        }), 200
        
    except Exception as e:
        print(f"Error getting prescription details: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/medication/update-prescription-status', methods=['PUT'])
def update_prescription_status(patient_id, prescription_id):
    """Update prescription status (active/inactive/completed)"""
    try:
        print(f"🔍 Updating prescription status for patient ID: {patient_id}, prescription ID: {prescription_id}")
        
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({'success': False, 'message': 'Status field is required'}), 400
        
        new_status = data['status']
        valid_statuses = ['active', 'inactive', 'completed']
        
        if new_status not in valid_statuses:
            return jsonify({'success': False, 'message': f'Invalid status. Must be one of: {valid_statuses}'}), 400
        
        # Find patient and update prescription status
        result = db.patients_collection.update_one(
            {
                "patient_id": patient_id,
                "prescriptions._id": prescription_id
            },
            {
                "$set": {
                    "prescriptions.$.status": new_status,
                    "prescriptions.$.last_updated": datetime.now().isoformat()
                }
            }
        )
        
        if result.modified_count > 0:
            print(f"✅ Prescription status updated successfully for patient: {patient_id}")
            return jsonify({
                'success': True,
                'message': f'Prescription status updated to {new_status}',
                'patientId': patient_id,
                'prescriptionId': prescription_id,
                'newStatus': new_status
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Prescription not found or no changes made'}), 404
            
    except Exception as e:
        print(f"Error updating prescription status: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

# ==================== OCR PRESCRIPTION PROCESSING ENDPOINTS ====================

@app.route('/medication/process-prescription-document', methods=['POST'])
def process_prescription_document():
    """Process prescription document using PaddleOCR service from medication folder"""
    try:
        print("🔍 Processing prescription document with PaddleOCR...")
        
        # Check if file is present in request
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        # Get additional data
        patient_id = request.form.get('patient_id', '')
        medication_name = request.form.get('medication_name', '')
        
        print(f"🔍 Processing file: {file.filename}")
        print(f"🔍 Patient ID: {patient_id}")
        print(f"🔍 Medication Name: {medication_name}")
        
        # Read file content
        file_content = file.read()
        
        # Use medication folder's enhanced OCR service if available, otherwise fallback to basic OCR
        if enhanced_ocr_service and OCR_SERVICES_AVAILABLE:
            print("🚀 Using medication folder's enhanced OCR service...")
            
            # Validate file type with enhanced service
            if not enhanced_ocr_service.validate_file_type(file.content_type, file.filename):
                return jsonify({
                    'success': False, 
                    'message': f'Unsupported file type: {file.content_type}. Supported types: {enhanced_ocr_service.allowed_types}'
                }), 400
            
            # Process with enhanced OCR service from medication folder
            import asyncio
            try:
                # Create event loop for async OCR service
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                ocr_result = loop.run_until_complete(
                    enhanced_ocr_service.process_file(
                        file_content=file_content,
                        filename=file.filename
                    )
                )
                
                loop.close()
                
                print("✅ Medication folder OCR processing successful")
                
                # Extract full text content in the format expected by medication folder
                if ocr_result.get('success'):
                    # Get the full text content from the medication folder service
                    full_text_content = ocr_result.get('full_content', '')
                    if not full_text_content and ocr_result.get('results'):
                        # Build full text content from results if not provided
                        full_text_content = ""
                        for i, result in enumerate(ocr_result['results'], 1):
                            text = result.get('text', '')
                            confidence = result.get('confidence', 0)
                            confidence_percent = f"{confidence * 100:.2f}%"
                            full_text_content += f"Text {i}: {text} (Confidence: {confidence_percent})\n"
                        full_text_content = full_text_content.strip()
                    
                    # Update OCR result with full text content
                    ocr_result['full_text_content'] = full_text_content
                    ocr_result['extracted_text'] = full_text_content  # For backward compatibility
                
            except Exception as e:
                print(f"⚠️ Medication folder OCR service error, falling back to basic OCR: {e}")
                if ocr_service:
                    ocr_result = ocr_service.process_file(file_content, file.filename)
                else:
                    return jsonify({'success': False, 'message': 'OCR service not available'}), 503
        elif ocr_service:
            print("⚠️ Using basic OCR service (medication folder not available)")
            
            # Validate file type with basic service
            if not ocr_service.validate_file_type(file.content_type, file.filename):
                return jsonify({
                    'success': False, 
                    'message': f'Unsupported file type: {file.content_type}. Supported types: {list(ocr_service.supported_formats.keys())}'
                }), 400
            
            ocr_result = ocr_service.process_file(file_content, file.filename)
        else:
            return jsonify({'success': False, 'message': 'OCR service not available'}), 503
        
        if not ocr_result['success']:
            return jsonify({
                'success': False,
                'message': f'OCR processing failed: {ocr_result["error"]}'
            }), 500
        
        # Extract the processed text
        extracted_text = ocr_result.get('extracted_text', '')
        
        if not extracted_text or extracted_text.strip() == '':
            return jsonify({
                'success': False,
                'message': 'No text could be extracted from the document'
            }), 400
        
        print(f"✅ Successfully extracted text from {file.filename}")
        print(f"🔍 Extracted text length: {len(extracted_text)} characters")
        
        # Return the extracted text for the user to review and edit
        return jsonify({
            'success': True,
            'message': 'Document processed successfully with PaddleOCR',
            'filename': file.filename,
            'file_type': ocr_result['file_type'],
            'extracted_text': extracted_text,
            'total_pages': ocr_result.get('total_pages', 1),
            'native_text_pages': ocr_result.get('native_text_pages', 0),
            'ocr_pages': ocr_result.get('ocr_pages', 0),
            'processing_details': {
                'method': 'paddleocr_extraction' if enhanced_ocr_service and OCR_SERVICES_AVAILABLE else 'basic_ocr_extraction',
                'confidence': ocr_result.get('results', [{}])[0].get('confidence', 0.0) if ocr_result.get('results') else 0.0,
                'service_used': 'PaddleOCR Enhanced' if enhanced_ocr_service and OCR_SERVICES_AVAILABLE else 'Basic OCR'
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Error processing prescription document: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/medication/process-with-paddleocr', methods=['POST'])
def process_with_paddleocr():
    """Process prescription document using medication folder's PaddleOCR service directly"""
    try:
        print("🚀 Processing prescription with medication folder PaddleOCR service...")
        
        if not enhanced_ocr_service or not OCR_SERVICES_AVAILABLE:
            return jsonify({
                'success': False, 
                'message': 'PaddleOCR service not available (paddlepaddle not installed)'
            }), 503
        
        # Check if file is present in request
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        # Get additional data
        patient_id = request.form.get('patient_id', '')
        medication_name = request.form.get('medication_name', '')
        
        print(f"🔍 Processing file: {file.filename}")
        print(f"🔍 Patient ID: {patient_id}")
        print(f"🔍 Medication Name: {medication_name}")
        
        # Validate file type with enhanced service
        if not enhanced_ocr_service.validate_file_type(file.content_type, file.filename):
            return jsonify({
                'success': False, 
                'message': f'Unsupported file type: {file.content_type}. Supported types: {enhanced_ocr_service.allowed_types}'
            }), 400
        
        # Read file content
        file_content = file.read()       
                    # Process with medication folder's enhanced OCR service
            
        try:
            # Create event loop for async OCR service
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            ocr_result = loop.run_until_complete(
                enhanced_ocr_service.process_file(
                    file_content=file_content,
                    filename=file.filename
                )
            )
            
            loop.close()
            
            print("✅ Medication folder OCR processing successful")
            print(f"🔍 Debug - OCR result keys: {list(ocr_result.keys())}")
            print(f"🔍 Debug - OCR result success: {ocr_result.get('success')}")
            
            # Extract full text content in the format expected by medication folder
            if ocr_result.get('success'):
                # Get the full text content from the medication folder service
                full_text_content = ocr_result.get('full_content', '')
                print(f"🔍 Debug - full_content from OCR: '{full_text_content}'")
                print(f"🔍 Debug - full_content length: {len(full_text_content)}")
                
                # If full_content is not available, extract from results
                if not full_text_content and ocr_result.get('results'):
                    print(f"🔍 Debug - Extracting from results: {len(ocr_result['results'])} results")
                    # Extract all text from results and combine them
                    extracted_texts = []
                    for result in ocr_result['results']:
                        text = result.get('text', '').strip()
                        if text:  # Only add non-empty text
                            extracted_texts.append(text)
                    
                    # Combine all extracted text into one continuous string
                    full_text_content = ' '.join(extracted_texts)
                    print(f"🔍 Debug - Combined text from results: '{full_text_content}'")
                    
                    # If still no content, try alternative fields
                    if not full_text_content:
                        full_text_content = ocr_result.get('extracted_text', '')
                        print(f"🔍 Debug - Trying extracted_text: '{full_text_content}'")
                    
                    # If still no content, try the raw text field
                    if not full_text_content:
                        full_text_content = ocr_result.get('text', '')
                        print(f"🔍 Debug - Trying text field: '{full_text_content}'")
                
                # If we still don't have content, create a fallback
                if not full_text_content:
                    full_text_content = "No text could be extracted from the document"
                    print(f"🔍 Debug - Using fallback text")
                
                # Update OCR result with full text content
                ocr_result['full_text_content'] = full_text_content
                ocr_result['extracted_text'] = full_text_content  # For backward compatibility
                print(f"🔍 Debug - Final full_text_content: '{full_text_content}'")
                print(f"🔍 Debug - Final full_text_content length: {len(full_text_content)}")
            else:
                print(f"🔍 Debug - OCR processing failed: {ocr_result.get('error', 'Unknown error')}")
            
            # Send results to webhook if processing was successful
            webhook_results = []
            if ocr_result.get("success") and webhook_service and webhook_service.is_configured():
                try:
                    print("🚀 Sending OCR results to webhook using medication folder service...")
                    
                    # Create new event loop for webhook service
                    webhook_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(webhook_loop)
                    
                    webhook_results = webhook_loop.run_until_complete(
                        webhook_service.send_ocr_result(ocr_result, file.filename)
                    )
                    
                    webhook_loop.close()
                    
                    # Log webhook delivery status
                    for webhook_result in webhook_results:
                        if webhook_result["success"]:
                            print(f"✅ Webhook sent successfully to {webhook_result['config_name']} ({webhook_result['url']})")
                        else:
                            print(f"❌ Webhook failed for {webhook_result['config_name']}: {webhook_result.get('error', 'Unknown error')}")
                    
                except Exception as e:
                    print(f"❌ Error sending webhook: {e}")
            
            # Return comprehensive result with full text content
            final_response = {
                'success': True,
                'message': 'Document processed successfully with medication folder OCR service',
                'filename': file.filename,
                'ocr_result': ocr_result,
                'full_text_content': ocr_result.get('full_text_content', ''),
                'webhook_delivery': {
                    'status': 'completed' if webhook_results else 'not_configured',
                    'results': webhook_results,
                    'timestamp': datetime.now().isoformat()
                },
                'service_used': 'Medication Folder Enhanced OCR',
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"🔍 Debug - Final response full_text_content: '{final_response['full_text_content']}'")
            print(f"🔍 Debug - Final response full_text_content length: {len(final_response['full_text_content'])}")
            print(f"🔍 Debug - Final response keys: {list(final_response.keys())}")
            
            return jsonify(final_response), 200
        
        except Exception as e:
            print(f"❌ PaddleOCR processing error: {e}")
            return jsonify({
                'success': False,
                'message': f'PaddleOCR processing failed: {str(e)}'
            }), 500
        
    except Exception as e:
        print(f"❌ Error in PaddleOCR processing: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/medication/process-prescription-text', methods=['POST'])
def process_prescription_text():
    """Process raw prescription text and extract structured medication information"""
    try:
        print("🔍 Processing prescription text for structured extraction...")
        
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'success': False, 'message': 'Text content is required'}), 400
        
        prescription_text = data['text']
        patient_id = data.get('patient_id', '')
        
        print(f"🔍 Processing text for patient: {patient_id}")
        print(f"🔍 Text length: {len(prescription_text)} characters")
        
        # Basic text processing and cleaning
        cleaned_text = prescription_text.strip()
        
        # Extract potential medication information using simple patterns
        # This is a basic implementation - in production, you'd use more sophisticated NLP
        extracted_info = {
            'medication_name': '',
            'dosage': '',
            'frequency': '',
            'duration': '',
            'instructions': '',
            'prescribed_by': '',
            'raw_text': cleaned_text
        }
        
        # Simple pattern matching for common prescription formats
        lines = cleaned_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for medication name patterns
            if any(keyword in line.lower() for keyword in ['tablet', 'capsule', 'syrup', 'injection', 'mg', 'ml']):
                if not extracted_info['medication_name']:
                    extracted_info['medication_name'] = line
            
            # Look for dosage patterns
            elif any(keyword in line.lower() for keyword in ['mg', 'ml', 'tablet', 'capsule', 'dose']):
                if not extracted_info['dosage']:
                    extracted_info['dosage'] = line
            
            # Look for frequency patterns
            elif any(keyword in line.lower() for keyword in ['daily', 'twice', 'three times', 'every', 'hour']):
                if not extracted_info['frequency']:
                    extracted_info['frequency'] = line
            
            # Look for duration patterns
            elif any(keyword in line.lower() for keyword in ['days', 'weeks', 'months', 'until', 'course']):
                if not extracted_info['duration']:
                    extracted_info['duration'] = line
        
        print(f"✅ Successfully processed prescription text")
        
        return jsonify({
            'success': True,
            'message': 'Prescription text processed successfully',
            'extracted_info': extracted_info,
            'processing_details': {
                'method': 'text_analysis',
                'confidence': 0.7,  # Basic pattern matching confidence
                'total_lines_processed': len(lines)
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Error processing prescription text: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/medication/process-with-mock-n8n', methods=['POST'])
def process_with_mock_n8n():
    """Process prescription with OCR and send to N8N webhook using proper webhook service"""
    try:
        print("🔍 Processing prescription with N8N webhook...")
        
        data = request.get_json()
        patient_id = data.get('patient_id')
        medication_name = data.get('medication_name')
        extracted_text = data.get('extracted_text')
        filename = data.get('filename')
        
        if not patient_id or not extracted_text:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        print(f"🔍 Processing for patient: {patient_id}")
        print(f"🔍 Medication: {medication_name}")
        print(f"🔍 Filename: {filename}")
        print(f"🔍 Text length: {len(extracted_text)} characters")
        
        # Prepare OCR data in the format expected by webhook service
        ocr_data = {
            'success': True,
            'results': [
                {
                    'text': extracted_text,
                    'confidence': 0.95,
                    'bbox': [0, 0, 100, 100]
                }
            ],
            'text_count': 1,
            'processing_details': {
                'confidence': 0.95,
                'processing_time': '0.5s'
            }
        }

        # Use proper webhook service if available, otherwise fallback to mock
        if webhook_service and webhook_service.is_configured():
            print("🚀 Using proper webhook service to send to N8N...")
            
            # Send to N8N webhook using the proper service
            import asyncio
            try:
                # Create event loop for async webhook service
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                webhook_results = loop.run_until_complete(
                    webhook_service.send_ocr_result(ocr_data, filename)
                )
                
                loop.close()
                
                # Check webhook results
                n8n_success = any(result.get('success', False) for result in webhook_results)
                
                if n8n_success:
                    print("✅ N8N webhook sent successfully")
                    n8n_result = {
                        'success': True,
                        'message': 'Prescription sent to N8N webhook successfully',
                        'webhook_results': webhook_results,
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    print("❌ N8N webhook failed, using mock service")
                    n8n_result = mock_n8n_service.process_prescription_webhook({
                        'patient_id': patient_id,
                        'medication_name': medication_name,
                        'extracted_text': extracted_text,
                        'filename': filename
                    })
                    
            except Exception as e:
                print(f"⚠️ Webhook service error, falling back to mock: {e}")
                n8n_result = mock_n8n_service.process_prescription_webhook({
                    'patient_id': patient_id,
                    'medication_name': medication_name,
                    'extracted_text': extracted_text,
                    'filename': filename
                })
        else:
            print("⚠️ Using mock N8N service (webhook service not available)")
            n8n_result = mock_n8n_service.process_prescription_webhook({
                'patient_id': patient_id,
                'medication_name': medication_name,
                'extracted_text': extracted_text,
                'filename': filename
            })

        print(f"✅ Processing completed successfully")
        
        return jsonify({
            'success': True,
            'message': 'Prescription processed successfully with OCR and N8N webhook',
            'ocr_result': {
                'extracted_text': extracted_text,
                'filename': filename,
                'file_type': 'text',
                'total_pages': 1
            },
            'n8n_result': n8n_result,
            'webhook_data': {
                'patient_id': patient_id,
                'medication_name': medication_name,
                'filename': filename,
                'extracted_text': extracted_text,
                'timestamp': datetime.now().isoformat()
            },
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"❌ Error processing with N8N webhook: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/medication/process-with-n8n-webhook', methods=['POST'])
def process_with_n8n_webhook():
    """Process prescription with OCR and send directly to N8N webhook using medication folder webhook service"""
    try:
        print("🚀 Processing prescription with N8N webhook using medication folder service...")
        
        if not webhook_service or not webhook_service.is_configured():
            return jsonify({
                'success': False, 
                'message': 'Webhook service not available or not configured'
            }), 503
        
        data = request.get_json()
        patient_id = data.get('patient_id')
        medication_name = data.get('medication_name')
        extracted_text = data.get('extracted_text')
        filename = data.get('filename')
        
        if not patient_id or not extracted_text:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        print(f"🔍 Processing for patient: {patient_id}")
        print(f"🔍 Medication: {medication_name}")
        print(f"🔍 Filename: {filename}")
        print(f"🔍 Text length: {len(extracted_text)} characters")
        
        # Prepare OCR data in the format expected by webhook service
        # This matches the structure from medication folder's webhook service
        ocr_data = {
            'success': True,
            'results': [
                {
                    'text': extracted_text,
                    'confidence': 0.95,
                    'bbox': [0, 0, 100, 100]
                }
            ],
            'text_count': 1,
            'processing_details': {
                'confidence': 0.95,
                'processing_time': '0.5s'
            }
        }

        # Send to N8N webhook using the medication folder's webhook service
        import asyncio
        try:
            # Create event loop for async webhook service
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            webhook_results = loop.run_until_complete(
                webhook_service.send_ocr_result(ocr_data, filename)
            )
            
            loop.close()
            
            # Check webhook results
            n8n_success = any(result.get('success', False) for result in webhook_results)
            
            if n8n_success:
                print("✅ N8N webhook sent successfully using medication folder service")
                return jsonify({
                    'success': True,
                    'message': 'Prescription sent to N8N webhook successfully',
                    'webhook_results': webhook_results,
                    'ocr_data': ocr_data,
                    'webhook_data': {
                        'patient_id': patient_id,
                        'medication_name': medication_name,
                        'filename': filename,
                        'extracted_text': extracted_text,
                        'timestamp': datetime.now().isoformat()
                    },
                    'timestamp': datetime.now().isoformat()
                }), 200
            else:
                print("❌ N8N webhook failed")
                return jsonify({
                    'success': False,
                    'message': 'Failed to send to N8N webhook',
                    'webhook_results': webhook_results,
                    'error': 'All webhook attempts failed'
                }), 500
                
        except Exception as e:
            print(f"❌ Error sending to N8N webhook: {e}")
            return jsonify({
                'success': False,
                'message': f'Error sending to N8N webhook: {str(e)}'
            }), 500

    except Exception as e:
        print(f"❌ Error processing with N8N webhook: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

# ==================== QUANTUM & LLM MANAGEMENT ENDPOINTS ====================

@app.route('/quantum/health', methods=['GET'])
def quantum_health_check():
    """Check quantum vector service health"""
    return jsonify({
        'success': True,
        'qdrant_available': QDRANT_AVAILABLE,
        'qdrant_connected': quantum_service.client is not None,
        'embedding_model_available': SENTENCE_TRANSFORMERS_AVAILABLE,
        'embedding_model_loaded': quantum_service.embedding_model is not None,
        'collection_status': quantum_service.ensure_collection(),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/quantum/collections', methods=['GET'])
def quantum_collections():
    """Get Qdrant collections information"""
    if not quantum_service.client:
        return jsonify({
            'success': False,
            'message': 'Qdrant client not available'
        }), 503
    
    try:
        collections = quantum_service.client.get_collections().collections
        names = [c.name for c in collections]
        return jsonify({
            'success': True,
            'collections': names,
            'total_collections': len(names),
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting collections: {str(e)}'
        }), 500

@app.route('/quantum/collection-status/<collection_name>', methods=['GET'])
def quantum_collection_status(collection_name):
    """Get specific collection status and statistics"""
    if not quantum_service.client:
        return jsonify({
            'success': False,
            'message': 'Qdrant client not available'
        }), 503
    
    try:
        collection_info = quantum_service.client.get_collection(collection_name)
        collection_stats = quantum_service.client.get_collection(collection_name).dict()
        
        return jsonify({
            'success': True,
            'collection_name': collection_name,
            'status': collection_stats.get('status'),
            'vectors_count': collection_stats.get('vectors_count', 0),
            'points_count': collection_stats.get('points_count', 0),
            'segments_count': collection_stats.get('segments_count', 0),
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting collection status: {str(e)}'
        }), 500

@app.route('/llm/health', methods=['GET'])
def llm_health_check():
    """Check LLM service health"""
    return jsonify({
        'success': True,
        'openai_available': OPENAI_AVAILABLE,
        'openai_configured': bool(OPENAI_API_KEY),
        'llm_client_connected': llm_service.client is not None,
        'model': LLM_MODEL,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/llm/test', methods=['POST'])
def llm_test():
    """Test LLM functionality with a simple prompt"""
    try:
        data = request.get_json()
        test_prompt = data.get('prompt', 'Hello, how are you?') if data else 'Hello, how are you?'
        
        if not llm_service.client:
            return jsonify({
                'success': False,
                'message': 'LLM service not available'
            }), 503
        
        try:
            response = llm_service.client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant. Respond briefly."},
                    {"role": "user", "content": test_prompt}
                ],
                temperature=0.1,
                max_tokens=50
            )
            
            content = response.choices[0].message.content.strip()
            
            return jsonify({
                'success': True,
                'test_prompt': test_prompt,
                'response': content,
                'model_used': LLM_MODEL,
                'timestamp': datetime.now().isoformat()
            }), 200
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'LLM test failed: {str(e)}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Request processing failed: {str(e)}'
        }), 500

@app.route('/quantum/add-knowledge', methods=['POST'])
def add_knowledge():
    """Add knowledge document to Qdrant vector database"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        required_fields = ['text', 'source', 'trimester']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        if not quantum_service.client or not quantum_service.embedding_model:
            return jsonify({
                'success': False,
                'message': 'Quantum vector service not available'
            }), 503
        
        # Generate embedding for the text
        text_vector = quantum_service.embed_text(data['text'])
        if not text_vector:
            return jsonify({
                'success': False,
                'message': 'Failed to generate text embedding'
            }), 500
        
        # Create point structure
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=text_vector,
            payload={
                "text": data['text'],
                "source": data['source'],
                "trimester": data['trimester'],
                "tags": data.get('tags', []),
                "triage": data.get('triage', 'general'),
                "updated_at": datetime.now().isoformat()
            }
        )
        
        # Ensure collection exists
        quantum_service.ensure_collection()
        
        # Upsert point
        quantum_service.client.upsert(
            collection_name=QDRANT_COLLECTION,
            points=[point]
        )
        
        return jsonify({
            'success': True,
            'message': 'Knowledge document added successfully',
            'document_id': point.id,
            'vector_size': len(text_vector),
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"Error adding knowledge: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/quantum/search-knowledge', methods=['POST'])
def search_knowledge():
    """Search knowledge base using vector similarity"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        query_text = data.get('text', '').strip()
        weeks_pregnant = data.get('weeks_pregnant', 1)
        limit = data.get('limit', TOP_K)
        
        if not query_text:
            return jsonify({
                'success': False,
                'message': 'Query text is required'
            }), 400
        
        if not quantum_service.client or not quantum_service.embedding_model:
            return jsonify({
                'success': False,
                'message': 'Quantum vector service not available'
            }), 503
        
        # Search knowledge base
        suggestions = quantum_service.search_knowledge(query_text, weeks_pregnant)
        
        return jsonify({
            'success': True,
            'query_text': query_text,
            'weeks_pregnant': weeks_pregnant,
            'suggestions': suggestions,
            'total_found': len(suggestions),
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"Error searching knowledge: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/get-patient-profile-by-email/<email>', methods=['GET'])
def get_patient_profile_by_email(email):
    """Get patient profile by email"""
    try:
        patient = db.patients_collection.find_one({"email": email})
        if not patient:
            return jsonify({'success': False, 'message': 'Patient not found'}), 404
        
        profile_data = {
            'patient_id': patient.get('patient_id'),
            'username': patient.get('username'),
            'email': patient.get('email'),
            'pregnancy_week': patient.get('pregnancy_week'),
            # Add other fields as needed
        }
        
        return jsonify({
            'success': True,
            'profile': profile_data
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/get-patient-profile/<patient_id>', methods=['GET'])
def get_patient_profile(patient_id):
    """Get patient profile by patient ID (same pattern as kick count)"""
    try:
        print(f"🔍 Getting patient profile for patient ID: {patient_id}")
        
        # Find patient by Patient ID (same as kick count storage)
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({
                'success': False,
                'message': f'Patient not found with ID: {patient_id}'
            }), 404
        
        # Prepare profile data (same structure as kick count)
        profile_data = {
            'patient_id': patient.get('patient_id'),
            'username': patient.get('username'),
            'email': patient.get('email'),
            'mobile': patient.get('mobile'),
            'first_name': patient.get('first_name'),
            'last_name': patient.get('last_name'),
            'age': patient.get('age'),
            'blood_type': patient.get('blood_type'),
            'date_of_birth': patient.get('date_of_birth'),
            'height': patient.get('height'),
            'weight': patient.get('weight'),
            'is_pregnant': patient.get('is_pregnant'),
            'pregnancy_week': patient.get('pregnancy_week'),
            'last_period_date': patient.get('last_period_date'),
            'expected_delivery_date': patient.get('expected_delivery_date'),
            'emergency_contact': patient.get('emergency_contact'),
            'status': patient.get('status'),
            'created_at': patient.get('created_at'),
            'last_updated': patient.get('last_updated'),
            'profile_completed_at': patient.get('profile_completed_at'),
            'email_verified': patient.get('email_verified'),
            'verified_at': patient.get('verified_at'),
            'password_updated_at': patient.get('password_updated_at'),
        }
        
        print(f"✅ Patient profile retrieved successfully for patient ID: {patient_id}")
        print(f"🆔 Patient ID: {profile_data['patient_id']}")
        print(f" Username: {profile_data['username']}")
        print(f"📧 Email: {profile_data['email']}")
        print(f"📅 Pregnancy Week: {profile_data['pregnancy_week']}")
        print(f" Expected Delivery: {profile_data['expected_delivery_date']}")
        
        return jsonify({
            'success': True,
            'profile': profile_data,
            'message': 'Patient profile retrieved successfully'
        }), 200
        
    except Exception as e:
        print(f"Error getting patient profile by patient ID: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/medication/test-status', methods=['GET'])
def test_medication_status():
    """Test endpoint to check medication service status"""
    try:
        status = {
            'paddle_ocr_available': PADDLE_OCR_AVAILABLE,
            'ocr_services_available': OCR_SERVICES_AVAILABLE,
            'enhanced_ocr_service': enhanced_ocr_service is not None,
            'ocr_service': ocr_service is not None,
            'webhook_service': webhook_service is not None,
            'webhook_config_service': webhook_config_service is not None,
            'timestamp': datetime.now().isoformat()
        }
        
        # Check webhook configurations
        if webhook_config_service:
            try:
                configs = webhook_config_service.get_all_configs()
                status['webhook_configs_count'] = len(configs)
                status['webhook_configs'] = [
                    {
                        'name': config.name,
                        'url': config.url,
                        'enabled': config.enabled
                    } for config in configs
                ]
            except Exception as e:
                status['webhook_configs_error'] = str(e)
        
        return jsonify({
            'success': True,
            'message': 'Medication service status check',
            'status': status
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error checking status: {str(e)}'
        }), 500

@app.route('/medication/test-file-upload', methods=['POST'])
def test_file_upload():
    """Test endpoint to verify file upload functionality"""
    try:
        print("🧪 Testing file upload endpoint...")
        
        # Check if file is present in request
        if 'file' not in request.files:
            return jsonify({
                'success': False, 
                'message': 'No file provided',
                'test_type': 'file_upload_test'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False, 
                'message': 'No file selected',
                'test_type': 'file_upload_test'
            }), 400
        
        # Get additional data
        patient_id = request.form.get('patient_id', '')
        medication_name = request.form.get('medication_name', '')
        
        print(f"✅ File upload test successful!")
        print(f"🔍 File: {file.filename}")
        print(f"🔍 Patient ID: {patient_id}")
        print(f"🔍 Medication: {medication_name}")
        print(f"🔍 File size: {len(file.read())} bytes")
        
        return jsonify({
            'success': True,
            'message': 'File upload test successful',
            'test_type': 'file_upload_test',
            'filename': file.filename,
            'patient_id': patient_id,
            'medication_name': medication_name,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"❌ File upload test error: {e}")
        return jsonify({
            'success': False,
            'message': f'File upload test failed: {str(e)}',
            'test_type': 'file_upload_test',
            'error': str(e)
        }), 500

# ==================== DATABASE HEALTH CHECK ====================

@app.route('/health/database', methods=['GET'])
def check_database_health():
    """Check database connection status"""
    try:
        if db.is_connected():
            return jsonify({
                'success': True,
                'message': 'Database is connected and healthy',
                'status': 'connected',
                'collections': {
                    'patients': db.patients_collection is not None,
                    'mental_health': db.mental_health_collection is not None
                }
            }), 200
        else:
            # Try to reconnect
            print("🔄 Database health check failed, attempting reconnection...")
            if db.reconnect():
                return jsonify({
                    'success': True,
                    'message': 'Database reconnected successfully',
                    'status': 'reconnected',
                    'collections': {
                        'patients': db.patients_collection is not None,
                        'mental_health': db.mental_health_collection is not None
                    }
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': 'Database is not connected and reconnection failed',
                    'status': 'disconnected',
                    'error': 'Database connection failed'
                }), 503
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Database health check failed',
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/health/database/reconnect', methods=['POST'])
def force_database_reconnect():
    """Force database reconnection"""
    try:
        print("🔄 Force reconnecting to database...")
        if db.reconnect():
            return jsonify({
                'success': True,
                'message': 'Database reconnected successfully',
                'status': 'reconnected',
                'collections': {
                    'patients': db.patients_collection is not None,
                    'mental_health': db.mental_health_collection is not None
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Database reconnection failed',
                'status': 'failed',
                'error': 'Unable to reconnect to database'
            }), 503
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Database reconnection failed',
            'status': 'error',
            'error': str(e)
        }), 500

# ==================== MENTAL HEALTH ENDPOINTS ====================

@app.route('/mental-health/mood-checkin', methods=['POST'])
def submit_mood_checkin():
    """Submit a mood check-in for a patient"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        # Extract required fields
        patient_id = data.get('patient_id')
        mood = data.get('mood')
        note = data.get('note', '')
        date_str = data.get('date')
        
        if not patient_id or not mood:
            return jsonify({
                'success': False,
                'message': 'Patient ID and mood are required'
            }), 400
        
        # Parse date (use current date if not provided)
        if date_str:
            try:
                checkin_date = datetime.strptime(date_str, '%d/%m/%Y').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Invalid date format. Use DD/MM/YYYY'
                }), 400
        else:
            checkin_date = datetime.now().date()
        
        # Check if database is connected
        if not db.is_connected():
            return jsonify({
                'success': False,
                'message': 'Database not connected'
            }), 503
        
        # Check if patient exists
        if db.patients_collection is None:
            return jsonify({
                'success': False,
                'message': 'Database connection error'
            }), 500
        
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({
                'success': False,
                'message': 'Patient not found'
            }), 404
        
        # Check if already checked in for this date (mood check-in only)
        existing_mood_checkin = db.mental_health_collection.find_one({
            "patient_id": patient_id,
            "date": checkin_date.isoformat(),
            "type": "mood_checkin"
        })
        
        if existing_mood_checkin:
            return jsonify({
                'success': False,
                'message': 'Already checked in for this date'
            }), 409
        
        # Create mood check-in entry
        mood_entry = {
            "patient_id": patient_id,
            "mood": mood,
            "note": note,
            "date": checkin_date.isoformat(),
            "timestamp": datetime.now().isoformat(),
            "type": "mood_checkin",
            "created_at": datetime.now().isoformat()
        }
        
        # Insert into mental health collection
        result = db.mental_health_collection.insert_one(mood_entry)
        
        if result.inserted_id:
            print(f"✅ Mood check-in saved for patient {patient_id}: {mood}")
            
            # Update patient's mental health logs count
            db.patients_collection.update_one(
                {"patient_id": patient_id},
                {
                    "$push": {"mental_health_logs": mood_entry},
                    "$inc": {"mental_health_logs_count": 1}
                }
            )
            
            return jsonify({
                'success': True,
                'message': 'Mood check-in saved successfully',
                'data': {
                    'id': str(result.inserted_id),
                    'patient_id': patient_id,
                    'mood': mood,
                    'date': checkin_date.isoformat(),
                    'timestamp': mood_entry['timestamp']
                }
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to save mood check-in'
            }), 500
            
    except Exception as e:
        print(f"❌ Mood check-in error: {e}")
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500

@app.route('/mental-health/history/<patient_id>', methods=['GET'])
def get_mental_health_history(patient_id):
    """Get mental health history for a patient"""
    try:
        # Check if database is connected
        if not db.is_connected():
            return jsonify({
                'success': False,
                'message': 'Database not connected'
            }), 503
        
        if db.mental_health_collection is None:
            return jsonify({
                'success': False,
                'message': 'Database connection error'
            }), 500
        
        # Get mood check-ins for the patient
        mood_entries = list(db.mental_health_collection.find(
            {"patient_id": patient_id, "type": "mood_checkin"},
            {"_id": 0}  # Exclude MongoDB _id
        ).sort("date", -1).limit(30))  # Last 30 entries
        
        # Get assessment entries for the patient
        assessment_entries = list(db.mental_health_collection.find(
            {"patient_id": patient_id, "type": "mental_health_assessment"},
            {"_id": 0}  # Exclude MongoDB _id
        ).sort("date", -1).limit(30))  # Last 30 entries
        
        return jsonify({
            'success': True,
            'data': {
                'patient_id': patient_id,
                'mood_history': mood_entries,
                'assessment_history': assessment_entries,
                'total_mood_entries': len(mood_entries),
                'total_assessment_entries': len(assessment_entries)
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Get mental health history error: {e}")
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500

@app.route('/mental-health/assessment', methods=['POST'])
def submit_mental_health_assessment():
    """Submit a mental health assessment for a patient"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        # Extract required fields
        patient_id = data.get('patient_id')
        score = data.get('score')
        date_str = data.get('date')
        
        if not patient_id or score is None:
            return jsonify({
                'success': False,
                'message': 'Patient ID and score are required'
            }), 400
        
        # Validate score range
        if not isinstance(score, (int, float)) or score < 1 or score > 10:
            return jsonify({
                'success': False,
                'message': 'Score must be a number between 1 and 10'
            }), 400
        
        # Parse date (use current date if not provided)
        if date_str:
            try:
                assessment_date = datetime.strptime(date_str, '%d/%m/%Y').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Invalid date format. Use DD/MM/YYYY'
                }), 400
        else:
            assessment_date = datetime.now().date()
        
        # Check if database is connected
        if not db.is_connected():
            return jsonify({
                'success': False,
                'message': 'Database not connected'
            }), 503
        
        # Check if patient exists
        if db.patients_collection is None:
            return jsonify({
                'success': False,
                'message': 'Database connection error'
            }), 500
        
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({
                'success': False,
                'message': 'Patient not found'
            }), 404
        
        # Check if already assessed for this date
        existing_assessment = db.mental_health_collection.find_one({
            "patient_id": patient_id,
            "date": assessment_date.isoformat(),
            "type": "mental_health_assessment"
        })
        
        if existing_assessment:
            return jsonify({
                'success': False,
                'message': 'Already assessed for this date'
            }), 409
        
        # Create assessment entry
        assessment_entry = {
            "patient_id": patient_id,
            "score": float(score),
            "date": assessment_date.isoformat(),
            "timestamp": datetime.now().isoformat(),
            "type": "mental_health_assessment",
            "created_at": datetime.now().isoformat()
        }
        
        # Insert into mental health collection
        result = db.mental_health_collection.insert_one(assessment_entry)
        
        if result.inserted_id:
            print(f"✅ Mental health assessment saved for patient {patient_id}: {score}/10")
            
            return jsonify({
                'success': True,
                'message': 'Mental health assessment saved successfully',
                'data': {
                    'id': str(result.inserted_id),
                    'patient_id': patient_id,
                    'score': float(score),
                    'date': assessment_date.isoformat(),
                    'timestamp': assessment_entry['timestamp']
                }
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to save assessment'
            }), 500
            
    except Exception as e:
        print(f"❌ Mental health assessment error: {e}")
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500

@app.route('/medication/save-tablet-tracking', methods=['POST'])
def save_tablet_tracking():
    """Save tablet tracking data in medication_daily_tracking array"""
    try:
        data = request.get_json()
        print(f"🔍 Saving tablet tracking in medication_daily_tracking array: {data}")
        
        # Validate required fields
        required_fields = ['patient_id', 'tablet_name', 'tablet_taken_today']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400
        
        patient_id = data['patient_id']
        tablet_name = data['tablet_name']
        tablet_taken_today = data['tablet_taken_today']
        is_prescribed = data.get('is_prescribed', False)
        notes = data.get('notes', '')
        date_taken = data.get('date_taken', '')
        time_taken = data.get('time_taken', '')
        tracking_type = data.get('type', 'daily_tracking')
        timestamp = data.get('timestamp', datetime.now().isoformat())
        
        # Find patient by Patient ID
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({'success': False, 'message': f'Patient not found with ID: {patient_id}'}), 404
        
        # Create tablet tracking entry for medication_daily_tracking array
        tablet_entry = {
            'tablet_name': tablet_name,
            'tablet_taken_today': tablet_taken_today,
            'is_prescribed': is_prescribed,
            'notes': notes,
            'date_taken': date_taken,
            'time_taken': time_taken,
            'type': tracking_type,
            'timestamp': timestamp
        }
        
        # Add to patient's medication_daily_tracking array
        if 'medication_daily_tracking' not in patient:
            patient['medication_daily_tracking'] = []
        
        patient['medication_daily_tracking'].append(tablet_entry)
        
        # Update patient document
        result = db.patients_collection.update_one(
            {"patient_id": patient_id},
            {"$set": {"medication_daily_tracking": patient['medication_daily_tracking']}}
        )
        
        if result.modified_count > 0:
            print(f"✅ Tablet tracking saved successfully in medication_daily_tracking array for patient: {patient_id}")
            return jsonify({
                'success': True,
                'message': f'Tablet "{tablet_name}" tracking saved successfully in medication_daily_tracking array',
                'tablet_entry': tablet_entry,
                'total_entries': len(patient['medication_daily_tracking'])
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Failed to save tablet tracking'}), 500
            
    except Exception as e:
        print(f"Error saving tablet tracking in medication_daily_tracking array: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/medication/get-tablet-tracking-history/<patient_id>', methods=['GET'])
def get_tablet_tracking_history(patient_id):
    """Get tablet tracking history from medication_daily_tracking array"""
    try:
        print(f"🔍 Getting tablet tracking history from medication_daily_tracking array for patient ID: {patient_id}")
        
        # Find patient by Patient ID
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({'success': False, 'message': f'Patient not found with ID: {patient_id}'}), 404
        
        # Get tablet tracking history from medication_daily_tracking array
        tablet_history = patient.get('medication_daily_tracking', [])
        
        # Sort by timestamp (most recent first)
        tablet_history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        print(f"✅ Retrieved {len(tablet_history)} tablet tracking entries from medication_daily_tracking array for patient: {patient_id}")
        
        return jsonify({
            'success': True,
            'patientId': patient_id,
            'tablet_tracking_history': tablet_history,
            'totalEntries': len(tablet_history)
        }), 200
        
    except Exception as e:
        print(f"Error getting tablet tracking history from medication_daily_tracking array: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/medication/send-reminders', methods=['POST'])
def send_medication_reminders():
    """Manually trigger medication reminder check and send emails"""
    try:
        print("🔍 Manual medication reminder trigger requested")
        
        # Check and send medication reminders
        reminders_sent = check_and_send_medication_reminders()
        
        return jsonify({
            'success': True,
            'message': f'Medication reminder check completed. {reminders_sent} reminders sent.',
            'reminders_sent': reminders_sent,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"Error sending medication reminders: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/medication/test-reminder/<patient_id>', methods=['POST'])
def test_medication_reminder(patient_id):
    """Test medication reminder email for a specific patient"""
    try:
        print(f"🔍 Testing medication reminder for patient ID: {patient_id}")
        
        # Find patient by Patient ID
        patient = db.patients_collection.find_one({"patient_id": patient_id})
        if not patient:
            return jsonify({'success': False, 'message': f'Patient not found with ID: {patient_id}'}), 404
        
        email = patient.get('email')
        username = patient.get('username')
        
        if not email or not username:
            return jsonify({'success': False, 'message': 'Patient email or username not found'}), 400
        
        # Send a test reminder email
        if send_medication_reminder_email(
            email=email,
            username=username,
            medication_name="Test Medication",
            dosage="Test Dose",
            time="Test Time",
            frequency="Test Frequency",
            special_instructions="This is a test reminder email"
        ):
            return jsonify({
                'success': True,
                'message': f'Test medication reminder sent successfully to {email}',
                'patient_email': email,
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Failed to send test reminder email'}), 500
            
    except Exception as e:
        print(f"Error testing medication reminder: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

# Initialize complete PaddleOCR and webhook services if available
if PADDLE_OCR_AVAILABLE:
    # Initialize webhook services (these should always be available)
    webhook_service = WebhookService()
    webhook_config_service = WebhookConfigService()
    
    # Initialize OCR services if available
    if OCR_SERVICES_AVAILABLE:
        enhanced_ocr_service = EnhancedOCRService()
        ocr_service = OCRService()
        print("✅ All PaddleOCR services initialized successfully")
    else:
        enhanced_ocr_service = None
        ocr_service = None
        print("⚠️ OCR services not available, using fallback OCR")
    
    print(f"🔍 Enhanced OCR service available: {enhanced_ocr_service is not None}")
    print(f"🔍 Basic OCR service available: {ocr_service is not None}")
    print(f"🔍 Webhook service available: {webhook_service is not None}")
    
    # Configure the N8N webhook
    n8n_config = WebhookConfig(
        id="n8n_prescription_webhook",
        name="N8N Prescription Processor",
        url="https://n8n.srv795087.hstgr.cloud/webhook/bf25c478-c4a9-44c5-8f43-08c3fcae51f9",
        method="POST",
        enabled=True,
        timeout=30,
        retry_attempts=3,
        retry_delay=2,
        headers={"Content-Type": "application/json"},
        payload_template={}  # Use default payload structure
    )
    
    # Add the N8N webhook configuration
    try:
        # Check if config already exists
        existing_configs = webhook_config_service.get_all_configs()
        config_exists = any(config.name == "N8N Prescription Processor" for config in existing_configs)
        
        if config_exists:
            print("✅ N8N webhook configuration already exists")
        else:
            # Create new config using WebhookConfigCreate
            from app.models.webhook_config import WebhookConfigCreate
            config_data = WebhookConfigCreate(
                name=n8n_config.name,
                url=n8n_config.url,
                enabled=n8n_config.enabled,
                method=n8n_config.method,
                headers=n8n_config.headers,
                timeout=n8n_config.timeout,
                retry_attempts=n8n_config.retry_attempts,
                retry_delay=n8n_config.retry_delay,
                payload_template=n8n_config.payload_template,
                filters={}
            )
            webhook_config_service.create_config(config_data)
            print("✅ N8N webhook configuration created successfully")
    except Exception as e:
        print(f"⚠️ Could not configure N8N webhook: {e}")
        print(f"💡 Error details: {str(e)}")
else:
    enhanced_ocr_service = None
    ocr_service = None
    webhook_service = None
    webhook_config_service = None
    print("⚠️ Using fallback services (PaddleOCR not available)")

# ==================== MEDICATION REMINDER SCHEDULER ====================
import threading
import time

def medication_reminder_scheduler():
    """Background scheduler for medication reminders"""
    while True:
        try:
            print("⏰ Medication reminder scheduler running...")
            check_and_send_medication_reminders()
            
            # Wait for 15 minutes before next check
            time.sleep(15 * 60)  # 15 minutes in seconds
            
        except Exception as e:
            print(f"❌ Error in medication reminder scheduler: {e}")
            # Wait 5 minutes before retrying on error
            time.sleep(5 * 60)

def start_medication_reminder_scheduler():
    """Start the medication reminder scheduler in a background thread"""
    try:
        scheduler_thread = threading.Thread(target=medication_reminder_scheduler, daemon=True)
        scheduler_thread.start()
        print("✅ Medication reminder scheduler started successfully")
        return scheduler_thread
    except Exception as e:
        print(f"❌ Failed to start medication reminder scheduler: {e}")
        return None

# ==================== NUTRITION BACKEND INTEGRATION ====================

@app.route('/nutrition/health', methods=['GET'])
def nutrition_health_check():
    """Nutrition service health check endpoint"""
    return jsonify({
        'success': True,
        'message': 'Nutrition service is running',
        'timestamp': datetime.now().isoformat(),
        'database_connected': db.patients_collection is not None
    })

@app.route('/nutrition/transcribe', methods=['POST'])
def transcribe_audio():
    """Transcribe audio using Whisper AI with Tamil language support"""
    try:
        print("🎤 Transcription request received")
        
        # Get OpenAI API key
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            return jsonify({
                'success': False,
                'message': 'OpenAI API key not configured'
            }), 500
        
        try:
            from openai import OpenAI
        except ImportError:
            return jsonify({
                'success': False,
                'message': 'OpenAI package not installed. Run: pip install openai'
            }), 500
        
        # Initialize OpenAI client
        client = OpenAI(api_key=openai_api_key)
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        audio_data = data.get('audio')
        language = data.get('language', 'auto')  # Default to auto-detect
        method = data.get('method', 'whisper')
        
        if not audio_data:
            return jsonify({
                'success': False,
                'message': 'Audio data is required'
            }), 400
        
        print(f"🔍 Processing audio with method: {method}, language: {language}")
        
        try:
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data)
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                temp_file.write(audio_bytes)
                temp_file_path = temp_file.name
            
            # Transcribe with Whisper
            with open(temp_file_path, 'rb') as audio_file:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language if language != 'auto' else None
                )
            
            transcription = response.text.strip()
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            # Language detection and translation logic
            translation_note = ""
            if language == 'auto' and transcription:
                # Simple Tamil detection (you can enhance this)
                tamil_keywords = ['நான்', 'நீங்கள்', 'உணவு', 'குடிக்க', 'சாப்பிட', 'வீடு', 'பள்ளி']
                detected_tamil = any(keyword in transcription for keyword in tamil_keywords)
                
                if detected_tamil:
                    translation_note = "Tamil detected - consider translation"
            
            print(f"✅ Transcription successful: {transcription[:50]}...")
            
            return jsonify({
                'success': True,
                'transcription': transcription,
                'language': language,
                'method': method,
                'translation_note': translation_note,
                'timestamp': datetime.now().isoformat()
            }), 200
            
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            return jsonify({
                'success': False,
                'message': f'Transcription failed: {str(e)}'
            }), 500
            
    except Exception as e:
        print(f"❌ Error in transcription: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/nutrition/analyze-with-gpt4', methods=['POST'])
def analyze_food_with_gpt4():
    """Analyze food using GPT-4"""
    try:
        print("🍎 GPT-4 analysis request received")
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        food_input = data.get('food_input', '')
        pregnancy_week = data.get('pregnancy_week', 1)
        user_id = data.get('userId', '')
        
        if not food_input:
            return jsonify({
                'success': False,
                'message': 'Food input is required'
            }), 400
        
        # Get OpenAI API key
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            return jsonify({
                'success': False,
                'message': 'OpenAI API key not configured'
            }), 500
        
        try:
            from openai import OpenAI
        except ImportError:
            return jsonify({
                'success': False,
                'message': 'OpenAI package not installed. Run: pip install openai'
            }), 500
        
        # Initialize OpenAI client
        client = OpenAI(api_key=openai_api_key)
        
        # Create GPT-4 prompt
        prompt = f"""
        Analyze this food item for a pregnant woman at week {pregnancy_week}:
        
        Food: {food_input}
        
        Provide a detailed analysis in JSON format with the following structure:
        {{
            "nutritional_breakdown": {{
                "estimated_calories": <number>,
                "protein_grams": <number>,
                "carbohydrates_grams": <number>,
                "fat_grams": <number>,
                "fiber_grams": <number>
            }},
            "pregnancy_benefits": {{
                "nutrients_for_fetal_development": ["list of specific nutrients"],
                "benefits_for_mother": ["list of benefits"],
                "week_specific_advice": "specific advice for week {pregnancy_week}"
            }},
            "safety_considerations": {{
                "food_safety_tips": ["list of safety tips"],
                "cooking_recommendations": ["cooking guidelines"]
            }},
            "smart_recommendations": {{
                "next_meal_suggestions": ["suggestions for next meal"],
                "hydration_tips": "water intake advice"
            }}
        }}
        
        Focus on pregnancy-specific nutrition needs.
        """
        
        # Call GPT-4
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a nutrition expert specializing in pregnancy nutrition. Provide accurate, detailed analysis in the exact JSON format requested."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=1500
        )
        
        # Extract response
        gpt_response = response.choices[0].message.content.strip()
        
        # Try to parse JSON response
        try:
            # Remove markdown formatting if present
            if gpt_response.startswith('```json'):
                gpt_response = gpt_response.replace('```json', '').replace('```', '').strip()
            
            analysis_data = json.loads(gpt_response)
            
            # Save to database if user_id provided
            if user_id:
                try:
                    # Find patient
                    patient = db.patients_collection.find_one({"patient_id": user_id})
                    if patient:
                        # Initialize food_data array if not exists
                        if 'food_data' not in patient:
                            patient['food_data'] = []
                        
                        # Add GPT-4 analysis to food_data
                        food_entry = {
                            'type': 'gpt4_analysis',
                            'food_input': food_input,
                            'analysis': analysis_data,
                            'pregnancy_week': pregnancy_week,
                            'timestamp': datetime.now().isoformat(),
                            'created_at': datetime.now()
                        }
                        
                        patient['food_data'].append(food_entry)
                        
                        # Update patient document
                        db.patients_collection.update_one(
                            {"patient_id": user_id},
                            {"$set": {"food_data": patient['food_data']}}
                        )
                        
                        print(f"✅ GPT-4 analysis saved to database for user: {user_id}")
                    else:
                        print(f"⚠️ Patient not found for user ID: {user_id}")
                except Exception as e:
                    print(f"⚠️ Could not save to database: {e}")
            
            print(f"✅ GPT-4 analysis successful for: {food_input[:50]}...")
            
            return jsonify({
                'success': True,
                'analysis': analysis_data,
                'food_input': food_input,
                'pregnancy_week': pregnancy_week,
                'timestamp': datetime.now().isoformat()
            }), 200
            
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parsing error: {e}")
            print(f"⚠️ Raw GPT response: {gpt_response[:200]}...")
            
            # Fallback analysis
            fallback_analysis = {
                "nutritional_breakdown": {
                    "estimated_calories": 0,
                    "protein_grams": 0,
                    "carbohydrates_grams": 0,
                    "fat_grams": 0,
                    "fiber_grams": 0
                },
                "pregnancy_benefits": {
                    "nutrients_for_fetal_development": ["General nutrients"],
                    "benefits_for_mother": ["General benefits"],
                    "week_specific_advice": f"Consult your doctor for week {pregnancy_week} specific advice"
                },
                "safety_considerations": {
                    "food_safety_tips": ["Ensure food is properly cooked", "Wash fruits and vegetables"],
                    "cooking_recommendations": ["Cook thoroughly", "Avoid raw foods"]
                },
                "smart_recommendations": {
                    "next_meal_suggestions": ["Balanced meal with protein and vegetables"],
                    "hydration_tips": "Drink plenty of water throughout the day"
                },
                "note": "Analysis generated with fallback due to parsing error"
            }
            
            return jsonify({
                'success': True,
                'analysis': fallback_analysis,
                'food_input': food_input,
                'pregnancy_week': pregnancy_week,
                'timestamp': datetime.now().isoformat(),
                'fallback_used': True
            }), 200
            
    except Exception as e:
        print(f"❌ Error in GPT-4 analysis: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/nutrition/save-food-entry', methods=['POST'])
def save_food_entry():
    """Save basic food entry to patient's food_data array"""
    try:
        print("🍽️ Food entry save request received")
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        user_id = data.get('userId')
        food_input = data.get('food_input', '')
        pregnancy_week = data.get('pregnancy_week', 1)
        
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'User ID is required'
            }), 400
        
        if not food_input:
            return jsonify({
                'success': False,
                'message': 'Food input is required'
            }), 400
        
        # Find patient
        patient = db.patients_collection.find_one({"patient_id": user_id})
        if not patient:
            return jsonify({
                'success': False,
                'message': f'Patient not found with ID: {user_id}'
            }), 404
        
        # Initialize food_data array if not exists
        if 'food_data' not in patient:
            patient['food_data'] = []
        
        # Create food entry
        food_entry = {
            'type': 'basic_entry',
            'food_input': food_input,
            'pregnancy_week': pregnancy_week,
            'timestamp': datetime.now().isoformat(),
            'created_at': datetime.now()
        }
        
        # Add to food_data array
        patient['food_data'].append(food_entry)
        
        # Update patient document
        result = db.patients_collection.update_one(
            {"patient_id": user_id},
            {"$set": {"food_data": patient['food_data']}}
        )
        
        if result.modified_count > 0:
            print(f"✅ Food entry saved successfully for user: {user_id}")
            return jsonify({
                'success': True,
                'message': 'Food entry saved successfully',
                'food_entry': food_entry,
                'total_entries': len(patient['food_data'])
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to save food entry'
            }), 500
            
    except Exception as e:
        print(f"❌ Error saving food entry: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/nutrition/get-food-entries/<user_id>', methods=['GET'])
def get_food_entries(user_id):
    """Get food entries from patient's food_data array"""
    try:
        print(f"🍽️ Getting food entries for user ID: {user_id}")
        
        # Find patient
        patient = db.patients_collection.find_one({"patient_id": user_id})
        if not patient:
            return jsonify({
                'success': False,
                'message': f'Patient not found with ID: {user_id}'
            }), 404
        
        # Get food_data array
        food_data = patient.get('food_data', [])
        
        # Sort by timestamp (most recent first)
        food_data.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        print(f"✅ Retrieved {len(food_data)} food entries for user: {user_id}")
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'food_data': food_data,
            'total_entries': len(food_data)
        }), 200
        
    except Exception as e:
        print(f"❌ Error getting food entries: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/nutrition/debug-food-data/<user_id>', methods=['GET'])
def debug_food_data(user_id):
    """Debug endpoint to check food data structure"""
    try:
        print(f"🔍 Debug food data for user ID: {user_id}")
        
        # Find patient
        patient = db.patients_collection.find_one({"patient_id": user_id})
        if not patient:
            return jsonify({
                'success': False,
                'message': f'Patient not found with ID: {user_id}'
            }), 404
        
        # Get food_data array
        food_data = patient.get('food_data', [])
        
        # Analyze data structure
        basic_entries = [entry for entry in food_data if entry.get('type') == 'basic_entry']
        gpt4_analyses = [entry for entry in food_data if entry.get('type') == 'gpt4_analysis']
        
        debug_info = {
            'user_id': user_id,
            'total_food_entries': len(food_data),
            'basic_entries_count': len(basic_entries),
            'gpt4_analyses_count': len(gpt4_analyses),
            'food_data_structure': {
                'has_food_data_field': 'food_data' in patient,
                'food_data_type': type(food_data).__name__,
                'food_data_length': len(food_data) if isinstance(food_data, list) else 'Not a list'
            },
            'sample_entries': food_data[:3] if food_data else []
        }
        
        print(f"✅ Debug info generated for user: {user_id}")
        
        return jsonify({
            'success': True,
            'debug_info': debug_info
        }), 200
        
    except Exception as e:
        print(f"❌ Error in debug food data: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

if __name__ == '__main__':
    print("🚀 Starting Patient Alert System Flask API...")
    print("📱 API will be available at: http://localhost:5000")
    print("🌐 Web app can be accessed at: http://localhost:8080")
    
    # Start medication reminder scheduler
    scheduler_thread = start_medication_reminder_scheduler()
    
    app.run(host='0.0.0.0', port=5000, debug=True) 