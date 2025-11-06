// WebSocket connection for live data
let ws = null;
let sessionId = null;

// Responsive sidebar toggle
const menuToggle = document.getElementById('menuToggle');
const sidebar = document.getElementById('sidebar');
const mainContent = document.getElementById('mainContent');

menuToggle.addEventListener('click', function() {
    sidebar.classList.toggle('active');
    mainContent.classList.toggle('expanded');
});

// Recommendation History Management
let recommendations = [];
let currentFilter = 'all';
let lastRecommendationHash = '';
let lastProcessedAdvice = '';

// Create a hash for recommendation to detect duplicates
function createRecommendationHash(text) {
    return btoa(text).substring(0, 16); // Simple hash
}

// Improved recommendation extraction with duplicate prevention
function extractRecommendations(aiText) {
    if (!aiText || aiText.includes('analyzing') || aiText.includes('temporarily') || aiText.includes('unavailable')) {
        return [];
    }
    
    // Skip if this is the same as last processed advice
    const currentHash = createRecommendationHash(aiText);
    if (currentHash === lastRecommendationHash) {
        return [];
    }
    
    lastRecommendationHash = currentHash;
    
    const recommendations = [];
    
    // More inclusive patterns to catch different recommendation formats
    const patterns = [
        // Numbered recommendations
        /\d+\.\s*(.*?)(?=\.|\n|$)/gi,
        // Bullet points and asterisks
        /\*\s*(.*?)(?=\.|\n|$)/gi,
        // "Recommendation X:" format
        /recommendation\s*\d*:?\s*(.*?)(?=\.|\n|$)/gi,
        // Actionable recommendation
        /actionable recommendation:?\s*(.*?)(?=\.|\n|$)/gi,
        // Additional suggestion
        /additional suggestion:?\s*(.*?)(?=\.|\n|$)/gi,
        // Standard patterns
        /(?:recommend|suggest|advise|encourage)\s+(.*?)(?=\.|\n|$)/gi,
        /(?:should|could|might)\s+(.*?)(?=\.|\n|$)/gi,
        /(?:consider|try)\s+(.*?)(?=\.|\n|$)/gi,
        /(?:it.*?(?:important|beneficial).*?to)\s+(.*?)(?=\.|\n|$)/gi
    ];
    
    patterns.forEach(pattern => {
        const matches = aiText.matchAll(pattern);
        for (const match of matches) {
            let recommendation = match[1] ? match[1].trim() : match[0].trim();
            
            // Clean up the recommendation
            recommendation = recommendation
                .replace(/^(that|the patient|you|i recommend|i suggest|we should|we could)\s+/i, '')
                .replace(/\s+/g, ' ')
                .trim();
            
            // Remove any trailing punctuation
            recommendation = recommendation.replace(/[.,;:]$/, '');
            
            // Capitalize first letter
            if (recommendation) {
                recommendation = recommendation.charAt(0).toUpperCase() + recommendation.slice(1);
                
                if (recommendation.length > 10 && !isDuplicateRecommendation(recommendation)) {
                    recommendations.push(recommendation);
                }
            }
        }
    });
    
    // If we found structured recommendations, use them
    if (recommendations.length > 0) {
        return recommendations;
    }
    
    // Fallback: Extract meaningful sentences from the entire text
    const sentences = aiText.split(/[.!?]+/).filter(s => {
        const clean = s.trim();
        return clean.length > 20 && 
               clean.length < 200 &&
               !clean.toLowerCase().includes('based on') &&
               !clean.toLowerCase().includes('patient presents') &&
               !clean.toLowerCase().includes('vital signs') &&
               !clean.toLowerCase().includes('i assess') &&
               !clean.toLowerCase().includes('overall health') &&
               (clean.toLowerCase().includes('recommend') ||
                clean.toLowerCase().includes('suggest') ||
                clean.toLowerCase().includes('advise') ||
                clean.toLowerCase().includes('encourage') ||
                clean.toLowerCase().includes('consider') ||
                clean.toLowerCase().includes('should') ||
                clean.toLowerCase().includes('could'));
    });
    
    sentences.slice(0, 3).forEach(sentence => {
        const cleanSentence = sentence.trim();
        if (!isDuplicateRecommendation(cleanSentence)) {
            recommendations.push(cleanSentence);
        }
    });
    
    return recommendations;
}


