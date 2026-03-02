<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>TYPOLOGY</title>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=Jost:wght@300;400;500&display=swap" rel="stylesheet"/>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --ink:#1a1714;
  --parchment:#f5f0e8;
  --gold:#b8975a;
  --muted:#7a7269;
  --surface:#f0ead8;
  --border:#ddd5c0;
  --white:#faf7f2;
  --error:#8b3a3a;
}
html,body{height:100%;background:var(--parchment);color:var(--ink);font-family:'Jost',sans-serif;font-weight:300}

/* LOADING */
#loading-screen{position:fixed;inset:0;background:var(--ink);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2rem;z-index:100;transition:opacity 0.8s ease}
#loading-screen.fade-out{opacity:0;pointer-events:none}
.loading-logo{font-family:'Cormorant Garamond',serif;font-size:clamp(2rem,6vw,3.5rem);font-weight:300;letter-spacing:0.35em;color:var(--gold)}
.loading-bar-wrap{width:220px;height:1px;background:rgba(255,255,255,0.1);position:relative;overflow:hidden}
.loading-bar-fill{position:absolute;top:0;left:-100%;height:100%;background:var(--gold);animation:loadSlide 3s ease forwards}
@keyframes loadSlide{to{left:0}}
.loading-text{font-size:0.75rem;letter-spacing:0.2em;color:var(--muted);text-transform:uppercase}

/* APP */
#app{display:none;height:100vh;flex-direction:column}
#app.visible{display:flex}

/* HEADER */
header{display:flex;align-items:center;justify-content:space-between;padding:1.25rem 2rem;border-bottom:1px solid var(--border);background:var(--white);flex-shrink:0}
.logo{font-family:'Cormorant Garamond',serif;font-size:1.4rem;letter-spacing:0.3em;font-weight:300}
.progress-wrap{display:flex;align-items:center;gap:1rem;font-size:0.72rem;letter-spacing:0.15em;color:var(--muted);text-transform:uppercase}
.progress-track{width:140px;height:2px;background:var(--border);border-radius:2px;overflow:hidden}
.progress-fill{height:100%;background:var(--gold);border-radius:2px;transition:width 0.6s ease;width:0%}

/* MAIN */
main{flex:1;display:flex;flex-direction:column;overflow:hidden}

/* MESSAGGI */
#messages{flex:1;overflow-y:auto;padding:2rem;display:flex;flex-direction:column;gap:1.25rem;scroll-behavior:smooth}
#messages::-webkit-scrollbar{width:4px}
#messages::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}
.msg{display:flex;gap:0.9rem;animation:msgIn 0.4s ease both}
@keyframes msgIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
.msg.user{flex-direction:row-reverse}
.avatar{width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-family:'Cormorant Garamond',serif;font-size:1rem;flex-shrink:0;margin-top:2px}
.avatar.sofia{background:var(--ink);color:var(--gold)}
.avatar.user-av{background:var(--gold);color:var(--white)}
.bubble{max-width:68%;padding:0.9rem 1.2rem;border-radius:4px;line-height:1.65;font-size:0.93rem}
.msg.sofia .bubble{background:var(--white);border:1px solid var(--border)}
.msg.user .bubble{background:var(--ink);color:var(--parchment)}

/* TYPING */
.typing{display:flex;align-items:center;gap:5px;padding:0.6rem 0}
.dot{width:6px;height:6px;border-radius:50%;background:var(--gold);animation:pulse 1.2s ease-in-out infinite}
.dot:nth-child(2){animation-delay:0.2s}
.dot:nth-child(3){animation-delay:0.4s}
@keyframes pulse{0%,60%,100%{opacity:0.3;transform:scale(0.8)}30%{opacity:1;transform:scale(1)}}

