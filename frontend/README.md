# Kalshi NBA Paper Trading Dashboard

A cyberpunk-themed trading terminal for monitoring and managing NBA paper trades on Kalshi prediction markets.

![Dashboard Preview](https://via.placeholder.com/800x400/0a0e17/00f0ff?text=Kalshi+NBA+Terminal)

## Tech Stack

- **Framework:** React 18
- **Build Tool:** Vite
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **Routing:** React Router v6
- **Icons:** Lucide React

## Design Aesthetic

**Cyberpunk Trading Terminal** - Dark, high-contrast interface with electric neon accents. Sharp geometric shapes, glowing borders, and data that feels alive.

**Color Palette:**
- Background: Deep space blacks (`#0a0e17`, `#111827`)
- Primary accent: Electric cyan (`#00f0ff`)
- Profit: Neon green (`#00ff88`)
- Loss: Hot red (`#ff3366`)
- Warning: Amber (`#ffcc00`)

**Typography:**
- Display: Orbitron (geometric, futuristic)
- Data: JetBrains Mono (crisp monospace)
- UI: Outfit (clean geometric sans)

## Getting Started

### Prerequisites

- Node.js 18+ (LTS recommended)
- npm or yarn

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Production Build

```bash
npm run build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Layout.tsx      # Main layout wrapper
│   │   │   ├── Header.tsx      # Top navigation bar
│   │   │   └── Sidebar.tsx     # Left navigation menu
│   │   └── ui/
│   │       ├── Panel.tsx       # Card-like container
│   │       ├── Button.tsx      # Button component
│   │       └── Badge.tsx       # Status badges
│   ├── data/
│   │   └── mockData.ts         # All hardcoded mock data
│   ├── pages/
│   │   ├── GamesPage.tsx       # /
│   │   ├── StrategiesPage.tsx  # /strategies
│   │   ├── TradingPage.tsx     # /trading
│   │   ├── PnLPage.tsx         # /pnl
│   │   └── RiskPage.tsx        # /risk
│   ├── App.tsx                 # Router setup
│   ├── main.tsx                # Entry point
│   └── index.css               # Global styles
├── public/
│   └── vite.svg                # Favicon
├── package.json
├── tailwind.config.js
├── tsconfig.json
├── vite.config.ts
├── FRONTEND_API_INTEGRATION.md # Backend integration guide
└── README.md                   # This file
```

## Pages

### Games (`/`)
- View and manage loaded NBA games
- See market orderbooks with bid/ask prices
- Browse and load games by date
- Place orders (Buy Yes/No buttons)

### Strategies (`/strategies`)
- View all trading strategies
- Enable/disable strategies
- See strategy configurations (JSON)
- Live signals feed with real-time updates

### Trading (`/trading`)
- Open positions table with P&L
- Order history with status badges
- Close positions functionality

### P&L (`/pnl`)
- Portfolio performance summary
- Total/unrealized/realized P&L
- Win rate and profit factor
- Position breakdown table

### Risk (`/risk`)
- Risk controls status (enabled/disabled)
- Progress bars for limit usage
- Loss streak and cooldown status
- All 12 risk limits configuration

## Current Status

This is a **static UI** with mock data. No backend connection.

### Implemented
- [x] All 5 pages with full UI
- [x] Responsive layout
- [x] Dark theme styling
- [x] Mock data for all components
- [x] Navigation routing

### Not Implemented (Next Phase)
- [ ] API client for backend calls
- [ ] WebSocket connection for real-time data
- [ ] State management (Zustand)
- [ ] Loading/error states
- [ ] Toast notifications

## Backend Integration

See [FRONTEND_API_INTEGRATION.md](./FRONTEND_API_INTEGRATION.md) for detailed API mapping.

## Environment Variables

Create `.env` for backend integration:

```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

## Development Notes

- All prices are in cents (¢)
- Use `font-mono` for numeric data
- Use `font-display` for headings
- Green = profit/success, Red = loss/danger
- Neon glow effects for important data

## License

Internal project - not for distribution.
