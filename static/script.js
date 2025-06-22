document.addEventListener('DOMContentLoaded', () => {
  const codeInput = document.getElementById('codeInput');
  const startBtn = document.getElementById('startBtn');
  const restartBtn = document.getElementById('restartBtn');
  const stopBtn = document.getElementById('stopBtn');
  const codeDisplay = document.getElementById('codeDisplay');
  const typingTest = document.getElementById('typingTest');
  const dateElem = document.getElementById('date');
  const timerElem = document.getElementById('timer');
  const liveWpmElem = document.getElementById('liveWpm');
  const progressBar = document.getElementById('progressBar');
  const summaryModal = document.getElementById('summaryModal');

  let code = '', index = 0, startTime = null;
  let startedTyping = false, errorState = false;
  let errorCount = 0, backspaceCount = 0, timerInterval = null;
  let chart = null;
  const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

  function beep() {
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const osc = audioCtx.createOscillator();
    osc.frequency.value = 440;
    osc.connect(audioCtx.destination);
    osc.start();
    setTimeout(() => osc.stop(), 100);
  }

  startBtn.addEventListener('click', function() {
    code = codeInput.value.replace(/\r\n|\r/g, '\n');
    if (!code) return;
    codeInput.style.display = 'none';
    startBtn.style.display = 'none';
    restartBtn.style.display = 'none';
    stopBtn.classList.remove('hidden');
    typingTest.classList.remove('hidden');
    codeDisplay.classList.add('typing-mode'); // Add class for increased font size
    codeDisplay.innerHTML = '';
    code.split('').forEach(c => {
      const span = document.createElement('span');
      span.dataset.char = c;
      if (c === '\n') {
        span.innerHTML = '⏎<br>'; 
      } else {
        span.textContent = c;
      }
      codeDisplay.appendChild(span);
    });
    index = 0; startedTyping = false; errorState = false;
    errorCount = 0; backspaceCount = 0;
    dateElem.textContent = new Date().toLocaleString();
    timerElem.textContent = '0.0';
    liveWpmElem.textContent = '0.0';
    progressBar.style.width = '0%';
    highlightActive();
    codeDisplay.focus();
  });

  stopBtn.addEventListener('click', stopTest);

  restartBtn.addEventListener('click', function() {
    if (!code) return;
    codeInput.style.display = 'none';
    startBtn.style.display = 'none';
    restartBtn.style.display = 'none';
    stopBtn.classList.remove('hidden');
    typingTest.classList.remove('hidden');
    codeDisplay.classList.add('typing-mode'); // Add class for increased font size
    codeDisplay.innerHTML = '';
    code.split('').forEach(c => {
      const span = document.createElement('span');
      span.dataset.char = c;
      if (c === '\n') {
        span.innerHTML = '⏎<br>'; 
      } else {
        span.textContent = c;
      }
      codeDisplay.appendChild(span);
    });
    index = 0; startedTyping = false; errorState = false;
    errorCount = 0; backspaceCount = 0;
    dateElem.textContent = new Date().toLocaleString();
    timerElem.textContent = '0.0';
    liveWpmElem.textContent = '0.0';
    progressBar.style.width = '0%';
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
    const spans = codeDisplay.querySelectorAll('span');
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
    const spans = codeDisplay.querySelectorAll('span');
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
        const allSpans = Array.from(codeDisplay.querySelectorAll('span'));
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