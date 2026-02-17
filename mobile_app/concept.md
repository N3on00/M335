# SpotOnSight Concept

## 1. Purpose and Scope

This document defines the product concept for SpotOnSight in the context of uK M335.
It captures the idea behind the app, the target users, the required features, the chosen architecture, the technology decisions, and the available mockups.

The goal is to make design and implementation decisions traceable for project review and future continuation.

## 2. App Vision and Value

SpotOnSight is a leisure-focused location app.

The app should help people:

- discover useful or beautiful places,
- save and organize these places,
- share spots with others,
- and coordinate shared outdoor or chill activities more easily.

The main value is reducing friction between "I want to go outside" and "I know where to go".

## 3. Target Group

Primary audience:

- people who actively spend free time outside,
- small friend groups who plan simple meetups,
- users who like location-based exploration.

Design implication:

- the app is intentionally broad and not niche-branded,
- language stays simple and neutral,
- interactions must be quick on mobile (few taps from map to action).

## 4. Requirements

### 4.1 Functional Requirements

- **FR-01 Authentication**: users can register, log in, log out, and restore session state.
- **FR-02 Spot Map**: users can view spots on an interactive map with accurate coordinates.
- **FR-03 Spot Creation**: users can create, edit, and delete their own spots.
- **FR-04 Spot Discovery**: users can filter spots by text, tags, owner, visibility, radius, and favorites.
- **FR-05 Spot Detail Actions**: users can open spot details, jump to spot location, favorite/unfavorite, and share.
- **FR-06 Social Layer**: users can follow/unfollow, view social feed sections, and discover friend-related content.
- **FR-07 Profile and Settings**: users can maintain profile data and app settings.
- **FR-08 Support Flow**: users can submit support requests.
- **FR-09 Cross-Platform Delivery**: the same frontend must run as web, Android, and iOS (Capacitor shells).
- **FR-10 Persistence**: user, spot, and social data must be stored persistently in MongoDB via backend APIs.

### 4.2 Non-Functional Requirements

- **NFR-01 Maintainability**: clear layering and reusable generic patterns so new features do not require rewriting base flows.
- **NFR-02 Reliability**: core map/social flows must be covered by automated tests (frontend + backend).
- **NFR-03 Usability**: mobile-first interactions (safe areas, compact controls, map-first actions).
- **NFR-04 Performance**: map and feed interactions should remain responsive under normal class-project data volume.
- **NFR-05 Security Baseline**: authenticated routes protected with JWT; no hardcoded production secrets.
- **NFR-06 Deployability**: project can be built for browser, Android, and iOS from one active client codebase.

## 5. Mockups

Main mockup source (Figma):

- https://www.figma.com/make/x9vrI65NL5HTfRvbtwK6dG/SpotOnSight-Mobile-App-UI?fullscreen=1&t=XXBlkcf2q9mBLpD0-1

Covered views for concept validation:

- Authentication (login/register)
- Home/Discover
- Map workspace (map + filters + result cards)
- Spot details modal
- Spot editor modal
- Social hub
- Profile
- Settings
- Support form

Mockups are used as direction, not pixel-locked contracts. During implementation, spacing and component behavior are adjusted for real content and mobile constraints.

## 6. App Functions

Core user stories:

- As a user, I want to browse a map with marked spots so I can quickly find places.
- As a user, I want to filter spots by area and category/tag so results match my needs.
- As a user, I want to create and share spots so I can contribute my own discoveries.

Extended implemented functions:

- Favorite management
- Share flow (backend logging + native/browser share fallback)
- Filter subscription snapshots for change alerts
- Owner profile lookup in map/social views
- Mobile shell support for Android and iOS

## 7. Architecture

### 7.1 Structure and Communication

SpotOnSight is split into two main runtime parts:

- **Client**: Vue web app (`webapp/`) as the active UI codebase.
- **Server**: FastAPI backend (`backend/`) for auth, spot/social operations, and persistence access.

Communication is HTTP/JSON between frontend services and backend endpoints.
MongoDB is only accessed by backend-side code.

### 7.2 Applied Patterns

- Frontend uses a layered, MVC-like flow:
  - screen/view composition,
  - behavior/controller orchestration,
  - service layer for API communication,
  - model helpers for mapping/normalization.
- Backend uses router + service/repository-oriented separation with DTO boundaries.

### 7.3 Why This Architecture Fits This Project

I chose this structure because the project is intended to continue after M335.
Generic registrations and shared behavior reduce repetitive wiring and make feature growth faster.
Keeping one active frontend and wrapping it for mobile avoids parallel feature development in separate clients.

## 8. Technology Choices

Active stack:

- **Vue 3 + Vite** for the active frontend because the current UI architecture and component system are already built around it.
- **Capacitor (Android/iOS shells)** so the same frontend can be shipped on mobile stores without rebuilding features per platform.
- **FastAPI + Uvicorn** for backend APIs because it fits the existing Python backend direction and quick iteration needs.
- **MongoDB** because spot/social data is document-shaped and evolved frequently during feature changes.
- **Vitest + Pytest** for automated validation of frontend and backend behavior.

Historical note:

- The project started with a **Python Kivy** client (`app/`) as the first cross-platform prototype.
- Active delivery later moved to the Vue + Capacitor path; the Python app remains as historical project evidence.

## 9. Related Project Documents

- `README.md` (setup and execution)
- `ARCHITECTURE.md` (technical architecture details)
- `API_SPEC.md` (API contract)
- `docs/test-concept.md` (test strategy)
- `docs/test-protocol.md` (executed tests)
- `docs/mobile-cross-platform-plan.md` (mobile rollout plan)
