# SIM Card Management System (DZ)

[![Status](https://img.shields.io/badge/status-production--ready-green)](#)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](#)
[![FastAPI](https://img.shields.io/badge/fastapi-0.118%2B-009688)](#)
[![Pydantic](https://img.shields.io/badge/pydantic-2.10%2B-e92063)](#)
[![License](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)

Professional, async-first REST + WebSocket API for managing **multiple Huawei
USB modems** at once. Ships with first-class support for Algerian operators
(**Ooredoo, Djezzy, Mobilis**) and runs on Linux, Windows and macOS — both
natively and inside Docker.

> **Repository:** <https://github.com/TerminalDZ/SIM-Card-Management-System-DZ>

---

## ✨ Highlights

- **Concurrent multi-modem orchestration** — detect, connect, monitor and
  drive any number of modems through a single HTTP/WebSocket API.
- **Strict layered architecture** (SOLID, KISS) — each class has one job:
  transport, AT client, detector, device, pool, repository.
- **Zero hardcoded operator data** — operator profiles live in
  [`data/operators.json`](data/operators.json) and can be edited at runtime.
- **Modern stack** — Python 3.10+, FastAPI 0.118+, Pydantic V2, Uvicorn,
  pyserial, type-checked with mypy and linted with ruff.
- **Production logging** — structured JSON output (optional) with rotating
  file handler and per-operation timing.
- **WebSocket broadcasts** — periodic status snapshots pushed to every
  connected client, plus connection lifecycle events.
- **Cross-platform** — works the same on Windows (`COM3`), Linux
  (`/dev/ttyUSB0`) and macOS (`/dev/cu.HUAWEIMobile`).
- **Docker ready** — multi-stage build, non-root runtime, USB device
  pass-through and health checks.

---

## 🗂 Project layout

```text
.
├── app/                         # Application package
│   ├── api/                     # HTTP routers (system, modems, legacy, ws…)
│   ├── core/                    # Logging + domain exceptions
│   ├── modem/                   # transport → at_client → device → pool
│   ├── operators/               # JSON-backed operator repository
│   ├── schemas/                 # Pydantic v2 models
│   ├── ws/                      # WebSocket connection manager
│   ├── config.py                # Typed settings (env-based)
│   └── main.py                  # FastAPI factory + lifespan
├── data/operators.json          # Editable operator registry
├── tests/                       # Pytest suite (encoders, AT client, pool, API)
├── Dockerfile                   # Multi-stage production image
├── docker-compose.yml           # USB pass-through + healthchecks
├── pyproject.toml               # Modern packaging + tool config
├── requirements.txt             # Pinned runtime deps
├── requirements-dev.txt         # Dev / testing deps
├── run.py                       # Convenience entry point
└── .env.example                 # Reference configuration
```

---

## 🛠 Requirements

| Component | Version |
|-----------|---------|
| Python    | 3.10 or newer |
| Modems    | Huawei E3531 / E3372 / E3131 / E173 / E398 (or any modem responding to AT over CDC-ACM / CDC-NCM) |
| OS        | Windows 10/11, Ubuntu 20.04+, Fedora, Debian, macOS 12+ |
| Docker    | 24+ (optional, recommended on Linux for production) |

---

## 🚀 Quick start (native)

```bash
git clone https://github.com/TerminalDZ/SIM-Card-Management-System-DZ.git
cd SIM-Card-Management-System-DZ

python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1

pip install -U pip
pip install -r requirements.txt

cp .env.example .env          # adjust as needed
python run.py                 # OR: python -m app
```

Open <http://localhost:8000/docs> for the auto-generated Swagger UI and
<http://localhost:8000/redoc> for ReDoc.

### Linux serial-port permissions

```bash
sudo usermod -aG dialout $USER
# log out / back in (or reboot) for the group change to apply
```

### Windows

`pyserial` uses Windows COM ports natively. Install Huawei Mobile Connect
drivers if `Device Manager` shows an unknown device. Run PowerShell as
**administrator** the first time so it can claim the COM port.

---

## 🐳 Docker

A multi-stage Dockerfile (Python 3.13 slim, non-root user, tini) and a
ready-to-run Compose file are included.

```bash
cp .env.example .env
docker compose up --build
```

The Compose file passes `/dev/ttyUSB0`…`/dev/ttyUSB3` through to the
container. Adjust the `devices:` list (and the `group_add` GID) to match
your host. Once the container is up, the API is reachable on
`http://localhost:8000`.

> 💡 **Windows users:** Docker Desktop on Windows cannot pass USB devices
> through directly. Either run the app natively on Windows (recommended)
> or use [usbipd-win](https://learn.microsoft.com/windows/wsl/connect-usb)
> to forward the modem into WSL2 and run Compose there.

---

## ⚙️ Configuration

All settings come from environment variables prefixed with `APP_` (a `.env`
file is auto-loaded). The full reference is in [`.env.example`](.env.example).

| Variable | Default | Purpose |
|----------|---------|---------|
| `APP_HOST` / `APP_PORT` | `0.0.0.0:8000` | HTTP bind address |
| `APP_LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `APP_LOG_FILE` | `logs/sim_manager.log` | Rotating file log (set empty to disable) |
| `APP_LOG_JSON` | `false` | Emit JSON-line logs |
| `APP_MODEM_BAUDRATE` | `115200` | Serial baud rate |
| `APP_MODEM_READ_TIMEOUT` | `10` | Per-command read timeout (seconds) |
| `APP_MODEM_COMMAND_RETRIES` | `2` | Retries on transport / timeout errors |
| `APP_MODEM_DEFAULT_APN` | `internet` | Default GPRS APN |
| `APP_MAX_CONCURRENT_MODEMS` | `10` | Hard cap on connected devices |
| `APP_AUTO_DETECT_ON_STARTUP` | `true` | Run discovery during lifespan startup |
| `APP_OPERATORS_FILE` | `data/operators.json` | Operator registry path |
| `APP_CORS_ORIGINS` | `["*"]` | JSON array of allowed origins |
| `APP_WS_BROADCAST_INTERVAL` | `15` | Seconds between status broadcasts |

### Adding a new operator

1. Open [`data/operators.json`](data/operators.json).
2. Append an object with the new operator's metadata (`id`, `name`, `mcc`,
   `imsi_prefixes`, `ussd`, `apn`, …).
3. Restart the service. The repository validates the file at startup; an
   invalid entry will fail fast.

No code change is required.

---

## 🌐 API surface

Browse the live, interactive documentation at `/docs`. The endpoints are
grouped into four tags:

### System

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Lightweight health probe |
| `GET` | `/api/performance` | Counters: connected modems, WS clients, etc. |
| `GET` | `/` | Service metadata |

### Operators

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/operators` | List all operator profiles |
| `GET` | `/api/operators/{id}` | Fetch a single profile |

### Multi-Modem

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/modems/detect` | Discover attached modems |
| `POST` | `/api/modems/connect` | Connect & configure a modem (`{"modem_id": "..."}`) |
| `POST` | `/api/modems/disconnect` | Release a connection |
| `GET`  | `/api/modems/status` | Aggregate snapshot |
| `GET`  | `/api/modems/{id}/status` | One device |
| `GET`  | `/api/modems/{id}/sim-info` | Read SIM identifiers |
| `GET`  | `/api/modems/{id}/sms` | List SMS in storage |
| `POST` | `/api/modems/{id}/sms/send` | Send an SMS |
| `DELETE` | `/api/modems/{id}/sms/{message_id}` | Delete a stored SMS |
| `POST` | `/api/modems/{id}/ussd` | Run a USSD command |
| `GET`  | `/api/modems/{id}/balance` | Balance via operator-specific USSD |

### Legacy (1.x compatibility)

`/api/status`, `/api/sim-info`, `/api/sms`, `/api/sms/send`,
`/api/sms/{message_id}`, `/api/ussd`, `/api/balance` — they all act on the
**first** connected modem. Prefer the per-modem endpoints in new clients.

### WebSocket

`ws://localhost:8000/ws` — every text frame the client sends is echoed back
as a `pong`, and the server publishes a `status_update` payload every
`APP_WS_BROADCAST_INTERVAL` seconds.

---

## 🧪 Testing

```bash
pip install -r requirements-dev.txt
pytest                       # full suite with coverage
ruff check app tests         # lint
mypy app                     # static types
```

The suite covers:

- GSM 7-bit / hex / UCS-2 encoders.
- The AT client (success, error, timeout, retries) against an in-memory
  transport.
- Operator repository loading, lookup and error paths.
- The modem pool (discovery, connect, double-connect, shutdown).
- HTTP smoke tests via `httpx.AsyncClient` and the FastAPI ASGI transport.

Hardware-dependent paths are intentionally not unit-tested — verify them
manually with a real modem, or write integration tests gated behind the
`integration` marker (already declared in `pyproject.toml`).

---

## 🧠 Architecture

```text
       ┌──────────────────────────────┐
       │           FastAPI            │
       │     routers + WS endpoint    │
       └──────────┬───────────────────┘
                  │ depends on
                  ▼
       ┌──────────────────────────────┐
       │          ModemPool           │  one per process
       │  detect / connect / status   │
       └──────┬─────────────┬─────────┘
              │             │
              ▼             ▼
   ┌──────────────────┐  ┌──────────────────────┐
   │  ModemDetector   │  │     ModemDevice      │  one per port
   │ list_ports + AT  │  │ status / SMS / USSD  │
   └──────────────────┘  └─────────┬────────────┘
                                   │ uses
                                   ▼
                          ┌──────────────────┐
                          │     ATClient     │  request/response framing
                          └────────┬─────────┘
                                   ▼
                          ┌──────────────────┐
                          │ SerialTransport  │  async wrapper over pyserial
                          └──────────────────┘
```

Cross-cutting concerns:

- `OperatorRepository` (read-only, JSON-backed) — single point of truth for
  USSD codes and APN settings.
- `WebSocketManager` — fan-out broadcasts and lifecycle.
- `Settings` (Pydantic) — environment-driven configuration with validation.

The dependency direction always flows **towards the hardware** — schemas
and routers never import from the modem layer except through the pool, and
the modem layer never imports from FastAPI.

---

## 🛡 Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `Modem … was not detected` | Port not enumerated yet | Replug the modem or call `POST /api/modems/detect` again |
| Detection lists ports but `responsive: false` | Another app holds the COM port (Huawei Mobile Partner / Hilink dashboard / Mobile Connect) | Quit the Huawei desktop app and rerun detection — it must release `COM12` (or equivalent) |
| `FileNotFoundError` opening `COMxx` (Windows) | Modem is in CD-ROM mode — `usb_modeswitch` hasn't switched it to modem mode yet (PID `0000`) | Run Huawei Mobile Partner once so it triggers the mode switch, then close it before starting this service |
| `Permission denied: /dev/ttyUSB0` (Linux) | User not in `dialout` group | `sudo usermod -aG dialout $USER`, then re-login |
| AT commands time out on every port | Wrong physical port — Huawei modems expose 2–3 COM ports and only one accepts AT | Try connecting to each `huawei_COMxx` in turn; the modem port is usually labelled "Modem" in Device Manager |
| SMS rejected with `+CMS ERROR: 304` | Charset/PDU mismatch or missing SMSC | The system uses UCS-2 by default — ensure the SIM has an SMSC configured (`AT+CSCA?`) |
| USSD returns empty text | Some operators reply to interactive USSD; the modem session keeps the menu open | Call the next code from the menu — not all USSD trees are scriptable |
| Container can't see modem | Missing device mapping | Update `docker-compose.yml` `devices:` and the `group_add` GID to match your host's `dialout` group |

Enable verbose logs with `APP_LOG_LEVEL=DEBUG` for a deeper trace.

### Windows-specific notes

Huawei modems on Windows are typically driven by the OEM `huawei_enum_vbus`
driver, which exposes three virtual COM ports per modem:

* **3G Modem** — accepts AT commands (this is the one we want).
* **3G PC UI Interface** — used by the Mobile Partner GUI; rarely answers AT.
* **3G Application Interface** — diagnostics; does not answer AT.

If `Huawei Mobile Partner` (or `HwMobileBroadband.exe`, `MobilePartner.exe`,
`DataCardMonitor.exe`) is running, it will keep an exclusive lock on the
modem port and the API will receive `FileNotFoundError` when it tries to
open it. The fix is to fully exit that software (or disable its
auto-start) before launching this service.

---

## 📜 Versioning & changelog

Current release: **3.0.0** — full rewrite with strict layered architecture,
Pydantic V2 schemas, Docker support, and a real test suite. Legacy 1.x
endpoints remain available for compatibility.

---

## 🤝 Contributing

Pull requests are welcome. Please run `ruff check`, `mypy app` and `pytest`
before opening a PR. New operators only require an entry in
[`data/operators.json`](data/operators.json).

## 📄 License

MIT — see [`LICENSE`](LICENSE).
