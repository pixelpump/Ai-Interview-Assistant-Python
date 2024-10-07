let listenButton = document.getElementById('listenButton');
let clearButton = document.getElementById('clearButton');
let questionsArea = document.getElementById('questionsArea');
let answersArea = document.getElementById('answersArea');
let apiKeyInput = document.getElementById('apiKeyInput');
let saveApiKeyButton = document.getElementById('saveApiKey');
let deleteApiKeyButton = document.getElementById('deleteApiKey');
let modal = document.getElementById('modal');
let modalMessage = document.getElementById('modal-message');
let closeModal = document.getElementsByClassName('close')[0];
let modalLogo = document.getElementById('modal-logo');

// Add these lines at the beginning of your script
let logoContainer = document.querySelector('.logo-container');
let closeLogo = document.querySelector('.close-logo');

// Add this event listener for the close logo button
closeLogo.addEventListener('click', () => {
    logoContainer.classList.add('logo-hidden');
});

// Check for existing API key on load
window.addEventListener('load', async () => {
    const hasApiKey = await eel.has_api_key()();
    updateApiKeyUI(hasApiKey);
});

listenButton.addEventListener('click', async () => {
    let isListening = await eel.toggle_listening()();
    listenButton.textContent = isListening ? 'Stop Listening' : 'Start Listening';
    listenButton.classList.toggle('listening', isListening);
    
    if (isListening) {
        let spinner = document.createElement('div');
        spinner.className = 'spinner';
        listenButton.appendChild(spinner);
    }
});

clearButton.addEventListener('click', () => {
    questionsArea.innerHTML = '';
    answersArea.innerHTML = '';
});

saveApiKeyButton.addEventListener('click', async () => {
    const apiKey = apiKeyInput.value.trim();
    if (apiKey) {
        const result = await eel.save_api_key(apiKey)();
        if (result) {
            showModal('Open AI API key saved successfully!', 'OpenAI_Logo.png');
            apiKeyInput.value = '';
            updateApiKeyUI(true);
        } else {
            showModal('Failed to save API key. Please try again.');
        }
    } else {
        showModal('Please enter a valid API key.');
    }
});

deleteApiKeyButton.addEventListener('click', async () => {
    const result = await eel.delete_api_key()();
    if (result) {
        showModal('API key removed successfully!');
        updateApiKeyUI(false);
    } else {
        showModal('Failed to delete API key. Please try again.');
    }
});

function updateApiKeyUI(hasApiKey) {
    apiKeyInput.style.display = hasApiKey ? 'none' : 'inline-block';
    saveApiKeyButton.style.display = hasApiKey ? 'none' : 'inline-block';
    deleteApiKeyButton.style.display = hasApiKey ? 'inline-block' : 'none';
    listenButton.disabled = !hasApiKey;
}

function showModal(message, logoSrc = null) {
    modalMessage.textContent = message;
    modalMessage.className = 'text-center'; // Ensure text is always centered
    if (logoSrc) {
        modalLogo.src = logoSrc;
        modalLogo.style.display = 'block';
    } else {
        modalLogo.style.display = 'none';
    }
    modal.style.display = 'block';
}

closeModal.onclick = function() {
    modal.style.display = 'none';
}

window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = 'none';
    }
}

eel.expose(update_ui);
function update_ui(question, answer) {
    if (question) {
        let p = document.createElement('p');
        p.textContent = question;
        questionsArea.appendChild(p);
        questionsArea.scrollTop = questionsArea.scrollHeight;
    }
    if (answer) {
        let answerContainer = document.createElement('div');
        answerContainer.className = 'answer-container';
        
        let p = document.createElement('p');
        try {
            const parsedAnswer = JSON.parse(answer);
            p.textContent = parsedAnswer.text;
            
            if (parsedAnswer.audio) {
                let audio = new Audio(`data:audio/mp3;base64,${parsedAnswer.audio}`);
                audio.onplay = function() {
                    eel.audio_playback_started()();
                };
                audio.onended = function() {
                    eel.audio_playback_ended()();
                };
                
                let muteIcon = document.createElement('span');
                muteIcon.className = 'mute-icon';
                muteIcon.innerHTML = '🔊';
                muteIcon.title = 'Mute/Unmute';
                muteIcon.onclick = function() {
                    audio.muted = !audio.muted;
                    muteIcon.innerHTML = audio.muted ? '🔇' : '🔊';
                };
                
                answerContainer.appendChild(muteIcon);
                
                audio.play().catch(e => console.error("Error playing audio:", e));
            }
        } catch (e) {
            console.error("Error parsing answer:", e);
            p.textContent = answer;
        }
        
        answerContainer.appendChild(p);
        answersArea.appendChild(answerContainer);
        answersArea.scrollTop = answersArea.scrollHeight;
    }
}

let ttsToggle = document.getElementById('ttsToggle');
let ttsEnabled = true;  // Set this to true by default

// Update the UI to reflect the default state
ttsToggle.classList.toggle('disabled', !ttsEnabled);

ttsToggle.addEventListener('click', async () => {
    ttsEnabled = await eel.toggle_tts()();
    ttsToggle.classList.toggle('disabled', !ttsEnabled);
});