// Check for duplicate recommendations
function isDuplicateRecommendation(text) {
    if (recommendations.length === 0) return false;
    
    const cleanText = text.toLowerCase().replace(/\s+/g, ' ').trim();
    
    // Check against existing recommendations with some tolerance
    return recommendations.some(rec => {
        const existingText = rec.text.toLowerCase().replace(/\s+/g, ' ').trim();
        
        // More lenient comparison - check if they share significant words
        const textWords = new Set(cleanText.split(/\s+/).filter(w => w.length > 3));
        const existingWords = new Set(existingText.split(/\s+/).filter(w => w.length > 3));
        
        const commonWords = [...textWords].filter(word => existingWords.has(word));
        const similarity = commonWords.length / Math.max(textWords.size, existingWords.size);
        
        // Consider duplicates if similarity is too high
        return similarity > 0.6;
    });
}

// Check if recommendation is meaningful (not too generic)
function isMeaningfulRecommendation(text) {
    const genericPatterns = [
        /maintain.*current/i,
        /continue.*monitor/i,
        /keep.*track/i,
        /stay.*hydrated/i,
        /get.*rest/i,
        /follow.*up/i,
        /seek.*medical/i
    ];
    
    // Allow more recommendations by being less restrictive
    const isTooGeneric = genericPatterns.some(pattern => pattern.test(text));
    
    // Check if it contains actionable words
    const hasActionableWords = /(recommend|suggest|advise|encourage|consider|try|should|could|might)/i.test(text);
    
    return !isTooGeneric || hasActionableWords;
}

// Improved categorization
function categorizeRecommendation(text) {
    const lowerText = text.toLowerCase();
    
    const categories = {
        'Relaxation': ['breath', 'breathe', 'relax', 'meditate', 'calm', 'mindful', 'deep breathing', 'visualization', 'progressive muscle'],
        'Exercise': ['exercise', 'activity', 'walk', 'movement', 'physical', 'yoga', 'stretch', 'fitness', 'brisk', 'walking'],
        'Stress Management': ['stress', 'anxiety', 'pressure', 'cope', 'manage stress', 'reduce stress', 'relaxation'],
        'Sleep & Rest': ['sleep', 'rest', 'fatigue', 'tired', 'energy', 'nap', 'bedtime', 'hours of sleep', 'sleep schedule'],
        'Nutrition': ['diet', 'food', 'water', 'hydrate', 'eat', 'nutrition', 'meal', 'drink', 'hydration', 'fluids'],
        'Monitoring': ['monitor', 'check', 'track', 'measure', 'observe', 'watch', 'keep track', 'check-in'],
        'Lifestyle': ['routine', 'habit', 'lifestyle', 'daily', 'regular', 'schedule', 'break', 'task', 'priority'],
        'Medical': ['doctor', 'medical', 'professional', 'clinic', 'hospital', 'physician', 'emergency']
    };
    
    for (const [category, keywords] of Object.entries(categories)) {
        if (keywords.some(keyword => lowerText.includes(keyword))) {
            return category;
        }
    }
    
    return 'General Health';
}


// Add recommendation to history with duplicate prevention
function addRecommendation(aiText) {
    // Skip if this is the same as last processed advice
    if (aiText === lastProcessedAdvice) {
        return;
    }
    
    lastProcessedAdvice = aiText;
    const extractedRecs = extractRecommendations(aiText);
    
    console.log('Extracted recommendations:', extractedRecs); // Debug log
    
    if (extractedRecs.length === 0) return;
    
    let addedCount = 0;
    const newRecommendations = [];
    
    extractedRecs.forEach((rec, index) => {
        // Check if this is a meaningful recommendation (more lenient now)
        if (isMeaningfulRecommendation(rec)) {
            const recommendation = {
                id: Date.now() + index + Math.random(),
                text: rec,
                category: categorizeRecommendation(rec),
                timestamp: new Date().toLocaleTimeString(),
                fullText: aiText,
                isNew: true
            };
            
            newRecommendations.push(recommendation);
            addedCount++;
        }
    });
    
    // Add new recommendations to the beginning
    if (newRecommendations.length > 0) {
        // Check for duplicates before adding
        const uniqueNewRecs = newRecommendations.filter(newRec => 
            !recommendations.some(existingRec => 
                isDuplicateRecommendation(newRec.text)
            )
        );
        
        if (uniqueNewRecs.length > 0) {
            recommendations.unshift(...uniqueNewRecs);
            
            // Limit total recommendations to 25 (increased from 20)
            if (recommendations.length > 25) {
                recommendations = recommendations.slice(0, 25);
            }
            
            // Only update display if we actually added something
            if (uniqueNewRecs.length > 0) {
                updateRecommendationsDisplay();
            }
        }
    }
}