/* INPUT */
#input-area{padding:1.25rem 2rem;border-top:1px solid var(--border);background:var(--white);flex-shrink:0}
#choice-buttons{display:flex;gap:1rem;margin-bottom:1rem}
.choice-btn{flex:1;padding:0.75rem 1rem;border:1px solid var(--border);background:var(--surface);color:var(--ink);font-family:'Jost',sans-serif;font-size:0.85rem;font-weight:400;letter-spacing:0.1em;cursor:pointer;border-radius:3px;transition:all 0.2s;text-transform:uppercase}
.choice-btn:hover{background:var(--ink);color:var(--parchment);border-color:var(--ink)}
.choice-btn.selected{background:var(--gold);color:var(--white);border-color:var(--gold)}
.input-row{display:flex;gap:0.75rem}
#user-input{flex:1;padding:0.8rem 1.1rem;border:1px solid var(--border);background:var(--surface);color:var(--ink);font-family:'Jost',sans-serif;font-size:0.9rem;font-weight:300;border-radius:3px;outline:none;transition:border-color 0.2s}
#user-input:focus{border-color:var(--gold)}
#user-input::placeholder{color:var(--muted)}
#send-btn{width:44px;height:44px;background:var(--ink);border:none;border-radius:3px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:background 0.2s;flex-shrink:0}
#send-btn:hover{background:var(--gold)}
#send-btn svg{width:18px;height:18px;fill:var(--parchment)}
#send-btn:disabled{opacity:0.4;cursor:not-allowed}
.hint{margin-top:0.5rem;font-size:0.72rem;letter-spacing:0.12em;color:var(--muted);text-align:center;text-transform:uppercase}

/* RISULTATO */
#result-panel{display:none;flex:1;overflow-y:auto;padding:3rem 2rem;animation:msgIn 0.6s ease}
#result-panel.visible{display:block}
.result-inner{max-width:640px;margin:0 auto}
.result-eyebrow{font-size:0.72rem;letter-spacing:0.25em;text-transform:uppercase;color:var(--gold);margin-bottom:0.75rem}
.result-title{font-family:'Cormorant Garamond',serif;font-size:clamp(1.3rem,3vw,2rem);font-weight:300;line-height:1.4;margin-bottom:0.5rem}
.result-sigla{font-size:0.85rem;letter-spacing:0.2em;color:var(--muted);text-transform:uppercase;margin-bottom:1.5rem}
.divider{height:1px;background:var(--border);margin:1.5rem 0}
.profile-desc{font-size:1rem;line-height:1.8;margin-bottom:2rem}
.scores-grid{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:2rem}
.score-label{font-size:0.7rem;letter-spacing:0.15em;text-transform:uppercase;color:var(--muted);margin-bottom:0.4rem;display:flex;justify-content:space-between}
.score-track{height:3px;background:var(--border);border-radius:2px;overflow:hidden}
.score-bar{height:100%;background:var(--gold);border-radius:2px;transition:width 1s ease 0.3s;width:0%}
.otroversion-badge{display:inline-flex;align-items:center;gap:0.5rem;padding:0.5rem 1.1rem;border:1px solid var(--gold);border-radius:20px;font-size:0.8rem;letter-spacing:0.15em;text-transform:uppercase;color:var(--gold);margin-bottom:2rem}
.restart-btn{padding:0.85rem 2rem;border:1px solid var(--ink);background:transparent;color:var(--ink);font-family:'Jost',sans-serif;font-size:0.8rem;letter-spacing:0.2em;text-transform:uppercase;cursor:pointer;border-radius:3px;transition:all 0.2s}
.restart-btn:hover{background:var(--ink);color:var(--parchment)}

/* TOAST */
#error-toast{display:none;position:fixed;bottom:2rem;left:50%;transform:translateX(-50%);background:var(--error);color:#fff;padding:0.75rem 1.5rem;border-radius:4px;font-size:0.85rem;z-index:200;white-space:nowrap}

@media(max-width:600px){
  header,#messages,#input-area{padding:1rem}
  .bubble{max-width:85%}
  #choice-buttons{flex-direction:column}
  .scores-grid{grid-template-columns:1fr}
}
</style>
</head>
<body>

<!-- SCHERMATA DI CARICAMENTO -->
<div id="loading-screen">
  <div class="loading-logo">T Y P O L O G Y</div>
  <div class="loading-bar-wrap"><div class="loading-bar-fill"></div></div>
  <div class="loading-text" id="loading-text">Connessione in corso…</div>
</div>

