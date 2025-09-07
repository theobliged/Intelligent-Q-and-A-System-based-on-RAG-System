// RAG functions

// Generate answer based on question
function generateAnswer() {
    const questionInput = document.getElementById('questionInput');
    const processingIndicator = document.getElementById('processingIndicator');
    const answerPlaceholder = document.getElementById('answerPlaceholder');
    const answerContent = document.getElementById('answerContent');
    const answerText = document.getElementById('answerText');
    const referencesList = document.getElementById('referencesList');
    
    if (questionInput.value.trim() === '') {
        alert('Please enter a question first.');
        return;
    }
    
    // Show processing indicator
    processingIndicator.style.display = 'flex';
    answerPlaceholder.style.display = 'none';
    answerContent.style.display = 'none';
    
    // Send question to server
    fetch('/ask', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            question: questionInput.value
        })
    })
    .then(response => response.json())
    .then(data => {
        // Hide processing indicator and show answer
        processingIndicator.style.display = 'none';
        answerContent.style.display = 'block';
        
        if (data.error) {
            answerText.textContent = `Error: ${data.error}`;
        } else {
            // Display answer
            answerText.textContent = data.answer;
            
            // Display references
            referencesList.innerHTML = '';
            if (data.sources && data.sources.length > 0) {
                data.sources.forEach(source => {
                    addReference(source, 'relevant section');
                });
            } else {
                referencesList.innerHTML = '<div class="reference-item">No specific references found</div>';
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        processingIndicator.style.display = 'none';
        answerContent.style.display = 'block';
        answerText.textContent = 'Error connecting to server. Please try again.';
    });
}

// Add reference to the references list
function addReference(filename, location) {
    const refItem = document.createElement('div');
    refItem.className = 'reference-item';
    refItem.innerHTML = `<i class="fas fa-file-alt"></i> ${filename} (${location})`;
    document.getElementById('referencesList').appendChild(refItem);
}