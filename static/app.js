/**
 * Triage AI - Frontend Application
 */

// API base URL (empty for same-origin)
const API_BASE = '';

// State
let sessionId = null;
let isComplete = false;

// DOM Elements
const chatScreen = document.getElementById('chat-screen');
const processingScreen = document.getElementById('processing-screen');
const resultScreen = document.getElementById('result-screen');
const chatMessages = document.getElementById('chat-messages');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const newTriageBtn = document.getElementById('new-triage-btn');
const resultContent = document.getElementById('result-content');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    startNewSession();
});

// Event Listeners
chatForm.addEventListener('submit', handleSubmit);
newTriageBtn.addEventListener('click', startNewSession);

/**
 * Start a new triage session
 */
async function startNewSession() {
    // Reset state
    sessionId = null;
    isComplete = false;
    chatMessages.innerHTML = '';

    // Show chat screen
    showScreen('chat');

    // Add welcome message
    addMessage('agent', 'Welcome to Triage AI. I\'ll ask you a few questions to understand your symptoms and help direct you to the right care.');

    try {
        const response = await fetch(`${API_BASE}/api/session`, {
            method: 'POST',
        });

        if (!response.ok) throw new Error('Failed to create session');

        const data = await response.json();
        sessionId = data.session_id;

        // Show first question
        setTimeout(() => {
            addMessage('agent', data.first_question);
            userInput.focus();
        }, 500);

    } catch (error) {
        console.error('Error creating session:', error);
        addMessage('system', 'Error connecting to server. Please refresh the page.');
    }
}

/**
 * Handle form submission
 */
async function handleSubmit(e) {
    e.preventDefault();

    const message = userInput.value.trim();
    if (!message || !sessionId) return;

    // Disable input while processing
    setInputEnabled(false);

    // Show user message
    addMessage('user', message);
    userInput.value = '';

    try {
        const response = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                message: message,
            }),
        });

        if (!response.ok) throw new Error('Failed to send message');

        const data = await response.json();

        if (data.is_complete) {
            isComplete = true;
            addMessage('system', 'Thank you! Processing your information...');
            setTimeout(() => processTriageResult(), 1000);
        } else {
            // Show next question
            setTimeout(() => {
                addMessage('agent', data.next_question);
                setInputEnabled(true);
                userInput.focus();
            }, 300);
        }

    } catch (error) {
        console.error('Error sending message:', error);
        addMessage('system', 'Error sending message. Please try again.');
        setInputEnabled(true);
    }
}

/**
 * Process triage through AI agents
 */
async function processTriageResult() {
    showScreen('processing');

    try {
        // Start processing
        const processResponse = await fetch(`${API_BASE}/api/process`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId }),
        });

        if (!processResponse.ok) throw new Error('Failed to process triage');

        const processData = await processResponse.json();

        // Get result
        const resultResponse = await fetch(`${API_BASE}/api/result/${processData.job_id}`);

        if (!resultResponse.ok) throw new Error('Failed to get result');

        const resultData = await resultResponse.json();

        if (resultData.status === 'completed' && resultData.result) {
            displayResult(resultData.result);
            showScreen('result');
        } else {
            throw new Error('Processing failed');
        }

    } catch (error) {
        console.error('Error processing triage:', error);
        showScreen('chat');
        addMessage('system', 'Error processing your information. Please try again or start a new session.');
    }
}

/**
 * Display triage result
 */
