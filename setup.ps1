# ============================================================
# Master-i151 — Project Structure Setup
# ============================================================

$root = "Master-i151"

# ------------------------------------------------------------
# Directories
# ------------------------------------------------------------

$directories = @(
    # Entry point
    "$root",

    # Production code
    "$root\src",
    "$root\src\application",
    "$root\src\domain",
    "$root\src\domain\game",
    "$root\src\domain\rules",
    "$root\src\domain\strategy",
    "$root\src\infrastructure",

    # Analysis / experimentation
    "$root\analysis",
    "$root\simulation",

    # Tests
    "$root\tests",
    "$root\tests\game",
    "$root\tests\rules",
    "$root\tests\strategy",
    "$root\tests\analysis",

    # Documentation
    "$root\docs",

    # Local data / experiments
    "$root\experiments"
)

foreach ($directory in $directories) {
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
}

# ------------------------------------------------------------
# Python files — Production
# ------------------------------------------------------------

$pythonFiles = @(
    # Entry point
    "$root\bot.py",

    # Application
    "$root\src\application\__init__.py",
    "$root\src\application\decision_service.py",

    # GameState — Dioman
    "$root\src\domain\__init__.py",
    "$root\src\domain\game\__init__.py",
    "$root\src\domain\game\state.py",
    "$root\src\domain\game\cards.py",
    "$root\src\domain\game\knowledge.py",
    "$root\src\domain\game\memory.py",

    # Rules — Kanté
    "$root\src\domain\rules\__init__.py",
    "$root\src\domain\rules\rules.py",
    "$root\src\domain\rules\actions.py",
    "$root\src\domain\rules\validators.py",

    # Strategy — Maiga
    "$root\src\domain\strategy\__init__.py",
    "$root\src\domain\strategy\evaluator.py",
    "$root\src\domain\strategy\heuristics.py",
    "$root\src\domain\strategy\scoring.py",
    "$root\src\domain\strategy\decision.py",

    # Infrastructure
    "$root\src\infrastructure\__init__.py",
    "$root\src\infrastructure\arena_adapter.py",

    # Analysis — Diarra
    "$root\analysis\__init__.py",
    "$root\analysis\replay.py",
    "$root\analysis\statistics.py",
    "$root\analysis\features.py",
    "$root\analysis\patterns.py",
    "$root\analysis\experiments.py",

    # Simulation — Diarra
    "$root\simulation\__init__.py",
    "$root\simulation\runner.py",
    "$root\simulation\scenarios.py"
)

foreach ($file in $pythonFiles) {
    New-Item -ItemType File -Path $file -Force | Out-Null
}

# ------------------------------------------------------------
# Test files
# ------------------------------------------------------------

$testFiles = @(
    "$root\tests\__init__.py",

    "$root\tests\game\__init__.py",
    "$root\tests\game\test_state.py",
    "$root\tests\game\test_cards.py",
    "$root\tests\game\test_knowledge.py",
    "$root\tests\game\test_memory.py",

    "$root\tests\rules\__init__.py",
    "$root\tests\rules\test_rules.py",
    "$root\tests\rules\test_actions.py",
    "$root\tests\rules\test_validators.py",

    "$root\tests\strategy\__init__.py",
    "$root\tests\strategy\test_evaluator.py",
    "$root\tests\strategy\test_heuristics.py",
    "$root\tests\strategy\test_decision.py",

    "$root\tests\analysis\__init__.py",
    "$root\tests\analysis\test_replay.py"
)

foreach ($file in $testFiles) {
    New-Item -ItemType File -Path $file -Force | Out-Null
}

# ------------------------------------------------------------
# Documentation
# ------------------------------------------------------------

$documentationFiles = @(
    "$root\README.md",
    "$root\requirements.txt",
    "$root\.gitignore",

    "$root\docs\architecture.md",
    "$root\docs\game-rules.md",
    "$root\docs\implementation-guide.md",
    "$root\docs\patterns.md",
    "$root\docs\experiments.md"
)

foreach ($file in $documentationFiles) {
    New-Item -ItemType File -Path $file -Force | Out-Null
}

# ------------------------------------------------------------
# Initial README
# ------------------------------------------------------------

@"
# Master-i151

Bot for the i151 Arena challenge.

## Team

- Dioman Keïta — GameState & Knowledge
- Kanté — Rules & Actions
- Maiga — Strategy & Evaluation
- Diarra — Simulation & Analysis

## Architecture

\`\`\`
PlayerView
    ↓
Arena Adapter
    ↓
GameState
    ↓
Rules / Actions
    ↓
Strategy / Evaluator
    ↓
Decision
    ↓
Action
\`\`\`

## Laboratory

\`\`\`
Replay
    ↓
Analysis
    ↓
Hypothesis
    ↓
Experiment
    ↓
Validated Pattern
    ↓
Strategy
\`\`\`

## Development

The production bot must remain independent from the analysis and
simulation tooling.

The competition entry point is:

\`\`\`
bot.py
\`\`\`
"@ | Set-Content "$root\README.md" -Encoding UTF8

# ------------------------------------------------------------
# Initial .gitignore
# ------------------------------------------------------------

@"
# Python
__pycache__/
*.py[cod]
*.pyo

# Virtual environment
.venv/
venv/
env/

# Testing
.pytest_cache/
.coverage
htmlcov/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Local experiments
experiments/*
!experiments/.gitkeep

# Replays / generated data
*.replay
*.jsonl
replays/
outputs/

# Build / packaging
dist/
build/
*.zip
"@ | Set-Content "$root\.gitignore" -Encoding UTF8

# ------------------------------------------------------------
# Requirements
# ------------------------------------------------------------

@"
i151-arena-sdk
"@ | Set-Content "$root\requirements.txt" -Encoding UTF8

# ------------------------------------------------------------
# Keep empty experiment directory in Git
# ------------------------------------------------------------

New-Item -ItemType File -Path "$root\experiments\.gitkeep" -Force | Out-Null

# ------------------------------------------------------------
# Display result
# ------------------------------------------------------------

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host " Master-i151 structure created successfully" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""

Set-Location $root

tree /F