// Main application logic

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
});

// Set up event listeners
function initializeEventListeners() {
    // File input handling
    document.getElementById('fileInput').addEventListener('change', function(event) {
        const files = event.target.files;
        if (files.length > 0) {
            handleFiles(files);
        }
    });
    
    // Drag and drop functionality
    const dropZone = document.getElementById('dropZone');
    
    dropZone.addEventListener('dragover', function(e) {
        e.preventDefault();
        dropZone.style.backgroundColor = '#e1f0fa';
        dropZone.style.borderColor = '#2980b9';
    });
    
    dropZone.addEventListener('dragleave', function() {
        dropZone.style.backgroundColor = '';
        dropZone.style.borderColor = '#3498db';
    });
    
    dropZone.addEventListener('drop', function(e) {
        e.preventDefault();
        dropZone.style.backgroundColor = '';
        dropZone.style.borderColor = '#3498db';
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFiles(files);
        }
    });
    
    // Question submission
    document.getElementById('askButton').addEventListener('click', generateAnswer);
    
    // Allow pressing Enter to submit question (while holding Shift for new line)
    document.getElementById('questionInput').addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            generateAnswer();
        }
    });
}

// Handle file uploads
function handleFiles(files) {
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        uploadDocument(file);
    }
}

// Upload document to server
function uploadDocument(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(`Error: ${data.error}`);
        } else {
            addDocumentToUI({
                name: data.filename,
                type: file.type,
                size: file.size,
                uploadedAt: new Date().toISOString()
            });
            alert(`File ${data.filename} uploaded successfully! Processed ${data.chunks} chunks.`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error uploading file');
    });
}

// Add document to the UI list
function addDocumentToUI(documentData) {
    const docItem = document.createElement('div');
    docItem.className = 'document-item';
    docItem.id = `doc-${encodeURIComponent(documentData.name)}`;
    docItem.innerHTML = `
        <div class="document-icon">
            <i class="fas fa-file-${getFileIcon(documentData.name)}"></i>
        </div>
        <div class="document-name">${documentData.name}</div>
        <div class="document-actions">
            <button class="action-btn" onclick="removeDocument('${encodeURIComponent(documentData.name)}')">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    document.getElementById('documentsList').appendChild(docItem);
}

// Remove a document
function removeDocument(documentName) {
    const decodedName = decodeURIComponent(documentName);
    if (confirm(`Are you sure you want to remove ${decodedName}?`)) {
        // Remove from UI
        const docElement = document.getElementById(`doc-${documentName}`);
        if (docElement) {
            docElement.remove();
        }
        
        // In a real app, you would also call the server to remove from vector store
        console.log(`Document ${decodedName} removed from UI`);
    }
}

// Get appropriate icon for file type
function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    if (ext === 'pdf') return 'pdf';
    if (['txt', 'md'].includes(ext)) return 'alt';
    if (['doc', 'docx'].includes(ext)) return 'word';
    if (['html', 'htm'].includes(ext)) return 'code';
    return 'file';
}