<p align="center">
  <img src="assets/logo.svg" alt="MT5Bridge REST API" width="680" />
</p>

<p align="center">
  <a href="https://opensource.org/licenses/Apache-2.0"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License" /></a>
  <a href="https://www.docker.com/"><img src="https://img.shields.io/badge/Platform-Docker-blue.svg?logo=docker" alt="Docker" /></a>
  <a href="https://github.com/sponsors/liberatti"><img src="https://img.shields.io/badge/Sponsor-♥-ea4aaa?style=flat&logo=github" alt="Sponsor" /></a>
</p>

High-performance, modular, and headless Docker solution designed to run **MetaTrader 5 (MT5)** on Linux via **WineHQ Staging**, exposing **all official MetaTrader 5 methods** through a robust **Python Flask REST API** with built-in **interactive Swagger UI / OpenAPI 3.0** documentation.

Based on the official MQL5 reference: [MetaTrader 5 on Linux](https://www.mql5.com/en/articles/625).


---

## ✨ Key Features

- 🐳 **Headless Linux Environment**: Runs MT5 terminal silently using WineHQ Staging + Xvfb virtual display with zero GUI overhead.
- 📖 **Built-in Interactive Swagger UI**: Full OpenAPI 3.0 documentation served at the root URL (`/`) with interactive *"Try it out"* request execution.
- ⚡ **Full MT5 Python API Coverage**: 100% method compatibility for Account, Symbols, Depth of Market (DOM), Historical Rates & Ticks, Orders, Positions, and Deals.
- 🛠️ **High-Level Trading Helpers**: Simplified endpoints for opening market/pending orders, modifying SL/TP, and closing positions.
- 🧱 **Standardized JSON Schema**: Predictable response structure and error handling powered by the `nxcore` framework.
- 🔄 **Auto-Recovery & Reconnect**: Background connection watchdog, automated initialization, and persistent Wine prefix volumes.

---

## 🏗️ Architecture Overview

```text
┌───────────────────────────────────────────────────────────┐
│                    Client Applications                    │
│   (Web Apps / Python Scripts / Trading Bots / Postman)    │
└─────────────────────────────┬─────────────────────────────┘
                              │ HTTP / REST (Port 5000)
                              ▼
┌───────────────────────────────────────────────────────────┐
│                  Docker Container: mt5bridge              │
│                                                           │
│   ┌───────────────────────────────────────────────────┐   │
│   │  Swagger UI / OpenAPI 3.0 Documentation (/)       │   │
│   │  Flask REST API (Waitress Multi-threaded WSGI)    │   │
│   └─────────────────────────┬─────────────────────────┘   │
│                             │ TCP Socket (Port 22347)     │
│                             ▼                             │
│   ┌───────────────────────────────────────────────────┐   │
│   │  RestGateway Expert Advisor (MQL5)                │   │
│   │  MetaTrader 5 Terminal 64-bit                     │   │
│   │  WineHQ Staging + Xvfb Display Server             │   │
│   └─────────────────────────┬─────────────────────────┘   │
└─────────────────────────────┼─────────────────────────────┘
                              │ TCP (Broker Protocol)
                              ▼
┌───────────────────────────────────────────────────────────┐
│             MetaTrader 5 Broker Trading Server            │
└───────────────────────────────────────────────────────────┘
```

---

## 📖 Swagger UI & Interactive Documentation

MT5Bridge comes with a **pre-configured, interactive Swagger UI** embedded directly into the service. You can explore all routes, review data models, inspect required query parameters, and execute live API requests directly from your browser.

- 🌐 **Interactive Swagger UI**: [`http://localhost:5000/`](http://localhost:5000/)
- 📄 **OpenAPI 3.0 Specification (JSON)**: [`http://localhost:5000/swagger.json`](http://localhost:5000/swagger.json)
- 💡 **Content Negotiation**: Requesting `http://localhost:5000/?format=json` or setting header `Accept: application/json` returns the raw OpenAPI specification.

![Swagger UI Preview](https://raw.githubusercontent.com/swagger-api/swagger-ui/master/flavor/swagger-ui.png)

---

## 🛠️ Quick Start

### 1. Run with Docker CLI

```bash
# Pull the latest Docker image
docker pull liberatti/mt5bridge:latest

# Run container with your demo or live broker credentials
docker run -d --name mt5bridge \
  -p 5000:5000 \
  -p 22347:22347 \
  -e MT5_LOGIN=999999999 \
  -e MT5_PASSWORD=YourPassword \
  -e MT5_SERVER=MetaQuotes-Demo \
  -e MT5_STARTUP_SYMBOL=EURUSD \
  -e MT5_STARTUP_PERIOD=H1 \
  liberatti/mt5bridge:latest
```

### 2. Run with Docker Compose (Recommended)

Use the provided [docker-compose.yml](file:///c:/devs/python/projetos_financeiros/mt5bridge/docker-compose.yml) configured with independent broker services:

```yaml
volumes:
  mt5_xp_data:
    driver: local
  mt5_btg_data:
    driver: local

services:
  mt5_xp:
    build:
      context: .
      dockerfile: Dockerfile
    image: liberatti/mt5bridge:latest
    ports:
      - "5000:5000"
      - "22347:22347"
    environment:
      - MT5_STARTUP_SYMBOL=PETR4
      - MT5_STARTUP_PERIOD=M1
      - MT5_LOGIN=999999999
      - MT5_PASSWORD=YourPassword
      - MT5_SERVER=XPMT5-DEMO
      - MT5_INVESTOR=999999999
      - SECURITY_ENABLED=false
      - API_KEY=YourApiKey
    volumes:
      - mt5_xp_data:/home/mt5user/.mt5

  mt5_btg:
    build:
      context: .
      dockerfile: Dockerfile
    image: liberatti/mt5bridge:latest
    ports:
      - "5001:5000"
      - "22348:22347"
    environment:
      - MT5_STARTUP_SYMBOL=PETR4
      - MT5_STARTUP_PERIOD=H1
      - MT5_LOGIN=xxxxx
      - MT5_PASSWORD=xxxxx
      # BTG Pactual opera apenas em ambiente de produção (PRD), não disponibiliza ambiente DEMO
      - MT5_SERVER=BancoBTGPactual-PRD
      - MT5_INVESTOR=xxxxx
      - SECURITY_ENABLED=false
      - API_KEY=xxxxx
    volumes:
      - mt5_btg_data:/home/mt5user/.mt5
```

Start the containers in the background:
```bash
# Start all brokers:
docker compose up -d

# Or start a specific broker instance:
docker compose up -d mt5_xp
docker compose up -d mt5_btg
```

Once running, access the interactive Swagger UI and REST API:
- **XP Investimentos instance**: [`http://localhost:5000/`](http://localhost:5000/) (TCP Gateway: `22347`)
- **BTG Pactual instance**: [`http://localhost:5001/`](http://localhost:5001/) (TCP Gateway: `22348`)

---

## ⚙️ Configuration & Environment Variables

| Variable | Default | Description |
| :--- | :--- | :--- |
| `MT5_LOGIN` | `""` | MetaTrader 5 account login number |
| `MT5_PASSWORD` | `""` | MetaTrader 5 account master password |
| `MT5_SERVER` | `MetaQuotes-Demo` | Broker trade server hostname or label (e.g. `MetaQuotes-Demo`, `XPMT5-DEMO`, `XPMT5-PRD`, `BancoBTGPactual-PRD`) |
| `MT5_INVESTOR` | `""` | Investor (read-only) password (optional) |
| `MT5_STARTUP_SYMBOL` | `EURUSD` | Default chart symbol initialized on startup (automatically adapts to `PETR4` for B3 brokers like XP and BTG) |
| `MT5_STARTUP_PERIOD` | `H1` | Default chart timeframe (`M1`, `M5`, `M15`, `H1`, `D1`, etc.) |
| `SECURITY_ENABLED` | `true` | Enables or disables API authentication verification |
| `API_KEY` | `""` | Secret API key required in `x-api-key` HTTP request header |
| `PORT` | `5000` | HTTP port exposed by the REST API |
| `HOST` | `0.0.0.0` | Bind host for Flask/Waitress server |
| `LOGLEVEL` | `INFO` | Application log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `THREADS` | `8` | Worker threads for Waitress WSGI production server |
| `MT5_STARTUP_TIMEOUT`| `90` | Max seconds to wait for MT5 & EA gateway startup |
| `SCREEN_RESOLUTION` | `1024x768x24` | Resolution for virtual framebuffer display (Xvfb) |

---

### 🏛️ Multi-Broker Support & `servers.dat`

The vanilla MetaQuotes installer only includes default connectivity to `MetaQuotes-Demo`. For private broker clusters such as **XP Investimentos** (`XPMT5-DEMO`, `XPMT5-PRD`) and **BTG Pactual** (`BancoBTGPactual-PRD`), the terminal requires a network access point catalog stored in **`config/servers.dat`**.

- **Pre-configured Catalogs**: The repository bundles `config/servers.dat`, `config/servers_xp.dat` and `config/servers_btg.dat` containing verified server endpoints for **XP Investimentos**, **BTG Pactual** and **MetaQuotes**.
- **Automatic Broker Detection**:
  - When `MT5_SERVER=XPMT5-DEMO` or `XPMT5-PRD`, the container automatically loads `servers_xp.dat` and defaults `MT5_STARTUP_SYMBOL` to `PETR4` (compatible with B3).
  - When `MT5_SERVER=BancoBTGPactual-PRD` or any server containing `BTG`, the container automatically loads `servers_btg.dat` and defaults `MT5_STARTUP_SYMBOL` to `PETR4` (compatible with B3).
  - When `MT5_SERVER=MetaQuotes-Demo`, it defaults to `EURUSD` (compatible with Forex demo).
> [!NOTE]
> **BTG Pactual Environment**: O BTG Pactual disponibiliza conexões MetaTrader 5 exclusivamente em ambiente de **produção (`BancoBTGPactual-PRD`)**; a instituição não possui ambiente `DEMO`. Para testes simulados na B3 utilize os servidores DEMO da XP (`XPMT5-DEMO`).
- **Adding Other Brokers**: To add other custom brokers (e.g., Clear, Genial), copy the `servers.dat` file from an existing Windows MT5 installation (`%APPDATA%\MetaQuotes\Terminal\<ID>\config\servers.dat`) into the project's `config/` folder before rebuilding.

---

## 📡 API Reference & Endpoints

All responses follow a consistent `nxcore` structure:

```json
// Success Response (HTTP 200)
{
  "code": 200,
  "data": { ... }
}

// Error Response (HTTP 400 / 500)
{
  "code": 400,
  "message": "Validation Error / Bad Request",
  "details": "...",
  "url": "http://localhost:5000/api/...",
  "method": "POST"
}
```

---

### 1. System & Account (`/api/...`)

| Endpoint | Method | Underlying MT5 Call | Description |
| :--- | :---: | :--- | :--- |
| `/api/login` | `POST` | Terminal Reconfig | Dynamically re-authenticates MT5 with new account, password, and broker server |
| `/api/version` | `GET` | `mt5.version()` | Returns MT5 terminal build number, release date, and version string |
| `/api/last_error` | `GET` | `mt5.last_error()` | Retrieves the last recorded error code and description |
| `/api/terminal_info` | `GET` | `mt5.terminal_info()` | Terminal state (connected, trade enabled, paths, build) |
| `/api/account_info` | `GET` | `mt5.account_info()` | Account balance, equity, margin, free margin, leverage |

#### Dynamic Authentication (`POST /api/login`) Example:
```json
{
  "login": 999999999999,
  "password": "YourPassword",
  "server": "XPMT5-DEMO",  // or "BancoBTGPactual-PRD"
  "symbol": "PETR4"
}
```

---

### 2. Symbols & Depth of Market (`/api/...`)

| Endpoint | Method | Underlying MT5 Call | Description |
| :--- | :---: | :--- | :--- |
| `/api/symbols_total` | `GET` | `mt5.symbols_total()` | Total number of financial instruments available on the server |
| `/api/symbols_get` | `GET` | `mt5.symbols_get()` | Lists available symbols with optional filter (e.g. `?group=*EUR*`) |
| `/api/symbol_info/<symbol>` | `GET` | `mt5.symbol_info()` | Complete instrument specification (tick size, spread, contract size) |
| `/api/symbol_info_tick/<symbol>`| `GET` | `mt5.symbol_info_tick()` | Real-time last tick (bid, ask, last, volume, timestamp) |
| `/api/symbol_select` | `POST` | `mt5.symbol_select()` | Adds/removes a symbol to/from the Market Watch window |
| `/api/market_book_add` | `POST` | `mt5.market_book_add()` | Subscribes to Depth of Market (DOM / Order Book) updates |
| `/api/market_book_get/<symbol>` | `GET` | `mt5.market_book_get()` | Returns current Level 2 DOM array for a symbol |
| `/api/market_book_release` | `POST` | `mt5.market_book_release()` | Unsubscribes from DOM updates for a symbol |

---

### 3. Market Data & Historical Rates (`/api/...`)

| Endpoint | Method | Query Parameters | Description |
| :--- | :---: | :--- | :--- |
| `/api/copy_rates_from` | `GET` | `symbol`, `timeframe`, `date_from`, `count` | Retrieves historical bars starting from a specific date/time |
| `/api/copy_rates_from_pos` | `GET` | `symbol`, `timeframe`, `start_pos`, `count` | Retrieves historical bars by offset index (0 = current bar) |
| `/api/copy_rates_range` | `GET` | `symbol`, `timeframe`, `date_from`, `date_to` | Retrieves historical bars within a date range |
| `/api/copy_ticks_from` | `GET` | `symbol`, `date_from`, `count`, `flags` | Retrieves raw tick history starting from a date |
| `/api/copy_ticks_range` | `GET` | `symbol`, `date_from`, `date_to`, `flags` | Retrieves raw tick history within a date range |

> **Supported Timeframes**: `M1`, `M2`, `M3`, `M4`, `M5`, `M6`, `M10`, `M12`, `M15`, `M20`, `M30`, `H1`, `H2`, `H3`, `H4`, `H6`, `H8`, `H12`, `D1`, `W1`, `MN1`.

---

### 4. Trading & Order Execution (`/api/...`)

| Endpoint | Method | Type | Description |
| :--- | :---: | :---: | :--- |
| `/api/order_check` | `POST` | Raw | Simulates order placement and checks funds/margin requirement |
| `/api/order_send` | `POST` | Raw | Sends raw `MqlTradeRequest` structure to broker |
| `/api/order_calc_margin` | `POST` | Util | Computes required margin for an order type and volume |
| `/api/order_calc_profit` | `POST` | Util | Calculates estimated floating profit/loss |
| `/api/orders_total` | `GET` | Read | Total count of active pending orders |
| `/api/orders_get` | `GET` | Read | Retrieves pending orders with optional filter (`?symbol=...&ticket=...`) |
| `/api/positions_total` | `GET` | Read | Total count of open market positions |
| `/api/positions_get` | `GET` | Read | Retrieves open positions (`?symbol=...&ticket=...`) |
| `/api/order/open` | `POST` | **Helper** | High-level order entry (`BUY`, `SELL`, `BUY_LIMIT`, `SELL_STOP`, etc.) |
| `/api/order/close` | `POST` | **Helper** | Closes an open position by ticket with automated opposite order |
| `/api/order/modify` | `POST` | **Helper** | Updates Stop Loss (`sl`) and Take Profit (`tp`) on open position |
| `/api/order/<ticket>` | `DELETE` | **Helper** | Cancels a pending order by ticket |

---

### 5. Historical Orders & Deals (`/api/...`)

| Endpoint | Method | Query Parameters | Description |
| :--- | :---: | :--- | :--- |
| `/api/history_orders_total` | `GET` | `date_from`, `date_to` | Returns total number of orders in trading history |
| `/api/history_orders_get` | `GET` | `date_from`, `date_to`, `group`, `ticket`, `position` | Retrieves historical closed/canceled orders |
| `/api/history_deals_total` | `GET` | `date_from`, `date_to` | Returns total number of executed transactions (deals) |
| `/api/history_deals_get` | `GET` | `date_from`, `date_to`, `group`, `ticket`, `position` | Retrieves deal records (executions, commissions, swaps, profits) |

---

## 💻 Code Examples

### Python Example (`requests`)

```python
import os
import requests

BASE_URL = "http://localhost:5000/api"
API_KEY = os.environ.get("API_KEY", "YourSecretApiKey")
HEADERS = {"x-api-key": API_KEY}

# 1. Check account balance & equity
account = requests.get(f"{BASE_URL}/account_info", headers=HEADERS).json()
print("Balance:", account["data"]["balance"], "Equity:", account["data"]["equity"])

# 2. Get real-time price tick
tick = requests.get(f"{BASE_URL}/symbol_info_tick/EURUSD", headers=HEADERS).json()
print("EURUSD Bid:", tick["data"]["bid"], "Ask:", tick["data"]["ask"])

# 3. Open a Market Buy Position
buy_res = requests.post(f"{BASE_URL}/order/open", headers=HEADERS, json={
    "symbol": "EURUSD",
    "order_type": "BUY",
    "volume": 0.01,
    "sl": 1.0500,
    "tp": 1.1000,
    "comment": "MT5Bridge Buy Order"
}).json()
print("Order Response:", buy_res)

# 4. List open positions
positions = requests.get(f"{BASE_URL}/positions_get", headers=HEADERS).json()
print("Open Positions:", positions["data"])
```

### cURL Example

```bash
# Get MT5 version
curl -X GET "http://localhost:5000/api/version" \
  -H "x-api-key: YourSecretApiKey"

# Get EURUSD live tick
curl -X GET "http://localhost:5000/api/symbol_info_tick/EURUSD" \
  -H "x-api-key: YourSecretApiKey"

# Open Market Buy Order (0.01 lots)
curl -X POST "http://localhost:5000/api/order/open" \
  -H "Content-Type: application/json" \
  -H "x-api-key: YourSecretApiKey" \
  -d '{
    "symbol": "EURUSD",
    "order_type": "BUY",
    "volume": 0.01,
    "comment": "Test Order"
  }'
```

---

## 💡 Free Demo Account Setup

1. Open a free demo account through the [MetaTrader Web Terminal](https://web.metatrader.app/terminal?mode=demo&lang=en) or the MetaTrader 5 app.
2. Select the standard **MetaQuotes-Demo** server.
3. Configure your account credentials (`MT5_LOGIN` and `MT5_PASSWORD`) in [docker-compose.yml](file:///home/liberatti/workspace/github.com/liberatti/mt5bridge/docker-compose.yml).

---

## 🧪 Automated Testing Suite

The repository includes an automated integration test script (`test_api.py`) that validates the complete API lifecycle, tests all endpoint categories, and performs a live test trade:

```bash
# Run the test suite with API Key authentication
python test_api.py --url http://localhost:5000 --api-key "YourSecretApiKey" --symbol EURUSD --volume 0.01

# Or authenticate using environment variable
export API_KEY="YourSecretApiKey"
python test_api.py --url http://localhost:5000 --symbol EURUSD --volume 0.01
```

Available arguments:
- `--url`: Base URL of the running API (default: `http://localhost:5000` or `API_URL` env).
- `--api-key`: API key sent in the `x-api-key` header (default: `API_KEY` env or empty).
- `--symbol`: Symbol used for test orders and data retrieval (default: `EURUSD`).
- `--volume`: Trading lot size (default: `0.01`).
- `--no-close`: Keeps the test position open instead of automatically closing it.

---

## 📄 License

This project is licensed under the **Apache License 2.0** - see the [LICENSE](file:///home/liberatti/workspace/github.com/liberatti/mt5bridge/LICENSE) file for details.