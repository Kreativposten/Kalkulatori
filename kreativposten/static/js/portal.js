// static/js/portal.js

// Hilfsfunktionen für Modals und Lightbox
function openModal(modalId) {
    document.getElementById(modalId).style.display = 'flex';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

function openLightbox(element) {
    const datei = JSON.parse(element.dataset.datei);
    const overlay = document.getElementById('lightbox-overlay');
    const filenameEl = document.getElementById('lightbox-filename');
    const imgEl = document.getElementById('lightbox-img');
    const pdfEl = document.getElementById('lightbox-pdf');
    const fallbackEl = document.getElementById('lightbox-fallback');
    const actionsEl = document.getElementById('lightbox-actions');

    // Reset all elements first
    imgEl.style.display = 'none';
    pdfEl.style.display = 'none';
    fallbackEl.style.display = 'none';
    imgEl.src = '';
    pdfEl.src = '';
    actionsEl.innerHTML = '';
    
    filenameEl.textContent = datei.original_filename;
    const viewUrl = `/view/auftragsdatei/${datei.saved_filename}`;
    const downloadUrl = `/download/auftragsdatei/${datei.saved_filename}`;
    const fileExtension = datei.original_filename.split('.').pop().toLowerCase();

    if (['png', 'jpg', 'jpeg', 'gif', 'webp'].includes(fileExtension)) {
        imgEl.src = viewUrl;
        imgEl.style.display = 'block';
    } else if (fileExtension === 'pdf') {
        pdfEl.src = viewUrl;
        pdfEl.style.display = 'block';
    } else {
        fallbackEl.style.display = 'block';
    }
    
    let actionsHtml = `<a href="${downloadUrl}" class="btn">Herunterladen</a>`;
    if (datei.freigabe_status === 'Freigabe ausstehend') {
        actionsHtml += `
            <button class="btn btn-warning" onclick="openModal('aenderung-modal-${datei.id}'); closeLightbox();">Änderungswunsch</button>
            <button class="btn btn-success" onclick="freigabeErteilen(${datei.id})">Druck freigeben</button>
        `;
    }
    actionsEl.innerHTML = actionsHtml;
    actionsEl.style.display = 'flex';

    overlay.style.display = 'flex';
}

function closeLightbox() {
    const overlay = document.getElementById('lightbox-overlay');
    if (overlay) {
        overlay.style.display = 'none';
        document.getElementById('lightbox-img').src = '';
        document.getElementById('lightbox-pdf').src = '';
    }
}

// Asynchrone Aktionen (API-Aufrufe)
async function angebotAnnehmen() {
    if (!confirm('Möchten Sie dieses Angebot verbindlich annehmen und einen Auftrag auslösen?')) return;
    try {
        const response = await fetch(`/portal/${PORTAL_TOKEN}/angebot-annehmen`, { method: 'POST' });
        if (response.ok) {
            alert('Vielen Dank! Ihr Auftrag wurde erstellt.');
            window.location.reload();
        } else {
            alert('Ein Fehler ist aufgetreten. Bitte versuchen Sie es erneut.');
        }
    } catch (error) {
        console.error('Fehler beim Annehmen des Angebots:', error);
        alert('Ein Netzwerkfehler ist aufgetreten.');
    }
}

async function freigabeErteilen(dateiId) {
    if (!confirm('Möchten Sie diesen Korrekturabzug verbindlich für den Druck freigeben? Diese Aktion kann nicht rückgängig gemacht werden.')) return;
    try {
        const response = await fetch(`/api/datei/${dateiId}/freigeben`, { method: 'POST' });
        if (response.ok) {
            window.location.reload();
        } else {
            alert('Ein Fehler ist aufgetreten. Bitte versuchen Sie es erneut.');
        }
    } catch (error) {
        console.error('Fehler beim Erteilen der Freigabe:', error);
        alert('Ein Netzwerkfehler ist aufgetreten.');
    }
}

// Hauptlogik, die nach dem Laden des DOMs ausgeführt wird
document.addEventListener('DOMContentLoaded', function() {
    // Event-Listener für Änderungswunsch-Formulare
    document.querySelectorAll('.aenderung-form').forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const dateiId = form.dataset.dateiId;
            const kommentarInput = form.querySelector('.aenderung-kommentar');
            const kommentar = kommentarInput.value;
            const formData = new FormData();
            formData.append('kommentar', kommentar);
            
            try {
                const response = await fetch(`/api/datei/${dateiId}/aenderung`, { method: 'POST', body: formData });
                if (response.ok) {
                    window.location.reload();
                } else {
                    alert('Fehler beim Senden des Änderungswunsches.');
                }
            } catch (error) {
                console.error('Fehler beim Senden des Änderungswunsches:', error);
                alert('Ein Netzwerkfehler ist aufgetreten.');
            }
        });
    });

    const eventsContainer = document.getElementById('activity-events-container');
    if (eventsContainer) {
        const messageForm = document.getElementById('message-form');
        const messageInput = document.getElementById('message-input');
        
        const scrollToBottom = () => {
            eventsContainer.scrollTop = eventsContainer.scrollHeight;
        };
        
        const addEreignisToChronik = (ereignis) => {
            const placeholder = eventsContainer.querySelector('p.placeholder-text');
            if (placeholder) placeholder.remove();

            const eventDiv = document.createElement('div');
            // Wichtig: 'sender' auf kleingeschrieben prüfen, da es in der JSON-Antwort so sein könnte
            eventDiv.className = `event ereignis-${ereignis.typ} sender-${(ereignis.sender || '').toLowerCase()}`;
            
            let iconHtml = '<span class="material-symbols-outlined">info</span>';
            if (ereignis.typ === 'nachricht' && (ereignis.sender || '').toLowerCase() === 'admin') iconHtml = '<span class="material-symbols-outlined">person</span>';
            else if (ereignis.typ === 'nachricht' && (ereignis.sender || '').toLowerCase() === 'kunde') iconHtml = '<span class="material-symbols-outlined">face</span>';
            else if (ereignis.typ === 'freigabe') iconHtml = `<span class="material-symbols-outlined" style="color: var(--success-color);">check_circle</span>`;
            else if (ereignis.typ === 'aenderung') iconHtml = `<span class="material-symbols-outlined" style="color: var(--warning-color);">sync_problem</span>`;
            else if (ereignis.typ === 'upload') iconHtml = '<span class="material-symbols-outlined">upload_file</span>';
            
            const eventDate = new Date(ereignis.zeit_iso);
            const formattedDate = eventDate.toLocaleString('de-DE', { day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit' });

            let senderInfoHtml = '';
            if (ereignis.typ === 'nachricht') {
               senderInfoHtml = `
                <div class="sender-info">
                    <span class="sender">${ereignis.sender}</span>
                    <span class="timestamp">${formattedDate}</span>
                </div>`;
            }

            // nl2br Implementierung in JS
            const inhaltHtml = ereignis.inhalt.replace(/(?:\r\n|\r|\n)/g, '<br>');

            eventDiv.innerHTML = `
                <div class="event-icon">${iconHtml}</div>
                <div class="event-content">
                    ${senderInfoHtml}
                    <div class="text">${inhaltHtml}</div>
                </div>
            `;
            eventsContainer.appendChild(eventDiv);
        };
        
        scrollToBottom();

        messageForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const inhalt = messageInput.value.trim();
            if (!inhalt) return;
            try {
                await fetch(`/api/auftrag/${PORTAL_TOKEN}/nachricht`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ inhalt: inhalt })
                });
                messageInput.value = '';
            } catch (error) {
                console.error('Fehler beim Senden der Nachricht:', error);
                alert('Nachricht konnte nicht gesendet werden.');
            }
        });

        // Polling für neue Ereignisse
        setInterval(async () => {
            let lastTimestamp = eventsContainer.dataset.lastTimestamp;
            try {
                const response = await fetch(`/api/auftrag/${AUFTRAG_ID}/ereignisse?since=${lastTimestamp}`);
                if (!response.ok) return;

                const neueEreignisse = await response.json();
                
                if (neueEreignisse.length > 0) {
                    neueEreignisse.forEach(addEreignisToChronik);
                    // Update den Timestamp für die nächste Abfrage
                    eventsContainer.dataset.lastTimestamp = neueEreignisse[neueEreignisse.length - 1].zeit_iso;
                    scrollToBottom();
                }
            } catch (error) {
                console.error('Fehler beim Abrufen neuer Ereignisse:', error);
            }
        }, 5000); // Alle 5 Sekunden prüfen
    }
});
