# MT5Bridge REST API

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![GitHub Repo](https://img.shields.io/badge/GitHub-liberatti%2Fmt5bridge-blue.svg?logo=github)](https://github.com/liberatti/mt5bridge)
[![Platform](https://img.shields.io/badge/Platform-Docker-blue.svg)](https://www.docker.com/)
[![Sponsor](https://img.shields.io/badge/Sponsor-♥-ea4aaa?style=flat&logo=github)](https://github.com/sponsors/liberatti)

High-performance, modular, and headless Docker environment designed to run **MetaTrader 5 (MT5)** on Linux via **WineHQ Staging**, exposing **all official `MetaTrader5` methods** through a **Python Flask REST API** powered by the **`nxcore`** framework on port `5000`.

Based on the official MQL5 article: [MetaTrader 5 on Linux](https://www.mql5.com/en/articles/625).

---

## 🚀 Key Features

- 🏗️ **Layered Architecture with nxcore**: Standardized Controllers, Services, and Logging Middleware (`nxcore.controllers.base_controller` and `nxcore.middleware.logging_manager`).
- ⚡ **100% Headless (No VNC Needed)**: Zero overhead from heavy desktop environments; runs silently in the background with `Xvfb`.
- 🚀 **High Concurrency & Multi-threading**: Production-grade multi-threaded WSGI server serving concurrent requests with configurable thread count (`THREADS=4`).
- 📊 **Structured Logging & Observability**: Standardized logging middleware with clean stack traces and response durations in milliseconds (`ms`).
- 🐍 **Full Coverage of `MetaTrader5`**: All official library methods mapped to clean HTTP REST (JSON) endpoints.
- 🔗 **Pure TCP JSON Gateway in MQL5**: Native TCP Socket JSON gateway in MQL5 (`RestGateway.mq5`), delivering ultra-low latency and direct execution without external drivers.
- 💾 **Data Persistence**: Dedicated Docker volume to permanently preserve accounts, server certificates, configurations, trade history, and cache.

---

## 📦 Project Structure

```text
.
├── Dockerfile                  # Ubuntu + WineHQ Staging + Xvfb + Linux Python container
├── docker-compose.yml          # Docker service orchestration and volume definition
├── entrypoint.sh               # Headless entrypoint script for Xvfb, MT5, and Flask API
├── requirements.txt            # Python dependencies (nxcore, Flask, Waitress, etc.)
├── README.md                   # Project documentation
├── LICENSE                     # Apache-2.0 License
├── config/
│   └── common.ini.j2           # Jinja2 template for MT5 startup configuration (common.ini)
├── mql5/
│   └── Experts/
│       └── RestGateway.mq5     # Native MQL5 Pure TCP JSON Socket Gateway
└── api/
    ├── app.py                  # Flask Application Factory and WSGI bootstrap
    ├── routes.py               # Centralized route and blueprint registration
    ├── templates/
    │   ├── swagger.html        # Interactive Swagger UI interface
    │   └── swagger.json        # OpenAPI 3.0 JSON specification
    ├── controllers/            # HTTP Interface Layer (REST Endpoints)
    │   ├── system_controller.py      # /api/version, /api/terminal_info, /api/account_info
    │   ├── symbols_controller.py     # /api/symbols_get, /api/symbol_info/<symbol>, etc.
    │   ├── market_data_controller.py # /api/copy_rates_from, /api/copy_ticks_from, etc.
    │   ├── trade_controller.py       # /api/order_send, /api/order/open, /api/positions_get, etc.
    │   └── history_controller.py     # /api/history_orders_get, /api/history_deals_get, etc.
    ├── services/               # Business Logic & MT5 Gateway Layer
    │   ├── base_service.py     # BaseService lifecycle and ensure_initialized()
    │   ├── mt5_gateway.py      # TCP Socket JSON client connected to RestGateway
    │   ├── system_service.py   # Connection, terminal status, and account info
    │   ├── symbols_service.py  # Symbol queries and Depth of Market (DOM)
    │   ├── market_data_service.py # Historical candles (OHLCV) and ticks
    │   ├── trade_service.py    # Order placement, margin/profit calculators, positions
    │   └── history_service.py  # Order and deal execution history
    └── utils/
        ├── parsers.py          # Parsers for dates, timeframes, and MT5 constants
        ├── response.py         # Response helpers delegating to nxcore base_controller
        └── template.py         # Jinja2 template renderer for common.ini
```

---

## 🛠️ Quick Start

```bash
# Clone the repository
git clone https://github.com/liberatti/mt5bridge.git
cd mt5bridge

# Start the container in background
docker compose up -d

# Follow the startup logs
docker compose logs -f
```

The REST API will be ready and accessible at `http://localhost:5000`.

---

## 📖 Swagger UI & Interactive Documentation

Access the built-in interactive Swagger UI with **100% documented endpoints**, request/response schemas, sample payloads, and the interactive "Try it out" feature:

- **Swagger UI**: [`http://localhost:5000/`](http://localhost:5000/)
- **OpenAPI 3.0 JSON Spec**: [`http://localhost:5000/swagger.json`](http://localhost:5000/swagger.json)

---

## 📡 Controllers & Endpoints Overview

All responses follow the standardized `nxcore` format:
```json
{
  "code": 200,
  "data": { ... }
}
```
Or for errors:
```json
{
  "code": 400,
  "message": "Validation Error / Bad Request",
  "details": "...",
  "url": "http://localhost:5000/api/...",
  "method": "POST"
}
```

---

### 1. `system_controller` (System & Connection)

| Endpoint | Method | MT5 Method | Description |
| :--- | :--- | :--- | :--- |
| `/api/version` | `GET` | `mt5.version()` | Returns MT5 terminal build and version |
| `/api/last_error` | `GET` | `mt5.last_error()` | Returns last error code and description |
| `/api/terminal_info` | `GET` | `mt5.terminal_info()` | Terminal state (connected, trade allowed, etc.) |
| `/api/account_info` | `GET` | `mt5.account_info()` | Account balance, equity, margin, leverage |

---

### 2. `symbols_controller` (Symbols & Market Depth)

| Endpoint | Method | MT5 Method | Description |
| :--- | :--- | :--- | :--- |
| `/api/symbols_total` | `GET` | `mt5.symbols_total()` | Total number of available symbols |
| `/api/symbols_get` | `GET` | `mt5.symbols_get()` | Lists all symbols (optional filter: `?group=*EUR*`) |
| `/api/symbol_info/<symbol>` | `GET` | `mt5.symbol_info()` | Full symbol specifications and parameters |
| `/api/symbol_info_tick/<symbol>` | `GET` | `mt5.symbol_info_tick()` | Last market tick (bid, ask, volume, time) |
| `/api/symbol_select` | `POST` | `mt5.symbol_select()` | Selects / adds a symbol to Market Watch |
| `/api/market_book_add` | `POST` | `mt5.market_book_add()` | Subscribes to Depth of Market (DOM) for symbol |
| `/api/market_book_get/<symbol>` | `GET` | `mt5.market_book_get()` | Fetches current DOM entries |
| `/api/market_book_release` | `POST` | `mt5.market_book_release()` | Unsubscribes from DOM |

---

### 3. `market_data_controller` (Historical Rates & Ticks)

| Endpoint | Method | MT5 Method | Parameters |
| :--- | :--- | :--- | :--- |
| `/api/copy_rates_from` | `GET` | `mt5.copy_rates_from()` | `symbol`, `timeframe`, `date_from`, `count` |
| `/api/copy_rates_from_pos` | `GET` | `mt5.copy_rates_from_pos()` | `symbol`, `timeframe`, `start_pos`, `count` |
| `/api/copy_rates_range` | `GET` | `mt5.copy_rates_range()` | `symbol`, `timeframe`, `date_from`, `date_to` |
| `/api/copy_ticks_from` | `GET` | `mt5.copy_ticks_from()` | `symbol`, `date_from`, `count`, `flags` |
| `/api/copy_ticks_range` | `GET` | `mt5.copy_ticks_range()` | `symbol`, `date_from`, `date_to`, `flags` |

---

### 4. `trade_controller` (Trading, Orders & Positions)

| Endpoint | Method | MT5 Method | Description |
| :--- | :--- | :--- | :--- |
| `/api/order_check` | `POST` | `mt5.order_check()` | Validates and simulates an order before placement |
| `/api/order_send` | `POST` | `mt5.order_send()` | Sends a raw trade request |
| `/api/order_calc_margin` | `POST` | `mt5.order_calc_margin()` | Calculates required margin for an order |
| `/api/order_calc_profit` | `POST` | `mt5.order_calc_profit()` | Calculates projected profit/loss |
| `/api/orders_total` | `GET` | `mt5.orders_total()` | Count of active pending orders |
| `/api/orders_get` | `GET` | `mt5.orders_get()` | List of pending orders (`?symbol=...&ticket=...`) |
| `/api/positions_total` | `GET` | `mt5.positions_total()` | Count of open positions |
| `/api/positions_get` | `GET` | `mt5.positions_get()` | List of open positions (`?symbol=...&ticket=...`) |
| `/api/order/open` | `POST` | Helper | Opens an order (`BUY`, `SELL`, `BUY_LIMIT`, etc.) |
| `/api/order/close` | `POST` | Helper | Closes an open position by ticket |
| `/api/order/modify` | `POST` | Helper | Modifies Stop Loss (SL) and Take Profit (TP) |
| `/api/order/<ticket>` | `DELETE` | Helper | Cancels a pending order |

---

### 5. `history_controller` (Historical Orders & Deals)

| Endpoint | Method | MT5 Method | Description |
| :--- | :--- | :--- | :--- |
| `/api/history_orders_total` | `GET` | `mt5.history_orders_total()` | Total historical orders count (`?date_from=...&date_to=...`) |
| `/api/history_orders_get` | `GET` | `mt5.history_orders_get()` | Details of historical orders |
| `/api/history_deals_total` | `GET` | `mt5.history_deals_total()` | Total executed deals count |
| `/api/history_deals_get` | `GET` | `mt5.history_deals_get()` | Details of executed deals |

---

## 💡 Free Demo Account Setup

1. You can open a free demo account through [MetaTrader Web Terminal](https://web.metatrader.app/terminal?mode=demo&lang=en) or the MetaTrader 5 desktop/mobile app.
2. Select the **MetaQuotes-Demo** server.
3. Configure your `MT5_LOGIN` and `MT5_PASSWORD` in `docker-compose.yml` to automatically connect on startup.

---

## 🧪 Running Automated API Tests

To validate the full API lifecycle and execute a live test trade (market buy and position close) on your demo account:

```bash
python test_api.py --url http://localhost:5000 --symbol EURUSD --volume 0.01
```

Available flags:
- `--url`: Base URL of the running API (default: `http://localhost:5000` or `API_URL` env).
- `--symbol`: Trading symbol for tick/rates/orders (default: `EURUSD`).
- `--volume`: Lot size for the test order (default: `0.01`).
- `--no-close`: Keeps the test position open instead of automatically closing it.

---

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](file:///home/liberatti/workspace/github.com/liberatti/mt5bridge/LICENSE) file for details.