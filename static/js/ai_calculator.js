/**
 * AI Roof Calculator JavaScript
 * Handles form submission, results display, and feedback
 */

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('ai-calculator-form');
    const resultsDiv = document.getElementById('ai-results');
    const feedbackModal = new bootstrap.Modal(document.getElementById('feedbackModal'));
    
    let currentCalculationId = null;
    
    // Form submission handler
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        
        // Show loading state
        submitBtn.innerHTML = '<span class="loading"></span> Calculating...';
        submitBtn.disabled = true;
        
        try {
            const formData = new FormData(form);
            const response = await fetch('/ai-calculate', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                displayResults(data);
                currentCalculationId = data.calculation_id;
            } else {
                showError(data.error || 'Calculation failed');
            }
            
        } catch (error) {
            console.error('Calculation error:', error);
            showError('Network error. Please check your connection and try again.');
        } finally {
            // Reset button
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
            feather.replace();
        }
    });
    
    // Display calculation results
    function displayResults(data) {
        const area = data.area;
        const materials = data.materials;
        const costs = data.formatted_costs;
        const recommendations = data.recommendations;
        const confidence = Math.round(data.confidence * 100);
        const method = data.method;
        
        let materialsHtml = '';
        for (const [key, value] of Object.entries(materials)) {
            materialsHtml += `<li class="list-group-item d-flex justify-content-between">
                <span>${formatMaterialKey(key)}</span>
                <strong>${value}</strong>
            </li>`;
        }
        
        let costsHtml = '';
        for (const [key, value] of Object.entries(costs)) {
            costsHtml += `<li class="list-group-item d-flex justify-content-between">
                <span>${formatCostKey(key)}</span>
                <strong>${value}</strong>
            </li>`;
        }
        
        let recommendationsHtml = '';
        recommendations.forEach(rec => {
            recommendationsHtml += `<li class="list-group-item">
                <i data-feather="check-circle" class="text-success me-2"></i>${rec}
            </li>`;
        });
        
        resultsDiv.innerHTML = `
            <div class="text-start">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h6><i data-feather="home"></i> Roof Area</h6>
                    <span class="badge bg-info">${area.toFixed(1)} sq ft</span>
                </div>
                
                <div class="mb-3">
                    <h6><i data-feather="package"></i> Materials Needed</h6>
                    <ul class="list-group list-group-flush">
                        ${materialsHtml}
                    </ul>
                </div>
                
                <div class="mb-3">
                    <h6><i data-feather="dollar-sign"></i> Cost Estimate</h6>
                    <ul class="list-group list-group-flush">
                        ${costsHtml}
                    </ul>
                </div>
                
                <div class="mb-3">
                    <h6><i data-feather="lightbulb"></i> AI Recommendations</h6>
                    <ul class="list-group list-group-flush">
                        ${recommendationsHtml}
                    </ul>
                </div>
                
                <div class="text-center">
                    <div class="row">
                        <div class="col-6">
                            <small class="text-muted">Confidence</small><br>
                            <span class="badge ${confidence >= 80 ? 'bg-success' : confidence >= 60 ? 'bg-warning' : 'bg-danger'}">${confidence}%</span>
                        </div>
                        <div class="col-6">
                            <small class="text-muted">Method</small><br>
                            <span class="badge bg-primary">${method.toUpperCase()}</span>
                        </div>
                    </div>
                    
                    <button class="btn btn-outline-primary btn-sm mt-3" onclick="openFeedbackModal()">
                        <i data-feather="message-circle"></i> Give Feedback
                    </button>
                </div>
            </div>
        `;
        
        feather.replace();
        
        // Show success toast
        showToast('Calculation completed successfully!', 'success');
    }
    
    // Show error message
    function showError(message) {
        resultsDiv.innerHTML = `
            <div class="alert alert-danger text-start">
                <i data-feather="alert-circle"></i>
                <strong>Error:</strong> ${message}
            </div>
        `;
        feather.replace();
        showToast(message, 'error');
    }
    
    // Format material keys for display
    function formatMaterialKey(key) {
        const keyMap = {
            'bundles': 'Shingle Bundles',
            'sheets': 'Metal Sheets',
            'tiles': 'Roof Tiles',
            'area_covered': 'Coverage Area (sq ft)',
            'squares': 'Roofing Squares'
        };
        return keyMap[key] || key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
    
    // Format cost keys for display
    function formatCostKey(key) {
        const keyMap = {
            'material_cost': 'Material Cost',
            'labor_cost': 'Labor Cost',
            'total_cost': 'Total Cost',
            'cost_per_sqft': 'Cost per Sq Ft'
        };
        return keyMap[key] || key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
    
    // Open feedback modal
    window.openFeedbackModal = function() {
        if (currentCalculationId) {
            document.getElementById('feedback-calc-id').value = currentCalculationId;
            feedbackModal.show();
        }
    };
    
    // Submit feedback
    document.getElementById('submit-feedback').addEventListener('click', async function() {
        const feedbackForm = document.getElementById('feedback-form');
        const formData = new FormData(feedbackForm);
        
        // Validate rating
        const rating = formData.get('rating');
        if (!rating) {
            showToast('Please select a rating', 'error');
            return;
        }
        
        try {
            const response = await fetch('/ai-feedback', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                showToast(data.message, 'success');
                feedbackModal.hide();
                feedbackForm.reset();
            } else {
                showToast(data.error, 'error');
            }
            
        } catch (error) {
            console.error('Feedback error:', error);
            showToast('Failed to submit feedback', 'error');
        }
    });
    
    // Auto-calculate area display
    const lengthInput = document.getElementById('length');
    const widthInput = document.getElementById('width');
    
    function updateAreaDisplay() {
        const length = parseFloat(lengthInput.value) || 0;
        const width = parseFloat(widthInput.value) || 0;
        const area = length * width;
        
        if (area > 0) {
            // Update form helper text or display
            const areaText = `Area: ${area.toFixed(1)} sq ft`;
            // You could add a helper element to show this
        }
    }
    
    lengthInput.addEventListener('input', updateAreaDisplay);
    widthInput.addEventListener('input', updateAreaDisplay);
    
    // Material type change handler
    document.getElementById('material_type').addEventListener('change', function() {
        const material = this.value;
        // Could add material-specific advice or modify form fields
        // For example, show different complexity options for different materials
    });
    
    // Calculation method info
    document.getElementById('method').addEventListener('change', function() {
        const method = this.value;
        let helpText = '';
        
        switch(method) {
            case 'ai':
                helpText = 'Uses OpenAI for intelligent analysis based on knowledge base';
                break;
            case 'ml':
                helpText = 'Uses machine learning models for fast offline predictions';
                break;
            case 'hybrid':
                helpText = 'Combines AI and ML for best accuracy and reliability';
                break;
        }
        
        // Could show this help text somewhere in the UI
    });
    
    // Knowledge search functionality (if needed)
    window.searchKnowledge = async function(query) {
        try {
            const response = await fetch(`/ai-knowledge?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (data.success) {
                // Display knowledge results
                console.log('Knowledge results:', data.knowledge);
            }
        } catch (error) {
            console.error('Knowledge search error:', error);
        }
    };
});

// Utility function for showing toasts (reuse from main.js if available)
function showToast(message, type = 'info') {
    // Use the existing toast function from main.js if available
    if (typeof window.showToast === 'function') {
        window.showToast(message, type);
        return;
    }
    
    // Fallback toast implementation
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} position-fixed top-0 end-0 m-3`;
    toast.style.zIndex = '9999';
    toast.innerHTML = `
        <div class="d-flex align-items-center">
            <i data-feather="${type === 'success' ? 'check-circle' : type === 'error' ? 'alert-circle' : 'info'}"></i>
            <span class="ms-2">${message}</span>
        </div>
    `;
    
    document.body.appendChild(toast);
    feather.replace();
    
    setTimeout(() => {
        toast.remove();
    }, 4000);
}