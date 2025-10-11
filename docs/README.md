# 📘 MSR Documentation

Welcome to the internal documentation of **My Smart Road (MSR)** —  
an AI-powered ecosystem for route optimization, IFTA automation, and intelligent trucking.

---

## 🧱 Project Structure

msr-app/
│
├── docs/
│ ├── flow.md # User journey (onboarding → route → IFTA)
│ ├── architecture.md # System architecture & API logic
│ ├── ui-kit.md # Design tokens & components
│ └── design/
│ └── icons/
│ └── msr_logo.png
│
├── frontend/ # React Native / Expo mobile app
├── backend/ # FastAPI / Node.js backend
├── LICENSE
└── README.md # Main project overview

---

## ⚙️ Architecture Overview

- **Frontend (Mobile):** Built in React Native with Expo.  
  Handles map rendering, fuel logic, and live driver interface.  
- **Backend:** FastAPI (Python) with modular REST endpoints (Fuel, Route, IFTA).  
- **Database:** Firebase / Supabase for authentication & storage.  
- **AI Layer:** Aggregates data from Fuel + Toll + Weather APIs for optimization.

More details in [`architecture.md`](architecture.md).

---

## 🧭 User Flow

See [`flow.md`](flow.md) for full journey:  
From onboarding and truck setup to fuel optimization and IFTA summary.

---

## 🎨 UI Kit

Visual components, icons, and design tokens are listed in [`ui-kit.md`](ui-kit.md).  
This includes colors, typography, and reusable interface elements.

---

## 🧩 Integrations

| Integration | Description |
|--------------|-------------|
| Fuel APIs | TA, Pilot, Loves, Petro networks |
| Weather | NOAA + OpenWeather real-time data |
| Maps | Google Maps / Mapbox SDK |
| IFTA | State tax & mileage aggregation |
| Tolls | TollGuru / custom route calculation |

---

## 🚀 Development Setup

> _This section will expand when coding begins._

- Fork the repo and clone locally  
- `npm install` for dependencies  
- `expo start` to run the app  
- `.env` to store API keys for fuel/weather/IFTA

---

## 🛡 License

Licensed under the [MIT License](../LICENSE).  
© 2025 **Lafwiron Projects**

---

*Smart roads start here — optimized fuel, time & peace of mind.*
