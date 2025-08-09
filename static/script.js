/**
 * Code Typing Trainer - Frontend JavaScript
 *
 * Handles all client-side functionality for the Code Typing Trainer application,
 * including typing test logic, error handling, metrics calculation, and visualization.
 *
 * Author: Ahmad Asmandar <ahmad.asmandar@gmx.com>
 * License: GNU General Public License v3.0 (GPL-3.0)
 * Version: 1.0.0
 * Date: 2025-06-22
 */

document.addEventListener('DOMContentLoaded', () => {
  // DOM element references
  const codeInput = document.getElementById('codeInput');  // Textarea for code input
  const startBtn = document.getElementById('startBtn');    // Button to start the test
  const restartBtn = document.getElementById('restartBtn'); // Button to restart with same code
  const stopBtn = document.getElementById('stopBtn');      // Button to stop the test
  const codeDisplay = document.getElementById('codeDisplay'); // Container for displaying code to type
  const typingTest = document.getElementById('typingTest'); // Test container
  const codeSyntax = document.getElementById('codeSyntax'); // Prism background layer
  const dateElem = document.getElementById('date');        // Element for displaying current date
  const timerElem = document.getElementById('timer');      // Element for displaying elapsed time
  const liveWpmElem = document.getElementById('liveWpm');  // Element for displaying live WPM
  const progressBar = document.getElementById('progressBar'); // Progress indicator
  const summaryModal = document.getElementById('summaryModal'); // Results modal
  const themeToggle = document.getElementById('themeToggle'); // Theme toggle button

  // State variables
  let code = '',              // The code to be typed
      index = 0,             // Current position in the code
      startTime = null;      // Timestamp when typing started
  let startedTyping = false, // Whether user has started typing
      errorState = false;    // Whether user is in error state (wrong character)
  let errorCount = 0,        // Number of typing errors
      backspaceCount = 0,    // Number of backspace key presses
      timerInterval = null;  // Timer interval reference
  let chart = null;          // Chart.js instance for WPM history
  let spansCache = [];       // Cached list of spans for performance
  
  // Audio context for error sound
  const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

  // --- Theme toggle (light/dark) ---
  const THEME_KEY = 'ctt.theme';
  function applyTheme(theme) {
    const root = document.documentElement;
    if (theme === 'light') {
      root.setAttribute('data-theme', 'light');
    } else {
      root.removeAttribute('data-theme'); // dark is default
    }
  }

  function updateThemeToggleIcon(theme) {
    if (!themeToggle) return;
    const icon = themeToggle.querySelector('i');
    if (!icon) return;
    // show moon in dark (click to go light), sun in light (click to go dark)
    if (theme === 'light') {
      icon.classList.remove('fa-moon');
      icon.classList.add('fa-sun');
      themeToggle.title = 'Switch to dark mode';
    } else {
      icon.classList.remove('fa-sun');
      icon.classList.add('fa-moon');
      themeToggle.title = 'Switch to light mode';
    }
  }

  (function initTheme() {
    let theme = localStorage.getItem(THEME_KEY);
    if (!theme) {
      // system preference fallback
      const prefersLight = window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches;
      theme = prefersLight ? 'light' : 'dark';
    }
    applyTheme(theme);
    updateThemeToggleIcon(theme);
  })();

  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const isLight = document.documentElement.getAttribute('data-theme') === 'light';
      const next = isLight ? 'dark' : 'light';
      applyTheme(next);
      localStorage.setItem(THEME_KEY, next);
      updateThemeToggleIcon(next);
    });
  }

  // Simple code templates by language/level (fallback if JSON not found)
  const CODE_TEMPLATES = {
    c: {
      beginner: `#include <stdio.h>\n\nint main(void) {\n    int sum = 0;\n    for (int i = 1; i <= 10; i++) {\n        sum += i;\n    }\n    printf("Sum: %d\\n", sum);\n    return 0;\n}\n`,
      intermediate: `#include <stdio.h>\n#include <string.h>\n\nvoid reverse(char *s) {\n    int n = strlen(s);\n    for (int i = 0, j = n - 1; i < j; i++, j--) {\n        char t = s[i]; s[i] = s[j]; s[j] = t;\n    }\n}\n\nint main(void) {\n    char buf[64] = "Hello, World!";\n    reverse(buf);\n    printf("%s\\n", buf);\n    return 0;\n}\n`,
      advanced: `#include <stdio.h>\n#include <stdlib.h>\n\ntypedef struct Node {\n    int val;\n    struct Node *next;\n} Node;\n\nNode* push(Node* head, int v) {\n    Node* n = malloc(sizeof(Node));\n    n->val = v; n->next = head;\n    return n;\n}\n\nvoid print(Node* head){\n    for(Node* p=head; p; p=p->next) printf("%d ", p->val);\n    printf("\\n");\n}\n\nvoid free_list(Node* head){\n    while(head){ Node* t=head; head=head->next; free(t);}\n}\n\nint main(void){\n    Node* head = NULL;\n    for(int i=0;i<5;i++) head = push(head, i*i);\n    print(head);\n    free_list(head);\n    return 0;\n}\n`
    },
    python: {
      beginner: `total = 0\nfor i in range(1, 11):\n    total += i\nprint(f"Sum: {total}")\n`,
      intermediate: `def reverse(s: str) -> str:\n    return s[::-1]\n\nprint(reverse("Hello, World!"))\n`,
      advanced: `from dataclasses import dataclass\nfrom typing import Optional\n\n@dataclass\nclass Node:\n    val: int\n    next: Optional['Node'] = None\n\ndef push(head: Optional[Node], v: int) -> Node:\n    return Node(v, head)\n\ndef print_list(head: Optional[Node]) -> None:\n    p = head\n    out = []\n    while p:\n        out.append(str(p.val))\n        p = p.next\n    print(" ".join(out))\n\nhead = None\nfor i in range(5):\n    head = push(head, i*i)\nprint_list(head)\n`
    }
  };

  // --- Comment detection and skipping ---
  function buildSkipMaskForComments(text, langId) {
    const n = text.length;
    const skip = new Array(n).fill(false);
    const lang = (langId || '').toLowerCase();

    function mark(i){ if (i>=0 && i<n) skip[i] = true; }

    if (lang === 'c' || lang === 'stm32' || lang === 'cpp' || lang === 'javascript' || lang === 'typescript' || lang === 'java' || lang === 'go') {
      // C-like: // line, /* block */, with string handling
      let inBlock = false, inLine = false, inStr = false, strDelim = '';
      for (let i=0; i<n; i++) {
        const c = text[i], p = i>0 ? text[i-1] : '', nn = i+1<n ? text[i+1] : '';
        if (inLine) {
          mark(i);
          if (c === '\n') { inLine = false; }
          continue;
        }
        if (inBlock) {
          mark(i);
          if (p === '*' && c === '/') { /* end of block */ }
          if (p === '*' && c === '/') { inBlock = false; }
          continue;
        }
        if (inStr) {
          if (c === strDelim && p !== '\\') { inStr = false; }
          continue;
        }
        if (c === '"' || c === '\'') { inStr = true; strDelim = c; continue; }
        if (c === '/' && nn === '/') { inLine = true; mark(i); mark(i+1); i++; continue; }
        if (c === '/' && nn === '*') { inBlock = true; mark(i); mark(i+1); i++; continue; }
      }
    } else if (lang === 'python') {
      // Python: # line, triple quotes and regular strings
      let inLine = false, inStr = false, strDelim = '', triple = false;
      for (let i=0; i<n; i++) {
        const c = text[i], p = i>0 ? text[i-1] : '', nn = text.slice(i, i+3);
        if (inLine) {
          mark(i);
          if (c === '\n') { inLine = false; }
          continue;
        }
        if (inStr) {
          if (triple) {
            if (nn === strDelim.repeat(3)) { mark(i); mark(i+1); mark(i+2); i+=2; inStr=false; triple=false; }
            else { mark(i); }
          } else {
            if (c === strDelim && p !== '\\') { inStr = false; } else { mark(i); }
          }
          continue;
        }
        if (c === '#') { inLine = true; mark(i); continue; }
        if (nn === "'''" || nn === '"""') { inStr = true; triple = true; strDelim = nn[0]; mark(i); mark(i+1); mark(i+2); i+=2; continue; }
        if (c === '"' || c === '\'') { inStr = true; strDelim = c; mark(i); continue; }
      }
    } else if (lang === 'vhdl') {
      // VHDL: -- line, naive string handling for "..."
      let inLine = false, inStr = false;
      for (let i=0; i<n; i++) {
        const c = text[i], nn = i+1<n ? text[i+1] : '';
        if (inLine) { mark(i); if (c==='\n') inLine=false; continue; }
        if (inStr) { if (c==='"') inStr=false; continue; }
        if (c==='"') { inStr=true; continue; }
        if (c==='-' && nn==='-') { inLine=true; mark(i); mark(i+1); i++; continue; }
      }
    } else if (lang === 'html') {
      // HTML: <!-- ... -->
      for (let i=0; i<n; i++) {
        if (text.slice(i, i+4) === '<!--') {
          mark(i); mark(i+1); mark(i+2); mark(i+3);
          i+=4; while (i<n && text.slice(i, i+3) !== '-->') { mark(i); i++; }
          if (i<n) { mark(i); mark(i+1); mark(i+2); }
        }
      }
    }
    return skip;
  }

  function advanceOverSkips(spans) {
    while (index < spans.length && spans[index].dataset.skip === '1') {
      spans[index].classList.add('correct');
      index++;
    }
  }

  // Build dropdowns from JSON templates
  const templateLangSel = document.getElementById('templateLang');
  const templateLevelSel = document.getElementById('templateLevel');
  const templateApplyBtn = document.getElementById('templateApply');
  let TEMPLATE_MAP = null; // { langId: { levelId: snippet } }
  let TEMPLATE_LABELS = {}; // { langId: label }

  function mapToPrismLanguage(langId) {
    const l = (langId || '').toLowerCase();
    if (l === 'stm32') return 'c';
    if (l === 'js' || l === 'javascript' || l === 'typescript') return 'javascript';
    if (l === 'py' || l === 'python') return 'python';
    if (l === 'c++' || l === 'cpp') return 'cpp';
    if (l === 'html') return 'markup';
    if (l === 'vhdl') return 'vhdl';
    if (l === 'c') return 'c';
    return 'none';
  }

  function renderSyntaxBackground(codeText, langId) {
    if (!codeSyntax || !window.Prism) return;
    const prismLang = mapToPrismLanguage(langId);
    // ensure a <code> child for Prism autoloader
    let codeEl = codeSyntax.querySelector('code');
    if (!codeEl) {
      codeEl = document.createElement('code');
      codeSyntax.innerHTML = '';
      codeSyntax.appendChild(codeEl);
    }
    codeEl.className = `language-${prismLang}`;
    codeEl.textContent = codeText;
    if (Prism.highlightElement) {
      Prism.highlightElement(codeEl);
    }
  }

  function populateLanguageDropdown(map) {
    if (!templateLangSel) return;
    templateLangSel.innerHTML = '';
    const ids = Object.keys(map).sort();
    ids.forEach(id => {
      const opt = document.createElement('option');
      opt.value = id;
      const label = TEMPLATE_LABELS[id] || (id === 'practice' ? 'Practice (Symbols)' : id.toUpperCase());
      opt.textContent = label;
      templateLangSel.appendChild(opt);
    });
  }

  function populateLevelDropdown(map, langId) {
    if (!templateLevelSel) return;
    templateLevelSel.innerHTML = '';
    const levels = map[langId] || {};
    Object.keys(levels).forEach(levelId => {
      const label = levelId[0].toUpperCase() + levelId.slice(1).replace('-', ' ');
      const opt = document.createElement('option');
      opt.value = levelId;
      opt.textContent = label;
      templateLevelSel.appendChild(opt);
    });
  }

  function convertApiTemplatesToMap(apiData) {
    // apiData: { languages: [ { name, levels: [ { level: 'files', snippets: [ { title, code } ] } ] } ] }
    const map = {};
    TEMPLATE_LABELS = {};
    (apiData.languages || []).forEach(lang => {
      const langId = lang.name;
      if (!langId) return;
      TEMPLATE_LABELS[langId] = langId.toUpperCase();
      const filesLevel = (lang.levels || []).find(l => Array.isArray(l.snippets));
      const levelsMap = {};
      if (filesLevel) {
        (filesLevel.snippets || []).forEach(sn => {
          if (sn && typeof sn.title === 'string' && typeof sn.code === 'string') {
            levelsMap[sn.title] = sn.code;
          }
        });
      }
      map[langId] = levelsMap;
    });
    return map;
  }

  function convertStaticJsonToMap(data) {
    // static/templates.json format used previously
    const map = {};
    TEMPLATE_LABELS = {};
    (data.languages || []).forEach(lang => {
      const langId = lang.id;
      if (!langId) return;
      TEMPLATE_LABELS[langId] = lang.label || langId.toUpperCase();
      map[langId] = map[langId] || {};
      (lang.levels || []).forEach(lvl => {
        if (lvl.id && typeof lvl.snippet === 'string') {
          map[langId][lvl.id] = lvl.snippet;
        }
      });
    });
    return map;
  }

  async function loadTemplates() {
    // 1) Try filesystem API
    try {
      const res = await fetch('/api/templates', { cache: 'no-cache' });
      if (res.ok) {
        const data = await res.json();
        const map = convertApiTemplatesToMap(data);
        if (Object.keys(map).length) {
          TEMPLATE_MAP = map;
          populateLanguageDropdown(map);
          const firstLang = Object.keys(map)[0];
          populateLevelDropdown(map, firstLang);
          return;
        }
      }
    } catch (_) {}

    // 2) Fallback to static JSON file
    try {
      const res = await fetch('static/templates.json', { cache: 'no-cache' });
      if (res.ok) {
        const data = await res.json();
        const map = convertStaticJsonToMap(data);
        if (Object.keys(map).length) {
          TEMPLATE_MAP = map;
          populateLanguageDropdown(map);
          const firstLang = Object.keys(map)[0];
          populateLevelDropdown(map, firstLang);
          return;
        }
      }
    } catch (_) {}

    // 3) Final fallback to built-in
    TEMPLATE_MAP = CODE_TEMPLATES;
    TEMPLATE_LABELS = Object.fromEntries(Object.keys(TEMPLATE_MAP).map(id => [id, id.toUpperCase()]));
    populateLanguageDropdown(TEMPLATE_MAP);
    populateLevelDropdown(TEMPLATE_MAP, Object.keys(TEMPLATE_MAP)[0]);
  }

  /**
   * Plays a short beep sound for error feedback
   * Uses Web Audio API to generate a 440Hz tone for 100ms
   */
  function beep() {
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const osc = audioCtx.createOscillator();
    osc.frequency.value = 440;  // A4 note frequency
    osc.connect(audioCtx.destination);
    osc.start();
    setTimeout(() => osc.stop(), 100);  // 100ms duration
  }

  /**
   * Start button click handler
   * Initializes the typing test with the code from the input textarea
   */
  startBtn.addEventListener('click', function() {
    // Normalize line endings to \n for cross-platform compatibility
    code = codeInput.value.replace(/\r\n|\r/g, '\n');
    if (!code) return;  // Don't start if there's no code
    
    // Hide input elements and show test interface
    codeInput.style.display = 'none';
    startBtn.style.display = 'none';
    restartBtn.style.display = 'none';
    stopBtn.classList.remove('hidden');
    typingTest.classList.remove('hidden');
    codeDisplay.classList.add('typing-mode'); // Add class for increased font size
    // Render syntax background with Prism and sync scroll
    renderSyntaxBackground(code, templateLangSel ? templateLangSel.value : '');
    codeDisplay.onscroll = () => { if (codeSyntax) codeSyntax.scrollTop = codeDisplay.scrollTop; };
    
    // Create spans for each character to enable individual styling (fast render)
    codeDisplay.innerHTML = '';
    const frag = document.createDocumentFragment();
    spansCache = [];
    const langId = templateLangSel ? templateLangSel.value : '';
    const skipMask = buildSkipMaskForComments(code, langId);
    for (let i=0; i<code.length; i++) {
      const c = code[i];
      const span = document.createElement('span');
      span.dataset.char = c;  // Store original character for comparison
      if (c === '\n') {
        span.innerHTML = '⏎<br>';  // Show newline character with visual indicator
      } else {
        span.textContent = c;
      }
      if (skipMask[i]) { span.dataset.skip = '1'; span.classList.add('commentSkip'); }
      spansCache.push(span);
      frag.appendChild(span);
    }
    codeDisplay.appendChild(frag);
    
    // Reset test state
    index = 0; 
    startedTyping = false; 
    errorState = false;
    errorCount = 0; 
    backspaceCount = 0;
    
    // Reset UI elements
    dateElem.textContent = new Date().toLocaleString();
    timerElem.textContent = '0.0';
    liveWpmElem.textContent = '0.0';
    progressBar.style.width = '0%';
    
    // Auto-skip initial skipped spans, then highlight
    advanceOverSkips(spansCache);
    highlightActive();
    codeDisplay.focus();
  });

  // Wire dropdown change handlers
  if (templateLangSel) {
    templateLangSel.addEventListener('change', () => {
      if (!TEMPLATE_MAP) return;
      populateLevelDropdown(TEMPLATE_MAP, templateLangSel.value);
    });
  }

  if (templateApplyBtn) {
    templateApplyBtn.addEventListener('click', () => {
      if (!TEMPLATE_MAP) return;
      const langId = templateLangSel.value;
      const levelId = templateLevelSel.value;
      const tpl = TEMPLATE_MAP[langId]?.[levelId];
      if (tpl) {
        codeInput.value = tpl;
        codeInput.focus();
      }
    });
  }

  // Initialize dynamic templates
  loadTemplates();

  // Stop button click handler
  stopBtn.addEventListener('click', stopTest);

  /**
   * Restart button click handler
   * Restarts the typing test with the same code
   */
  restartBtn.addEventListener('click', function() {
    if (!code) return;  // Don't restart if there's no code
    
    // Hide input elements and show test interface
    codeInput.style.display = 'none';
    startBtn.style.display = 'none';
    restartBtn.style.display = 'none';
    stopBtn.classList.remove('hidden');
    typingTest.classList.remove('hidden');
    codeDisplay.classList.add('typing-mode'); // Add class for increased font size
    
    // Rebuild spans (fast render) and refresh cache
    codeDisplay.innerHTML = '';
    const frag = document.createDocumentFragment();
    spansCache = [];
    for (const c of code) {
      const span = document.createElement('span');
      span.dataset.char = c;  // Store original character for comparison
      if (c === '\n') {
        span.innerHTML = '⏎<br>';  // Show newline character with visual indicator
      } else {
        span.textContent = c;
      }
      spansCache.push(span);
      frag.appendChild(span);
    }
    codeDisplay.appendChild(frag);
    
    // Reset test state
    index = 0; 
    startedTyping = false; 
    errorState = false;
    errorCount = 0; 
    backspaceCount = 0;
    
    // Reset UI elements
    dateElem.textContent = new Date().toLocaleString();
    timerElem.textContent = '0.0';
    liveWpmElem.textContent = '0.0';
    progressBar.style.width = '0%';
    
    // Set initial cursor position and focus
    highlightActive();
    codeDisplay.focus();
  });

  codeDisplay.addEventListener('keydown', function(e) {
    if (summaryModal.classList.contains('show')) {
      if (e.key === 'Enter') closeModal();
      return;
    }
    const ignore = ['Shift','Control','Alt','Meta','AltGraph','CapsLock','Tab','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'];

    if (ignore.includes(e.key)) return;
    e.preventDefault();
    const spans = spansCache;
    // Always advance over any skipped (comment) spans before processing input
    advanceOverSkips(spans);
    if (!startedTyping) {
      startedTyping = true;
      startTime = Date.now();
      timerInterval = setInterval(() => {
        const elapsed = (Date.now() - startTime) / 1000;
        timerElem.textContent = elapsed.toFixed(1);
        const liveWpm = elapsed>0 ? ((index/5)/(elapsed/60)) : 0;
        liveWpmElem.textContent = liveWpm.toFixed(1);
      }, 100);
    }
    if (errorState) {
      if (e.key === 'Backspace') {
        spans[index].classList.remove('errorCursor');
        errorState = false;
        // Count backspace used to correct errors
        backspaceCount++;
        // Immediately highlight the current position after error correction
        highlightActive();
      }
      return;
    }
    if (e.key === 'Backspace') {
      if (index > 0) {
        index--;
        spans[index].classList.remove('correct');
        backspaceCount++;
        progressBar.style.width = (index/spans.length*100)+'%';
      }
      highlightActive();
      return;
    }
    const current = spans[index]?.dataset.char;
    // Skip any comment spans encountered at current position
    advanceOverSkips(spans);
    const current2 = spans[index]?.dataset.char;
    if (e.key === ' ' && current2===' ') {
      while(index<spans.length && spans[index].dataset.char===' ') {
        spans[index].classList.add('correct');
        index++;
      }
    } else if (e.key==='Enter' && current2==='\n') { spans[index].classList.add('correct'); index++;
    } else if (e.key.length===1 && e.key===current2) { spans[index].classList.add('correct'); index++;
    } else { spans[index].classList.add('errorCursor'); errorState=true; errorCount++; beep(); }
    // After moving forward, skip any subsequent comment spans
    advanceOverSkips(spans);
    progressBar.style.width=(index/spans.length*100)+'%';
    highlightActive();
    if (index===spans.length) finishTest();
  });

  function highlightActive() {
    const spans = spansCache;
    spans.forEach(s=>s.classList.remove('active'));
    if (spans[index] && !spans[index].classList.contains('errorCursor')) {
      spans[index].classList.add('active');
      
      // Auto-scrolling functionality
      if (spans[index]) {
        // Find the current line element (parent <br> or the pre itself)
        let currentLine = spans[index];
        let lineCount = 0;
        let currentLineTop = 0;
        
        // Count lines and find the current line's position
        const allSpans = spansCache;
        let lineStarts = [0]; // Track the start index of each line
        
        // Find all line breaks to determine line positions
        allSpans.forEach((span, i) => {
          if (span.innerHTML.includes('<br>') && i < allSpans.length - 1) {
            lineStarts.push(i + 1);
          }
        });
        
        // Find which line our current index is on
        let currentLineIndex = 0;
        for (let i = 0; i < lineStarts.length; i++) {
          if (index >= lineStarts[i]) {
            currentLineIndex = i;
          } else {
            break;
          }
        }
        
        // If we're at least 3 lines down, scroll to keep current line and 2 lines above visible
        if (currentLineIndex >= 2) {
          // Find the element at the start of the line 2 lines above current
          const targetLineIndex = lineStarts[currentLineIndex - 2];
          if (allSpans[targetLineIndex]) {
            // Scroll to position this element near the top of the viewport
            allSpans[targetLineIndex].scrollIntoView({ block: 'start', behavior: 'smooth' });
          }
        }
      }
    }
  }

  function finishTest() {
    clearInterval(timerInterval);
    const elapsed = (Date.now()-startTime)/1000;
    const wpmVal = Math.round((index/5)/(elapsed/60));
    document.getElementById('modalWpm').textContent = wpmVal;
    document.getElementById('modalErrors').textContent = errorCount;
    document.getElementById('modalBackspaces').textContent = backspaceCount;
    summaryModal.classList.add('show');
    
    // Update chart
    chart.data.labels.push(new Date().toLocaleDateString());
    chart.data.datasets[0].data.push(wpmVal);
    chart.update();
    
    // Save results without reloading the page
    fetch('/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({wpm:wpmVal,errors:errorCount,backspaces:backspaceCount})})
      .then(response => response.json())
      .then(data => {
        // Update the history table with the new entry
        const historyTable = document.querySelector('#historyTable tbody');
        if (historyTable) {
          const newRow = document.createElement('tr');
          newRow.innerHTML = `
            <td>${data.timestamp}</td>
            <td>${wpmVal}</td>
            <td>${errorCount}</td>
            <td>${backspaceCount}</td>
          `;
          
          // Insert at the beginning of the table
          if (historyTable.firstChild) {
            historyTable.insertBefore(newRow, historyTable.firstChild);
          } else {
            historyTable.appendChild(newRow);
          }
          
          // Remove the last row if there are more than 20 entries
          if (historyTable.children.length > 20) {
            historyTable.removeChild(historyTable.lastChild);
          }
        }
      });
  }

  function stopTest() {
    clearInterval(timerInterval);
    typingTest.classList.add('hidden');
    codeDisplay.classList.remove('typing-mode'); // Remove increased font size class
    codeInput.style.display = 'block';
    startBtn.style.display = 'inline-block';
    stopBtn.classList.add('hidden');
    restartBtn.style.display = 'inline-block';
    progressBar.style.width = '0%';
    timerElem.textContent = '0.0';
    liveWpmElem.textContent = '0.0';
    startedTyping = false;
    errorState = false;
  }

  function closeModal() {
    summaryModal.classList.remove('show');
    typingTest.classList.add('hidden');
    codeDisplay.classList.remove('typing-mode'); // Remove increased font size class
    codeInput.style.display = 'block';
    startBtn.style.display = 'inline-block';
    stopBtn.classList.add('hidden');
    restartBtn.style.display = 'inline-block';
    progressBar.style.width = '0%';
    timerElem.textContent = '0.0';
    liveWpmElem.textContent = '0.0';
    clearInterval(timerInterval);
  }

  document.getElementById('closeModal').addEventListener('click', closeModal);

  // Chart initialization only (table is now rendered by Flask template)
  (function(){
    const sorted = historyData.slice().sort((a,b)=>new Date(a.timestamp)-new Date(b.timestamp));
    const labels = sorted.map(i=>new Date(i.timestamp).toLocaleDateString());
    const data = sorted.map(i=>i.wpm);
    const ctx=document.getElementById('wpmChart');
    chart=new Chart(ctx,{
      type:'line',
      data:{
        labels,
        datasets:[{
          label:'WPM',
          data,
          fill: true,
          backgroundColor: 'rgba(100, 181, 246, 0.1)', // Light blue with transparency
          borderColor: '#64B5F6', // Light blue
          borderWidth: 2,
          tension: 0.3,
          pointRadius: 5,
          pointHoverRadius: 8,
          pointBackgroundColor: '#64B5F6',
          pointBorderColor: '#1976D2',
          pointBorderWidth: 2,
          pointHoverBackgroundColor: '#42A5F5',
          pointHoverBorderColor: '#1565C0',
          pointHoverBorderWidth: 3
        }]
      },
      options:{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          tooltip: {
            enabled: true,
            backgroundColor: 'rgba(30, 30, 46, 0.9)',
            titleColor: '#e0e0e0',
            bodyColor: '#e0e0e0',
            borderColor: '#64B5F6',
            borderWidth: 1,
            cornerRadius: 8,
            displayColors: false,
            callbacks: {
              title: function(context) {
                return `Date: ${context[0].label}`;
              },
              label: function(context) {
                return `WPM: ${context.parsed.y}`;
              }
            }
          },
          legend: {
            labels: {
              color: '#e0e0e0'
            }
          }
        },
        scales: {
          x: {
            ticks: {
              color: '#e0e0e0'
            },
            grid: {
              color: 'rgba(224, 224, 224, 0.1)'
            }
          },
          y: {
            ticks: {
              color: '#e0e0e0'
            },
            grid: {
              color: 'rgba(224, 224, 224, 0.1)'
            }
          }
        }
      }
    });
  })();
});