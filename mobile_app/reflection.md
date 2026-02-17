# Reflection

## 1. Project Scope and Goal
This project was created in the context of uK M335 as **SpotOnSight**, a map-based app for discovering, saving, and sharing leisure spots.

My goal was not only to build a working app, but also to improve the codebase quality over time: clearer architecture, better testing, and cleaner documentation.

## 2. Design Reference
Main mockup source (Figma):  
https://www.figma.com/make/x9vrI65NL5HTfRvbtwK6dG/SpotOnSight-Mobile-App-UI?fullscreen=1&t=XXBlkcf2q9mBLpD0-1

## 3. How the Project Evolved
At the beginning, I started with a Python/Kivy client because it was the fastest cross-platform path I knew at the time.  
That phase helped me validate core ideas quickly (auth flow, session behavior, map interactions).

As the project got larger, I realized that continuing with this direction would slow down long-term feature delivery.  
After improving my web/mobile knowledge, I moved the active implementation to a Vue frontend with FastAPI + MongoDB backend and used Capacitor for Android/iOS packaging.

This pivot was one of the most important decisions in the project: one active frontend, one backend, and mobile wrappers instead of parallel app implementations.

## 4. What Went Well
- The product vision stayed stable through technical changes.
- The project now has a clear active stack and better architectural structure.
- Mobile integration baseline (Android/iOS shells) is implemented.
- Several reliability issues were solved in map/social behavior:
  - better map edge hint behavior,
  - improved “Go to” flow,
  - stronger share fallback behavior,
  - more reliable filter subscription handling.
- Testing quality improved significantly:
  - frontend regression tests pass,
  - mobile-focused tests pass,
  - backend tests pass.
- Documentation quality is much better than in the early project phase.

## 5. Main Challenges
- The biggest challenge was changing direction without losing momentum.
- During refactoring, some modules became too large before being split.
- There were edge cases in backend/frontend ID handling (legacy string IDs vs ObjectId-like flows).
- Mobile integration is technically ready, but release-signing automation for store delivery is still open work.

## 6. What I Learned
- A fast prototype is useful, but architecture needs to be revisited once complexity grows.
- Reusable patterns and generic registrations reduce repetitive coding and make future work easier.
- Small UX details (default states, smooth navigation, fallback behavior) matter a lot to overall quality.
- Test evidence and execution protocol are essential deliverables, not optional extras.
- Clear decision documentation prevents confusion when the project evolves.

## 7. What I Would Do Differently
If I started again, I would:
- define architecture boundaries earlier,
- introduce automated tests earlier in the project lifecycle,
- avoid allowing large orchestration files to grow too much before extracting logic,
- prepare release/signing pipeline requirements earlier.

## 8. Final Assessment
Overall, the project went well and improved significantly over time.  
The project is now in a stronger technical state than the initial version: cleaner structure, better reliability, better testing, and better documentation.

Most importantly, I can continue this project after M335 on a maintainable foundation.