function displayResult(result) {
    const { classification, routing, anamnesis } = result;

    const colorEmoji = {
        'RED': '🔴',
        'YELLOW': '🟡',
        'GREEN': '🟢',
        'BLUE': '🔵',
    };

    let html = `
        <div class="triage-badge ${classification.color}">
            <h2>${colorEmoji[classification.color]} ${classification.color} - ${classification.priority}</h2>
            <p class="priority">${getWaitTime(classification.color)}</p>
        </div>

        <div class="result-section">
            <h3>Patient Information</h3>
            <p><strong>Name:</strong> ${anamnesis.patient_name}</p>
            <p><strong>Date of Birth:</strong> ${anamnesis.date_of_birth}</p>
            ${anamnesis.phone_number ? `<p><strong>Phone:</strong> ${anamnesis.phone_number}</p>` : ''}
            ${anamnesis.emergency_contact_name ? `
                <p><strong>Emergency Contact:</strong> ${anamnesis.emergency_contact_name}
                ${anamnesis.emergency_contact_phone ? `(${anamnesis.emergency_contact_phone})` : ''}</p>
            ` : ''}
        </div>

        <div class="result-section">
            <h3>Clinical Summary</h3>
            <p><strong>Chief Complaint:</strong> ${anamnesis.chief_complaint}</p>
            <p><strong>Severity:</strong> ${anamnesis.pain_scale || 'N/A'}/10</p>
            <p><strong>Onset:</strong> ${anamnesis.onset}</p>
            ${anamnesis.location ? `<p><strong>Location:</strong> ${anamnesis.location}</p>` : ''}
            ${anamnesis.associated_symptoms.length > 0 ? `
                <p><strong>Associated Symptoms:</strong> ${anamnesis.associated_symptoms.join(', ')}</p>
            ` : ''}
            ${anamnesis.allergies && anamnesis.allergies.length > 0 ? `
                <p><strong>Allergies:</strong> <span style="color: #dc2626;">${anamnesis.allergies.join(', ')}</span></p>
            ` : ''}
        </div>

        <div class="result-section">
            <h3>Routing</h3>
            <p><strong>Department:</strong> ${routing.department}</p>
            <p><strong>Urgency:</strong> ${routing.urgency}</p>
            ${routing.room_type ? `<p><strong>Room Type:</strong> ${routing.room_type}</p>` : ''}
        </div>

        <div class="result-section">
            <h3>Classification Reasoning</h3>
            <p>${classification.reasoning}</p>
            ${classification.risk_factors.length > 0 ? `
                <p><strong>Risk Factors:</strong></p>
                <ul>
                    ${classification.risk_factors.map(f => `<li>${f}</li>`).join('')}
                </ul>
            ` : ''}
        </div>
    `;

    if (routing.preliminary_orders.length > 0) {
        html += `
            <div class="result-section">
                <h3>Preliminary Orders</h3>
                <ul>
                    ${routing.preliminary_orders.map(o => `<li>${o}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    if (routing.contraindications.length > 0) {
        html += `
            <div class="result-section contraindications">
                <h3>Contraindications</h3>
                <ul>
                    ${routing.contraindications.map(c => `<li>${c}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    if (routing.notes_for_staff) {
        html += `
            <div class="result-section">
                <h3>Notes for Staff</h3>
                <p>${routing.notes_for_staff}</p>
            </div>
        `;
    }

    resultContent.innerHTML = html;
}

/**
 * Get wait time description by color
 */
function getWaitTime(color) {
    const times = {
        'RED': 'Immediate attention required',
        'YELLOW': 'Wait time: 30-60 minutes',
        'GREEN': 'Wait time: 1-4 hours',
        'BLUE': 'Wait time: 4+ hours',
    };
    return times[color] || '';
}

/**
 * Add a message to the chat
 */
function addMessage(type, text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.textContent = text;
    chatMessages.appendChild(messageDiv);

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Show a specific screen
 */
function showScreen(screen) {
    chatScreen.classList.add('hidden');
    processingScreen.classList.add('hidden');
    resultScreen.classList.add('hidden');

    switch (screen) {
        case 'chat':
            chatScreen.classList.remove('hidden');
            break;
        case 'processing':
            processingScreen.classList.remove('hidden');
            break;
        case 'result':
            resultScreen.classList.remove('hidden');
            break;
    }
}

/**
 * Enable/disable input
 */
function setInputEnabled(enabled) {
    userInput.disabled = !enabled;
    sendBtn.disabled = !enabled;
}
