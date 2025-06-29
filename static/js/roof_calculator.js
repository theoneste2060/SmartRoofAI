// Roof Calculator JavaScript

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing calculator...');
    const calculatorForm = document.getElementById('roofCalculatorForm');
    const resultsDiv = document.getElementById('calculatorResults');
    const resultsContent = document.getElementById('resultsContent');
    const productsContent = document.getElementById('productsContent');
    
    console.log('Calculator form found:', calculatorForm);
    console.log('Results div found:', resultsDiv);
    
    if (calculatorForm) {
        calculatorForm.addEventListener('submit', function(e) {
            console.log('Form submitted!');
            e.preventDefault();
            calculateRoof();
        });
    } else {
        console.error('Calculator form not found!');
    }
});

async function calculateRoof() {
    console.log('calculateRoof function called');
    
    const length = parseFloat(document.getElementById('roofLength').value);
    const width = parseFloat(document.getElementById('roofWidth').value);
    const roofType = document.getElementById('roofType').value;
    const materialType = document.getElementById('materialType').value;
    
    console.log('Form values:', { length, width, roofType, materialType });
    
    // Validate inputs
    if (!length || !width || !roofType || !materialType) {
        alert('Please fill in all fields');
        return;
    }
    
    console.log('Sending request to /calculate_roof...');
    
    try {
        const response = await fetch('/calculate_roof', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                length: length,
                width: width,
                roof_type: roofType,
                material_type: materialType
            })
        });
        
        console.log('Response received:', response);
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            throw new Error('Calculation failed');
        }
        
        const data = await response.json();
        console.log('Response data:', data);
        displayResults(data);
        
    } catch (error) {
        console.error('Error:', error);
        alert('Error calculating roof materials. Please try again.');
    }
}

function displayResults(data) {
    console.log('displayResults called with data:', data);
    
    const { calculation, recommended_products } = data;
    
    console.log('Calculation:', calculation);
    console.log('Recommended products:', recommended_products);
    
    // Display calculation results
    document.getElementById('resultsContent').innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <h6>Roof Specifications</h6>
                <ul class="list-unstyled">
                    <li><strong>Base Area:</strong> ${calculation.area.toFixed(1)} m²</li>
                    <li><strong>Adjusted Area:</strong> ${calculation.adjusted_area.toFixed(1)} m²</li>
                    <li><strong>Final Area (with waste):</strong> ${calculation.final_area.toFixed(1)} m²</li>
                </ul>
            </div>
            <div class="col-md-6">
                <h6>Material Requirements</h6>
                <ul class="list-unstyled">
                    <li><strong>Material Type:</strong> ${calculation.material_type}</li>
                    <li><strong>Units Needed:</strong> ${calculation.units_needed}</li>
                    <li><strong>Coverage per Unit:</strong> ${calculation.coverage_per_unit} m²</li>
                </ul>
            </div>
        </div>
    `;
    
    // Display recommended products
    if (recommended_products && recommended_products.length > 0) {
        const productsHTML = recommended_products.map(product => `
            <div class="col-md-4 mb-2">
                <div class="card">
                    <div class="card-body p-3">
                        <h6 class="card-title">${product.name}</h6>
                        <p class="text-primary mb-1">RWF ${(product.price * 1000).toLocaleString()}</p>
                        <small class="text-muted">${product.category}</small>
                        <div class="mt-2">
                            <a href="/product/${product.id}" class="btn btn-sm btn-outline-primary">View Product</a>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
        
        document.getElementById('productsContent').innerHTML = `
            <div class="row">
                ${productsHTML}
            </div>
        `;
    } else {
        document.getElementById('productsContent').innerHTML = `
            <p class="text-muted">No specific product recommendations available for this material type.</p>
        `;
    }
    
    // Show results
    const resultsDiv = document.getElementById('calculatorResults');
    console.log('Results div:', resultsDiv);
    resultsDiv.style.display = 'block';
    
    // Scroll to results
    resultsDiv.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
    });
    
    console.log('Results displayed successfully');
    
    // Show success message
    if (window.SmartRoof && window.SmartRoof.showToast) {
        window.SmartRoof.showToast('Roof calculation completed successfully!', 'success');
    }
}

// Additional calculator functions
function getRoofComplexityFactor(roofType) {
    const factors = {
        'flat': 1.0,
        'gable': 1.1,
        'hip': 1.2,
        'mansard': 1.3,
        'gambrel': 1.25
    };
    return factors[roofType] || 1.1;
}

function getMaterialCoverage(materialType) {
    const coverage = {
        'Metal Sheets': 2.32,  // m² per sheet
        'Shingles': 3.07,      // m² per bundle
        'Tiles': 0.093,        // m² per tile
        'Membrane': 9.29,      // m² per roll
        'Polycarbonate': 1.86  // m² per sheet
    };
    return coverage[materialType] || 2.32;
}

function calculateCost(unitsNeeded, pricePerUnit) {
    const subtotal = unitsNeeded * pricePerUnit;
    const tax = subtotal * 0.08;
    const total = subtotal + tax;
    
    return {
        subtotal: subtotal,
        tax: tax,
        total: total
    };
}

// Export functions
window.RoofCalculator = {
    calculateRoof,
    displayResults,
    getRoofComplexityFactor,
    getMaterialCoverage,
    calculateCost
};
