# MetaTrader 5 Flask REST API no Docker (Linux / Wine)

Ambiente Docker headless, modular e pronto para produção para executar o **MetaTrader 5 (MT5)** no Linux através do **WineHQ Staging**, expondo **todos os métodos da biblioteca oficial `MetaTrader5`** através de uma **API REST em Flask (Python)** organizada em **Controllers, Services e Blueprints** na porta `5000`.

Baseado no artigo oficial da MQL5: [MetaTrader 5 no Linux](https://www.mql5.com/pt/articles/625).

---

## 🚀 Principais Recursos

- 🏗️ **Arquitetura Modular (Controllers, Services & Blueprints)**: Separação clara de responsabilidades (`controllers/`, `services/`, `utils/`).
- ⚡ **100% Headless (Sem VNC)**: Não há necessidade de interfaces gráficas pesadas; roda silenciosamente em background com `Xvfb`.
- 🚀 **Alta Concorrência & Multi-threading**: Servidor de produção WSGI multi-thread atendendo múltiplas requisições simultâneas com número configurável de threads (`THREADS=8`).
- 📊 **Log Estruturado de Requisições**: Middleware de log de acesso registrando IP, método, rota, status HTTP, tamanho da resposta e tempo de resposta em milissegundos (`ms`).
- 🐍 **Cobertura Total da biblioteca `MetaTrader5`**: Todos os métodos da biblioteca oficial mapeados em endpoints HTTP REST (JSON).
- 🔗 **Comunicação Nativa IPC**: Python 3.11 para Windows roda internamente no prefixo Wine, conectando-se diretamente ao `terminal64.exe` do MT5 via IPC de alta velocidade.
- 💾 **Persistência de Dados**: O volume Docker armazena contas, configurações, histórico e cache permanentemente.

---

## 📦 Estrutura do Projeto

```
.
├── Dockerfile                  # Imagem Ubuntu + WineHQ Staging + Xvfb + Python 3.11 Windows
├── docker-compose.yml          # Orquestração do serviço Docker e volume
├── entrypoint.sh               # Inicializador headless do Xvfb, MT5 e Flask API
├── .env.example                # Exemplo de configurações de porta
├── .dockerignore               # Arquivos ignorados no build
├── README.md                   # Documentação completa da API
└── api/
    ├── app.py                  # Factory da aplicação Flask e bootstrap
    ├── routes.py               # Registro centralizado de rotas e blueprints
    ├── templates/
    │   ├── swagger.html        # Template HTML standalone da interface Swagger UI
    │   └── swagger.json        # Especificação OpenAPI 3.0 em JSON
    ├── requirements.txt        # Dependências Python (MetaTrader5, Flask, waitress, etc.)
    ├── services/
    │   ├── __init__.py         # Export dos Services
    │   ├── base_service.py     # BaseService com ciclo de vida e ensure_initialized()
    │   ├── system_service.py   # Operações de conexão, login, terminal e conta
    │   ├── symbols_service.py  # Operações de símbolos e Book de Ofertas (DOM)
    │   ├── market_data_service.py # Cópia de rates (OHLCV) e ticks
    │   ├── trade_service.py    # Envio de ordens, cálculos de margem/lucro, posições
    │   └── history_service.py  # Histórico de ordens e negócios (deals)
    ├── utils/
    │   ├── __init__.py         # Exports de utils
    │   ├── response.py         # Helper de padronização de respostas JSON (make_response)
    │   └── parsers.py          # Parsers de datas, timeframes e mapeamento de constantes MT5
    └── controllers/
        ├── __init__.py         # Registro modular dos Blueprints
        ├── system_controller.py      # /api/initialize, /api/login, /api/account_info, etc.
        ├── symbols_controller.py     # /api/symbols_get, /api/symbol_info/<symbol>, etc.
        ├── market_data_controller.py # /api/copy_rates_from, /api/copy_ticks_from, etc.
        ├── trade_controller.py       # /api/order_send, /api/order/open, /api/positions_get, etc.
        └── history_controller.py     # /api/history_orders_get, /api/history_deals_get, etc.
```

---

## 🛠️ Como Iniciar

```bash
# Iniciar a API em background
docker compose up -d

# Acompanhar logs
docker compose logs -f
```

A API estará pronta em `http://localhost:5000`.

---

## 📖 Swagger UI / Documentação Interativa

Acesse a interface interativa do Swagger UI com **100% dos métodos documentados**, schemas de requisição, exemplos e botão "Try it out":

- **Swagger UI**: [`http://localhost:5000/`](http://localhost:5000/)
- **OpenAPI 3.0 JSON Spec**: [`http://localhost:5000/swagger.json`](http://localhost:5000/swagger.json)

---

## 📡 Mapeamento dos Controllers e Blueprints

Todas as rotas retornam respostas no formato padrão:
```json
{
  "success": true,
  "data": { ... },
  "message": "Mensagem opcional",
  "error": null
}
```

---

### 1. `system_controller` (Sistema e Conexão)

| Endpoint | Método | Método MT5 | Descrição |
| :--- | :--- | :--- | :--- |
| `/api/initialize` | `POST` / `GET` | `mt5.initialize()` | Inicializa a conexão com o terminal MT5 |
| `/api/shutdown` | `POST` | `mt5.shutdown()` | Encerra a conexão com o MT5 |
| `/api/version` | `GET` | `mt5.version()` | Versão e build do terminal MT5 |
| `/api/last_error` | `GET` | `mt5.last_error()` | Último código e mensagem de erro |
| `/api/terminal_info` | `GET` | `mt5.terminal_info()` | Informações de estado do terminal |
| `/api/account_info` | `GET` | `mt5.account_info()` | Saldo, equity, margem, alavancagem |
| `/api/login` | `POST` | `mt5.login()` | Login com credenciais da corretora |

---

### 2. `symbols_controller` (Símbolos e Livro de Ofertas)

| Endpoint | Método | Método MT5 | Descrição |
| :--- | :--- | :--- | :--- |
| `/api/symbols_total` | `GET` | `mt5.symbols_total()` | Quantidade total de símbolos disponíveis |
| `/api/symbols_get` | `GET` | `mt5.symbols_get()` | Lista todos os símbolos (filtro opcional: `?group=*EUR*`) |
| `/api/symbol_info/<symbol>` | `GET` | `mt5.symbol_info()` | Dados detalhados de um ativo específico |
| `/api/symbol_info_tick/<symbol>` | `GET` | `mt5.symbol_info_tick()` | Último tick de preço (bid, ask, volume, tempo) |
| `/api/symbol_select` | `POST` | `mt5.symbol_select()` | Habilitar/desabilitar símbolo no Market Watch |
| `/api/market_book_add` | `POST` | `mt5.market_book_add()` | Inscrever-se no Livro de Ofertas (DOM) do ativo |
| `/api/market_book_get/<symbol>` | `GET` | `mt5.market_book_get()` | Obter entradas do Livro de Ofertas |
| `/api/market_book_release` | `POST` | `mt5.market_book_release()` | Cancelar inscrição do Livro de Ofertas |

---

### 3. `market_data_controller` (Histórico de Preços e Candles)

| Endpoint | Método | Método MT5 | Parâmetros |
| :--- | :--- | :--- | :--- |
| `/api/copy_rates_from` | `GET` | `mt5.copy_rates_from()` | `symbol`, `timeframe`, `date_from`, `count` |
| `/api/copy_rates_from_pos` | `GET` | `mt5.copy_rates_from_pos()` | `symbol`, `timeframe`, `start_pos`, `count` |
| `/api/copy_rates_range` | `GET` | `mt5.copy_rates_range()` | `symbol`, `timeframe`, `date_from`, `date_to` |
| `/api/copy_ticks_from` | `GET` | `mt5.copy_ticks_from()` | `symbol`, `date_from`, `count`, `flags` |
| `/api/copy_ticks_range` | `GET` | `mt5.copy_ticks_range()` | `symbol`, `date_from`, `date_to`, `flags` |

---

### 4. `trade_controller` (Negociação, Ordens e Posições)

| Endpoint | Método | Método MT5 | Descrição |
| :--- | :--- | :--- | :--- |
| `/api/order_check` | `POST` | `mt5.order_check()` | Valida e simula uma ordem antes do envio |
| `/api/order_send` | `POST` | `mt5.order_send()` | Envia requisição bruta de trade para a corretora |
| `/api/order_calc_margin` | `POST` | `mt5.order_calc_margin()` | Calcula a margem necessária para uma ordem |
| `/api/order_calc_profit` | `POST` | `mt5.order_calc_profit()` | Calcula o lucro projetado para uma variação de preço |
| `/api/orders_total` | `GET` | `mt5.orders_total()` | Total de ordens pendentes ativas |
| `/api/orders_get` | `GET` | `mt5.orders_get()` | Lista ordens pendentes (`?symbol=...&ticket=...`) |
| `/api/positions_total` | `GET` | `mt5.positions_total()` | Total de posições abertas no momento |
| `/api/positions_get` | `GET` | `mt5.positions_get()` | Lista posições abertas (`?symbol=...&ticket=...`) |
| `/api/order/open` | `POST` | Helper | Abrir ordem (`BUY`, `SELL`, `BUY_LIMIT`, etc.) |
| `/api/order/close` | `POST` | Helper | Fechar posição aberta por ticket (total ou parcial) |
| `/api/order/modify` | `POST` | Helper | Modificar SL e TP de uma posição |
| `/api/order/<ticket>` | `DELETE` | Helper | Cancelar ordem pendente |

---

### 5. `history_controller` (Histórico de Negócios e Ordens)

| Endpoint | Método | Método MT5 | Descrição |
| :--- | :--- | :--- | :--- |
| `/api/history_orders_total` | `GET` | `mt5.history_orders_total()` | Total de ordens no histórico (`?date_from=...&date_to=...`) |
| `/api/history_orders_get` | `GET` | `mt5.history_orders_get()` | Detalhes de ordens no histórico |
| `/api/history_deals_total` | `GET` | `mt5.history_deals_total()` | Total de negócios (deals) executados |
| `/api/history_deals_get` | `GET` | `mt5.history_deals_get()` | Detalhes dos negócios executados no histórico |


## Pegue uma conta Demo gratuita
Abra o app do MetaTrader 5 no celular ou no MetaTrader 5 Web.
Crie uma conta demo gratuita em MetaQuotes-Demo e anote o Login (número da conta) e a Senha.