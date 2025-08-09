# Code Typing Trainer

A web‑based typing trainer focused on practicing **programming code** rather than plain text.  
Built with **Flask**, vanilla **JavaScript**, and lightweight CSS for a dark theme with a yellow accent.

---

## What’s New (2025)

- **Filesystem templates** under `templates/<language>/` with dynamic picker (`/api/templates`).
- **STM32/HAL C** samples extended to 16 files; each function is its own template. `templates/stm32/`
- **VHDL** pack with 10+ practical templates. `templates/vhdl/`
- **Comment skipping**: comments are preserved in templates but skipped during typing (frontend).
- **Modern typing UI**:
  - Optional line numbers (Ln), current line highlight (Line), and a non‑invasive syntax background (Syntax).
  - Classic yellow block for the active character.
  - Smooth scrolling keeps context lines visible.
  - Skipped comment regions are dimmed consistently.
- **Toggle persistence**: Ln/Syntax/Line states are saved in `localStorage` per browser.
- **Portable browser support**: prefers `Chromium/chrome.exe` or `Firefox/FirefoxPortable.exe` if present.

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

```text
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
└── templates/
    ├── c/                 # C examples
    ├── python/            # Python examples
    ├── stm32/             # STM32/HAL C templates
    └── vhdl/              # VHDL templates
```

---

## Quick Start

```bash
# 1. Extract project
cd code_typing_trainer

# 2. Install dependencies (minimal)
pip install -r requirements-min.txt

# 3. Launch (auto‑opens browser)
python app.py
```

The server runs on **http://127.0.0.1:5000** (port configurable in `app.py`).

Note: `requirements.txt` in this repo contains a legacy, broad dependency set for historical experiments.
For this app, use the minimal file `requirements-min.txt`.

### Windows portable EXE (no Python needed)

If you downloaded `code_web_trainer.zip` from the Releases page (v1.0 or later):

1. Extract the zip anywhere (e.g., `Downloads/Code_web_trainer/`).
2. Run `code_web_trainer.exe`.
3. Your default browser should open at `http://127.0.0.1:5000/`.
4. To stop, close the app window. No installation required.

---

## Usage

1. Paste or type the code you want to practice in the textarea.  
2. Click **Start**. The textarea hides, the code appears with a yellow block cursor and increased font size.  
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
| `app.py`              | `SETTINGS_FILE` path, browser auto‑open logic, history retention, APIs. |
| `static/script.js`    | Key bindings, sound toggle (`beep()`), toggles, syntax background, and live calculations. |
| `requirements-min.txt`| Minimal dependencies for this app. |

---

## Customisation Tips

* **Theme** – tweak CSS variables in `static/style.css` (`--bg`, `--accent`…).  
* **Sound** – comment out or adjust `beep()` in `static/script.js`.  
* **History limit** – change `history[-30:]` slice in `app.py`.  
* **Port** – change `app.run(debug=True)` in `app.py`.  

### UI Toggles

The control row includes three toggles:

- **Ln**: show/hide line numbers in the gutter.
- **Syntax**: enable a passive Prism.js background layer behind the spans.
- **Line**: highlight the current line.  

Your toggle choices are persisted in `localStorage` and restored on reload.

### Prism.js & Security (SRI)

- Prism resources are loaded lazily when the **Syntax** toggle is on.
- We include `crossorigin="anonymous"` and `referrerpolicy="no-referrer"` on dynamic includes.
- You can optionally enable Subresource Integrity (SRI) by filling the hashes in `static/script.js` under `PRISM_SRI`:

```js
const PRISM_SRI = {
  core: '',
  clike: '',
  c: '',
  python: '',
  markup: '',
  themeTomorrow: ''
};
```

How to compute SRI (example):

```bash
# Download file and compute SHA384 base64
curl -sL https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-core.min.js | \
  openssl dgst -sha384 -binary | openssl base64 -A
# Prefix with 'sha384-' and paste into PRISM_SRI.core
```

Alternatively, self‑host Prism assets in `static/` and avoid CDN entirely.

### Template Upload (Admin)

- Endpoint: `POST /api/upload_template` (localhost only).
- Fields: `language` (folder name), `file` (the code file).
- Language is strictly validated: only letters, digits, `-`, `_` (1–30 chars). File name is sanitized via `werkzeug.utils.secure_filename`.

---

## Contributing

1. Fork / clone repo.  
2. Create feature branch (`git checkout -b feature/<name>`).  
3. Commit & push, then open a PR.

---

## Publishing a GitHub Release (step‑by‑step)

### Using the GitHub web UI

1. **Push changes** to `main` (or your release branch).
2. (Optional) **Create a tag** locally: `git tag v1.0.1 && git push --tags`.
3. **Build your artifact** (e.g., Windows EXE) and zip it as `code_web_trainer.zip`.
4. On GitHub, go to your repo → **Releases** → **Draft a new release**.
5. **Choose a tag** (select existing or type a new like `v1.0.1`), set target branch.
6. Add a **Release title** (e.g., `v1.0.1`) and **Notes/Changelog**.
7. **Upload assets**: drag `code_web_trainer.zip` (and optionally checksums) into the assets area.
8. Click **Publish release**.

### Using GitHub CLI (optional)

```bash
# Install GitHub CLI first: https://cli.github.com/
# Login once
gh auth login

# Create release with asset (from repo root)
gh release create v1.0.1 code_web_trainer.zip \
  --title "v1.0.1" \
  --notes "Changelog: fixes, UI polish, SRI, upload hardening"
```

## License

GNU General Public License v3.0 (GPL-3.0) – This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

See [GNU GPL-3.0](https://www.gnu.org/licenses/gpl-3.0.en.html) for full license details.

---

© 2025 Ahmad Asmandar - [ahmad.asmandar@gmx.com](mailto:ahmad.asmandar@gmx.com)
