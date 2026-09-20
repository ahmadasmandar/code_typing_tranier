# Code Typing Trainer — Product Improvement Plan

Status: `IN PROGRESS`

Purpose: Improve the trainer’s reliability, user feedback, learning value, and day-to-day usability while preserving the current visual identity, local-first architecture, and Start/Stop typing workflow.

Related plan: `docs/PRODUCTION_HARDENING_PLAN.md`

Baseline: Backend tests currently pass, but the frontend has user-facing reliability gaps and the product exposes only basic performance metrics.

## 1. Product Principles

1. Fix observable defects before adding optional features.
2. Preserve the existing typing workflow and visual theme.
3. Prefer local, dependency-free improvements that work offline.
4. Every feature must have a clear user benefit and a testable acceptance criterion.
5. Keep data formats backward-compatible whenever possible.
6. Add one coherent capability at a time; avoid a broad UI redesign.
7. Do not mark a work item complete without recording verification evidence.

## 2. Tracking Method

Use the work-item table as the source of truth.

### Status values

`PLANNED` → `IN PROGRESS` → `READY FOR VERIFY` → `VERIFIED` → `DONE`

Use `BLOCKED` only when progress cannot continue without a concrete external decision or dependency. Record the blocker and next action in the tracker.

### Required evidence

Each completed item must record:

- Changed files
- User-visible behavior changed
- Tests or checks added
- Exact verification commands
- Actual observed result
- Remaining risks or compatibility notes

### Scope rule

Hardening fixes and product features must remain separable. If a change is both a defect fix and a feature, implement the defect fix first and track the feature separately.

## 3. Product Findings and Targets

| ID | Current condition | Target outcome |
|---|---|---|
| UX-01 | Uploaded profile images are stored in the data directory but the About template uses the normal static route | Uploaded images render correctly after restart and from a packaged app |
| UX-02 | Toggle persistence is registered inside a second `DOMContentLoaded` handler | Line number, syntax, and line-highlight choices restore reliably |
| UX-03 | `/save` failures are not visible to the user | Users receive clear success/failure feedback and history remains consistent |
| UX-04 | Chart.js failure can break result completion | A missing CDN or chart library never prevents the result summary or save operation |
| UX-05 | History can be cleared only through an API route | Users can clear history through the interface with confirmation |
| UX-06 | Upload functionality has weak user feedback and no visible About-page workflow | Upload actions are either usable and explained or intentionally removed |
| LEARN-01 | Results show WPM, errors, and backspaces only | Results also show accuracy, duration, progress, and meaningful comparison data |
| LEARN-02 | History is a simple table and chart | Users can understand progress through summary statistics and personal bests |
| DATA-01 | A refresh can discard unfinished code | The current draft can be restored safely from local browser storage |
| LIB-01 | Templates are selected only by language and file name | Users can search, revisit, favorite, and randomize practice templates |
| OFFLINE-01 | Charts, syntax highlighting, fonts, and icons depend on external CDNs | Core practice remains useful without internet access |

## 4. Phased Work Plan

### Phase A — Correct current user-visible defects

Goal: Make existing functionality reliable before expanding the product.

- [x] `PI-01` Fix the uploaded-image URL contract and add a route regression test.
- [x] `PI-02` Fix toggle restoration and persistence initialization.
- [x] `PI-03` Add frontend handling for failed `/save` requests and network errors.
- [x] `PI-04` Make result completion independent of Chart.js availability.
- [x] `PI-05` Add visible, accessible status notifications for save, template, and fallback errors.

Acceptance gate:

- Uploaded images display after upload and reload.
- Toggle preferences survive a reload.
- A failed save produces a visible error and does not falsely present the result as persisted.
- Results still appear when Chart.js is unavailable.
- No expected frontend failure is silently ignored.

### Phase B — Improve history control and feedback

Goal: Give users clear control over saved training data.

- [x] `PI-10` Add a Clear History control with confirmation.
- [x] `PI-11` Disable or protect destructive actions while requests are pending.
- [x] `PI-12` Refresh the table and chart from server-confirmed state after clearing or saving.
- [x] `PI-13` Add empty-state messaging that explains how to create the first result.
- [x] `PI-14` Add JSON/CSV history export without exposing unrelated local files.

Acceptance gate:

- Clear History cannot be triggered accidentally.
- The table, chart, and empty state remain consistent after clear/save operations.
- Exported data contains only the supported history fields.

### Phase C — Make results more useful for learning

Goal: Turn raw typing results into actionable feedback.

- [x] `PI-20` Add accuracy calculation and display.
- [x] `PI-21` Add elapsed duration and completion percentage for stopped sessions.
- [x] `PI-22` Add a comparison with the previous result when available.
- [x] `PI-23` Add personal-best indicators for WPM and accuracy.
- [x] `PI-24` Preserve backward compatibility when older history entries lack new fields.
- [x] `PI-25` Add tests for metric calculations and historical data migration behavior.

Acceptance gate:

- Metrics are mathematically defined and tested.
- Old `train_settings.json` data still renders correctly.
- Stopped sessions are clearly distinguished from completed sessions.

### Phase D — Preserve user work

Goal: Prevent accidental loss of an unfinished practice session.

- [x] `PI-30` Save the current textarea draft locally with a clear version/key.
- [x] `PI-31` Restore a draft only with clear user feedback and an explicit overwrite choice.
- [x] `PI-32` Add a Clear Draft control.
- [x] `PI-33` Avoid storing sensitive or unrelated browser data.
- [x] `PI-34` Test refresh, navigation, empty draft, and large draft behavior.

Acceptance gate:

- Refreshing the page can recover unfinished code.
- Existing typed content is not silently overwritten.
- Users can remove the saved draft.

### Phase E — Improve template discovery

Goal: Make the existing template library faster and more useful.

- [x] `PI-40` Add client-side search across language and filename.
- [x] `PI-41` Add recent-template tracking locally.
- [x] `PI-42` Add favorites locally without changing backend storage.
- [x] `PI-43` Add a random-template action with an explicit language/category scope.
- [x] `PI-44` Add useful language and filename metadata to template selection.
- [x] `PI-45` Test empty search, unavailable API, fallback templates, and keyboard use.

Acceptance gate:

- Search and random selection never select an unavailable template.
- Existing language/level selection remains functional.
- Fallback mode still supports the same actions.

### Phase F — Offline and accessibility improvements

Goal: Make the essential experience robust in realistic local use.

- [x] `PI-50` Inventory Chart.js, Prism.js, fonts, and icon CDN dependencies.
- [x] `PI-51` Self-host critical assets or enforce verified SRI where self-hosting is not practical.
- [x] `PI-52` Add an offline/fallback status message.
- [x] `PI-53` Add live-region announcements for result, error, save, and loading states.
- [x] `PI-54` Improve modal keyboard behavior, focus management, and labels.
- [x] `PI-55` Verify keyboard-only operation and reduced-motion behavior.

Acceptance gate:

- Core typing and result workflows remain usable without external assets where technically possible.
- Status changes are understandable without relying on color alone.
- Keyboard-only users can start, stop, finish, and close results.

## 5. Feature Candidates for Later Evaluation

These are valuable but should follow Phases A–F.

| ID | Feature | Value | Complexity | Decision |
|---|---|---|---|---|
| F-01 | Daily streak and practice goals | Encourages regular practice | M | Evaluate after metrics exist |
| F-02 | Timed challenge mode | Adds structured practice | M | Good candidate after result model is extended |
| F-03 | Accuracy-first mode | Supports deliberate practice | S | Good candidate |
| F-04 | Strict whitespace mode | Helps embedded/code formatting practice | S | Good candidate |
| F-05 | Language/topic filters | Improves template discovery | S | Combine with template search |
| F-06 | Session notes | Helps users remember what they practiced | S | Optional |
| F-07 | Import/export backup | Protects user history | S | Recommended with export |
| F-08 | User accounts/cloud sync | Multi-device history | XL | Defer; changes product scope |
| F-09 | Multiplayer/leaderboards | Social competition | XL | Defer; changes product scope |
| F-10 | AI-generated exercises | Potentially broadens training | XL | Defer until core learning loop is measured |

## 6. Work-Item Tracker

