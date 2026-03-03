# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Selenium-based automation tool for listing and deleting items on Facebook Marketplace. The UI is in **Hebrew** — all selectors, labels, and text matching use Hebrew strings.

## Environment Setup

- **Python venv**: `.venv/bin/python` (Python 3.10, selenium 4.21.0)
- Always run with: `.venv/bin/python main.py`
- Install deps: `pip install -r requirements.txt` or use `uv sync` (pyproject.toml exists)
- Credentials: `facebook_credentials.env` (FACEBOOK_EMAIL, FACEBOOK_PASSWORD)
- Cookies stored per-account in `.{email}/cookies.pkl`

## Architecture

**Lister** (`Lister.py`) — Main orchestrator. Handles Chrome driver setup, cookie-based login, credential login, and two core flows:
- `list(item)` — Creates a marketplace listing by driving the create-item form
- `delete_all_items()` — Deletes all listings from the selling page. Uses a JS-first strategy (fast, bypasses overlays) with Selenium fallback selectors. Tracks fallback usage and prints a prompt to update selector priority.

**Item** (`Lister.py`, line ~700) — Nested in the same file as Lister. Handles individual listing form interactions: image upload, title, price, category, condition, location, description, SKU, hide-from-friends, next, publish.

**Element** (`Element.py`) — XPath-based element resolver. Reads element definitions from `elements-{locale}.json`, supports parameterized XPaths with defaults via `format_xpath`.

**Helpers** (`Helpers.py`) — JSON read/write, XPath formatting (`format_xpath`), directory creation.

**Locales** (`locales.py`) — `Locale` enum. Currently hardcoded to `Locale.Hebrew` in both Lister and Element.

**Element definitions** (`elements-he.json`, `elements-en.json`) — JSON files mapping element names to XPath selectors, types (button/input/element), and default values.

**Entry point** (`main.py`) — Imports product dicts from `items_to_publish.py`, calls `list_my_personal_items()` or `delete_my_items()`.

## Key Patterns

- **Hebrew selectors**: All Facebook DOM interaction uses Hebrew aria-labels and text. Key strings: `'אפשרויות נוספות עבור'` (more options), `'מחיקת המודעה'` (delete listing), `'מחיקה'` (confirm delete), `'מחיקת מודעה'` (delete dialog label).
- **JS clicks preferred over Selenium clicks**: `_js_click_menu_item()` and `_js_click_dialog_button()` bypass overlay interception issues. Selenium is fallback only.
- **`_safe_click()`**: Catches `ElementClickInterceptedException` and falls back to JS click.
- **Multiple `role='dialog'` elements**: Must scope to the correct dialog by `aria-label` containing `'מחיקת מודעה'` — unscoped selectors hit the wrong dialog.
- **Selector ordering matters**: `delete_all_items()` tries selectors in list order and reports when non-primary selectors succeed, suggesting reordering.
- **`typing.List`** not `list[str]` — Python 3.8 compat style used throughout.
