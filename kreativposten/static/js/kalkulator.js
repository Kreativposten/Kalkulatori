// kreativposten/js/kalkulator.js

// --- Hilfsfunktionen ---
function debounce(func, delay) {
    let timeout;
    return function(...args) {
        const context = this;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), delay);
    };
}

function formatCurrency(value) {
    const number = Number(value) || 0;
    return number.toLocaleString('de-DE', { style: 'currency', currency: 'EUR' });
}

function populateProduktSelect(selectElement, produktDaten) {
    selectElement.innerHTML = '<option value="">Produkt auswählen...</option>';
    (produktDaten || []).forEach(p => {
        const option = document.createElement('option');
        option.value = p.id;
        option.textContent = p.name;
        selectElement.appendChild(option);
    });
}

// --- Logik für Varianten (Farben/Größen) ---

async function fetchVariantenData(produktId, positionDiv) {
    const variantenContainer = positionDiv.querySelector('.varianten-container');
    variantenContainer.innerHTML = '<p style="text-align: center; color: #6c757d;">Lade Varianten...</p>';
    
    try {
        const response = await fetch(`/api/produkt/${produktId}/varianten-data`);
        if (!response.ok) throw new Error('Netzwerkfehler');
        const data = await response.json();
        
        positionDiv.dataset.variantenData = JSON.stringify(data);
        variantenContainer.innerHTML = ''; // Leeren, falls schon Zeilen da sind
        addVariante(positionDiv.querySelector('[data-action="add-variante"]'));
        
    } catch (error) {
        console.error("Fehler beim Laden der Variantendaten:", error);
        variantenContainer.innerHTML = '<p style="color: red; text-align: center;">Fehler beim Laden der Varianten.</p>';
    }
}

function populateFarbenDropdown(selectFarbe, positionDiv) {
    const variantenData = JSON.parse(positionDiv.dataset.variantenData || '{}');
    const farben = Object.keys(variantenData).sort();
    
    selectFarbe.innerHTML = '<option value="">Farbe wählen...</option>';
    farben.forEach(farbe => {
        const option = document.createElement('option');
        option.value = farbe;
        option.textContent = farbe;
        selectFarbe.appendChild(option);
    });
    // Reset Größen-Dropdown
    const groessenSelect = selectFarbe.closest('.varianten-row').querySelector('.groesse-select');
    if (groessenSelect) groessenSelect.innerHTML = '<option value="">-</option>';
}

function populateGroessenDropdown(selectGroesse, positionDiv, selectedFarbe) {
    const variantenData = JSON.parse(positionDiv.dataset.variantenData || '{}');
    const groessen = variantenData[selectedFarbe] || [];
    
    selectGroesse.innerHTML = '<option value="">Größe wählen...</option>';
    groessen.sort().forEach(groesse => {
        const option = document.createElement('option');
        option.value = groesse;
        option.textContent = groesse;
        selectGroesse.appendChild(option);
    });
}

// --- Logik für Positionen ---

function addPosition() {
    const posContainer = document.getElementById('positions-container');
    const posIndex = posContainer.children.length;
    const posDiv = document.createElement('div');
    posDiv.className = 'position';
    posDiv.dataset.posIndex = posIndex;

    posDiv.innerHTML = `
        <h2><span>Position ${posIndex + 1}</span><button type="button" class="btn-delete" data-action="delete-position">Löschen</button></h2>
        
        <div class="form-group produkt-typ-auswahl">
            <label>Textilgruppe</label>
            <div style="padding: 5px 0;">
                <input type="radio" id="typ-standard-${posIndex}" name="produkt_typ_${posIndex}" value="standard" checked><label for="typ-standard-${posIndex}">Standardartikel</label>
                <input type="radio" id="typ-katalog-${posIndex}" name="produkt_typ_${posIndex}" value="katalog" style="margin-left: 15px;"><label for="typ-katalog-${posIndex}">Katalogartikel</label>
                <input type="radio" id="typ-mitgebracht-${posIndex}" name="produkt_typ_${posIndex}" value="mitgebracht" style="margin-left: 15px;"><label for="typ-mitgebracht-${posIndex}">Mitgebrachtes Textil</label>
            </div>
        </div>

        <div class="form-group produkt-auswahl-standard">
            <label>Standardartikel</label>
            <select class="produkt-select"></select>
        </div>
        
        <div class="form-group produkt-auswahl-katalog" style="display:none;">
            <label for="katalog-suche-${posIndex}">Katalogartikel suchen</label>
            <input type="text" class="produkt-suche-input" id="katalog-suche-${posIndex}" placeholder="Name oder Teil des Namens eingeben...">
            <select class="produkt-select" size="5" style="margin-top: 5px;"></select>
        </div>
        
        <div class="form-group produkt-beschreibung-mitgebracht" style="display:none;">
            <label>Beschreibung des mitgebrachten Textils</label>
            <input type="text" class="produkt-beschreibung-input" placeholder="z.B. T-Shirt Kunde Meier">
        </div>

        <h4>Varianten</h4>
        <div class="varianten-header"><span>Menge</span><span>Farbe</span><span>Größe</span><span>Lagerstatus</span><span></span></div>
        <div class="varianten-container"></div>
        <button type="button" class="btn-add" data-action="add-variante">+ Variante</button>
        
        <div class="prints-container" style="margin-top: 1.5rem;"></div>
        <button type="button" class="btn-add" data-action="add-print">+ Druck</button>
    `;
    posContainer.appendChild(posDiv);
    
    populateProduktSelect(posDiv.querySelector('.produkt-auswahl-standard select'), STANDARD_PRODUKTE_DATA);
    populateProduktSelect(posDiv.querySelector('.produkt-auswahl-katalog select'), KATALOG_PRODUKTE_DATA);
    
    addVariante(posDiv.querySelector('[data-action="add-variante"]'));
    return posDiv;
}

