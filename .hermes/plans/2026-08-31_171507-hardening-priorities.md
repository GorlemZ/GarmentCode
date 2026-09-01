# GarmentCode Packaging, Testability, and Maintainability Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task. Apply strict RED–GREEN–REFACTOR for behavior changes, and require spec-compliance review followed by code-quality review for each PR-sized phase.

**Goal:** Rendere GarmentCode installabile da una wheel reale, verificabile automaticamente e più semplice da mantenere, senza cambiare la geometria prodotta né rendere obbligatorie le pipeline GUI, Maya o Warp per gli utenti del solo nucleo 2D.

**Architecture:** Procedere per vertical slice e piccoli PR ordinati: prima congelare il comportamento corrente con smoke/golden test, poi correggere il packaging, introdurre CI, separare le dipendenze opzionali e solo infine affrontare eccezioni, lint e decomposizione dei moduli. Ogni gate deve installare e testare la wheel da una directory esterna al checkout, così il source tree non può mascherare errori di packaging.

**Tech Stack:** Python 3.9 e 3.11, setuptools tramite `pyproject.toml`, pytest, Ruff, GitHub Actions, `uv` per ambienti/build riproducibili, YAML/JSON/SVG come formati di fixture.

---

## 1. Contesto verificato

- Repository: `/Users/andreagorletta/LocalWork/Personal/GarmentCode`
- Branch base: `main`
- Versione corrente: `2.0.2`
- Il core 2D costruisce correttamente la T-shirt di esempio: 8 pannelli, 16 cuciture, nessuna autointersezione.
- I due file `test_garmentcode.py` e `test_garment_sim.py` sono script manuali, non test pytest.
- Non esiste CI.
- La wheel corrente contiene `garmentcode/`, `meshgen/`, `pattern/` e `mayaqltools/`, ma non il package `pygarment/` usato dagli import sorgente.
- Il codice dichiara Python `>=3.6`, ma usa sintassi Python 3.8+ e la documentazione raccomanda 3.9.
- CairoSVG su macOS richiede che la libreria Cairo di Homebrew sia visibile al loader.
- La simulazione completa dipende dal fork esterno `NvidiaWarp-GarmentCode` e non deve bloccare la suite core.

## 2. Vincoli e decisioni

1. **Nessuna modifica geometrica intenzionale nei PR P0/P1.** Le fixture devono proteggere il comportamento corrente prima di toccare packaging o struttura.
2. **La wheel è la fonte di verità.** Un editable install non è una verifica sufficiente.
3. **Il primo packaging fix conserva una wheel universale corretta.** Le DLL Cairo già presenti nel repository non vanno incluse in una wheel `py3-none-any`; Windows deve usare un runtime Cairo esterno e architecture-matched nel `PATH` finché non viene progettata una distribuzione platform-specific separata.
4. **Gli asset dimostrativi restano repository-level.** La prima wheel supporta la libreria `pygarment`; GUI, programmi completi e dataset richiedono il checkout finché non viene progettato un package dati dedicato.
5. **Warp, Maya e Qualoth non entrano nei test core.** Avranno smoke test separati e condizionali.
6. **Python supportato inizialmente: 3.9 e 3.11.** Aggiungere 3.12 solo dopo aver verificato l’intero grafo delle dipendenze; rimuovere 3.9 solo con decisione esplicita e documentata.
7. **Un PR per fase.** Non mescolare packaging, refactoring geometrico e modernizzazione stilistica.

## 3. Definition of Done globale

- `uv build --wheel` produce una wheel contenente `pygarment/__init__.py` e tutti i moduli importati dal core.
- La wheel viene installata in un ambiente vuoto e `import pygarment` funziona da una directory esterna al repository.
- Il golden smoke produce 8 pannelli, 16 cuciture e nessuna autointersezione.
- I test di round-trip JSON e SVG passano su Python 3.9 e 3.11.
- La CI esegue test, wheel smoke e Ruff sui nuovi standard concordati.
- `pip install .` non installa GUI, rendering, meshing o simulazione se non richiesti.
- Gli extra `gui`, `mesh`, `simulation`, `maya` e `dev` sono documentati e testati almeno a livello di risoluzione/import.
- Le eccezioni applicative ereditano da `Exception`; `KeyboardInterrupt` e `SystemExit` non vengono intercettati dai catch generici.
- Repository pulito dopo build e test; nessun `build/`, `*.egg-info` o output temporaneo rimane tracciato.