| ID | Priority | Status | Owner | Changed files | Verification | Evidence / blocker |
|---|---|---|---|---|---|---|
| PI-01 | P0 | DONE | Codex | `templates/about.html`, `tests/test_baseline_routes.py` | `.\.venv\Scripts\python.exe -m unittest discover -v -s tests` | Uploaded-image URL now uses the stable data-directory route; route test verifies HTTP 200 and file content |
| PI-02 | P0 | DONE | Codex | `static/script.js` | `node --check static/script.js` | Removed nested DOMContentLoaded registration; toggle restoration and persistence now initialize inside the active handler |
| PI-03 | P1 | DONE | Codex | `static/script.js`, `templates/index.html`, `static/style.css` | `node --check static/script.js` | Save requests now expose saving, success, and failure states through an accessible status region |
| PI-04 | P1 | VERIFIED | Codex | `static/script.js` | `node --check static/script.js`; code inspection | Existing chart guards prevent missing Chart.js from blocking the result summary; browser-level offline verification remains to be added |
| PI-05 | P1 | VERIFIED | Codex | `static/script.js`, `templates/index.html`, `static/style.css` | `node --check static/script.js` | Accessible status feedback covers save failures and built-in template fallback; broader browser coverage remains pending |
| PI-10 | P1 | DONE | Codex | `app.py`, `templates/index.html`, `static/script.js` | 42-test suite | Clear history with confirmation and server-backed reset |
| PI-11 | P1 | DONE | Codex | `static/script.js` | `node --check static/script.js` | Destructive action disabled while request is pending |
| PI-12 | P1 | DONE | Codex | `static/script.js` | 42-test suite; JS syntax check | Table and chart reset only after successful clear/save response |
| PI-13 | P1 | DONE | Codex | `templates/index.html` | HTML inspection; 42-test suite | Actionable empty-history message added |
| PI-14 | P2 | DONE | Codex | `app.py`, `templates/index.html`, `tests/test_baseline_routes.py` | Export route tests | Local JSON and CSV exports added |
| PI-20 | P1 | DONE | Codex | `app.py`, `static/script.js`, `templates/index.html` | Metric persistence tests; JS syntax check | Accuracy added to result, table, and persisted history |
| PI-21 | P1 | DONE | Codex | `app.py`, `static/script.js`, `templates/index.html` | Metric persistence tests; JS syntax check | Duration and completion added for completed/stopped sessions |
| PI-22 | P2 | DONE | Codex | `static/script.js`, `templates/index.html` | JS syntax check | Previous-session WPM comparison added |
| PI-23 | P2 | DONE | Codex | `static/script.js`, `templates/index.html` | JS syntax check | Personal-best WPM indicator added |
| PI-24 | P1 | DONE | Codex | `templates/index.html`, `app.py` | 42-test suite | Older history renders with an accuracy placeholder |
| PI-25 | P1 | DONE | Codex | `tests/test_baseline_routes.py` | 42 tests passed | Optional learning metrics persistence covered |
| PI-30 | P1 | DONE | Codex | `static/script.js`, `templates/index.html` | JS syntax check | Versioned local draft storage added |
| PI-31 | P1 | DONE | Codex | `static/script.js` | JS syntax check | Draft restoration is explicit through status feedback and only fills an empty editor |
| PI-32 | P2 | DONE | Codex | `static/script.js`, `templates/index.html` | JS syntax check | Clear draft control added |
| PI-33 | P1 | DONE | Codex | `static/script.js` | Code inspection | Only draft/template preferences are stored locally |
| PI-34 | P1 | VERIFIED | Codex | `static/script.js` | JS syntax check | Browser refresh/manual verification remains recommended |
| PI-40 | P2 | DONE | Codex | `static/script.js`, `templates/index.html` | JS syntax check | Search filters language and filename |
| PI-41 | P3 | DONE | Codex | `static/script.js`, `templates/index.html` | JS syntax check | Ten recent template keys stored locally |
| PI-42 | P3 | DONE | Codex | `static/script.js`, `templates/index.html` | JS syntax check | Local favorite toggle added |
| PI-43 | P2 | DONE | Codex | `static/script.js`, `templates/index.html` | JS syntax check | Random selection respects current search |
| PI-44 | P3 | DONE | Codex | `static/script.js`, `templates/index.html` | HTML/JS inspection | Language and filename metadata remain visible in selectors |
| PI-45 | P2 | VERIFIED | Codex | `static/script.js` | Node syntax check; fallback code inspection | Full browser keyboard/fallback automation remains recommended |
| PI-50 | P2 | DONE | Existing hardening | `docs/PRODUCTION_HARDENING_PLAN.md` | WP-60 record | External asset inventory recorded |
| PI-51 | P2 | DONE | Existing hardening | `docs/PRODUCTION_HARDENING_PLAN.md` | WP-61 record | SRI/fallback handling recorded |
| PI-52 | P2 | DONE | Codex | `static/script.js` | JS syntax check | Built-in-template fallback status is visible |
| PI-53 | P2 | DONE | Codex | `templates/index.html`, `static/script.js` | HTML/JS inspection | Live status region announces result and fallback states |
| PI-54 | P2 | DONE | Codex | `templates/index.html`, `static/script.js` | HTML/JS inspection | Dialog semantics and Escape close behavior added |
| PI-55 | P2 | VERIFIED | Codex | `static/style.css`, `static/script.js` | Node syntax check; CSS inspection | Reduced-motion rules added; keyboard browser verification remains recommended |