function addVariante(button) {
    const variantenContainer = button.previousElementSibling;
    const positionDiv = button.closest('.position');
    const produktTyp = positionDiv.querySelector('input[type="radio"]:checked').value;
    
    const row = document.createElement('div');
    row.className = 'varianten-row';

    if (produktTyp === 'mitgebracht') {
        row.innerHTML = `
            <input type="number" class="menge-input" value="1" min="1">
            <input type="text" class="farbe-input" placeholder="z.B. Schwarz">
            <input type="text" class="groesse-input" placeholder="z.B. M">
            <span class="stock-status"></span>
            <button type="button" class="btn-delete" data-action="delete-variante">×</button>`;
    } else {
        row.innerHTML = `
            <input type="number" class="menge-input" value="1" min="1">
            <select class="farbe-select"><option value="">-</option></select>
            <select class="groesse-select"><option value="">-</option></select>
            <span class="stock-status"></span>
            <button type="button" class="btn-delete" data-action="delete-variante">×</button>`;
        
        const produktId = positionDiv.querySelector(`.produkt-auswahl-${produktTyp} .produkt-select`).value;
        if (produktId) {
            populateFarbenDropdown(row.querySelector('.farbe-select'), positionDiv);
        }
    }
    variantenContainer.appendChild(row);
}

// *** HIER KOMMEN DIE FEHLENDEN FUNKTIONEN HIN ***
function addPrint(button) {
    const printsContainer = button.previousElementSibling;
    const printRow = document.createElement('div');
    printRow.className = 'print-row';
    printRow.innerHTML = `
        <button type="button" class="btn-delete" data-action="delete-print">×</button>
        <div class="print-row-grid">
            <div>
                <div class="form-group">
                    <label>Druckposition</label>
                    <input type="text" class="druck-position-input" placeholder="z.B. Brust links, Rücken...">
                </div>
                <label>Druckgröße</label>
                <div style="display: flex; gap: 0.5rem;">
                    <select class="druck-select">
                        <option value="Kein">Kein Druck</option>
                        <option value="Klein">Klein</option>
                        <option value="Mittel">Mittel</option>
                        <option value="Groß">Groß</option>
                    </select>
                </div>
                <div style="display:flex; align-items:center; gap:0.5rem; margin-top:0.5rem;">
                    <input type="checkbox" class="freistellen-check" style="width: auto;">
                    <label style="margin:0;font-weight:normal;">Motiv nicht freigestellt</label>
                </div>
            </div>
            <div>
                <label>Motiv-Datei</label>
                <input type="file" class="druck-file-input" accept="image/*,.pdf,.ai,.eps" style="font-size:0.85em">
                <img class="print-preview">
                <input type="hidden" class="druck-filename">
            </div>
        </div>
    `;
    printsContainer.appendChild(printRow);
}

async function handleFileUpload(fileInput) {
    const file = fileInput.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    try {
        const response = await fetch('/upload-image', { method: 'POST', body: formData });
        const result = await response.json();
        if (result.success) {
            const printRow = fileInput.closest('.print-row');
            printRow.querySelector('.print-preview').src = '/uploads/' + result.filename;
            printRow.querySelector('.druck-filename').value = result.filename;
            debouncedCalculate();
        } else { 
            alert('Fehler beim Hochladen: ' + result.error); 
        }
    } catch (error) { 
        alert('Ein Netzwerkfehler ist beim Hochladen aufgetreten.'); 
    }
}
// *** ENDE DER FEHLENDEN FUNKTIONEN ***

