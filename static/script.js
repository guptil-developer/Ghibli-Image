let currentConvertedFilename = '';

document.getElementById('file-input').addEventListener('change', function() {
    document.getElementById('file-name').textContent = 
        this.files && this.files.length > 0 ? this.files[0].name : 'Choose an image...';
});

function convertImage() {
    const fileInput = document.getElementById('file-input');
    const loadingIndicator = document.getElementById('loading-indicator');
    const resultContainer = document.getElementById('result-container');
    const errorMessage = document.getElementById('error-message');
    
    // Reset UI
    errorMessage.style.display = 'none';
    resultContainer.style.display = 'none';
    
    if (!fileInput.files || fileInput.files.length === 0) {
        showError('Please select an image first');
        return;
    }

    // Show loading indicator
    loadingIndicator.style.display = 'block';

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    axios.post('/convert', formData, {
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    })
    .then(response => {
        // Display results
        document.getElementById('original-image').src = `/uploaded/${response.data.original}`;
        document.getElementById('converted-image').src = `/converted/${response.data.converted}`;
        currentConvertedFilename = response.data.converted;
        
        // Hide loading, show results
        loadingIndicator.style.display = 'none';
        resultContainer.style.display = 'block';
    })
    .catch(error => {
        loadingIndicator.style.display = 'none';
        showError(error.response?.data?.error || error.message || 'Conversion failed');
    });
}

function downloadImage() {
    if (!currentConvertedFilename) {
        showError('No converted image available');
        return;
    }
    window.location.href = `/download/${currentConvertedFilename}`;
}

function showError(message) {
    const errorElement = document.getElementById('error-message');
    errorElement.textContent = message;
    errorElement.style.display = 'block';
}