// Update the recommendations display (without shaking)
function updateRecommendationsDisplay() {
    const container = document.getElementById('recommendationsList');
    const countElement = document.getElementById('recommendationCount');
    
    if (!container || !countElement) return;
    
    countElement.textContent = recommendations.length;
    
    if (recommendations.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">📋</div>
                <div>AI recommendations will appear here as they are generated</div>
            </div>
        `;
        return;
    }
    
    const filteredRecs = currentFilter === 'all' 
        ? recommendations 
        : recommendations.filter(rec => rec.category === currentFilter);
    
    const newContent = filteredRecs.map(rec => `
        <div class="recommendation-item ${rec.isNew ? 'recommendation-highlight' : ''}" id="rec-${rec.id}">
            <div class="recommendation-content">${rec.text}</div>
            <div class="recommendation-meta">
                <span class="recommendation-time">${rec.timestamp}</span>
                <span class="recommendation-category">${rec.category}</span>
            </div>
        </div>
    `).join('');
    
    // Only update DOM if content actually changed
    if (container.innerHTML !== newContent) {
        container.innerHTML = newContent;
        
        // Auto-scroll to top when new recommendations are added
        if (filteredRecs.some(rec => rec.isNew)) {
            container.scrollTop = 0;
        }
    }
    
    // Remove highlight after 3 seconds (shorter time)
    setTimeout(() => {
        let needsUpdate = false;
        recommendations.forEach(rec => {
            if (rec.isNew) {
                rec.isNew = false;
                needsUpdate = true;
            }
        });
        if (needsUpdate) {
            updateRecommendationsDisplay();
        }
    }, 3000);
}

// Filter recommendations
function filterRecommendations(category) {
    currentFilter = category;
    
    // Update filter buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    updateRecommendationsDisplay();
}

// Clear all recommendations
function clearRecommendations() {
    if (confirm('Are you sure you want to clear all recommendations?')) {
        recommendations = [];
        lastRecommendationHash = '';
        lastProcessedAdvice = '';
        updateRecommendationsDisplay();
    }
}

// Toggle recommendations panel
function toggleRecommendations() {
    const panel = document.getElementById('recommendationsPanel');
    const icon = document.getElementById('toggleIcon');
    
    if (!panel || !icon) return;
    
    if (panel.style.display === 'none') {
        panel.style.display = 'block';
        icon.textContent = '▼';
    } else {
        panel.style.display = 'none';
        icon.textContent = '▶';
    }
}

// Export recommendations
function exportRecommendations() {
    if (recommendations.length === 0) {
        alert('No recommendations to export.');
        return;
    }
    
    const exportData = recommendations.map(rec => 
        `[${rec.timestamp}] [${rec.category}] ${rec.text}`
    ).join('\n\n');
    
    const blob = new Blob([exportData], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `medical-recommendations-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Add filter buttons to the recommendations panel
function initializeRecommendationFilters() {
    const categories = ['all', 'Relaxation', 'Exercise', 'Stress Management', 'Sleep & Rest', 'Nutrition', 'Monitoring', 'Lifestyle', 'Medical', 'General Health'];
    
    const filterButtons = categories.map(cat => `
        <button class="filter-btn ${cat === 'all' ? 'active' : ''}" 
                onclick="filterRecommendations('${cat}')">
            ${cat === 'all' ? 'All' : cat}
        </button>
    `).join('');
    
    const recommendationsPanel = document.getElementById('recommendationsPanel');
    if (recommendationsPanel) {
        recommendationsPanel.innerHTML = `
            <div class="filter-buttons">
                ${filterButtons}
            </div>
            <div id="recommendationsList">
                <div class="empty-state">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">📋</div>
                    <div>AI recommendations will appear here as they are generated</div>
                </div>
            </div>
        `;
    }
}

// Close sidebar when clicking outside on mobile
document.addEventListener('click', function(event) {
    if (window.innerWidth <= 1024) {
        if (!sidebar.contains(event.target) && !menuToggle.contains(event.target)) {
            sidebar.classList.remove('active');
            mainContent.classList.remove('expanded');
        }
    }
});

// Adjust layout on window resize
window.addEventListener('resize', function() {
    if (window.innerWidth > 1024) {
        sidebar.classList.remove('active');
        mainContent.classList.remove('expanded');
    }
});

async function startMonitoring() {
    try {
        const response = await fetch('/api/sessions/start', { method: 'POST' });
        const data = await response.json();
        sessionId = data.session_id;
        
        document.getElementById('alertsContainer').innerHTML = 
            '<div class="alert alert-success">Starting AI-powered diagnosis analysis...</div>';
        
        // Update AI assessment to show loading
        document.getElementById('aiAdvice').innerHTML = `
            <div class="ai-loading">
                <span>AI is analyzing your vital signs</span>
                <div class="loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        
        // Reset recommendation state when starting new session
        recommendations = [];
        lastRecommendationHash = '';
        lastProcessedAdvice = '';
        updateRecommendationsDisplay();
                
        ws = new WebSocket(`ws://${window.location.host}/ws/${sessionId}`);
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
        
            // Update video feed FIRST (no blocking)
            document.getElementById('videoFeed').src = 'data:image/jpeg;base64,' + data.frame;
            
            // Update face detection status
            const faceStatus = document.getElementById('faceStatus');
            if (data.face_detected) {
                faceStatus.textContent = 'Face Detected';
                faceStatus.style.background = 'var(--success)';
            } else {
                faceStatus.textContent = 'No Face Detected';
                faceStatus.style.background = 'var(--danger)';
            }
            
            // Update diagnosis data
            if (data.diagnosis) {
                document.getElementById('heartRate').textContent = data.diagnosis.heart_rate;
                document.getElementById('stressLevel').textContent = data.diagnosis.stress_level;
                document.getElementById('fatigueRisk').textContent = data.diagnosis.fatigue_risk;
                document.getElementById('confidence').textContent = data.diagnosis.confidence;
                
                const healthStatus = document.getElementById('healthStatus');
                healthStatus.textContent = data.diagnosis.health_status;
                
                if (data.diagnosis.health_status === 'Warning') {
                    healthStatus.style.color = 'var(--warning)';
                } else if (data.diagnosis.health_status === 'Normal') {
                    healthStatus.style.color = 'var(--success)';
                } else {
                    healthStatus.style.color = 'var(--secondary)';
                }
                
                // Update AI Medical Assessment
                if (data.diagnosis.ai_advice && data.diagnosis.ai_advice !== 'Analyzing...') {
                    document.getElementById('aiAdvice').innerHTML = data.diagnosis.ai_advice;
                    
                    // Extract and store recommendations (with duplicate prevention)
                    addRecommendation(data.diagnosis.ai_advice);
                }
                
                // Update alerts
                const alertsContainer = document.getElementById('alertsContainer');
                alertsContainer.innerHTML = '';
                
                data.diagnosis.alerts.forEach(alert => {
                    const alertElem = document.createElement('div');
                    alertElem.className = 'alert';
                    
                    if (alert.includes('Warning') || alert.includes('High') || alert.includes('Elevated')) {
                        alertElem.classList.add('alert-danger');
                    } else if (alert.includes('Normal')) {
                        alertElem.classList.add('alert-success');
                    } else {
                        alertElem.classList.add('alert-warning');
                    }
                    
                    alertElem.innerHTML = `
                        <div>${alert.includes('Warning') ? '⚠️' : 'ℹ️'}</div>
                        <div>${alert}</div>
                    `;
                    alertsContainer.appendChild(alertElem);
                });
            }
        };
                
        ws.onclose = function() {
            document.getElementById('alertsContainer').innerHTML = 
                '<div class="alert alert-warning">Diagnosis session ended.</div>';
            document.getElementById('aiAdvice').innerHTML = 
                '<div class="ai-loading"><span>Monitoring session ended. Start a new session for AI assessment.</span></div>';
        };
        
        ws.onerror = function(error) {
            console.error('WebSocket error:', error);
            document.getElementById('alertsContainer').innerHTML = 
                '<div class="alert alert-danger">WebSocket connection error</div>';
        };
        
    } catch (error) {
        console.error('Error starting monitoring:', error);
        document.getElementById('alertsContainer').innerHTML = 
            '<div class="alert alert-danger">Error starting monitoring session</div>';
    }
}
        
function stopMonitoring() {
    if (ws) {
        ws.close();
    }
    if (sessionId) {
        fetch(`/api/sessions/${sessionId}/stop`, { method: 'POST' }).catch(console.error);
        sessionId = null;
    }
}

// Modal functions
function openNewPatientModal() {
    const modal = document.getElementById('newPatientModal');
    if (modal) {
        modal.style.display = 'flex';
    }
}

function closeNewPatientModal() {
    const modal = document.getElementById('newPatientModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Close modal when clicking outside
window.addEventListener('click', function(event) {
    const modal = document.getElementById('newPatientModal');
    if (event.target === modal) {
        closeNewPatientModal();
    }
});

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeRecommendationFilters();
    
    // Add any other initialization code here
    console.log('Medical Kiosk Dashboard initialized');
});