// --- Haupt-Daten- und UI-Logik ---
async function checkVarianteStatus(element) {
    const row = element.closest('.varianten-row');
    const positionDiv = row.closest('.position');
    const produktTyp = positionDiv.querySelector('input[type="radio"]:checked').value;
    const statusSpan = row.querySelector('.stock-status');
    statusSpan.textContent = ''; // Reset

    if (produktTyp === 'mitgebracht') return;

    const produktSelect = positionDiv.querySelector(`.produkt-auswahl-${produktTyp} select`);
    const produktId = produktSelect.value;
    const farbe = row.querySelector('.farbe-select').value;
    const groesse = row.querySelector('.groesse-select').value;

    if (!produktId || !farbe || !groesse) return;

    statusSpan.textContent = 'prüft...';
    try {
        const response = await fetch(`/api/variante/check?produkt_id=${produktId}&groesse=${encodeURIComponent(groesse)}&farbe=${encodeURIComponent(farbe)}`);
        const data = await response.json();
        statusSpan.innerHTML = data.exists ? `🟢 An Lager (${data.lagerbestand} Stk.)` : '🔴 Muss bestellt werden';
    } catch (error) { statusSpan.textContent = 'Fehler'; }
}

function getFormData() {
    const data = {
        id: document.getElementById('angebot-id-hidden').value,
        kunde: { name: document.getElementById('kunde-name').value, firma: document.getElementById('kunde-firma').value },
        dringlichkeit: document.getElementById('dringlichkeit').value,
        abholdatum: document.getElementById('abholdatum').value,
        manual_adjustments: {
            mode: document.querySelector('input[name="adjustment-mode"]:checked').value,
            surcharge: { applied: document.getElementById('apply-surcharge').checked, amount: parseFloat(document.getElementById('surcharge-amount').value) || 0 },
            additional_costs: { applied: document.getElementById('apply-zusatzkosten').checked, description: document.getElementById('zusatzkosten-desc').value, amount: parseFloat(document.getElementById('zusatzkosten-amount').value) || 0 },
            discount: { applied: document.getElementById('apply-rabatt').checked, description: document.getElementById('rabatt-desc').value, percent: parseFloat(document.getElementById('rabatt-percent').value) || 0 },
            fixed_price: parseFloat(document.getElementById('fixed-price-amount').value) || 0
        },
        positions: []
    };

    document.querySelectorAll('.position').forEach(posEl => {
        const produktTyp = posEl.querySelector('input[type="radio"]:checked').value;
        let produktId = null;
        let produktBeschreibung = null;

        if (produktTyp !== 'mitgebracht') {
            const produktSelect = posEl.querySelector(`.produkt-auswahl-${produktTyp} select`);
            if (produktSelect && produktSelect.value) {
                produktId = parseInt(produktSelect.value);
            }
        } else {
            produktBeschreibung = posEl.querySelector('.produkt-beschreibung-input').value;
        }

        const posData = {
            produkt_typ: produktTyp,
            produkt_id: produktId,
            produkt_beschreibung: produktBeschreibung,
            varianten: [],
            drucke: []
        };
        posEl.querySelectorAll('.varianten-row').forEach(varEl => {
            const menge = parseInt(varEl.querySelector('.menge-input').value) || 0;
            if (menge > 0) {
                let farbe, groesse;
                if (produktTyp === 'mitgebracht') {
                    farbe = varEl.querySelector('.farbe-input').value;
                    groesse = varEl.querySelector('.groesse-input').value;
                } else {
                    farbe = varEl.querySelector('.farbe-select').value;
                    groesse = varEl.querySelector('.groesse-select').value;
                }
                posData.varianten.push({ menge: menge, groesse: groesse, farbe: farbe });
            }
        });
        posEl.querySelectorAll('.print-row').forEach(printEl => {
            posData.drucke.push({ typ: printEl.querySelector('.druck-select').value, position: printEl.querySelector('.druck-position-input').value, freistellen: printEl.querySelector('.freistellen-check').checked, filename: printEl.querySelector('.druck-filename').value });
        });
        
        if (produktId || (produktTyp === 'mitgebracht' && posData.varianten.length > 0) ) {
            data.positions.push(posData);
        }
    });
    return data;
}

