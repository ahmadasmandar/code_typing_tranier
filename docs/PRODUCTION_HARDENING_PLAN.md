# Code Typing Trainer — Production Hardening Work Plan

Status: `PLANNED`

Owner: Ahmad Asmandar

Scope: Reliability, security, persistence, packaging, testing, and operational hardening while preserving the current product purpose, UX, visual identity, and local single-user workflow.

Baseline: Audit score `50/100` based on repository evidence inspected on 2026-09-20.

## 1. Working Rules

1. Work in small, independently reviewable changes.
2. Complete one work item only after its acceptance criteria and verification command pass.
3. Do not mix unrelated refactoring, visual redesign, dependency upgrades, or feature work into a hardening change.
4. Preserve the existing public routes unless a change is required to remove a demonstrated risk.
5. Never claim a test, build, packaging run, or security property without recording the command and observed result.
6. Keep user data out of source control. `train_settings.json`, uploads, build output, and virtual environments remain local artifacts.
7. Stop and reassess if a change affects the application’s data format, browser workflow, packaging layout, or network exposure model.

## 2. Tracking Method

Use the work-item table below as the single source of progress. Update it in the same commit as the implementation or verification it describes.

### Status vocabulary

`PLANNED` → `IN PROGRESS` → `BLOCKED` or `READY FOR VERIFY` → `VERIFIED` → `DONE`

Use `BLOCKED` only with a written blocker and the next action needed. `DONE` requires both implementation evidence and verification evidence.

### Required evidence per work item

For every item, record:

- Changed files
- Exact commands executed
- Observed result, including exit code or HTTP status
- Tests added or updated
- Remaining risks or assumptions
- Commit/PR reference when one exists

### Change-control rule

One logical work item should normally produce one focused commit. Use Conventional Commit format:

```text
<type>(<scope>): <imperative subject>
```

Do not commit, push, tag, or publish as part of this plan unless explicitly authorized.

## 3. Baseline Findings and Completion Targets

| ID | Finding | Baseline | Completion target |
|---|---|---|---|
| BUILD-01 | PyInstaller asset inclusion is incomplete | `app.spec` has `datas=[]` | Packaged app starts from a different working directory and serves `/`, `/about`, `/api/templates`, CSS, and JavaScript successfully |
| REL-01 | Profile-image upload endpoint is incomplete | Authorized `POST /upload_image` returns `500` | Valid, invalid, missing, and unauthorized upload cases return intentional responses |
| REL-02 | Persistence is cwd-relative and non-atomic | Relative paths; direct `open(..., 'w')` | Stable user-data location, locked read-modify-write, atomic replacement, recovery behavior |
| SEC-01 | IP check is not authentication; state changes lack CSRF controls | `remote_addr` check and unprotected `/clear` | Local-only boundary is explicit and state-changing browser requests are protected |
| SEC-02 | `/save` accepts unvalidated payloads | Direct `.get()` calls on `request.json` | Invalid payloads return `400`; valid payloads are normalized and bounded |
| CONFIG-01 | Debug mode is enabled in the startup path | `app.run(debug=True)` | Production default is non-debug; development debug mode is explicit |
| BUILD-02 | Dependency manifests disagree | Conflicting pins and version ranges | One authoritative supported installation path and consistent lock metadata |
| TEST-01 | No application regression suite | No tracked tests or CI | Focused backend and packaging smoke coverage runs repeatably |
| SEC-03 | CDN scripts are not fully integrity-pinned | Chart.js has no SRI; Prism hashes are empty | Assets are self-hosted or loaded with verified SRI |

## 4. Execution Plan and Gates

### Phase 0 — Establish a clean baseline

**Goal:** Make later results attributable to hardening work.

- [x] `WP-00` Record Python, OS, package, and repository state.
- [x] `WP-01` Add the initial backend test harness without changing behavior.
- [x] `WP-02` Capture baseline route responses and the known `/upload_image` failure.

**Gate 0:** Baseline commands, outputs, and current known failures are recorded before behavior changes.

Suggested baseline commands:

```powershell
python --version
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m py_compile app.py
git status --short
```

### Phase 1 — Restore broken behavior and define contracts

**Goal:** Remove confirmed correctness failures before hardening surrounding infrastructure.

- [x] `WP-10` Complete `/upload_image` or formally remove the unused endpoint and its dead configuration.
- [x] `WP-11` Define response contracts for `/save`, `/clear`, `/upload_image`, and `/api/upload_template`.
- [x] `WP-12` Validate `/save` JSON structure, numeric types, finite values, and non-negative ranges.
- [x] `WP-13` Add tests for malformed requests, valid requests, route status codes, and history retention.

**Gate 1:** Valid existing frontend behavior still succeeds; malformed requests receive intentional `4xx` responses; no route returns `500` for expected invalid input.

