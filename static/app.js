/**
 * Triage AI - Frontend Application with Multilingual Support
 */

// API base URL (empty for same-origin)
const API_BASE = '';

// State
let sessionId = null;
let isComplete = false;
let currentLanguage = 'en';
let isLanguageSelection = false;
let currentQuestion = 0;
const totalQuestions = 14;

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
const headerStatus = document.getElementById('header-status');
const chatProgress = document.getElementById('chat-progress');
const progressFill = document.getElementById('progress-fill');
const progressText = document.getElementById('progress-text');

// Translations for UI elements
const translations = {
    en: {
        welcome: 'Welcome to Triage AI. I\'ll ask you a few questions to understand your symptoms and help direct you to the right care.',
        selectLanguage: 'Please select your preferred language:',
        processing: 'Thank you! Processing your information...',
        errorConnect: 'Error connecting to server. Please refresh the page.',
        errorSend: 'Error sending message. Please try again.',
        errorProcess: 'Error processing your information. Please try again or start a new session.',
        typeAnswer: 'Type your answer...',
        send: 'Send',
        newTriage: 'Start New Triage',
        sessionActive: 'Session Active',
        questionOf: 'Question {current} of {total}',
        triageComplete: 'Triage Complete',
        step1: 'Analyzing patient data',
        step2: 'Classifying urgency level',
        step3: 'Determining department routing',
        processingTitle: 'Processing your information...',
        processingSubtitle: 'Our AI agents are analyzing your symptoms'
    },
    es: {
        welcome: 'Bienvenido a Triage AI. Le haré algunas preguntas para entender sus síntomas y ayudarle a recibir la atención adecuada.',
        selectLanguage: 'Por favor seleccione su idioma preferido:',
        processing: '¡Gracias! Procesando su información...',
        errorConnect: 'Error al conectar con el servidor. Por favor, actualice la página.',
        errorSend: 'Error al enviar el mensaje. Por favor, inténtelo de nuevo.',
        errorProcess: 'Error al procesar su información. Por favor, inténtelo de nuevo o inicie una nueva sesión.',
        typeAnswer: 'Escriba su respuesta...',
        send: 'Enviar',
        newTriage: 'Iniciar Nuevo Triage',
        sessionActive: 'Sesión Activa',
        questionOf: 'Pregunta {current} de {total}',
        triageComplete: 'Triage Completado',
        step1: 'Analizando datos del paciente',
        step2: 'Clasificando nivel de urgencia',
        step3: 'Determinando derivación departamental',
        processingTitle: 'Procesando su información...',
        processingSubtitle: 'Nuestros agentes de IA están analizando sus síntomas'
    },
    'pt-BR': {
        welcome: 'Bem-vindo ao Triage AI. Farei algumas perguntas para entender seus sintomas e ajudá-lo a receber o atendimento adequado.',
        selectLanguage: 'Por favor, selecione seu idioma preferido:',
        processing: 'Obrigado! Processando suas informações...',
        errorConnect: 'Erro ao conectar ao servidor. Por favor, atualize a página.',
        errorSend: 'Erro ao enviar a mensagem. Por favor, tente novamente.',
        errorProcess: 'Erro ao processar suas informações. Por favor, tente novamente ou inicie uma nova sessão.',
        typeAnswer: 'Digite sua resposta...',
        send: 'Enviar',
        newTriage: 'Iniciar Novo Triage',
        sessionActive: 'Sessão Ativa',
        questionOf: 'Pergunta {current} de {total}',
        triageComplete: 'Triagem Concluída',
        step1: 'Analisando dados do paciente',
        step2: 'Classificando nível de urgência',
        step3: 'Determinando encaminhamento departamental',
        processingTitle: 'Processando suas informações...',
        processingSubtitle: 'Nossos agentes de IA estão analisando seus sintomas'
    },
    it: {
        welcome: 'Benvenuto a Triage AI. Le farò alcune domande per comprendere i suoi sintomi e aiutarla a ricevere le cure appropriate.',
        selectLanguage: 'Per favore, selezioni la lingua preferita:',
        processing: 'Grazie! Elaborazione delle informazioni in corso...',
        errorConnect: 'Errore di connessione al server. Per favore, aggiorna la pagina.',
        errorSend: 'Errore nell\'invio del messaggio. Per favore, riprova.',
        errorProcess: 'Errore nell\'elaborazione delle informazioni. Per favore, riprova o avvia una nuova sessione.',
        typeAnswer: 'Scrivi la tua risposta...',
        send: 'Invia',
        newTriage: 'Inizia Nuovo Triage',
        sessionActive: 'Sessione Attiva',
        questionOf: 'Domanda {current} di {total}',
        triageComplete: 'Triage Completato',
        step1: 'Analisi dei dati del paziente',
        step2: 'Classificazione del livello di urgenza',
        step3: 'Determinazione dell\'indirizzamento dipartimentale',
        processingTitle: 'Elaborazione delle informazioni in corso...',
        processingSubtitle: 'I nostri agenti IA stanno analizzando i suoi sintomi'
    }
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    startNewSession();
});

