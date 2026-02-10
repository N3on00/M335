# SpotOnSight Mobile (Kivy) – MVC + Registry/Decorators

This is a **starter skeleton** designed for:
- DRY/KISS structure
- MVC-ish separation (View/Screens, Controller, Data/DTO/Services)
- **Decorator-based auto-registration** of UI components and actions
- Per-container registries so views can stay generic and extensible

## Run (desktop dev)
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Notes
- Mobile packaging (Android) comes later (Buildozer).
- Map screen is a placeholder; we’ll plug in `kivy-garden.mapview` when you want.
