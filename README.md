# 🚀 Galaxium Travels - Interplanetary Booking System

A full-stack app for booking interplanetary flights: a React frontend and a FastAPI backend that serves both a REST API and an MCP (Model Context Protocol) server from the same process.

## 🌟 Features

- **Space-themed UI** - Responsive interface with an animated starfield
- **Four seat classes** - Economy, Flexi, Business and Galaxium, each with its own price and seat inventory
- **Fare rules & refunds** - Per-class refund rules, with a refund preview before cancelling
- **Dual protocol backend** - Every operation is available via REST and as an MCP tool
- **Type-safe** - Strict TypeScript frontend and typed Python backend
- **Simple identity** - Name + email sign-in (stored in `localStorage`, no passwords)

## 🏗️ Architecture

```
galaxium-travels/
├── booking_system_backend/     # FastAPI + FastMCP + SQLAlchemy (SQLite)
│   ├── server.py              # REST routes and MCP tools
│   ├── services/              # Business logic (shared by REST and MCP)
│   ├── models.py              # ORM models
│   ├── schemas.py             # Pydantic schemas, pricing and refund rules
│   ├── seed.py                # Demo data
│   └── tests/                 # pytest suite
│
├── booking_system_frontend/    # React 19 + Vite + TypeScript + Tailwind
│   └── src/
│       ├── components/        # Reusable UI components
│       ├── pages/             # Home, Flights, MyBookings
│       ├── services/          # API client
│       └── types/             # Shared TypeScript types
│
└── start.sh                   # Starts backend and frontend (macOS/Linux)
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** - Python env/package manager (`brew install uv`)
- **Node.js 18+** and npm

### Option 1: One command (macOS/Linux)

```bash
./start.sh
```

This creates the Python venv, installs dependencies, then starts the backend (port 8080) and frontend (port 5173) in one terminal. Press `Ctrl+C` to stop both.

### Option 2: Manual start

Backend:
```bash
cd booking_system_backend
uv venv --python 3.11 .venv
uv pip install -r requirements.txt
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python server.py
```

Frontend (new terminal):
```bash
cd booking_system_frontend
npm install
npm run dev
```

> Windows users: there is no `start.bat`; use the manual steps above.

## 🌐 Endpoints

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8080 |
| Swagger docs | http://localhost:8080/docs |
| MCP endpoint | http://localhost:8080/mcp |

## 📚 Documentation

- [Backend README](booking_system_backend/README.md) - API endpoints, MCP tools, database schema, testing
- [Frontend README](booking_system_frontend/README.md) - components, styling, build, deployment

## 🎯 User Guide

### Booking a flight

1. **Browse** - Open the Flights page to see all routes
2. **Search** - Filter by origin or destination
3. **Sign in** - Click "Book Now" and enter your name and email
4. **Pick a seat class** - Compare prices and availability, then confirm
5. **Manage** - View bookings and cancel from "My Bookings"; the cancel dialog shows your refund first

### Seat classes and refunds

Prices are the flight's base price × the class multiplier. Refund rules are applied at cancellation time.

| Class | Price multiplier | Refund | Refund window |
|---|---|---|---|
| Economy | ×1.0 | 80% | more than 72h before departure |
| Flexi | ×1.5 | 100% | more than 24h before departure |
| Business | ×3.0 | 75% | any time before departure |
| Galaxium | ×6.0 | 100% | any time before departure |

The source of truth is `SEAT_CLASS_MULTIPLIERS` and `REFUND_RULES` in [`booking_system_backend/schemas.py`](booking_system_backend/schemas.py).

### Demo data

The database is **cleared and re-seeded on every backend start**, so changes don't persist across restarts. It contains:
- **10 users** - Alice, Bob, Charlie, Diana, Eve, Frank, Grace, Heidi, Ivan, Judy (e.g. `alice@example.com`)
- **10 flights** - Routes between Earth, Mars, Moon, Venus, Jupiter, Europa and Pluto (all departing in 2099)
- **20 sample bookings** - Mixed statuses and seat classes

## 🛠️ Technology Stack

**Backend:** FastAPI, SQLAlchemy, Pydantic, FastMCP, SQLite, Uvicorn

**Frontend:** React 19, TypeScript, Vite, Tailwind CSS, Framer Motion, React Router, Axios, React Hot Toast, Lucide icons

## 🧪 Testing

```bash
# Backend (must run from booking_system_backend/)
cd booking_system_backend && pytest

# Frontend: type-check + production build, and lint
cd booking_system_frontend && npm run build && npm run lint
```

The frontend has no test runner.

## 📦 Production Deployment

Backend:
```bash
cd booking_system_backend
uv pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8080
```

A `Dockerfile` is provided for the backend only:
```bash
docker build -t galaxium-backend booking_system_backend
docker run -p 8080:8080 galaxium-backend
```

Frontend:
```bash
cd booking_system_frontend
npm run build   # deploy the 'dist' folder to any static host
```

## 🎨 Customization

**API URL** - copy `booking_system_frontend/.env.example` to `.env` and edit (defaults to `http://localhost:8080`):
```env
VITE_API_URL=https://your-api-url.com
```

**Theme colors** - edit `booking_system_frontend/tailwind.config.js`, then use the tokens (e.g. `cosmic-purple`, `nebula-pink`) via Tailwind classes.

## 🐛 Troubleshooting

**Backend won't start**
- Check Python 3.11+: `python --version`
- Check port 8080 is free
- Reinstall dependencies: `uv pip install -r requirements.txt`

**Schema changes not showing up**
- There are no migrations. After editing `models.py`, delete `booking_system_backend/booking.db`.

**Frontend won't start**
- Check Node 18+: `node --version`
- Check port 5173 is free
- Reinstall: `rm -rf node_modules && npm install`

**Connection issues**
- Confirm the backend is running at http://localhost:8080
- Check `VITE_API_URL` in the frontend `.env`
- Check CORS settings in `server.py`
- Note: REST errors return HTTP 200 with `{success: false, error, error_code, details}`; only invalid requests return 422.

## 📄 License

Apache 2.0 - see [LICENSE](LICENSE).

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes and run the tests
4. Submit a pull request

---

**Built with ❤️ for space travelers** 🚀✨