// Event Listeners
chatForm.addEventListener('submit', handleSubmit);
newTriageBtn.addEventListener('click', startNewSession);

/**
 * Get translated text for current language
 */
function t(key) {
    return translations[currentLanguage]?.[key] || translations.en[key];
}

/**
 * Update progress bar
 */
function updateProgress(questionNumber) {
    currentQuestion = questionNumber;
    if (questionNumber <= 0) {
        chatProgress.classList.add('hidden');
        return;
    }
    chatProgress.classList.remove('hidden');
    const percent = Math.round((questionNumber / totalQuestions) * 100);
    progressFill.style.width = percent + '%';
    const text = t('questionOf')
        .replace('{current}', questionNumber)
        .replace('{total}', totalQuestions);
    progressText.textContent = text;
    headerStatus.textContent = text;
}

/**
 * Animate processing steps sequentially
 */
function animateProcessingSteps() {
    const steps = [
        document.getElementById('step-1'),
        document.getElementById('step-2'),
        document.getElementById('step-3')
    ];

    // Set translated text
    const stepKeys = ['step1', 'step2', 'step3'];
    steps.forEach((step, i) => {
        const textEl = step.querySelector('.step-text');
        textEl.textContent = t(stepKeys[i]);
        step.classList.remove('active', 'completed');
    });

    // Animate steps with delays
    const delays = [0, 3000, 7000];
    delays.forEach((delay, i) => {
        setTimeout(() => {
            // Mark previous steps as completed
            for (let j = 0; j < i; j++) {
                steps[j].classList.remove('active');
                steps[j].classList.add('completed');
            }
            steps[i].classList.add('active');
        }, delay);
    });
}

/**
 * Start a new triage session
 */
async function startNewSession() {
    // Reset state
    sessionId = null;
    isComplete = false;
    currentLanguage = 'en';
    isLanguageSelection = false;
    currentQuestion = 0;
    chatMessages.innerHTML = '';

    // Show chat screen
    showScreen('chat');
    updateProgress(0);
    headerStatus.textContent = '';

    // Add welcome message in English (default)
    addMessage('agent', translations.en.welcome);

    try {
        const response = await fetch(`${API_BASE}/api/session`, {
            method: 'POST',
        });

        if (!response.ok) throw new Error('Failed to create session');

        const data = await response.json();
        sessionId = data.session_id;
        isLanguageSelection = data.is_language_selection;

        // Show language selection
        if (data.is_language_selection && data.language_options) {
            setTimeout(() => {
                addMessage('agent', translations.en.selectLanguage);
                addLanguageButtons(data.language_options);
            }, 500);
        }

    } catch (error) {
        console.error('Error creating session:', error);
        addMessage('system', t('errorConnect'));
    }
}

/**
 * Add language selection buttons
 */
