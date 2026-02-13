# SpotOnSight Web App (Vue)

Vue 3 + Vite implementation that mirrors the mobile app architecture and features:

- Auth-first flow (register/login/help)
- Spot CRUD with image upload (base64)
- Favorites, shares, and follow/unfollow basics
- Notifications with copyable technical details
- Registry-driven component/action composition (controller-like orchestration)

## UI Stack

- Bootstrap 5 + Bootswatch (Flatly) for modern base design
- Bootstrap Icons for consistent iconography
- AOS (Animate On Scroll) + Vue transitions for page/notification motion
- Custom visual layer for gradients, glassy alerts, and modal/map polish

## Run

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```

## Environment Variables

Create `.env` in `webapp/` if needed:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_SUPPORT_EMAIL=support@spotonsight.app
```