async function calculateLive() {
    const dataForServer = getFormData();
    try {
        const response = await fetch('/calculate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(dataForServer) });
        const result = await response.json();
        updateLiveCalcUI(result);
    } catch (error) { console.error("Fehler bei der Live-Kalkulation:", error); }
}

function updateLiveCalcUI(result) {
    document.getElementById('angebot-nr-display').textContent = 'Projekt-Nr: ' + result.angebot_nr;
    const detailsContainer = document.getElementById('live-calc-details');
    detailsContainer.innerHTML = '';
    (result.positionen || []).forEach((pos, index) => {
        const posDiv = document.createElement('div');
        posDiv.className = 'live-calc-position';
        let artikelHTML = pos.artikel_liste.map(artikel => `<li>${artikel}</li>`).join('');
        let content = `<div class="pos-header"><h3>Pos. ${index + 1} - ${pos.name}</h3><h3>${formatCurrency(pos.pos_gesamt_brutto)}</h3></div><ul class="artikel-liste">${artikelHTML}</ul>`;
        if (pos.textil_gesamt_brutto > 0) {
            content += `<div class="cost-block"><strong>Textil-Kosten</strong><div class="calc-line"><span>Grundpreis:</span><span>${pos.menge} Stk. &times; ${formatCurrency(pos.textil_einzel_brutto)} = ${formatCurrency(pos.textil_gesamt_vor_rabatt)}</span></div><div class="calc-line"><span>Mengenrabatt (${pos.textil_rabatt_prozent.toFixed(0)}%):</span><span>-${formatCurrency(pos.textil_gesamrabatt_betrag)}</span></div><div class="calc-line calc-line-total"><span>Textil Gesamt:</span><span>${formatCurrency(pos.textil_gesamt_brutto)}</span></div></div>`;
        }
        if (pos.druck_gesamt_brutto > 0) {
             content += `<div class="cost-block"><strong>Druck-Kosten</strong><div class="calc-line"><span>Grundpreis (Summe):</span><span>${formatCurrency(pos.druck_gesamt_vor_rabatt)}</span></div><div class="calc-line"><span>Mengenrabatt (${pos.druck_rabatt_prozent.toFixed(0)}%):</span><span>-${formatCurrency(pos.druck_gesamrabatt_betrag)}</span></div><div class="calc-line calc-line-total"><span>Druck Gesamt:</span><span>${formatCurrency(pos.druck_gesamt_brutto)}</span></div></div>`;
        }
        if (pos.zuschlag_freistellen_brutto > 0) {
            content += `<div class="cost-block"><strong>Zuschläge</strong><div class="calc-line"><span>Motiv nicht freigestellt:</span><span>${formatCurrency(pos.zuschlag_freistellen_brutto)}</span></div></div>`;
        }
        posDiv.innerHTML = content;
        detailsContainer.appendChild(posDiv);
    });
    document.getElementById('total-positions').textContent = formatCurrency(result.positions_total_brutto);
    const adjustments = getFormData().manual_adjustments;
    const adjustmentsSummary = document.getElementById('adjustments-summary');
    adjustmentsSummary.innerHTML = '';
    if (result.dringlichkeits_zuschlag_brutto > 0) { adjustmentsSummary.innerHTML += `<div class="calc-line"><span>Dringlichkeits-Zuschlag:</span><span>${formatCurrency(result.dringlichkeits_zuschlag_brutto)}</span></div>`; }
    if (adjustments.surcharge.applied) { adjustmentsSummary.innerHTML += `<div class="calc-line"><span>Zusatzaufschlag:</span><span>${formatCurrency(adjustments.surcharge.amount)}</span></div>`; }
    if (adjustments.additional_costs.applied) { adjustmentsSummary.innerHTML += `<div class="calc-line"><span>${adjustments.additional_costs.description || 'Zusatzkosten'}:</span><span>${formatCurrency(adjustments.additional_costs.amount)}</span></div>`; }
    if (adjustments.discount.applied) { adjustmentsSummary.innerHTML += `<div class="calc-line"><span>${adjustments.discount.description || 'Sonderrabatt'} (${adjustments.discount.percent}%):</span><span class="text-danger">-${formatCurrency(result.rabatt_betrag_brutto)}</span></div>`; }
    document.getElementById('total-netto').textContent = formatCurrency(result.final_netto);
    document.getElementById('total-mwst').textContent = formatCurrency(result.final_mwst);
    document.getElementById('total-brutto').textContent = formatCurrency(result.final_brutto);
    const fixedPriceSavings = document.getElementById('fixed-price-savings');
    if (adjustments.mode === 'fixed') {
        const savings = result.berechneter_total_brutto - adjustments.fixed_price;
        fixedPriceSavings.textContent = savings > 0 ? `Ersparnis: ${formatCurrency(savings)}` : '';
    } else { fixedPriceSavings.textContent = ''; }
}

async function saveAngebot() {
    const dataForServer = getFormData();
    if (!dataForServer.kunde.name) { alert("Bitte geben Sie einen Kundennamen ein."); return; }
    const statusDiv = document.getElementById('status-messages');
    statusDiv.textContent = "Speichere...";
    try {
        const response = await fetch('/save-angebot', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(dataForServer) });
        const result = await response.json();
        if (result.success) {
            document.getElementById('angebot-id-hidden').value = result.angebot_id;
            document.getElementById('angebot-nr-display').textContent = 'Projekt-Nr: ' + result.angebot_nr;
            statusDiv.textContent = result.message;
            statusDiv.className = 'status-messages success';
        } else {
            statusDiv.textContent = "Fehler: " + (result.error || 'Unbekannt');
            statusDiv.className = 'status-messages error';
        }
    } catch (error) { statusDiv.textContent = "Netzwerkfehler."; statusDiv.className = 'status-messages error'; }
}