### Phase 2 — Make persistence safe and portable

**Goal:** Prevent data loss, corruption, and working-directory surprises.

- [ ] `WP-20` Define the application data directory for source and packaged execution.
- [ ] `WP-21` Resolve `train_settings.json` and profile uploads against that data directory.
- [ ] `WP-22` Add a process-level lock around settings read-modify-write operations.
- [ ] `WP-23` Write JSON to a same-directory temporary file, flush it, and atomically replace the destination.
- [ ] `WP-24` Handle missing, invalid, unreadable, and interrupted settings files with safe recovery behavior.
- [ ] `WP-25` Add tests for alternate working directories, malformed JSON, concurrent saves, and retained history.

**Gate 2:** Launching from the repository directory and another directory uses the same user-data location; concurrent saves do not corrupt JSON or silently lose retained entries.

### Phase 3 — Enforce the local security boundary

**Goal:** Keep the product local by design and reduce browser-driven state changes.

- [ ] `WP-30` Make host and debug settings explicit configuration values with safe production defaults.
- [ ] `WP-31` Centralize the loopback check and document IPv4/IPv6 behavior.
- [ ] `WP-32` Add CSRF/origin protection for browser state-changing routes, especially `/clear` and upload endpoints.
- [ ] `WP-33` Decide whether uploads are part of the supported product. If yes, keep them local-only with size, extension, and content validation; if no, remove them.
- [ ] `WP-34` Add security tests for non-loopback requests, missing origins, invalid content types, oversized uploads, and traversal-like names.

**Gate 3:** No supported state-changing request bypasses the intended local boundary, and the application never relies on an IP check as a substitute for authentication when network exposure is enabled.

### Phase 4 — Make packaging reproducible

**Goal:** Ensure the distributed executable contains and locates all required assets.

- [ ] `WP-40` Choose the supported dependency source: `pyproject.toml` plus lockfile, or a cleaned requirements file.
- [ ] `WP-41` Remove conflicting duplicate pins and align Flask, Werkzeug, Jinja2, Python, and PyInstaller versions.
- [ ] `WP-42` Add `templates/`, `static/`, icons, and required runtime data to `app.spec` using portable paths.
- [ ] `WP-43` Prevent packaged mode from writing mutable user data inside the installation directory.
- [ ] `WP-44` Build the package from a clean environment.
- [ ] `WP-45` Run the executable from a working directory outside the repository.

**Gate 4:** A clean installation and packaged smoke test pass without manually copying repository directories after the build.

### Phase 5 — Add regression and operational verification

**Goal:** Prevent the known failures from returning.

- [ ] `WP-50` Add focused Flask tests for every route and failure path.
- [ ] `WP-51` Add persistence tests for atomicity, recovery, and concurrent saves.
- [ ] `WP-52` Add a packaged-app smoke test covering startup, page rendering, static assets, and template discovery.
- [ ] `WP-53` Add a lightweight lint/type/style check only if it can be introduced without changing runtime behavior.
- [ ] `WP-54` Add a repeatable verification command to the contributor documentation.

**Gate 5:** The verification suite is repeatable from a clean environment and detects each P0/P1 finding.

### Phase 6 — Reduce external asset trust

**Goal:** Remove avoidable third-party executable-asset risk.

- [ ] `WP-60` Inventory all external JavaScript and CSS assets.
- [ ] `WP-61` Prefer self-hosting pinned assets in `static/`, or record and enforce valid SRI hashes.
- [ ] `WP-62` Verify that the application still renders charts and syntax highlighting when the network is unavailable.

**Gate 6:** Core typing functionality works without a live CDN dependency, or the remaining dependency and failure behavior are explicitly documented.

## 5. Work-Item Tracker

Update this table as work proceeds. Do not mark an item `DONE` without evidence.

