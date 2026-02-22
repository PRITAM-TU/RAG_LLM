import os
import sys
import shutil
from flask import Flask, request, render_template, jsonify, send_file
from werkzeug.utils import secure_filename
import PyPDF2
from datetime import datetime

# Add the parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your custom modules
try:
    from src.data_loader import load_all_documents
    from src.vectorstore import FaissVectorStore
    from src.search import RAGSearch
except ImportError as e:
    print(f"Error importing modules: {e}")
    # Create placeholder classes for testing
    class RAGSearch:
        def __init__(self):
            pass
        
        def search_and_summarize(self, query, top_k=5):
            return f"This is a simulated response for: '{query}'"
    
    class FaissVectorStore:
        def __init__(self, path):
            self.path = path
        def load(self):
            pass
        def add_documents(self, docs):
            pass

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'data/sample_data'
ALLOWED_EXTENSIONS = {'pdf'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global variables for the search system
search_system = None
vector_store = None

def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
    return text

def initialize_search_system():
    """Initialize the RAG search system"""
    global search_system, vector_store
    
    try:
        # First, initialize the search system without vector_store parameter
        # Since your RAGSearch doesn't accept vector_store in __init__
        search_system = RAGSearch()
        
        # Load documents
        print("Loading documents...")
        docs = load_all_documents(UPLOAD_FOLDER)
        
        # Initialize vector store
        print("Initializing vector store...")
        vector_store = FaissVectorStore("faiss_store")
        
        # Load existing index or create new one
        try:
            vector_store.load()
            print("Loaded existing FAISS index")
        except:
            print("Building new FAISS index...")
            if docs:
                vector_store.build_from_documents(docs)
        
        # If your RAGSearch has a method to set the vector store, use it here
        # For example, if it has an attribute:
        if hasattr(search_system, 'vector_store'):
            search_system.vector_store = vector_store
        elif hasattr(search_system, 'store'):
            search_system.store = vector_store
        
        print("Search system initialized successfully")
        return True
        
    except Exception as e:
        print(f"Error initializing search system: {e}")
        import traceback
        traceback.print_exc()
        return False

def process_and_index_document(filepath, filename):
    """Process a single document and add to vector store"""
    global vector_store, search_system
    
    try:
        # Extract text from PDF
        text = extract_text_from_pdf(filepath)
        
        if not text:
            return False, "No text could be extracted from PDF"
        
        # Create document object - adjust this based on your Document class structure
        # This is a generic approach - you may need to modify based on your actual Document class
        try:
            from src.data_loader import Document
            doc = Document(
                content=text,
                metadata={
                    'filename': filename,
                    'path': filepath,
                    'uploaded_at': datetime.now().isoformat(),
                    'source': 'upload'
                }
            )
        except ImportError:
            # If Document class doesn't exist, create a simple dict
            doc = {
                'content': text,
                'metadata': {
                    'filename': filename,
                    'path': filepath,
                    'uploaded_at': datetime.now().isoformat(),
                    'source': 'upload'
                }
            }
        
        # Add to vector store if it has the add_documents method
        if vector_store and hasattr(vector_store, 'add_documents'):
            vector_store.add_documents([doc])
            return True, "Document processed and added to vector store successfully"
        else:
            # If vector_store doesn't have add_documents, we need to rebuild the index
            # Reload all documents and rebuild
            docs = load_all_documents(UPLOAD_FOLDER)
            vector_store.build_from_documents(docs)
            return True, "Document processed and index rebuilt successfully"
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, str(e)

@app.route('/', methods=['GET'])
def home():
    """Render the home page"""
    return render_template('index.html')

@app.route('/upload-page', methods=['GET'])
def upload_page():
    """Render the upload page"""
    return render_template('upload.html')

@app.route('/search', methods=['POST'])
def search():
    """Handle search requests"""
    global search_system
    
    query = request.form.get('query', '').strip()
    
    if not query:
        return render_template('results.html', 
                             query=query, 
                             summary="Please enter a valid query.")
    
    top_k_str = request.form.get('top_k', '5')
    try:
        top_k = int(top_k_str)
        top_k = max(1, min(20, top_k))
    except ValueError:
        top_k = 5
    
    try:
        # Initialize search system if not already done
        if search_system is None:
            success = initialize_search_system()
            if not success:
                return render_template('results.html', 
                                     query=query, 
                                     summary="Search system is not initialized properly. Please check the logs.")
        
        print(f"Searching for: '{query}' with top_k={top_k}")
        
        # Call search_and_summarize method
        if hasattr(search_system, 'search_and_summarize'):
            summary = search_system.search_and_summarize(query, top_k=top_k)
        else:
            # Fallback if method doesn't exist
            summary = f"Search functionality not fully implemented. Your query was: '{query}'"
        
        return render_template('results.html', 
                             query=query, 
                             summary=summary)
    
    except Exception as e:
        print(f"Error during search: {e}")
        import traceback
        traceback.print_exc()
        return render_template('results.html', 
                             query=query, 
                             summary=f"An error occurred: {str(e)}")

@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle file uploads and processing"""
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        
        if not files or files[0].filename == '':
            return jsonify({'error': 'No files selected'}), 400
        
        uploaded_files = []
        failed_files = []
        
        for file in files:
            if file and allowed_file(file.filename):
                # Secure the filename
                filename = secure_filename(file.filename)
                
                # Add timestamp to avoid duplicates
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                name, ext = os.path.splitext(filename)
                unique_filename = f"{name}_{timestamp}{ext}"
                
                # Save the file
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(filepath)
                
                # Process and index the document
                success, message = process_and_index_document(filepath, unique_filename)
                
                if success:
                    uploaded_files.append({
                        'original': file.filename,
                        'saved_as': unique_filename,
                        'status': 'success',
                        'message': message
                    })
                else:
                    failed_files.append({
                        'original': file.filename,
                        'error': message
                    })
                    # Remove file if processing failed
                    if os.path.exists(filepath):
                        os.remove(filepath)
            else:
                failed_files.append({
                    'original': file.filename,
                    'error': 'Invalid file type. Only PDF files are allowed.'
                })
        
        # Reinitialize search system if files were uploaded successfully
        if uploaded_files:
            # Option 1: Reinitialize completely
            initialize_search_system()
            
            # Option 2: If your vector store supports incremental updates, you might not need full reinit
        
        return jsonify({
            'success': True,
            'uploaded': uploaded_files,
            'failed': failed_files,
            'message': f"Successfully uploaded {len(uploaded_files)} files. Failed: {len(failed_files)}"
        })
        
    except Exception as e:
        print(f"Upload error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents', methods=['GET'])
def list_documents():
    """List all uploaded documents"""
    try:
        documents = []
        for filename in os.listdir(UPLOAD_FOLDER):
            if filename.endswith('.pdf'):
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                stat = os.stat(filepath)
                documents.append({
                    'name': filename,
                    'size': f"{stat.st_size / 1024 / 1024:.2f} MB",
                    'size_bytes': stat.st_size,
                    'date': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M'),
                    'path': filepath
                })
        
        # Sort by date (newest first)
        documents.sort(key=lambda x: x['date'], reverse=True)
        
        return jsonify({'documents': documents})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents/<filename>', methods=['DELETE'])
def delete_document(filename):
    """Delete a document"""
    try:
        # Secure the filename to prevent directory traversal
        safe_filename = secure_filename(filename)
        filepath = os.path.join(UPLOAD_FOLDER, safe_filename)
        
        if os.path.exists(filepath):
            os.remove(filepath)
            
            # Rebuild search system without the deleted document
            initialize_search_system()
            
            return jsonify({'success': True, 'message': 'Document deleted successfully'})
        else:
            return jsonify({'error': 'Document not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents/<filename>', methods=['GET'])
def view_document(filename):
    """View/download a document"""
    try:
        # Secure the filename
        safe_filename = secure_filename(filename)
        filepath = os.path.join(UPLOAD_FOLDER, safe_filename)
        
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=False, download_name=safe_filename)
        else:
            return jsonify({'error': 'Document not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reindex', methods=['POST'])
def reindex_documents():
    """Force reindexing of all documents"""
    try:
        success = initialize_search_system()
        if success:
            return jsonify({'success': True, 'message': 'Reindexing completed successfully'})
        else:
            return jsonify({'error': 'Reindexing failed'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search-system/status', methods=['GET'])
def search_system_status():
    """Get search system status"""
    global search_system, vector_store
    
    try:
        # Count documents
        pdf_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.pdf')]
        
        status = {
            'status': 'initialized' if search_system is not None else 'not_initialized',
            'document_count': len(pdf_files),
            'vector_store_loaded': vector_store is not None,
            'upload_folder': UPLOAD_FOLDER,
            'search_system_type': str(type(search_system)) if search_system else None
        }
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    pdf_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.pdf')]
    
    return jsonify({
        'status': 'healthy',
        'search_system': search_system is not None,
        'document_count': len(pdf_files),
        'upload_folder': UPLOAD_FOLDER,
        'debug_mode': app.debug
    })

if __name__ == "__main__":
    # Initialize the search system before starting the server
    print("Initializing RAG Search Application...")
    initialize_search_system()
    
    print(f"Upload folder: {UPLOAD_FOLDER}")
    print(f"Document count: {len([f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.pdf')])}")
    print("Starting Flask server...")
    app.run(debug=True, host='127.0.0.1', port=5000)