<!-- APP -->
<div id="app">
  <header>
    <div class="logo">T Y P O L O G Y</div>
    <div class="progress-wrap">
      <span id="progress-label">0 / 72</span>
      <div class="progress-track"><div class="progress-fill" id="progress-fill"></div></div>
    </div>
  </header>

  <main>
    <!-- CHAT -->
    <div id="chat-view" style="display:flex;flex-direction:column;flex:1;overflow:hidden;">
      <div id="messages"></div>
      <div id="input-area">
        <div id="choice-buttons" style="display:none;">
          <button class="choice-btn" id="btn-a" onclick="sendChoice('A')">A</button>
          <button class="choice-btn" id="btn-b" onclick="sendChoice('B')">B</button>
        </div>
        <div class="input-row">
          <input id="user-input" type="text" placeholder="Scrivi A, B oppure un messaggio…" autocomplete="off"/>
          <button id="send-btn" onclick="sendMessage()">
            <svg viewBox="0 0 24 24"><path d="M2 12L22 2 15 22 11 13z"/></svg>
          </button>
        </div>
        <div class="hint">Scegli A o B · oppure scrivi e premi Invio</div>
      </div>
    </div>

    <!-- RISULTATO -->
    <div id="result-panel">
      <div class="result-inner" id="result-inner"></div>
    </div>
  </main>
</div>

<div id="error-toast"></div>

<script>
const API = 'https://typologytest.onrender.com';

let conversationHistory = [];
let responses = {};
let currentQuestionIndex = 0;
let isWaiting = false;

// ── UTILITY ──────────────────────────────────────────────────────────────────

function showError(msg) {
  const t = document.getElementById('error-toast');
  t.textContent = msg;
  t.style.display = 'block';
  setTimeout(() => t.style.display = 'none', 4000);
}

function updateProgress(n) {
  const pct = Math.round((n / 72) * 100);
  document.getElementById('progress-fill').style.width = pct + '%';
  document.getElementById('progress-label').textContent = n + ' / 72';
}

function scrollDown() {
  const m = document.getElementById('messages');
  setTimeout(() => m.scrollTop = m.scrollHeight, 50);
}

// ── MESSAGGI ─────────────────────────────────────────────────────────────────

function addMessage(role, text) {
  const m = document.getElementById('messages');
  const div = document.createElement('div');
  div.className = 'msg ' + (role === 'assistant' ? 'sofia' : 'user');
  div.innerHTML = `
    <div class="avatar ${role === 'assistant' ? 'sofia' : 'user-av'}">${role === 'assistant' ? 'S' : 'T'}</div>
    <div class="bubble">${text.replace(/\n/g, '<br>')}</div>`;
  m.appendChild(div);
  scrollDown();
}

function showTyping() {
  const m = document.getElementById('messages');
  const div = document.createElement('div');
  div.className = 'msg sofia';
  div.id = 'typing-ind';
  div.innerHTML = `<div class="avatar sofia">S</div>
    <div class="bubble"><div class="typing">
      <div class="dot"></div><div class="dot"></div><div class="dot"></div>
    </div></div>`;
  m.appendChild(div);
  scrollDown();
}

function removeTyping() {
  const t = document.getElementById('typing-ind');
  if (t) t.remove();
}

// ── API CON RETRY AUTOMATICO ──────────────────────────────────────────────────

async function callAPI(endpoint, body, retries = 4) {
  for (let i = 0; i < retries; i++) {
    try {
      const res = await fetch(API + endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(65000)
      });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      return await res.json();
    } catch (e) {
      if (i < retries - 1) {
        showError('Connessione lenta… tentativo ' + (i + 2) + '/' + retries);
        await new Promise(r => setTimeout(r, 4000));
      } else {
        throw e;
      }
    }
  }
}

// ── INVIO MESSAGGI ────────────────────────────────────────────────────────────

async function sendMessage() {
  const input = document.getElementById('user-input');
  const text = input.value.trim();
  if (!text || isWaiting) return;
  const u = text.toUpperCase();
  if (u === 'A' || u === 'B') { sendChoice(u); return; }
  input.value = '';
  addMessage('user', text);
  await fetchResponse(text, null);
}

async function sendChoice(choice) {
  if (isWaiting) return;
  document.getElementById('btn-a').classList.toggle('selected', choice === 'A');
  document.getElementById('btn-b').classList.toggle('selected', choice === 'B');
  responses[String(currentQuestionIndex + 1)] = choice;
  addMessage('user', choice === 'A' ? 'Opzione A' : 'Opzione B');
  await fetchResponse(choice, choice);
}