function addLanguageButtons(languageOptions) {
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'language-buttons';

    const flags = {
        'en': 'https://flagcdn.com/w40/us.png',
        'es': 'https://flagcdn.com/w40/es.png',
        'pt-BR': 'https://flagcdn.com/w40/br.png',
        'it': 'https://flagcdn.com/w40/it.png'
    };

    for (const [code, name] of Object.entries(languageOptions)) {
        const button = document.createElement('button');
        button.className = 'language-btn';
        button.innerHTML = `${name} <img class="flag" src="${flags[code] || ''}" alt="${code}">`;
        button.setAttribute('data-language', code);
        button.addEventListener('click', () => selectLanguage(code));
        buttonContainer.appendChild(button);
    }

    chatMessages.appendChild(buttonContainer);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Disable text input during language selection
    userInput.disabled = true;
    sendBtn.disabled = true;
}

/**
 * Handle language selection
 */
async function selectLanguage(languageCode) {
    currentLanguage = languageCode;

    // Remove language buttons
    const buttonContainer = document.querySelector('.language-buttons');
    if (buttonContainer) {
        buttonContainer.remove();
    }

    // Show selected language as user message
    const languageName = {
        'en': 'English',
        'es': 'Español',
        'pt-BR': 'Português (Brasil)',
        'it': 'Italiano'
    }[languageCode];
    addMessage('user', languageName);

    // Update UI text to selected language
    updateUILanguage();

    // Enable input
    setInputEnabled(false);

    try {
        const response = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                message: languageCode,
            }),
        });

        if (!response.ok) throw new Error('Failed to send language selection');

        const data = await response.json();
        isLanguageSelection = false;

        // Show first question and update progress
        setTimeout(() => {
            addMessage('agent', data.next_question);
            updateProgress(1);
            setInputEnabled(true);
            userInput.focus();
        }, 300);

    } catch (error) {
        console.error('Error selecting language:', error);
        addMessage('system', t('errorSend'));
        setInputEnabled(true);
    }
}

/**
 * Update UI elements to current language
 */
function updateUILanguage() {
    userInput.placeholder = t('typeAnswer');
    const sendText = sendBtn.querySelector('.send-text');
    if (sendText) sendText.textContent = t('send');
    newTriageBtn.textContent = t('newTriage');
    headerStatus.textContent = t('sessionActive');
}

/**
 * Handle form submission
 */
async function handleSubmit(e) {
    e.preventDefault();

    const message = userInput.value.trim();
    if (!message || !sessionId || isLanguageSelection) return;

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
            addMessage('system', t('processing'));
            setTimeout(() => processTriageResult(), 1000);
        } else {
            // Show next question and update progress
            setTimeout(() => {
                addMessage('agent', data.next_question);
                updateProgress(data.question_number || currentQuestion + 1);
                setInputEnabled(true);
                userInput.focus();
            }, 300);
        }

    } catch (error) {
        console.error('Error sending message:', error);
        addMessage('system', t('errorSend'));
        setInputEnabled(true);
    }
}

/**
 * Process triage through AI agents
 */
async function processTriageResult() {
    showScreen('processing');

    // Update processing screen text based on language
    document.getElementById('processing-title').textContent = t('processingTitle');
    document.getElementById('processing-subtitle').textContent = t('processingSubtitle');

    // Start step animation
    animateProcessingSteps();

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
        addMessage('system', t('errorProcess'));
    }
}

/**
 * Display triage result
 */
