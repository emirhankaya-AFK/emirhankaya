# Job Tracker & Automation

[English](README.md) | [Türkçe](README_TR.md) | [Deutsch](README_DE.md)

FastAPI-Anwendung zum Speichern von Stellenanzeigen, Erklären von Skill-Matches und Verwalten des Bewerbungsstatus.

![Demo](docs/demo.svg)

## Funktionen
- Statusfluss: saved, applied, interview, rejected
- Python/FastAPI/SQL/Docker-Skill-Matching
- Parsing echter Gehälter in USD, EUR, GBP und TRY
- Filter für volunteer, unpaid, equity-only und token-only Angebote
- Erweiterungspunkte für Playwright und PostgreSQL

## Start

    pip install -e ".[dev]"
    uvicorn app.main:app --reload
    pytest -q

Nur Angebote mit realer Geldvergütung sollten in eine Bewerbungsliste gelangen.