async function fetchResponse(userText, choice) {
  isWaiting = true;
  document.getElementById('send-btn').disabled = true;
  document.getElementById('choice-buttons').style.display = 'none';
  showTyping();

  const history = [...conversationHistory];

  try {
    const data = await callAPI('/api/chat', {
      message: userText,
      conversation_history: conversationHistory,
      responses: responses,
      current_question_index: currentQuestionIndex
    });

    removeTyping();
    conversationHistory = [
      ...history,
      { role: 'user', content: userText },
      { role: 'assistant', content: data.response }
    ];
    addMessage('assistant', data.response);

    if (data.completed) {
      setTimeout(() => loadAndShowResult(), 1500);
    } else {
      currentQuestionIndex = data.question_index + 1;
      if (choice) updateProgress(currentQuestionIndex);
      document.getElementById('btn-a').classList.remove('selected');
      document.getElementById('btn-b').classList.remove('selected');
      document.getElementById('choice-buttons').style.display = 'flex';
    }
  } catch (e) {
    removeTyping();
    addMessage('assistant', 'Si è verificato un problema di connessione. Riprova a rispondere.');
    document.getElementById('choice-buttons').style.display = 'flex';
  }

  isWaiting = false;
  document.getElementById('send-btn').disabled = false;
}

// ── RISULTATO ─────────────────────────────────────────────────────────────────

async function loadAndShowResult() {
  updateProgress(72);
  document.getElementById('chat-view').style.display = 'none';
  document.getElementById('result-panel').classList.add('visible');
  try {
    const data = await callAPI('/api/submit', { responses });
    renderResult(data);
  } catch (e) {
    document.getElementById('result-inner').innerHTML =
      '<p style="color:var(--error)">Errore nel calcolo. Ricarica la pagina.</p>';
  }
}

function renderResult(d) {
  const s = d.scores;
  document.getElementById('result-inner').innerHTML = `
    <div class="result-eyebrow">Il tuo profilo tipologico</div>
    <div class="result-title">${d.nome_esteso}</div>
    <div class="result-sigla">${d.sigla}</div>
    <div class="otroversion-badge">◆ ${d.otroversion}</div>
    <div class="divider"></div>
    <div class="profile-desc">${d.profile_description}</div>
    <div class="scores-grid">
      ${[
        ['Pensiero (T)', s.T],
        ['Sentimento (F)', s.F],
        ['Sensazione (S)', s.S],
        ['Intuizione (N)', s.N],
        ['Estroversione (E)', s.E],
        ['Introversione (I)', s.I]
      ].map(([l, v]) => `
        <div class="score-item">
          <div class="score-label"><span>${l}</span><span>${v}%</span></div>
          <div class="score-track"><div class="score-bar" data-val="${v}"></div></div>
        </div>`).join('')}
    </div>
    <div class="divider"></div>
    <button class="restart-btn" onclick="location.reload()">Ricomincia il test</button>
  `;
  setTimeout(() => {
    document.querySelectorAll('.score-bar').forEach(b => b.style.width = b.dataset.val + '%');
  }, 300);
}

// ── AVVIO: aspetta il backend poi mostra l'app ────────────────────────────────

async function wakeAndStart() {
  const loadText = document.getElementById('loading-text');
  let dots = 0;
  const spin = setInterval(() => {
    dots = (dots + 1) % 4;
    loadText.textContent = 'Avvio del servizio' + '.'.repeat(dots);
  }, 600);

  // Polling sul backend: fino a 8 tentativi da 5 secondi = ~40 secondi max
  for (let i = 0; i < 8; i++) {
    try {
      const r = await fetch(API + '/', { signal: AbortSignal.timeout(12000) });
      if (r.ok) break;
    } catch (e) { /* continua */ }
    await new Promise(r => setTimeout(r, 5000));
  }

  clearInterval(spin);
  loadText.textContent = 'Pronto!';
  await new Promise(r => setTimeout(r, 400));

  // Fade out loading, mostra app
  document.getElementById('loading-screen').classList.add('fade-out');
  setTimeout(() => {
    document.getElementById('loading-screen').style.display = 'none';
    document.getElementById('app').classList.add('visible');
  }, 800);

  // Prima domanda
  showTyping();
  try {
    const data = await callAPI('/api/chat', {
      message: 'Inizia il test',
      conversation_history: [],
      responses: {},
      current_question_index: 0
    });
    removeTyping();
    conversationHistory = [
      { role: 'user', content: 'Inizia il test' },
      { role: 'assistant', content: data.response }
    ];
    addMessage('assistant', data.response);
    document.getElementById('choice-buttons').style.display = 'flex';
  } catch (e) {
    removeTyping();
    addMessage('assistant', 'Ciao! Sono Sofia. Problemi di connessione — ricarica la pagina per iniziare.');
  }
}

document.getElementById('user-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') sendMessage();
});

wakeAndStart();
</script>
</body>
</html>