| ID | Priority | Status | Owner | Changed files | Verification | Evidence / blocker |
|---|---|---|---|---|---|---|
| WP-00 | P1 | DONE | Ahmad Asmandar | None (environment and repo inspection) | `python --version`, `pip check`, `py_compile`, `git status` | Baseline recorded: Python 3.12.11 on Windows, pip check clean, git commit `c56348b` on `code_audit`, `uv.lock` pre-existing modification preserved |
| WP-01 | P1 | DONE | Ahmad Asmandar | `tests/__init__.py`, `tests/test_baseline_routes.py` | `.\.venv\Scripts\python.exe -m unittest discover -v -s tests` | Initial stdlib `unittest` + Flask test client harness added (8 tests passing in 0.023s), no application behavior changed |
| WP-02 | P1 | DONE | Ahmad Asmandar | `tests/test_baseline_routes.py` | `.\.venv\Scripts\python.exe -m unittest discover -v -s tests` | Captured baseline route contracts for `/`, `/about`, `/api/templates`, `/upload_image` (302 remote, 500 loopback baseline failure REL-01), `/api/upload_template` (403 remote, 400 invalid local), and `/save` / `/clear` |
| WP-10 | P1 | DONE | Ahmad Asmandar | `app.py` | `.\.venv\Scripts\python.exe -m unittest discover -v -s tests` | Completed `/upload_image` endpoint: loopback-only check, file validation via `allowed_file`, `secure_filename`, saves image to uploads folder, records `profile_image` in settings, redirects to `/about` without 500 error |
| WP-11 | P1 | DONE | Ahmad Asmandar | `app.py`, `tests/test_baseline_routes.py` | `.\.venv\Scripts\python.exe -m unittest discover -v -s tests` | Defined explicit response contracts across all routes: `/save` (200 JSON success, 400 JSON on invalid), `/clear` (200 JSON), `/upload_image` (302 redirect), `/api/upload_template` (200 JSON on save, 400 JSON on missing/invalid, 403 on remote) |
| WP-12 | P1 | DONE | Ahmad Asmandar | `app.py` | `.\.venv\Scripts\python.exe -m unittest discover -v -s tests` | Implemented `_validate_non_negative_number` in `/save`: enforces dictionary JSON, finite non-negative numbers, bounds (wpm <= 2000, errors/backspaces <= 100000), integer types for counts, and rejects booleans/strings/infinities/NaNs |
| WP-13 | P1 | DONE | Ahmad Asmandar | `tests/test_baseline_routes.py` | `.\.venv\Scripts\python.exe -m unittest discover -v -s tests` | Expanded test suite to 20 tests covering valid submissions, malformed JSON, negative values, booleans, non-finite values, history 20-entry capping and ordering, image uploads, template uploads, and unauthorized remote access |
| WP-20 | P1 | PLANNED |  |  |  |  |
| WP-21 | P1 | PLANNED |  |  |  |  |
| WP-22 | P1 | PLANNED |  |  |  |  |
| WP-23 | P1 | PLANNED |  |  |  |  |
| WP-24 | P1 | PLANNED |  |  |  |  |
| WP-25 | P1 | PLANNED |  |  |  |  |
| WP-30 | P1 | PLANNED |  |  |  |  |
| WP-31 | P2 | PLANNED |  |  |  |  |
| WP-32 | P2 | PLANNED |  |  |  |  |
| WP-33 | P1 | PLANNED |  |  |  |  |
| WP-34 | P2 | PLANNED |  |  |  |  |
| WP-40 | P1 | PLANNED |  |  |  |  |
| WP-41 | P1 | PLANNED |  |  |  |  |
| WP-42 | P0 | PLANNED |  |  |  |  |
| WP-43 | P1 | PLANNED |  |  |  |  |
| WP-44 | P0 | PLANNED |  |  |  |  |
| WP-45 | P0 | PLANNED |  |  |  |  |
| WP-50 | P1 | PLANNED |  |  |  |  |
| WP-51 | P1 | PLANNED |  |  |  |  |
| WP-52 | P0 | PLANNED |  |  |  |  |
| WP-53 | P2 | PLANNED |  |  |  |  |
| WP-54 | P2 | PLANNED |  |  |  |  |
| WP-60 | P2 | PLANNED |  |  |  |  |
| WP-61 | P2 | PLANNED |  |  |  |  |
| WP-62 | P2 | PLANNED |  |  |  |  |

## 6. Definition of Done

The hardening effort is complete only when all of the following are true:

- [ ] P0 and P1 items are `DONE` or have an explicitly accepted residual risk.
- [ ] The app starts with debug disabled by default.
- [ ] The packaged build includes all required templates and static assets.
- [ ] The packaged app works outside the repository working directory.
- [ ] Settings writes are portable, atomic, recoverable, and tested under concurrent access.
- [ ] Expected invalid requests do not produce `500` responses.
- [ ] Upload behavior is either fully implemented and tested or intentionally removed.
- [ ] Dependencies have one documented supported installation path.
- [ ] Route, persistence, security-boundary, and packaging smoke tests pass.
- [ ] The final verification log contains exact commands and observed results.
- [ ] No unrelated UX, visual, feature, or architectural changes were introduced.

## 7. Verification Log

Append one entry per verification session. Keep the output concise but factual.