function displayResult(result) {
    const { classification, routing, anamnesis } = result;

    const labels = {
        en: {
            patientInfo: 'Patient Information',
            name: 'Name',
            dob: 'Date of Birth',
            phone: 'Phone',
            emergencyContact: 'Emergency Contact',
            clinicalSummary: 'Clinical Summary',
            chiefComplaint: 'Chief Complaint',
            severity: 'Severity',
            onset: 'Onset',
            location: 'Location',
            associatedSymptoms: 'Associated Symptoms',
            allergies: 'Allergies',
            routing: 'Routing',
            department: 'Department',
            urgency: 'Urgency',
            roomType: 'Room Type',
            classificationReasoning: 'Classification Reasoning',
            riskFactors: 'Risk Factors',
            preliminaryOrders: 'Preliminary Orders',
            contraindications: 'Contraindications',
            notesForStaff: 'Notes for Staff'
        },
        es: {
            patientInfo: 'Información del Paciente',
            name: 'Nombre',
            dob: 'Fecha de Nacimiento',
            phone: 'Teléfono',
            emergencyContact: 'Contacto de Emergencia',
            clinicalSummary: 'Resumen Clínico',
            chiefComplaint: 'Motivo Principal',
            severity: 'Severidad',
            onset: 'Inicio',
            location: 'Ubicación',
            associatedSymptoms: 'Síntomas Asociados',
            allergies: 'Alergias',
            routing: 'Derivación',
            department: 'Departamento',
            urgency: 'Urgencia',
            roomType: 'Tipo de Sala',
            classificationReasoning: 'Razonamiento de Clasificación',
            riskFactors: 'Factores de Riesgo',
            preliminaryOrders: 'Órdenes Preliminares',
            contraindications: 'Contraindicaciones',
            notesForStaff: 'Notas para el Personal'
        },
        'pt-BR': {
            patientInfo: 'Informações do Paciente',
            name: 'Nome',
            dob: 'Data de Nascimento',
            phone: 'Telefone',
            emergencyContact: 'Contato de Emergência',
            clinicalSummary: 'Resumo Clínico',
            chiefComplaint: 'Queixa Principal',
            severity: 'Severidade',
            onset: 'Início',
            location: 'Localização',
            associatedSymptoms: 'Sintomas Associados',
            allergies: 'Alergias',
            routing: 'Encaminhamento',
            department: 'Departamento',
            urgency: 'Urgência',
            roomType: 'Tipo de Sala',
            classificationReasoning: 'Raciocínio da Classificação',
            riskFactors: 'Fatores de Risco',
            preliminaryOrders: 'Ordens Preliminares',
            contraindications: 'Contraindicações',
            notesForStaff: 'Notas para a Equipe'
        },
        it: {
            patientInfo: 'Informazioni del Paziente',
            name: 'Nome',
            dob: 'Data di Nascita',
            phone: 'Telefono',
            emergencyContact: 'Contatto di Emergenza',
            clinicalSummary: 'Riepilogo Clinico',
            chiefComplaint: 'Motivo Principale',
            severity: 'Gravità',
            onset: 'Insorgenza',
            location: 'Localizzazione',
            associatedSymptoms: 'Sintomi Associati',
            allergies: 'Allergie',
            routing: 'Indirizzamento',
            department: 'Reparto',
            urgency: 'Urgenza',
            roomType: 'Tipo di Sala',
            classificationReasoning: 'Ragionamento della Classificazione',
            riskFactors: 'Fattori di Rischio',
            preliminaryOrders: 'Ordini Preliminari',
            contraindications: 'Controindicazioni',
            notesForStaff: 'Note per il Personale'
        }
    };

    const l = labels[currentLanguage] || labels.en;

    // Format timestamp
    let timestampStr = '';
    if (result.timestamp) {
        const date = new Date(result.timestamp);
        timestampStr = date.toLocaleString(currentLanguage === 'pt-BR' ? 'pt-BR' : currentLanguage, {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    let html = `
        <div class="result-header">
            <h2>${t('triageComplete')}</h2>
            ${timestampStr ? `<p class="result-timestamp">${timestampStr}</p>` : ''}
        </div>

        <div class="triage-badge ${classification.color}">
            <h2>${classification.color} — ${classification.priority}</h2>
            <p class="priority">${getWaitTime(classification.color)}</p>
        </div>

        <div class="result-section">
            <h3>${l.patientInfo}</h3>
            <p><strong>${l.name}:</strong> ${anamnesis.patient_name}</p>
            <p><strong>${l.dob}:</strong> ${anamnesis.date_of_birth}</p>
            ${anamnesis.phone_number ? `<p><strong>${l.phone}:</strong> ${anamnesis.phone_number}</p>` : ''}
            ${anamnesis.emergency_contact_name ? `
                <p><strong>${l.emergencyContact}:</strong> ${anamnesis.emergency_contact_name}
                ${anamnesis.emergency_contact_phone ? `(${anamnesis.emergency_contact_phone})` : ''}</p>
            ` : ''}
        </div>

        <div class="result-section">
            <h3>${l.clinicalSummary}</h3>
            <p><strong>${l.chiefComplaint}:</strong> ${anamnesis.chief_complaint}</p>
            <p><strong>${l.severity}:</strong> ${anamnesis.pain_scale || 'N/A'}/10</p>
            <p><strong>${l.onset}:</strong> ${anamnesis.onset}</p>
            ${anamnesis.location ? `<p><strong>${l.location}:</strong> ${anamnesis.location}</p>` : ''}
            ${anamnesis.associated_symptoms.length > 0 ? `
                <p><strong>${l.associatedSymptoms}:</strong> ${anamnesis.associated_symptoms.join(', ')}</p>
            ` : ''}
            ${anamnesis.allergies && anamnesis.allergies.length > 0 ? `
                <p><strong>${l.allergies}:</strong> <span style="color: var(--color-red); font-weight: 600;">${anamnesis.allergies.join(', ')}</span></p>
            ` : ''}
        </div>

        <div class="result-section section-routing">
            <h3>${l.routing}</h3>
            <p><strong>${l.department}:</strong> ${routing.department}</p>
            <p><strong>${l.urgency}:</strong> ${routing.urgency}</p>
            ${routing.room_type ? `<p><strong>${l.roomType}:</strong> ${routing.room_type}</p>` : ''}
        </div>

        <div class="result-section section-classification">
            <h3>${l.classificationReasoning}</h3>
            <p>${classification.reasoning}</p>
            ${classification.risk_factors.length > 0 ? `
                <p><strong>${l.riskFactors}:</strong></p>
                <ul>
                    ${classification.risk_factors.map(f => `<li>${f}</li>`).join('')}
                </ul>
            ` : ''}
        </div>
    `;

    if (routing.preliminary_orders.length > 0) {
        html += `
            <div class="result-section section-orders">
                <h3>${l.preliminaryOrders}</h3>
                <ul>
                    ${routing.preliminary_orders.map(o => `<li>${o}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    if (routing.contraindications.length > 0) {
        html += `
            <div class="result-section contraindications">
                <h3>${l.contraindications}</h3>
                <ul>
                    ${routing.contraindications.map(c => `<li>${c}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    if (routing.notes_for_staff) {
        html += `
            <div class="result-section">
                <h3>${l.notesForStaff}</h3>
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
        en: {
            'RED': 'Immediate attention required',
            'YELLOW': 'Wait time: 30-60 minutes',
            'GREEN': 'Wait time: 1-4 hours',
            'BLUE': 'Wait time: 4+ hours',
        },
        es: {
            'RED': 'Se requiere atención inmediata',
            'YELLOW': 'Tiempo de espera: 30-60 minutos',
            'GREEN': 'Tiempo de espera: 1-4 horas',
            'BLUE': 'Tiempo de espera: más de 4 horas',
        },
        'pt-BR': {
            'RED': 'Atenção imediata necessária',
            'YELLOW': 'Tempo de espera: 30-60 minutos',
            'GREEN': 'Tempo de espera: 1-4 horas',
            'BLUE': 'Tempo de espera: mais de 4 horas',
        },
        it: {
            'RED': 'Attenzione immediata necessaria',
            'YELLOW': 'Tempo di attesa: 30-60 minuti',
            'GREEN': 'Tempo di attesa: 1-4 ore',
            'BLUE': 'Tempo di attesa: oltre 4 ore',
        }
    };
    return times[currentLanguage]?.[color] || times.en[color] || '';
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