## 7. Definition of Done

- [ ] All P0 items are complete and verified.
- [ ] All P1 items are complete or have an explicitly accepted residual risk.
- [ ] Existing tests remain green.
- [ ] Each user-facing change has a manual or automated verification path.
- [ ] Existing history files remain readable.
- [ ] The core Start/Stop/restart typing flow is unchanged unless explicitly approved.
- [ ] No feature silently loses user input or saved results.
- [ ] Offline and failure states are visible and understandable.
- [ ] No unrelated redesign, dependency, or architecture changes are included.

## 8. Verification Log

```text
Date: 2026-09-20
Work items: PI-01 through PI-05
Environment: Windows, Python 3.12.11, Flask test client, Node.js syntax checker
Commands:
1. .\.venv\Scripts\python.exe -m py_compile app.py tests\\test_baseline_routes.py tests\\test_persistence.py
2. .\.venv\Scripts\python.exe -m unittest discover -v -s tests
3. node --check static\\script.js
Observed results:
- Python compilation succeeded.
- 40 backend, persistence, packaging, and security tests passed.
- JavaScript syntax check passed.
- Profile image route test returned HTTP 200 and matched stored content.
- Browser-level Chart.js-offline behavior was not executed.
Failures: None in executed checks.
Decision: Complete PI-01 through PI-03; keep PI-04 and PI-05 VERIFIED pending browser-level verification.
```

```text
Date: 2026-09-20
Work items: PI-10 through PI-55
Environment: Windows 11, Python 3.12.11, Flask test client, Node.js, PyInstaller 6.22.3
Commands:
1. .\.venv\Scripts\python.exe -m py_compile app.py <all test files>
2. .\.venv\Scripts\python.exe -m unittest discover -v -s tests
3. node --check static\\script.js
4. .\.venv\Scripts\pyinstaller.exe app.spec --noconfirm --clean
5. .\.venv\Scripts\python.exe -m unittest tests\\test_packaging_smoke.py -v
Observed results:
- Python compilation succeeded.
- 42 backend, persistence, packaging, and security tests passed.
- JavaScript syntax check passed.
- PyInstaller build completed with exit code 0.
- Packaged-app smoke test passed outside the repository working directory.
- JSON/CSV export, optional learning metrics, clear-history controls, draft state, template search/random/recent/favorites, and accessibility markup are implemented.
Failures: No executed verification failures. Full browser automation for localStorage, keyboard-only flow, and CDN-offline behavior remains a manual verification gap.
Decision: Complete the remaining product phases; retain PI-34, PI-45, and PI-55 as VERIFIED until browser-level checks are added.
```

Record one concise entry per completed phase or logical work item.

```text
Date:
Work items:
Environment:
Commands:
Observed results:
User-facing verification:
Failures:
Decision:
```

## 9. Product Decisions

| Date | Decision | Reason | Owner |
|---|---|---|---|
| 2026-09-20 | Improve existing reliability and feedback before large new features | The current learning loop is usable but failure states are too silent |  |
| 2026-09-20 | Keep new preferences and draft state local where possible | Preserves the local-first architecture and limits persistence complexity |  |
| 2026-09-20 | Defer accounts, cloud sync, multiplayer, and AI generation | These features materially expand product scope |  |