```text
Date: 2026-09-20
Work items: WP-00, WP-01, WP-02 (Phase 0 Baseline)
Environment: Windows 11 x86_64, Python 3.12.11, Flask 3.1.3, Werkzeug 3.1.8
Commands:
1. .\.venv\Scripts\python.exe --version -> Python 3.12.11 (exit code 0)
2. .\.venv\Scripts\python.exe -m pip check -> No broken requirements found. (exit code 0)
3. .\.venv\Scripts\python.exe -m py_compile app.py -> (clean compilation, exit code 0)
4. git status --short -> M uv.lock (preserved), ?? docs/, ?? tests/ (exit code 0)
5. .\.venv\Scripts\python.exe -m unittest discover -v -s tests -> Ran 8 tests in 0.023s (OK, exit code 0)
Observed results:
- GET /: HTTP 200 (HTML rendered)
- GET /about: HTTP 200 (HTML rendered)
- GET /api/templates: HTTP 200 (JSON payload with languages list)
- POST /upload_image (remote IP): HTTP 302 (redirect to /about)
- POST /upload_image (127.0.0.1): HTTP 500 (TypeError: view function ended without return statement; baseline REL-01 reproduced)
- POST /api/upload_template (remote IP): HTTP 403 (JSON error: not authorized)
- POST /api/upload_template (127.0.0.1 missing fields): HTTP 400 (JSON error: missing language or file)
- POST /save & POST /clear: HTTP 200 (JSON status: saved / cleared)
Failures:
- None unexpected; baseline finding REL-01 confirmed and captured as an expected baseline failure test.
Decision:
- Use standard library unittest with Flask test_client for backend test harness to avoid introducing new dependencies or lockfile churn.
```

```text
Date: 2026-09-20
Work items: WP-10, WP-11, WP-12, WP-13 (Phase 1 Contracts & Validation)
Environment: Windows 11 x86_64, Python 3.12.11, Flask 3.1.3, Werkzeug 3.1.8
Commands:
1. .\.venv\Scripts\python.exe -m py_compile app.py tests/test_baseline_routes.py -> (clean compilation, exit code 0)
2. .\.venv\Scripts\python.exe -m unittest discover -v -s tests -> Ran 20 tests in 0.225s (OK, exit code 0)
Observed results:
- /save: 200 on valid int/float payloads, 400 on non-JSON, array, negative, boolean, non-finite, out-of-bounds, or non-integral error/backspace values. History correctly capped at 20 entries and ordered newest-first.
- /clear: 200 on POST, history cleared.
- /upload_image: 302 redirect for unauthorized remote, missing file, empty filename, disallowed extension, and valid image upload (saving file and updating profile_image in settings). Finding REL-01 resolved.
- /api/upload_template: 403 on remote, 400 on missing fields, 400 on invalid/traversal language name, 200 on valid snippet upload.
- /, /about, /api/templates: all 200 OK.
Failures:
- None.
Decision:
- Complete /upload_image handler rather than removing, preserving existing about.html profile image rendering contract.
- Validate raw language folder name with strict regex ^[a-zA-Z0-9_-]{1,30}$ before sanitization to reject path traversal attempts with 400.
```

## 8. Risk Register

| Risk | Trigger | Mitigation | Owner | Status |
|---|---|---|---|---|
| Existing user history is lost during path migration | First launch after data-directory change | Detect and migrate the old file once; keep a backup before replacement |  | OPEN |
| Packaged build behaves differently from source run | Missing runtime asset or altered base path | Run the executable outside the repository in every packaging change |  | OPEN |
| Security hardening breaks local browser workflow | Browser-origin or IPv6 assumptions differ | Test the actual local browser workflow before and after each security change |  | OPEN |
| Dependency cleanup breaks legacy scripts | Historical files rely on broad requirements | Keep the supported app dependency set explicit and verify documented commands |  | OPEN |
| Concurrent persistence change creates deadlocks | Lock lifetime is too broad | Keep lock scope limited to load/modify/save and test failure paths |  | OPEN |

## 9. Decision Records

Record decisions that affect scope or compatibility here.

| Date | Decision | Reason | Alternatives rejected | Owner |
|---|---|---|---|---|
| 2026-09-20 | Preserve Flask, vanilla JavaScript, JSON history, and current UI | These are adequate for the demonstrated local product | Framework migration, database migration, UI redesign |  |
| 2026-09-20 | Use standard library `unittest` and `app.test_client()` for backend test harness | Zero external dependencies required, fast execution (<0.03s), native to Python 3.12, avoids lockfile churn | Installing pytest, webtest, or external test runners | Ahmad Asmandar |
| 2026-09-20 | Complete `/upload_image` with local-only validation rather than deleting it | Keeps existing `about.html` profile image presentation functional and resolves Finding `REL-01` | Removing profile image functionality and related templates | Ahmad Asmandar |
| 2026-09-20 | Strict pre-sanitization validation on `/api/upload_template` language folder | Rejects traversal paths (`../c`, `c/sub`) with HTTP 400 rather than silently mutating them | Allowing silent sanitization to alter folder targets | Ahmad Asmandar |