---

# Fase P0 — Packaging affidabile

## Task 1: Aggiungere l’infrastruttura minima di test

**Objective:** Creare un runner pytest minimale senza alterare il codice di produzione.

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/test_core_smoke.py`
- Modify: `.gitignore`
- Modify: `pyproject.toml`

**Step 1 — RED:** aggiungere `tests/test_core_smoke.py` con un test che costruisce `MetaGarment('t-shirt', ...)` usando `assets/bodies/mean_all.yaml` e `assets/design_params/t-shirt.yaml`, quindi verifica:

```python
assert pattern.name == "t-shirt"
assert len(pattern.pattern["panels"]) == 8
assert len(pattern.pattern["stitches"]) == 16
assert garment.is_self_intersecting() is False
```

**Step 2 — Verify RED:** eseguire:

```bash
uv run --python 3.11 --with pytest pytest tests/test_core_smoke.py -v
```

Expected: FAIL durante setup/import perché le dipendenze di test non sono ancora dichiarate nel progetto.

**Step 3 — GREEN:** aggiungere solo configurazione pytest e dipendenze di sviluppo necessarie nel `pyproject.toml`; non migrare ancora tutti i metadati.

**Step 4 — Verify GREEN:** eseguire il test con Cairo visibile su macOS:

```bash
DYLD_FALLBACK_LIBRARY_PATH="$(brew --prefix cairo)/lib" uv run --python 3.11 --extra dev pytest tests/test_core_smoke.py -v
```

Expected: `1 passed`.

**Step 5 — Cleanup:** ignorare `.pytest_cache/`, `.ruff_cache/`, `.coverage`, `htmlcov/` e `.venv/`.

**Step 6 — Commit:** `test: add core garment smoke coverage`

---

## Task 2: Congelare gli output strutturali del cartamodello

**Objective:** Proteggere la semantica del core prima di cambiare packaging e import.

**Files:**
- Create: `tests/fixtures/tshirt_summary.json`
- Create: `tests/test_pattern_regression.py`
- Test: `assets/Patterns/shirt_mean_specification.json`

**Step 1 — RED:** aggiungere un test che estrae una summary deterministica del pattern:

- nomi ordinati dei pannelli;
- numero di vertici e spigoli per pannello;
- numero di cuciture;
- proprietà principali e unità;
- bounding box arrotondati con tolleranza esplicita.

Non fare snapshot dell’intero JSON: sarebbe troppo fragile rispetto all’ordine e ai float.

**Step 2 — Verify RED:** eseguire il singolo test e verificare che fallisca perché la fixture non esiste.

**Step 3 — GREEN:** generare una volta `tests/fixtures/tshirt_summary.json` dal commit base e revisionarla manualmente.

**Step 4 — Verify GREEN:** eseguire due volte il test in processi distinti per rilevare non-determinismo.

**Step 5 — Commit:** `test: lock t-shirt pattern structure`

---

## Task 3: Scrivere il test che riproduce la wheel rotta

**Objective:** Dimostrare il difetto di packaging senza dipendere dal checkout.

**Files:**
- Create: `tests/packaging/test_wheel_install.py`
- Create: `scripts/check_wheel.py`

**Step 1 — RED:** il test deve:

1. costruire la wheel in una directory temporanea;
2. creare un virtualenv temporaneo;
3. installare la wheel senza editable mode;
4. impostare `cwd` a una directory temporanea esterna al repository;
5. eseguire:

```python
import pygarment
from pygarment.garmentcode.component import Component
from pygarment.pattern.core import BasicPattern
```

6. aprire la wheel come ZIP e verificare `pygarment/__init__.py`.

**Step 2 — Verify RED:** eseguire:

```bash
uv run --extra dev pytest tests/packaging/test_wheel_install.py -v
```

Expected: FAIL perché `pygarment/__init__.py` non è nella wheel.

**Step 3 — Commit solo test:** `test: reproduce broken wheel namespace`

---

## Task 4: Migrare i metadati in `pyproject.toml` e correggere il namespace

**Objective:** Produrre una wheel coerente con gli import `pygarment.*`.

**Files:**
- Modify: `pyproject.toml`
- Delete after parity check: `setup.cfg`
- Rename: `ReadMe.md` → `README.md`
- Test: `tests/packaging/test_wheel_install.py`

**Step 1 — GREEN minimale:** configurare setuptools per cercare package dalla root e includere solo `pygarment*`, ad esempio:

```toml
[tool.setuptools.packages.find]
where = ["."]
include = ["pygarment*"]
```

Aggiungere in `[project]` nome, versione, descrizione, README, licenza, autori, URL, `requires-python = ">=3.9"` e dipendenze correnti senza ancora separarle.

**Step 2 — Preserve universal-wheel semantics:** non includere DLL o altre librerie native nella wheel `py3-none-any`; documentare Cairo come dipendenza runtime esterna per Windows/macOS/Linux.

**Step 3 — Metadata parity:** confrontare METADATA della wheel vecchia e nuova per nome, versione, licenza, URL e requirements. Eliminare `setup.cfg` solo quando la parità intenzionale è documentata.

**Step 4 — Verify GREEN:** eseguire:

```bash
uv build --wheel
uv run --extra dev pytest tests/packaging/test_wheel_install.py -v
```

Expected: PASS; la wheel contiene `pygarment/__init__.py`, `pygarment/data_config.py` e i sottopackage Python, ma nessuna libreria nativa (`.dll`, `.dylib`, `.pyd`, `.so`).

**Step 5 — Full regression:** `uv run --extra dev pytest tests -q`.

**Step 6 — Commit:** `build: package the pygarment namespace correctly`

---

## Task 5: Documentare installazione riproducibile e Cairo

**Objective:** Rendere l’installazione eseguibile su Linux, macOS e Windows senza conoscenze implicite.

**Files:**
- Modify: `docs/Installation.md`
- Modify: `README.md`
- Create: `docs/Troubleshooting.md`

**Steps:**

1. Documentare Python 3.9/3.11 e ambiente virtuale con `uv` o `venv`.
2. Aggiungere comandi Linux/macOS/Windows per Cairo.
3. Su macOS documentare Homebrew e il loader path; verificare il comando in una shell nuova.
4. Distinguere chiaramente core, GUI, meshing e simulazione Warp.
5. Correggere riferimenti obsoleti a `assets/body_measurements` e altri path non esistenti.
6. Eseguire tutti i comandi copiati dalla documentazione in un ambiente temporaneo.
7. Commit: `docs: clarify supported installation paths`.

**P0 exit gate:** wheel installabile da ambiente vuoto, smoke e regression test verdi, documentazione riprodotta su questa macchina.

---

# Fase P1 — Test e CI

## Task 6: Testare primitive geometriche e curve

**Objective:** Coprire i building block modificati più frequentemente.

**Files:**
- Create: `tests/garmentcode/test_edge.py`
- Create: `tests/garmentcode/test_edge_factory.py`
- Create: `tests/garmentcode/test_operators.py`

**Vertical slices TDD:**

1. Edge lineare: lunghezza e reverse.
2. Bezier quadratica: endpoint e lunghezza entro tolleranza.
3. Bezier cubica: serializzazione dei control point.
4. Suddivisione: somma delle lunghezze e orientamento.
5. `cut_corner`: continuità e assenza di edge degeneri.
6. Input fuori range: tipo di eccezione e messaggio.

Per ogni slice: scrivere un test, osservare RED, implementare/fissare il minimo, osservare GREEN, eseguire il file completo, commit atomico.

---

## Task 7: Testare pannelli, componenti, interfacce e cuciture

**Files:**
- Create: `tests/garmentcode/test_panel.py`
- Create: `tests/garmentcode/test_component.py`
- Create: `tests/garmentcode/test_interface.py`
- Create: `tests/garmentcode/test_connector.py`

**Behaviors:**

- trasformazioni 2D/3D preservano distanze attese;
- `Component.assembly()` non perde pannelli o stitches;
- nomi pannello duplicati falliscono esplicitamente;
- orientamento delle cuciture è serializzato;
- mirror e reverse mantengono manifold/orientamento;
- default mutabili non condividono stato fra istanze.

Commit per famiglia: `test: cover <family> behavior`.

---

## Task 8: Testare serializzazione e SVG

**Files:**
- Create: `tests/pattern/test_roundtrip.py`
- Create: `tests/pattern/test_normalization.py`
- Create: `tests/pattern/test_svg.py`
- Create: `tests/fixtures/patterns/`

**Behaviors:**

1. JSON load → serialize → reload conserva proprietà semantiche.
2. Conversione unità termina in centimetri.
3. Normalizzazione edge loop è idempotente.
4. Pattern vuoto solleva `EmptyPatternError`.
5. SVG valido contiene un path per ogni pannello atteso.
6. Output non dipende dal `cwd` quando viene fornito un path esplicito.

Usare parser XML e proprietà strutturali; non confrontare SVG intero come stringa.

---

## Task 9: Separare test core e integration

**Files:**
- Modify: `pyproject.toml`
- Create: `tests/meshgen/test_boxmesh_smoke.py`
- Create: `tests/gui/test_gui_import.py`
- Create: `tests/simulation/test_warp_import.py`

**Markers:** `core`, `mesh`, `gui`, `simulation`, `maya`, `slow`.

**Commands:**

```bash
pytest -m core -q
pytest -m "mesh and not slow" -q
pytest -m gui -q
pytest -m simulation -q
```

I test Warp/Maya devono fare skip con motivo esplicito quando il prerequisito esterno non è installato; non devono trasformare un prerequisito assente in un falso PASS.

---

## Task 10: Aggiungere GitHub Actions

**Files:**
- Create: `.github/workflows/test.yml`
- Create: `.github/workflows/package.yml`
- Create: `.github/dependabot.yml`

**`test.yml`:**

- Linux, Python 3.9 e 3.11;
- macOS, Python 3.11 per Cairo e portabilità;
- installazione tramite `uv`;
- `pytest -m core`;
- cache uv;
- timeout espliciti.

**`package.yml`:**

- build sdist e wheel;
- installazione wheel in ambiente pulito;
- test da directory esterna;
- `twine check` o equivalente;
- upload artefatti, senza pubblicazione automatica iniziale.

**RED:** aprire il PR con i workflow e verificare che il packaging test fallisca se si reintroduce la vecchia configurazione.

**GREEN:** tutti i job obbligatori verdi per due esecuzioni consecutive.

Commit: `ci: validate core and wheel distributions`.

**P1 exit gate:** test core ripetibili, CI verde, nessuna dipendenza da Warp/Maya per il job core.

---

# Fase P2 — Dipendenze opzionali e confini architetturali

## Task 11: Definire una matrice import/dipendenze

**Objective:** Evitare di spostare dipendenze “a intuito”.

**Files:**
- Create: `tests/packaging/test_optional_imports.py`
- Create: `docs/Dependency-groups.md`

**Test matrix:**

| Installazione | Deve funzionare | Non deve essere richiesto |
|---|---|---|
| base | `import pygarment`, DSL, JSON | NiceGUI, pyrender, CGAL, Warp, Maya |
| `[gui]` | `import gui.gui_pattern` | Warp se non si usa 3D |
| `[mesh]` | `BoxMesh` | NiceGUI, Maya |
| `[simulation]` | adapter Warp | Maya, NiceGUI |
| `[maya]` | moduli Maya in ambiente supportato | GUI web |
| `[dev]` | pytest, Ruff, build checks | runtime production extra |

Ogni riga diventa prima un test RED eseguito in virtualenv isolato.

---

## Task 12: Rimuovere import eager non necessari dal core

**Files likely to modify:**
- `pygarment/pattern/wrappers.py`
- `pygarment/__init__.py`
- `pygarment/meshgen/__init__.py`
- `gui/gui_pattern.py`

**Approach:**

1. Aggiungere test che `import pygarment` funzioni senza CairoSVG, NiceGUI, CGAL, libigl, pyrender e Warp.
2. Spostare import pesanti nel metodo che li usa oppure introdurre adapter piccoli.
3. Non catturare genericamente `ImportError`: produrre messaggi che nominano l’extra richiesto.
4. Verificare che l’uso SVG continui a fallire chiaramente se manca CairoSVG.
5. Eseguire core test nell’ambiente minimale.

Commit separati per confine di import.

---

## Task 13: Dichiarare gli extra nel `pyproject.toml`

**Files:**
- Modify: `pyproject.toml`
- Modify: `docs/Installation.md`
- Test: `tests/packaging/test_optional_imports.py`

**Steps:**

1. Spostare NiceGUI in `gui`.
2. Spostare trimesh/libigl/pyrender/CGAL in `mesh` secondo gli import verificati.
3. Dichiarare l’integrazione Warp in `simulation`; se non installabile da indice, documentare il comando Git separato invece di aggiungere una URL fragile.
4. Trattare Maya/Qualoth come extra/documentazione condizionale.
5. Mettere pytest, Ruff, build e checker metadata in `dev`.
6. Testare ogni extra in un ambiente nuovo, non riutilizzato.
7. Aggiornare README con tabella delle capability.

**P2 exit gate:** installazione base leggera, extra verificati, messaggi di errore azionabili.

---

# Fase P3 — Manutenibilità e riduzione del rischio

## Task 14: Correggere la gerarchia delle eccezioni

**Objective:** Evitare che errori applicativi richiedano `except BaseException`.

**Files likely to modify:**
- `pygarment/pattern/core.py`
- `pygarment/meshgen/simulation.py`
- `pygarment/meshgen/boxmeshgen.py`
- `pygarment/mayaqltools/mayascene.py`
- `assets/garment_programs/meta_garment.py`
- relativi caller e nuovi test `tests/test_exceptions.py`

**TDD slices:**

1. Testare che ogni errore applicativo sia `isinstance(error, Exception)`.
2. Testare che `KeyboardInterrupt` attraversi i boundary batch/GUI.
3. Cambiare una famiglia di eccezioni alla volta da `BaseException` a `Exception`.
4. Sostituire catch larghi con tuple di errori attesi.
5. Conservare cleanup con `finally` o context manager.
6. Eseguire test core e integration dopo ogni famiglia.

Commit: uno per pattern, meshgen, Maya e garment programs.

---

## Task 15: Introdurre Ruff senza “big bang”

**Files:**
- Modify: `pyproject.toml`
- Create: `.github/workflows/lint.yml`

**Approach:**

1. Bloccare subito `E9,F63,F7,F82` sull’intero repository.
2. Applicare `I`, `F401`, `F841`, `W605` una directory alla volta.
3. Non eseguire `--fix` globale sui programmi geometrici nello stesso PR del packaging.
4. Correggere gli 11 default mutabili con test di non-condivisione stato prima della modifica.
5. Portare i warning a zero per i file toccati, mantenendo una baseline temporanea per il legacy Maya.

Verification:

```bash
ruff check . --select E9,F63,F7,F82
ruff check pygarment/garmentcode tests
pytest -m core -q
```

---

## Task 16: Spezzare i moduli ad alto accoppiamento

**Order:** solo dopo P0–P2 e copertura adeguata.

**Candidates:**
- `gui/callbacks.py`
- `pygarment/pattern/core.py`
- `pygarment/meshgen/datasim_utils.py`
- `pygarment/meshgen/garment.py`
- `pygarment/meshgen/sim_config.py`

**Proposed boundaries:**

- `gui/state.py`, `gui/layout.py`, `gui/uploads.py`, `gui/rendering.py`;
- `pygarment/pattern/serialization.py`, `normalization.py`, `validation.py`;
- `pygarment/meshgen/config.py`, `pipeline.py`, `quality.py`.

**Rules:**

1. Characterization test prima di ogni estrazione.
2. Spostare una funzione/classe per commit.
3. Nessuna modifica algoritmica durante il move.
4. Confrontare golden summary e round-trip dopo ogni commit.
5. Solo dopo estrazione verde, introdurre API più piccole.

**P3 exit gate:** eccezioni corrette, lint critico obbligatorio, moduli ridotti senza variazioni nelle fixture geometriche.

---

# Strategia di commit e PR

1. PR `test/core-characterization`
2. PR `build/fix-wheel-layout`
3. PR `ci/core-and-wheel`
4. PR `test/domain-coverage`
5. PR `build/optional-dependencies`
6. PR `refactor/exception-hierarchy`
7. PR progressivi `chore/ruff-<area>`
8. PR separati `refactor/<module-boundary>`

Ogni PR deve includere:

- obiettivo unico;
- RED osservato e riportato;
- comandi GREEN con output reale;
- rischi e rollback;
- nessun file generato;
- diff di wheel contents quando tocca packaging;
- confronto golden quando tocca geometria o serializzazione.

# Verifica finale end-to-end

Da clone pulito:

```bash
uv sync --extra dev
uv run pytest -m core -q
uv run ruff check . --select E9,F63,F7,F82
uv build --sdist --wheel
uv run pytest tests/packaging/test_wheel_install.py -v
```

Da directory esterna al checkout, in ambiente pulito:

```bash
python -m venv /tmp/pygarment-wheel-check
/tmp/pygarment-wheel-check/bin/pip install dist/pygarment-*.whl
cd /tmp
/tmp/pygarment-wheel-check/bin/python -c "import pygarment; print(pygarment.__file__)"
```

Expected: il path stampato punta a `site-packages/pygarment/__init__.py`, non al checkout.

---

# Review adversariale del piano e fix applicati

## Critica 1: rischio di un unico refactoring troppo grande

**Attacco:** packaging, test, dependency split e cleanup in un solo flusso produrrebbero un diff non revisionabile e renderebbero impossibile attribuire regressioni geometriche.

**Fix applicato:** il lavoro è stato diviso in quattro gate P0–P3 e otto PR suggeriti; packaging e refactoring algoritmico non condividono un PR.

## Critica 2: un editable install potrebbe nascondere lo stesso bug osservato

**Attacco:** testare `pip install -e .` dalla root farebbe passare `import pygarment` grazie al checkout, anche con una wheel ancora rotta.

**Fix applicato:** il wheel smoke costruisce l’artefatto, lo installa in un virtualenv nuovo e lo importa da una directory esterna; controlla anche direttamente il contenuto ZIP.

## Critica 3: correggere il package layout potrebbe dichiarare falsamente supporto Windows universale

**Attacco:** includere DLL x86-64 dentro una wheel `py3-none-any` correggerebbe alcuni ambienti Windows ma dichiarerebbe compatibilità falsa su altre architetture e allargherebbe l'attacco supply-chain.

**Fix applicato:** P0 esclude le DLL dalla wheel universale, aggiunge test che vietano librerie native nella wheel e documenta Cairo come prerequisito esterno architecture-matched.

## Critica 4: snapshot completi sarebbero fragili e ostacolerebbero modifiche legittime

**Attacco:** confrontare tutto il JSON/SVG byte-per-byte genererebbe falsi positivi per ordine, float e metadata.

**Fix applicato:** le fixture verificano proprietà semantiche, conteggi, nomi, bbox con tolleranze e XML strutturale.

## Critica 5: la simulazione esterna renderebbe la CI intrinsecamente instabile

**Attacco:** pretendere Warp, GPU, Maya e Qualoth nei job core renderebbe i test lenti o non riproducibili.

**Fix applicato:** marker e workflow separano core, mesh, GUI, simulation e Maya; i prerequisiti mancanti producono skip motivati solo nei job dedicati.

## Critica 6: separare le dipendenze prima degli import boundary romperebbe il core

**Attacco:** CairoSVG e altri package sono importati eager; spostarli subito negli extra farebbe fallire `import pygarment`.

**Fix applicato:** P2 introduce prima test di matrice e lazy import/adapters, poi modifica gli extra nel metadata.

## Critica 7: Python 3.9 potrebbe non essere più supportato dalle ultime dipendenze

**Attacco:** dichiarare 3.9 senza pin o CI potrebbe produrre una promessa falsa.

**Fix applicato:** la matrice parte da 3.9 e 3.11, ma il supporto è condizionato alla risoluzione reale; ogni extra viene installato in ambiente isolato. Un eventuale bump è una decisione esplicita, non un effetto collaterale.

## Critica 8: Ruff globale potrebbe introdurre churn e regressioni

**Attacco:** 358 rilievi e auto-fix globale genererebbero rumore e toccherebbero algoritmi geometrici senza copertura.

**Fix applicato:** si bloccano subito solo errori critici; il resto viene corretto directory per directory, dopo i characterization test.

## Critica 9: il piano iniziale non proteggeva abbastanza `KeyboardInterrupt`

**Attacco:** sostituire meccanicamente `BaseException` potrebbe cambiare cleanup e comportamento delle pipeline batch.

**Fix applicato:** Task 14 richiede test espliciti che `KeyboardInterrupt` attraversi i boundary e sposta cleanup in `finally`/context manager prima di restringere i catch.

## Critica 10: gli asset non sono chiaramente parte della distribuzione

**Attacco:** una wheel corretta del solo namespace non rende automaticamente eseguibili GUI e programmi in `assets/`.

**Fix applicato:** il piano dichiara esplicitamente la prima wheel come core library; GUI e programmi completi restano checkout-level fino a una decisione separata su package dati ed entry point.

## Esito review

Il piano revisionato evita i failure mode più probabili: source shadowing, regressioni geometriche non rilevate, supporto Windows perso, CI dipendente da software esterno e dependency split prematuro. Non rimangono blocker architetturali noti per iniziare dal Task 1; la sola decisione da rivalutare durante P2 è la disponibilità effettiva delle versioni Python/dipendenze nella matrice supportata.
