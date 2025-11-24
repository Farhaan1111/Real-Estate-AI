class SearchApp {
    constructor() {
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        document.getElementById('searchForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.performSearch();
        });
    }

    async performSearch() {
        const query = document.getElementById('searchQuery').value.trim();
        const projectType = document.getElementById('projectType').value;
        const location = document.getElementById('location').value;
        const status = document.getElementById('projectStatus').value;

        // Build enhanced query
        let enhancedQuery = query;
        if (projectType) enhancedQuery += ` ${projectType} project`;
        if (location) enhancedQuery += ` in ${location}`;
        if (status) enhancedQuery += ` ${status}`;

        if (!enhancedQuery.trim()) {
            alert('Please enter a search query');
            return;
        }

        this.showLoading();

        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: enhancedQuery })
            });

            const data = await response.json();
            this.displayResults(data);

        } catch (error) {
            console.error('Search error:', error);
            this.displayError('Network error occurred. Please try again.');
        }
    }

    showLoading() {
        document.getElementById('searchResults').innerHTML = `
            <div class="text-center py-4">
                <div class="loading" style="width: 40px; height: 40px; margin: 0 auto;"></div>
                <p class="mt-2">Searching RERA database...</p>
            </div>
        `;
    }

    displayResults(data) {
        const resultsContainer = document.getElementById('searchResults');
        
        if (!data.success) {
            resultsContainer.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    ${data.response}
                </div>
            `;
            return;
        }

        let resultsHtml = `
            <div class="card">
                <div class="card-header bg-success text-white">
                    <h5 class="mb-0">
                        <i class="fas fa-check-circle me-2"></i>
                        Found ${data.retrieval_info.documents_found} results
                    </h5>
                </div>
                <div class="card-body">
                    <div class="row mb-4">
                        <div class="col-md-6">
                            <strong>Query Type:</strong> ${data.retrieval_info.query_type}<br>
                            <strong>Categories:</strong> ${data.retrieval_info.categories.join(', ')}<br>
                            <strong>RAG Used:</strong> ${data.retrieval_info.use_rag ? 'Yes' : 'No'}
                        </div>
                        <div class="col-md-6">
                            <strong>Reasoning:</strong> ${data.retrieval_info.reasoning}
                        </div>
                    </div>

                    <div class="ai-response mb-4 p-3 bg-light rounded">
                        <h6><i class="fas fa-robot me-2"></i>AI Summary:</h6>
                        <p class="mb-0">${data.ai_response}</p>
                    </div>
        `;

        if (data.documents && data.documents.length > 0) {
            resultsHtml += `<h6 class="mb-3">Retrieved Documents:</h6>`;
            
            data.documents.forEach((doc, index) => {
                resultsHtml += `
                    <div class="document-card mb-3 p-3 border rounded">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h6 class="mb-0">${doc.project_name}</h6>
                            <span class="badge bg-primary">Score: ${doc.score}</span>
                        </div>
                        <div class="mb-2">
                            <small class="text-muted">
                                <i class="fas fa-tag me-1"></i>${doc.chunk_type}
                                ${doc.registration_number ? `| <i class="fas fa-id-card me-1"></i>${doc.registration_number}` : ''}
                            </small>
                        </div>
                        <p class="mb-2">${doc.content_preview}</p>
                        <div class="retrieval-types">
                            ${doc.retrieval_types.map(type => 
                                `<span class="badge bg-secondary me-1">${type}</span>`
                            ).join('')}
                        </div>
                        <button class="btn btn-sm btn-outline-primary mt-2" 
                                onclick="this.parentNode.querySelector('.full-content').classList.toggle('d-none')">
                            <i class="fas fa-eye me-1"></i>Toggle Full Content
                        </button>
                        <div class="full-content d-none mt-2 p-2 bg-white border rounded">
                            <pre class="mb-0" style="white-space: pre-wrap; font-size: 0.9em;">${doc.full_content}</pre>
                        </div>
                    </div>
                `;
            });
        }

        resultsHtml += `</div></div>`;
        resultsContainer.innerHTML = resultsHtml;
    }

    displayError(message) {
        document.getElementById('searchResults').innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                ${message}
            </div>
        `;
    }
}

// Initialize search app
document.addEventListener('DOMContentLoaded', () => {
    new SearchApp();
});