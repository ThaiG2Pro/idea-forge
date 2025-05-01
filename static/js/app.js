document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const ideaForm = document.getElementById('idea-form');
    const keywordInput = document.getElementById('keyword');
    const iterationsSelect = document.getElementById('iterations');
    const inputSection = document.getElementById('input-section');
    const loadingSection = document.getElementById('loading-section');
    const resultsSection = document.getElementById('results-section');
    const loadingStep = document.querySelector('.loading-step');
    const downloadPdfBtn = document.getElementById('download-pdf');
    const startNewBtn = document.getElementById('start-new');
    const keywordPills = document.querySelectorAll('.keyword-pill');
    
    // Global variables to store the conversation and summary data
    let conversationData = null;
    let summaryData = null;
    
    // Add click events to sample keyword pills
    keywordPills.forEach(pill => {
        pill.addEventListener('click', function() {
            keywordInput.value = this.textContent;
        });
    });
    
    // Handle form submission
    ideaForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const keyword = keywordInput.value.trim();
        const iterations = iterationsSelect.value;
        
        if (!keyword) {
            alert('Please enter a keyword or concept');
            return;
        }
        
        // Show loading section
        inputSection.classList.add('hidden');
        loadingSection.classList.remove('hidden');
        
        // Start the brainstorming process
        startBrainstorming(keyword, iterations);
    });
    
    // Start brainstorming process
    function startBrainstorming(keyword, iterations) {
        loadingStep.textContent = 'Generating initial ideas...';
        
        fetch('/api/start_process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                keyword: keyword,
                iterations: iterations
            })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.error || 'Server error occurred');
                });
            }
            return response.json();
        })
        .then(data => {
            // Store the data globally
            conversationData = data.conversation;
            summaryData = data.summary;
            
            // Display the results
            displayResults(data);
            
            // Hide loading, show results
            loadingSection.classList.add('hidden');
            resultsSection.classList.remove('hidden');
        })
        .catch(error => {
            alert('Error: ' + error.message);
            // Return to input section on error
            loadingSection.classList.add('hidden');
            inputSection.classList.remove('hidden');
        });
    }
    
    // Display results in the UI
    function displayResults(data) {
        const { conversation, summary } = data;
        
        // Display final idea
        const finalIdeaElement = document.getElementById('final-idea');
        const finalIdea = summary.final_idea;
        
        finalIdeaElement.innerHTML = `
            <div class="idea-card">
                <div class="idea-title">${finalIdea.title}</div>
                <div class="idea-description">${finalIdea.description}</div>
                <div class="evaluation-scores">
                    <span class="score-item">Total Score: ${finalIdea.total_score}</span>
                </div>
            </div>
        `;
        
        // Display development path
        const developmentPathElement = document.getElementById('development-path');
        developmentPathElement.innerHTML = '';
        
        // Add original keyword as first step
        const originalItem = document.createElement('li');
        originalItem.textContent = summary.original_keyword;
        developmentPathElement.appendChild(originalItem);
        
        // Add optimization points
        summary.optimization_points.forEach(point => {
            const listItem = document.createElement('li');
            listItem.textContent = point;
            developmentPathElement.appendChild(listItem);
        });
        
        // Display detailed conversation
        const conversationElement = document.getElementById('conversation');
        conversationElement.innerHTML = '';
        
        // Group conversation by iterations
        const iterations = {};
        
        conversation.forEach(entry => {
            if (entry.role === 'system') return;
            
            const step = entry.step || '';
            const iterationMatch = step.match(/Iteration (\d+)/);
            
            if (iterationMatch) {
                const iterationNum = iterationMatch[1];
                if (!iterations[iterationNum]) {
                    iterations[iterationNum] = [];
                }
                iterations[iterationNum].push(entry);
            }
        });
        
        // Create HTML for each iteration
        Object.keys(iterations).forEach(iterNum => {
            const iterEntries = iterations[iterNum];
            const iterationDiv = document.createElement('div');
            iterationDiv.className = 'iteration';
            
            // Add iteration title
            const titleDiv = document.createElement('div');
            titleDiv.className = 'iteration-title';
            titleDiv.textContent = `Iteration ${iterNum}`;
            iterationDiv.appendChild(titleDiv);
            
            // Process entries in this iteration
            iterEntries.forEach(entry => {
                if (entry.role === 'assistant1') {
                    // Brainstorming section
                    const ideasDiv = document.createElement('div');
                    ideasDiv.className = 'ideas';
                    
                    const ideasTitleDiv = document.createElement('div');
                    ideasTitleDiv.className = 'section-subtitle';
                    ideasTitleDiv.textContent = 'Ideas Generated:';
                    ideasDiv.appendChild(ideasTitleDiv);
                    
                    // Add each idea
                    entry.content.ideas.forEach(idea => {
                        const ideaCard = document.createElement('div');
                        ideaCard.className = 'idea-card';
                        
                        ideaCard.innerHTML = `
                            <div class="idea-title">${idea.title}</div>
                            <div class="idea-description">${idea.description}</div>
                            <div class="idea-features">
                                <strong>Key Features:</strong>
                                <ul>
                                    ${idea.key_features.map(feature => `<li>${feature}</li>`).join('')}
                                </ul>
                            </div>
                        `;
                        
                        ideasDiv.appendChild(ideaCard);
                    });
                    
                    iterationDiv.appendChild(ideasDiv);
                    
                } else if (entry.role === 'assistant2') {
                    // Evaluation section
                    const evalDiv = document.createElement('div');
                    evalDiv.className = 'evaluation';
                    
                    const evalTitleDiv = document.createElement('div');
                    evalTitleDiv.className = 'section-subtitle';
                    evalTitleDiv.textContent = 'Evaluation:';
                    evalDiv.appendChild(evalTitleDiv);
                    
                    // Add evaluations
                    entry.content.evaluations.forEach(eval => {
                        const evalCard = document.createElement('div');
                        evalCard.className = 'evaluation-card';
                        
                        evalCard.innerHTML = `
                            <div class="idea-title">${eval.title}</div>
                            <div class="evaluation-scores">
                                <span class="score-item">Problem: ${eval.solving_real_problem}/10</span>
                                <span class="score-item">Market: ${eval.market_potential}/10</span>
                                <span class="score-item">Feasibility: ${eval.feasibility}/10</span>
                                <span class="score-item">Total: ${eval.total_score}/30</span>
                            </div>
                            <div class="evaluation-comment">${eval.comments}</div>
                        `;
                        
                        evalDiv.appendChild(evalCard);
                    });
                    
                    // Add selected idea
                    const selectedDiv = document.createElement('div');
                    selectedDiv.className = 'selected-idea';
                    selectedDiv.innerHTML = `
                        Selected Idea: ${entry.content.selected_idea.title}
                        <span class="score-item">Score: ${entry.content.selected_idea.total_score}</span>
                    `;
                    evalDiv.appendChild(selectedDiv);
                    
                    iterationDiv.appendChild(evalDiv);
                }
            });
            
            conversationElement.appendChild(iterationDiv);
        });
    }
    
    // Download PDF
    downloadPdfBtn.addEventListener('click', function() {
        if (!conversationData || !summaryData) {
            alert('No data available to download');
            return;
        }
        
        // Show loading
        resultsSection.classList.add('hidden');
        loadingSection.classList.remove('hidden');
        loadingStep.textContent = 'Generating PDF...';
        
        fetch('/api/generate_pdf', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                conversation: conversationData,
                summary: summaryData
            })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.error || 'PDF generation failed');
                });
            }
            return response.blob();
        })
        .then(blob => {
            // Create download link
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `idea_forge_${new Date().toISOString().slice(0, 10)}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            
            // Show results section again
            loadingSection.classList.add('hidden');
            resultsSection.classList.remove('hidden');
        })
        .catch(error => {
            alert('Error: ' + error.message);
            loadingSection.classList.add('hidden');
            resultsSection.classList.remove('hidden');
        });
    });
    
    // Start new brainstorming session
    startNewBtn.addEventListener('click', function() {
        // Reset form values
        ideaForm.reset();
        
        // Clear data
        conversationData = null;
        summaryData = null;
        
        // Show input section
        resultsSection.classList.add('hidden');
        inputSection.classList.remove('hidden');
    });
}); 