from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import PyPDF2
import docx
import markdown
from bs4 import BeautifulSoup
import requests
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
import openai
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'txt', 'docx', 'md', 'html', 'htm'}

# Initialize components
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
chroma_client = chromadb.Client()
collection = chroma_client.create_collection(name="documents")

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def extract_text_from_file(filepath, filename):
    """Extract text from various file formats"""
    if filename.endswith('.pdf'):
        return extract_text_from_pdf(filepath)
    elif filename.endswith('.docx'):
        return extract_text_from_docx(filepath)
    elif filename.endswith(('.md', '.markdown')):
        return extract_text_from_markdown(filepath)
    elif filename.endswith(('.html', '.htm')):
        return extract_text_from_html(filepath)
    elif filename.endswith('.txt'):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file format: {filename}")

def extract_text_from_pdf(filepath):
    """Extract text from PDF file"""
    with open(filepath, 'rb') as f:
        pdf_reader = PyPDF2.PdfReader(f)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text

def extract_text_from_docx(filepath):
    """Extract text from DOCX file"""
    doc = docx.Document(filepath)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def extract_text_from_markdown(filepath):
    """Extract text from Markdown file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        md_text = f.read()
    return markdown.markdown(md_text)  # Convert to HTML then extract text

def extract_text_from_html(filepath):
    """Extract text from HTML file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        html_content = f.read()
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup.get_text()

def chunk_text(text, chunk_size=500, overlap=50):
    """Split text into overlapping chunks"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_document():
    """Handle document upload and processing"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    # Save file
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    try:
        # Extract text from file
        text = extract_text_from_file(filepath, filename)
        
        # Chunk the text
        chunks = chunk_text(text)
        
        # Generate embeddings and store in vector database
        embeddings = embedding_model.encode(chunks).tolist()
        
        # Add to ChromaDB
        ids = [f"{filename}_{i}" for i in range(len(chunks))]
        collection.add(
            embeddings=embeddings,
            documents=chunks,
            metadatas=[{"source": filename} for _ in chunks],
            ids=ids
        )
        
        # Clean up uploaded file
        os.remove(filepath)
        
        return jsonify({
            'message': 'File processed successfully',
            'filename': filename,
            'chunks': len(chunks)
        })
        
    except Exception as e:
        # Clean up on error
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': str(e)}), 500

@app.route('/ask', methods=['POST'])
def ask_question():
    """Handle question answering"""
    data = request.get_json()
    question = data.get('question', '')
    
    if not question:
        return jsonify({'error': 'No question provided'}), 400
    
    try:
        # Retrieve relevant chunks
        query_embedding = embedding_model.encode([question]).tolist()
        
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=3
        )
        
        # Format results
        relevant_chunks = []
        for i in range(len(results['documents'][0])):
            relevant_chunks.append({
                'text': results['documents'][0][i],
                'source': results['metadatas'][0][i]['source'],
                'score': results['distances'][0][i]
            })
        
        # Generate answer using OpenAI API
        context = "\n\n".join([f"From {chunk['source']}:\n{chunk['text']}" for chunk in relevant_chunks])
        
        # For demonstration, we'll use a simple response
        # In production, you would use the OpenAI API
        answer = {
            'response': f"Based on the documents, here's what I found about '{question}': {context[:200]}...",
            'sources': list(set([chunk['source'] for chunk in relevant_chunks]))
        }
        
        return jsonify({
            'question': question,
            'answer': answer['response'],
            'sources': answer['sources']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)