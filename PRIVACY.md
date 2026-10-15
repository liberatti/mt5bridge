# Privacy Policy & Terms of Use
**MT5Bridge - MetaTrader 5 Linux Headless Gateway & REST API**

*Last Updated: October 15, 2026*

---

## 1. Overview & Privacy Commitment

**MT5Bridge** is an open-source, self-hosted Dockerized gateway and native Python Flask REST API for MetaTrader 5 running on Linux with WineHQ. The software is designed with a strict **privacy-first, self-contained, zero-telemetry architecture**.

**We operate no external telemetry servers, collect zero user or trading data, and never transmit, sell, or monetize your financial or account credentials to third parties.**

---

## 2. Data Handling & Security

### 2.1. Broker Credentials & Account Data
- Your MetaTrader 5 account credentials (login ID, password, broker server name, and investor password) are configured **exclusively by you** through container environment variables (`MT5_LOGIN`, `MT5_PASSWORD`, `MT5_SERVER`, `MT5_INVESTOR`) or dynamically via authenticated REST endpoints (`/api/login`).
- Credentials are transmitted strictly between your local MT5Bridge container and your designated broker's MetaTrader 5 trade server over official encrypted MetaQuotes protocols.
- The developers and maintainers of MT5Bridge have **zero access** to your broker credentials, trading history, open positions, balance, or equity.

### 2.2. API Authentication & Security
- When `SECURITY_ENABLED=true` is configured, all REST API requests require authentication via API key (`x-api-key` header) or JWT bearer tokens.
- Secret keys (`JWT_SECRET_KEY`, `API_KEY`) reside only in your local deployment environment.

### 2.3. Zero Telemetry & Logging
- MT5Bridge contains **no telemetry trackers, analytics beacons, or third-party tracking scripts**.
- All application and container logs (Wine, MetaTrader 5 terminal, and Flask/Waitress WSGI logs) are kept entirely inside your container and local mounted volumes (`/home/mt5user/.mt5`).

---

## 3. Network Communications

MT5Bridge communicates exclusively across:
1. **Local Network / Host:** Inbound REST API requests on port `5000` (HTTP) and optional internal MQL5 TCP gateway communication on localhost port `22347`.
2. **Broker Trade Servers:** Direct outbound TCP connections initiated by the official MetaTrader 5 terminal client to your chosen broker servers (e.g., XP Investimentos, BTG Pactual, MetaQuotes demo/live servers).
3. **Official Upstream Dependencies:** Initial build-time package retrieval from official package repositories (Ubuntu Noble, WineHQ, and MetaQuotes setup executable).

---

## 4. Financial Risk Disclaimer & Terms of Use

> [!IMPORTANT]
> **PLEASE READ CAREFULLY:** Your use of MT5Bridge constitutes full and unconditional acceptance of the following terms:

### 4.1. "AS IS" Open-Source Software
MT5Bridge is provided free of charge under the **Apache License 2.0**, on an "AS IS" and "AS AVAILABLE" basis, without warranties of any kind, whether express, statutory, or implied, including but not limited to warranties of merchantability, fitness for a particular purpose, uptime, network latency, or non-infringement.

### 4.2. High-Risk Financial Trading
Trading foreign exchange (Forex), contracts for difference (CFDs), stocks, futures, equities, and options on margin carries a high level of risk and may not be suitable for all investors. High leverage can work against you as well as for you. Before deciding to trade or automate trading operations, you should carefully consider your investment objectives, level of experience, and risk appetite.

### 4.3. Technical Risk & Latency
Algorithmic trading and automated execution are subject to technical risks, including but not limited to:
- Internet connectivity failures, packet loss, or high latency;
- Wine emulation anomalies, Xvfb framebuffer delays, or terminal crashes;
- Broker server disconnects, slippage, off-quotes, or execution requotes;
- Software bugs, unexpected restarts, or server downtime.

### 4.4. Sole User Responsibility
You, the end user, assume **sole and exclusive responsibility** for:
- Verifying the accuracy and sanity of all trade parameters (symbol, volume, deviation, stop loss, take profit, order type) before sending orders;
- Implementing independent risk management, position sizing, and stop-loss mechanisms;
- Securing the deployment environment, firewall rules, and API authentication keys;
- Complying with applicable financial market regulations, broker terms of service, and local tax laws.

### 4.5. Limitation of Liability
To the maximum extent permitted by applicable law, the author, developers, and contributors of MT5Bridge shall NOT be liable for any direct, indirect, incidental, special, consequential, punitive, or exemplary damages, including but not limited to:
- Financial trading losses, margin calls, or liquidation of trading accounts;
- Lost profits, missed trading opportunities, or slippage;
- System downtime, operational interruptions, or corrupted configurations.

---

## 5. Changes to This Policy

This Privacy Policy and Terms of Use may be updated periodically to reflect architectural changes or regulatory compliance. Any updates will be published directly in the official GitHub repository.

---

## 6. Contact & Support

For technical inquiries, bug reports, or security disclosures:
- **GitHub Repository:** [https://github.com/liberatti/mt5bridge](https://github.com/liberatti/mt5bridge)
- **Issues & Discussions:** [https://github.com/liberatti/mt5bridge/issues](https://github.com/liberatti/mt5bridge/issues)
- **Maintainer:** `liberatti`
