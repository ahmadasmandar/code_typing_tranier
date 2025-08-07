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
  const dateElem = document.getElementById('date');        // Element for displaying current date
  const timerElem = document.getElementById('timer');      // Element for displaying elapsed time
  const liveWpmElem = document.getElementById('liveWpm');  // Element for displaying live WPM
  const progressBar = document.getElementById('progressBar'); // Progress indicator
  const summaryModal = document.getElementById('summaryModal'); // Results modal

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

  // Dynamically load templates from JSON and render buttons
  const templateContainer = document.getElementById('templateRow');

  function renderTemplateButtons(sourceTemplates) {
    if (!templateContainer) return;
    templateContainer.innerHTML = '';
    const frag = document.createDocumentFragment();

    Object.entries(sourceTemplates).forEach(([langId, levels]) => {
      const group = document.createElement('div');
      group.className = 'template-group';

      const label = document.createElement('div');
      label.className = 'template-label';
      label.textContent = langId.toUpperCase();
      group.appendChild(label);

      ['beginner','intermediate','advanced'].forEach(levelId => {
        if (!levels[levelId]) return;
        const btn = document.createElement('button');
        btn.className = 'template-btn';
        btn.dataset.lang = langId;
        btn.dataset.level = levelId;
        btn.textContent = `${langId.toUpperCase()} · ${levelId[0].toUpperCase()}${levelId.slice(1)}`;
        btn.addEventListener('click', () => {
          const tpl = sourceTemplates[langId]?.[levelId] || '';
          if (tpl) {
            codeInput.value = tpl;
            codeInput.focus();
          }
        });
        group.appendChild(btn);
      });

      frag.appendChild(group);
    });

    templateContainer.appendChild(frag);
  }

  async function loadTemplatesJSON() {
    try {
      const res = await fetch('static/templates.json', { cache: 'no-cache' });
      if (!res.ok) throw new Error('Failed to load templates.json');
      const data = await res.json();
      // Convert JSON structure to the flat map used by renderer
      const map = {};
      (data.languages || []).forEach(lang => {
        const langId = lang.id;
        if (!langId) return;
        map[langId] = map[langId] || {};
        (lang.levels || []).forEach(lvl => {
          if (lvl.id && typeof lvl.snippet === 'string') {
            map[langId][lvl.id] = lvl.snippet;
          }
        });
      });
      if (Object.keys(map).length) {
        renderTemplateButtons(map);
        return;
      }
      // fallback if empty
      renderTemplateButtons(CODE_TEMPLATES);
    } catch (e) {
      // Fallback to built-in templates if fetch/parse fails
      renderTemplateButtons(CODE_TEMPLATES);
    }
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
    
    // Create spans for each character to enable individual styling (fast render)
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

  // Initialize dynamic templates
  loadTemplatesJSON();

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
    if (e.key === ' ' && current===' ') {
      while(index<spans.length && spans[index].dataset.char===' ') {
        spans[index].classList.add('correct');
        index++;
      }
    } else if (e.key==='Enter' && current==='\n') { spans[index].classList.add('correct'); index++;
    } else if (e.key.length===1 && e.key===current) { spans[index].classList.add('correct'); index++;
    } else { spans[index].classList.add('errorCursor'); errorState=true; errorCount++; beep(); }
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