function toggleAdjustmentMode() {
    const isStandard = document.getElementById('mode-standard').checked;
    document.getElementById('standard-adjustments').style.display = isStandard ? 'block' : 'none';
    document.getElementById('fixed-price-adjustment').style.display = isStandard ? 'none' : 'block';
    debouncedCalculate();
}

// --- Event Handlers ---
const debouncedCalculate = debounce(calculateLive, 400);
const debouncedCheckVariante = debounce(checkVarianteStatus, 500);

document.addEventListener('DOMContentLoaded', () => {
    const calculatorForm = document.getElementById('calculator-form');
    if (!calculatorForm) return;

    calculatorForm.addEventListener('click', (e) => {
        const action = e.target.dataset.action;
        if (action === 'add-position') addPosition();
        if (action === 'add-variante') addVariante(e.target);
        if (action === 'add-print') addPrint(e.target);
        if (action === 'delete-position') { e.target.closest('.position').remove(); debouncedCalculate(); }
        if (action === 'delete-variante') { e.target.closest('.varianten-row').remove(); debouncedCalculate(); }
        if (action === 'delete-print') { e.target.closest('.print-row').remove(); debouncedCalculate(); }
        if (action === 'save-angebot') saveAngebot();
    });

    calculatorForm.addEventListener('input', (e) => {
        const target = e.target;
        if (target.matches('input[type="text"], input[type="number"], input[type="date"], textarea')) {
            debouncedCalculate();
        }
        if (target.matches('.produkt-suche-input')) {
            const positionDiv = target.closest('.position');
            const suchtext = target.value.toLowerCase();
            const gefilterteProdukte = KATALOG_PRODUKTE_DATA.filter(p => p.name.toLowerCase().includes(suchtext));
            populateProduktSelect(positionDiv.querySelector('.produkt-auswahl-katalog select'), gefilterteProdukte);
        }
    });
    
    calculatorForm.addEventListener('change', (e) => {
        const target = e.target;
        if (target.matches('input[name="adjustment-mode"]')) {
            toggleAdjustmentMode();
            return;
        }
        if (target.matches('.druck-file-input')) {
            handleFileUpload(target);
            return;
        }
        
        if (target.matches('input[name^="produkt_typ_"]')) {
            const positionDiv = target.closest('.position');
            const selectedType = target.value;

            positionDiv.querySelector('.produkt-auswahl-standard').style.display = selectedType === 'standard' ? 'block' : 'none';
            positionDiv.querySelector('.produkt-auswahl-katalog').style.display = selectedType === 'katalog' ? 'block' : 'none';
            positionDiv.querySelector('.produkt-beschreibung-mitgebracht').style.display = selectedType === 'mitgebracht' ? 'block' : 'none';
            
            positionDiv.querySelector('.varianten-container').innerHTML = '';
            addVariante(positionDiv.querySelector('[data-action="add-variante"]'));
        }
        
        if (target.matches('.produkt-select')) {
            const positionDiv = target.closest('.position');
            const produktId = target.value;
            if (produktId) {
                fetchVariantenData(produktId, positionDiv);
            } else {
                positionDiv.querySelector('.varianten-container').innerHTML = '';
                addVariante(positionDiv.querySelector('[data-action="add-variante"]'));
            }
        }
        
        if (target.matches('.farbe-select')) {
            const positionDiv = target.closest('.position');
            const row = target.closest('.varianten-row');
            populateGroessenDropdown(row.querySelector('.groesse-select'), positionDiv, target.value);
        }
        
        if(target.matches('.groesse-select')) {
             debouncedCheckVariante(target);
        }
        
        debouncedCalculate();
    });

    addPosition();
    toggleAdjustmentMode();
});