
# Code Typing Trainer

A web‑based typing trainer focused on practicing **programming code** rather than plain text.  
Built with **Flask**, vanilla **JavaScript**, and lightweight CSS for a dark theme with a yellow accent.

![Code Typing Trainer Screenshot](static/screenshot.png)

---

## Key Features

| Category | Details |
|---|---|
| **Code‑specific training** | Handles indentation, whitespace sequences, and preserves newlines (displayed as ⏎). |
| **Accurate metrics** | Live WPM calculation, error count, backspace count, progress bar, and total time. |
| **Error handling** | Immediate visual feedback (green for correct, yellow cursor for errors) and optional beep. |
| **Stop / Restart** | Stop button aborts a session without reloading, Restart re‑uses the same input. |
| **History & Analytics** | Results persisted to `train_settings.json`, displayed in a history table and plotted with Chart.js. |
| **Single input workflow** | One textarea for code entry that hides on start; typing field appears in the same space. |
| **Cross‑platform** | Tested on modern Chrome & Firefox. Ignores AltGr for German keyboard compatibility. |
| **About page** | Information about the creator with professional background and contact details. |

---

## Folder Structure

```
code_typing_trainer/
│
├── app.py                  # Flask backend
├── requirements.txt        # Python deps
├── train_settings.json     # Persisted results/history
│
├── templates/
│   ├── index.html          # Main page
│   └── about.html          # About page
│
└── static/
    ├── style.css           # Dark theme + layout
    ├── script.js           # Front‑end logic
    ├── fav.ico             # Favicon
    └── uploads/            # Profile image storage
        └── .gitkeep        # Placeholder for directory structure
```

---

## Quick Start

```bash
# 1. Extract project
cd code_typing_trainer

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch (auto‑opens browser)
python app.py
```

The server runs on **http://127.0.0.1:5000** (port configurable in `app.py`).

---

## Usage

1. Paste or type the code you want to practice in the textarea.  
2. Click **Start**. The textarea hides, the code appears with a yellow cursor and increased font size.  
3. Type. On mistakes the current char turns red and a beep sounds (optional).  
4. Press **Stop** any time or type to the end to finish.  
5. A summary modal shows results; press **Enter** or **Close** to dismiss.  
6. Review your history and WPM chart to track improvement over time.
7. Click the **About** link to learn more about the creator.

---

## Configuration

| File | Purpose |
|---|---|
| `train_settings.json` | Auto‑created; stores an array `history[]` with recent results *(timestamp, wpm, errors, backspaces)*. |
| `app.py`              | `SETTINGS_FILE` path, browser auto‑open logic, history retention (`history[-30:]`). |
| `static/script.js`    | Key bindings, sound toggle (`beep()`), and live calculations. |

---

## Customisation Tips

* **Theme** – tweak CSS variables in `static/style.css` (`--bg`, `--accent`…).  
* **Sound** – comment out or adjust `beep()` in `static/script.js`.  
* **History limit** – change `history[-30:]` slice in `app.py`.  
* **Port** – change `app.run(debug=True)` in `app.py`.  

---

## Contributing

1. Fork / clone repo.  
2. Create feature branch (`git checkout -b feature/<name>`).  
3. Commit & push, then open a PR.

---

## License

GNU General Public License v3.0 (GPL-3.0) – This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

See [GNU GPL-3.0](https://www.gnu.org/licenses/gpl-3.0.en.html) for full license details.

---

© 2025 Ahmad Asmandar - [ahmad.asmandar@gmx.com](mailto:ahmad.asmandar@gmx.com)
