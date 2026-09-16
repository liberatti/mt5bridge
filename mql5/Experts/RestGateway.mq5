//+------------------------------------------------------------------+
//|                                                  RestGateway.mq5 |
//|                                  Copyright 2026, liberatti       |
//|                                             https://github.com   |
//+------------------------------------------------------------------+
#property copyright "liberatti"
#property link      "https://github.com"
#property version   "1.00"
#property description "Pure TCP Socket JSON Gateway for MetaTrader 5 REST API"

#define AF_INET         2
#define SOCK_STREAM     1
#define IPPROTO_TCP     6
#define INVALID_SOCKET_VAL (ulong)(~0)
#define SOCKET_ERROR    -1
#define FIONBIO         0x8004667E
#define SOL_SOCKET_VAL  0xFFFF
#define SO_RCVTIMEO_VAL 0x1006
#define SO_SNDTIMEO_VAL 0x1005

//+------------------------------------------------------------------+
//| WinWinsock2 DLL Imports (64-bit compliant with Dynamic Arrays)   |
//+------------------------------------------------------------------+
#import "ws2_32.dll"
int WSAStartup(ushort wVersionRequested, uchar &lpWSAData[]);
int WSACleanup();
ulong socket(int af, int type, int protocol);
int ioctlsocket(ulong s, int cmd, uint &argp);
int setsockopt(ulong s, int level, int optname, uchar &optval[], int optlen);
int bind(ulong s, uchar &name[], int namelen);
int listen(ulong s, int backlog);
ulong accept(ulong s, uchar &addr[], int &addrlen);
int send(ulong s, uchar &buf[], int len, int flags);
int recv(ulong s, uchar &buf[], int len, int flags);
int closesocket(ulong s);
int WSAGetLastError();
#import


input int InpPort = 22347; // TCP Port to listen on

ulong g_server_socket = INVALID_SOCKET_VAL;


//+------------------------------------------------------------------+
//| Helper: Escape JSON String                                       |
//+------------------------------------------------------------------+
string JsonEscape(string str)
{
   string res = "";
   int len = StringLen(str);
   for(int i = 0; i < len; i++)
   {
      ushort ch = StringGetCharacter(str, i);
      if(ch == '\"') res += "\\\"";
      else if(ch == '\\') res += "\\\\";
      else if(ch == '\n') res += "\\n";
      else if(ch == '\r') res += "\\r";
      else if(ch == '\t') res += "\\t";
      else res += ShortToString(ch);
   }
   return res;
}

//+------------------------------------------------------------------+
//| Helper: Extract JSON String Field                                |
//+------------------------------------------------------------------+
string ExtractJsonString(string json, string field)
{
   string key = "\"" + field + "\"";
   int pos = StringFind(json, key);
   if(pos < 0) return "";
   
   pos = StringFind(json, ":", pos + StringLen(key));
   if(pos < 0) return "";
   
   // Skip whitespace
   int start = pos + 1;
   while(start < StringLen(json) && (StringGetCharacter(json, start) == ' ' || StringGetCharacter(json, start) == '\t'))
      start++;
      
   if(start >= StringLen(json)) return "";
   
   if(StringGetCharacter(json, start) == '\"')
   {
      start++;
      int end = StringFind(json, "\"", start);
      if(end < 0) return "";
      return StringSubstr(json, start, end - start);
   }
   else
   {
      int end = start;
      while(end < StringLen(json))
      {
         ushort ch = StringGetCharacter(json, end);
         if(ch == ',' || ch == '}' || ch == ']' || ch == '\n' || ch == '\r' || ch == ' ')
            break;
         end++;
      }
      return StringSubstr(json, start, end - start);
   }
}

long ExtractJsonInt(string json, string field, long default_val = 0)
{
   string val = ExtractJsonString(json, field);
   if(val == "") return default_val;
   return StringToInteger(val);
}

double ExtractJsonDouble(string json, string field, double default_val = 0.0)
{
   string val = ExtractJsonString(json, field);
   if(val == "") return default_val;
   return StringToDouble(val);
}

//+------------------------------------------------------------------+
//| Handlers                                                         |
//+------------------------------------------------------------------+
string HandlePing()
{
   return "{\"status\":\"ok\",\"action\":\"ping\",\"data\":{\"pong\":true,\"time\":" + (string)(long)TimeCurrent() + "}}";
}

string HandleVersion()
{
   int build = (int)TerminalInfoInteger(TERMINAL_BUILD);
   return "{\"status\":\"ok\",\"action\":\"version\",\"data\":{\"version\":500,\"build\":" + (string)build + ",\"release_date\":\"" + __DATE__ + "\"}}";
}

string HandleTerminalInfo()
{
   string res = "{\"status\":\"ok\",\"action\":\"terminal_info\",\"data\":{";
   res += "\"community_account\":" + (TerminalInfoInteger(TERMINAL_COMMUNITY_ACCOUNT) ? "true" : "false") + ",";
   res += "\"community_connection\":" + (TerminalInfoInteger(TERMINAL_COMMUNITY_CONNECTION) ? "true" : "false") + ",";
   res += "\"connected\":" + (TerminalInfoInteger(TERMINAL_CONNECTED) ? "true" : "false") + ",";
   res += "\"dlls_allowed\":" + (TerminalInfoInteger(TERMINAL_DLLS_ALLOWED) ? "true" : "false") + ",";
   res += "\"trade_allowed\":" + (TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) ? "true" : "false") + ",";
   res += "\"email_enabled\":" + (TerminalInfoInteger(TERMINAL_EMAIL_ENABLED) ? "true" : "false") + ",";
   res += "\"ftp_enabled\":" + (TerminalInfoInteger(TERMINAL_FTP_ENABLED) ? "true" : "false") + ",";
   res += "\"notifications_enabled\":" + (TerminalInfoInteger(TERMINAL_NOTIFICATIONS_ENABLED) ? "true" : "false") + ",";
   res += "\"mqid\":" + (TerminalInfoInteger(TERMINAL_MQID) ? "true" : "false") + ",";
   res += "\"build\":" + (string)TerminalInfoInteger(TERMINAL_BUILD) + ",";
   res += "\"maxbars\":" + (string)TerminalInfoInteger(TERMINAL_MAXBARS) + ",";
   res += "\"codepage\":" + (string)TerminalInfoInteger(TERMINAL_CODEPAGE) + ",";
   res += "\"ping_last\":" + (string)TerminalInfoInteger(TERMINAL_PING_LAST) + ",";
   res += "\"community_balance\":" + DoubleToString(TerminalInfoDouble(TERMINAL_COMMUNITY_BALANCE), 2) + ",";
   res += "\"retransmission\":" + DoubleToString(TerminalInfoDouble(TERMINAL_RETRANSMISSION), 2) + ",";
   res += "\"company\":\"" + JsonEscape(TerminalInfoString(TERMINAL_COMPANY)) + "\",";
   res += "\"name\":\"" + JsonEscape(TerminalInfoString(TERMINAL_NAME)) + "\",";
   res += "\"path\":\"" + JsonEscape(TerminalInfoString(TERMINAL_PATH)) + "\",";
   res += "\"data_path\":\"" + JsonEscape(TerminalInfoString(TERMINAL_DATA_PATH)) + "\",";
   res += "\"commondata_path\":\"" + JsonEscape(TerminalInfoString(TERMINAL_COMMONDATA_PATH)) + "\"";
   res += "}}";
   return res;
}

string HandleAccountInfo()
{
   string res = "{\"status\":\"ok\",\"action\":\"account_info\",\"data\":{";
   res += "\"login\":" + (string)AccountInfoInteger(ACCOUNT_LOGIN) + ",";
   res += "\"trade_mode\":" + (string)AccountInfoInteger(ACCOUNT_TRADE_MODE) + ",";
   res += "\"leverage\":" + (string)AccountInfoInteger(ACCOUNT_LEVERAGE) + ",";
   res += "\"limit_orders\":" + (string)AccountInfoInteger(ACCOUNT_LIMIT_ORDERS) + ",";
   res += "\"margin_so_mode\":" + (string)AccountInfoInteger(ACCOUNT_MARGIN_SO_MODE) + ",";
   res += "\"trade_allowed\":" + (AccountInfoInteger(ACCOUNT_TRADE_ALLOWED) ? "true" : "false") + ",";
   res += "\"trade_expert\":" + (AccountInfoInteger(ACCOUNT_TRADE_EXPERT) ? "true" : "false") + ",";
   res += "\"margin_mode\":" + (string)AccountInfoInteger(ACCOUNT_MARGIN_MODE) + ",";
   res += "\"currency_digits\":" + (string)AccountInfoInteger(ACCOUNT_CURRENCY_DIGITS) + ",";
   res += "\"fifo_close\":" + (AccountInfoInteger(ACCOUNT_FIFO_CLOSE) ? "true" : "false") + ",";
   res += "\"balance\":" + DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2) + ",";
   res += "\"credit\":" + DoubleToString(AccountInfoDouble(ACCOUNT_CREDIT), 2) + ",";
   res += "\"profit\":" + DoubleToString(AccountInfoDouble(ACCOUNT_PROFIT), 2) + ",";
   res += "\"equity\":" + DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY), 2) + ",";
   res += "\"margin\":" + DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN), 2) + ",";
   res += "\"margin_free\":" + DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN_FREE), 2) + ",";
   res += "\"margin_level\":" + DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN_LEVEL), 2) + ",";
   res += "\"margin_so_call\":" + DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN_SO_CALL), 2) + ",";
   res += "\"margin_so_so\":" + DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN_SO_SO), 2) + ",";
   res += "\"margin_initial\":" + DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN_INITIAL), 2) + ",";
   res += "\"margin_maintenance\":" + DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN_MAINTENANCE), 2) + ",";
   res += "\"assets\":" + DoubleToString(AccountInfoDouble(ACCOUNT_ASSETS), 2) + ",";
   res += "\"liabilities\":" + DoubleToString(AccountInfoDouble(ACCOUNT_LIABILITIES), 2) + ",";
   res += "\"commission_blocked\":" + DoubleToString(AccountInfoDouble(ACCOUNT_COMMISSION_BLOCKED), 2) + ",";
   res += "\"name\":\"" + JsonEscape(AccountInfoString(ACCOUNT_NAME)) + "\",";
   res += "\"server\":\"" + JsonEscape(AccountInfoString(ACCOUNT_SERVER)) + "\",";
   res += "\"currency\":\"" + JsonEscape(AccountInfoString(ACCOUNT_CURRENCY)) + "\",";
   res += "\"company\":\"" + JsonEscape(AccountInfoString(ACCOUNT_COMPANY)) + "\"";
   res += "}}";
   return res;
}

string HandleSymbolsTotal()
{
   int total = SymbolsTotal(false);
   return "{\"status\":\"ok\",\"action\":\"symbols_total\",\"data\":{\"total\":" + (string)total + "}}";
}

string FormatSymbolInfo(string symbol)
{
   MqlTick tick;
   SymbolInfoTick(symbol, tick);
   int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
   
   string res = "{";
   res += "\"custom\":" + (SymbolInfoInteger(symbol, SYMBOL_CUSTOM) ? "true" : "false") + ",";
   res += "\"chart_mode\":" + (string)SymbolInfoInteger(symbol, SYMBOL_CHART_MODE) + ",";
   res += "\"select\":" + (SymbolInfoInteger(symbol, SYMBOL_SELECT) ? "true" : "false") + ",";
   res += "\"visible\":" + (SymbolInfoInteger(symbol, SYMBOL_VISIBLE) ? "true" : "false") + ",";
   res += "\"session_deals\":" + (string)SymbolInfoInteger(symbol, SYMBOL_SESSION_DEALS) + ",";
   res += "\"session_buy_orders\":" + (string)SymbolInfoInteger(symbol, SYMBOL_SESSION_BUY_ORDERS) + ",";
   res += "\"session_sell_orders\":" + (string)SymbolInfoInteger(symbol, SYMBOL_SESSION_SELL_ORDERS) + ",";
   res += "\"volume\":" + (string)SymbolInfoInteger(symbol, SYMBOL_VOLUME) + ",";
   res += "\"volumehigh\":" + (string)SymbolInfoInteger(symbol, SYMBOL_VOLUMEHIGH) + ",";
   res += "\"volumelow\":" + (string)SymbolInfoInteger(symbol, SYMBOL_VOLUMELOW) + ",";
   res += "\"time\":" + (string)SymbolInfoInteger(symbol, SYMBOL_TIME) + ",";
   res += "\"digits\":" + (string)digits + ",";
   res += "\"spread\":" + (string)SymbolInfoInteger(symbol, SYMBOL_SPREAD) + ",";
   res += "\"spread_float\":" + (SymbolInfoInteger(symbol, SYMBOL_SPREAD_FLOAT) ? "true" : "false") + ",";
   res += "\"ticks_bookdepth\":" + (string)SymbolInfoInteger(symbol, SYMBOL_TICKS_BOOKDEPTH) + ",";
   res += "\"trade_calc_mode\":" + (string)SymbolInfoInteger(symbol, SYMBOL_TRADE_CALC_MODE) + ",";
   res += "\"trade_mode\":" + (string)SymbolInfoInteger(symbol, SYMBOL_TRADE_MODE) + ",";
   res += "\"start_time\":" + (string)SymbolInfoInteger(symbol, SYMBOL_START_TIME) + ",";
   res += "\"expiration_time\":" + (string)SymbolInfoInteger(symbol, SYMBOL_EXPIRATION_TIME) + ",";
   res += "\"trade_stops_level\":" + (string)SymbolInfoInteger(symbol, SYMBOL_TRADE_STOPS_LEVEL) + ",";
   res += "\"trade_freeze_level\":" + (string)SymbolInfoInteger(symbol, SYMBOL_TRADE_FREEZE_LEVEL) + ",";
   res += "\"trade_exemode\":" + (string)SymbolInfoInteger(symbol, SYMBOL_TRADE_EXEMODE) + ",";
   res += "\"swap_mode\":" + (string)SymbolInfoInteger(symbol, SYMBOL_SWAP_MODE) + ",";
   res += "\"swap_rollover3days\":" + (string)SymbolInfoInteger(symbol, SYMBOL_SWAP_ROLLOVER3DAYS) + ",";
   res += "\"margin_hedged_use_leg\":" + (SymbolInfoInteger(symbol, SYMBOL_MARGIN_HEDGED_USE_LEG) ? "true" : "false") + ",";
   res += "\"expiration_mode\":" + (string)SymbolInfoInteger(symbol, SYMBOL_EXPIRATION_MODE) + ",";
   res += "\"filling_mode\":" + (string)SymbolInfoInteger(symbol, SYMBOL_FILLING_MODE) + ",";
   res += "\"order_mode\":" + (string)SymbolInfoInteger(symbol, SYMBOL_ORDER_MODE) + ",";
   res += "\"order_gtc_mode\":" + (string)SymbolInfoInteger(symbol, SYMBOL_ORDER_GTC_MODE) + ",";
   res += "\"option_mode\":" + (string)SymbolInfoInteger(symbol, SYMBOL_OPTION_MODE) + ",";
   res += "\"option_right\":" + (string)SymbolInfoInteger(symbol, SYMBOL_OPTION_RIGHT) + ",";
   res += "\"bid\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_BID), digits) + ",";
   res += "\"bidhigh\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_BIDHIGH), digits) + ",";
   res += "\"bidlow\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_BIDLOW), digits) + ",";
   res += "\"ask\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_ASK), digits) + ",";
   res += "\"askhigh\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_ASKHIGH), digits) + ",";
   res += "\"asklow\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_ASKLOW), digits) + ",";
   res += "\"last\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_LAST), digits) + ",";
   res += "\"lasthigh\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_LASTHIGH), digits) + ",";
   res += "\"lastlow\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_LASTLOW), digits) + ",";
   res += "\"volume_real\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_VOLUME_REAL), 2) + ",";
   res += "\"volumehigh_real\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_VOLUMEHIGH_REAL), 2) + ",";
   res += "\"volumelow_real\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_VOLUMELOW_REAL), 2) + ",";
   res += "\"option_strike\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_OPTION_STRIKE), digits) + ",";
   res += "\"point\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_POINT), digits) + ",";
   res += "\"trade_tick_value\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE), 4) + ",";
   res += "\"trade_tick_value_profit\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE_PROFIT), 4) + ",";
   res += "\"trade_tick_value_loss\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE_LOSS), 4) + ",";
   res += "\"trade_tick_size\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_SIZE), digits) + ",";
   res += "\"trade_contract_size\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_TRADE_CONTRACT_SIZE), 2) + ",";
   res += "\"trade_accrued_interest\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_TRADE_ACCRUED_INTEREST), 2) + ",";
   res += "\"trade_face_value\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_TRADE_FACE_VALUE), 2) + ",";
   res += "\"trade_liquidity_rate\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_TRADE_LIQUIDITY_RATE), 2) + ",";
   res += "\"volume_min\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN), 2) + ",";
   res += "\"volume_max\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX), 2) + ",";
   res += "\"volume_step\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP), 2) + ",";
   res += "\"volume_limit\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_VOLUME_LIMIT), 2) + ",";
   res += "\"swap_long\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_SWAP_LONG), 4) + ",";
   res += "\"swap_short\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_SWAP_SHORT), 4) + ",";
   res += "\"margin_initial\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_MARGIN_INITIAL), 2) + ",";
   res += "\"margin_maintenance\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_MARGIN_MAINTENANCE), 2) + ",";
   res += "\"session_volume\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_SESSION_VOLUME), 2) + ",";
   res += "\"session_turnover\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_SESSION_TURNOVER), 2) + ",";
   res += "\"session_interest\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_SESSION_INTEREST), 2) + ",";
   res += "\"session_buy_orders_volume\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_SESSION_BUY_ORDERS_VOLUME), 2) + ",";
   res += "\"session_sell_orders_volume\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_SESSION_SELL_ORDERS_VOLUME), 2) + ",";
   res += "\"session_open\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_SESSION_OPEN), digits) + ",";
   res += "\"session_close\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_SESSION_CLOSE), digits) + ",";
   res += "\"session_aw\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_SESSION_AW), digits) + ",";
   res += "\"session_price_settlement\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_SESSION_PRICE_SETTLEMENT), digits) + ",";
   res += "\"session_price_limit_min\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_SESSION_PRICE_LIMIT_MIN), digits) + ",";
   res += "\"session_price_limit_max\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_SESSION_PRICE_LIMIT_MAX), digits) + ",";
   res += "\"margin_hedged\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_MARGIN_HEDGED), 2) + ",";
   res += "\"price_change\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_PRICE_CHANGE), 4) + ",";
   res += "\"price_volatility\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_PRICE_VOLATILITY), 4) + ",";
   res += "\"price_theoretical\":" + DoubleToString(SymbolInfoDouble(symbol, SYMBOL_PRICE_THEORETICAL), digits) + ",";
   res += "\"price_greeks_delta\":0.0,";
   res += "\"price_greeks_theta\":0.0,";
   res += "\"price_greeks_gamma\":0.0,";
   res += "\"price_greeks_vega\":0.0,";
   res += "\"price_greeks_rho\":0.0,";
   res += "\"price_greeks_omega\":0.0,";
   res += "\"price_sensitivity\":0.0,";
   res += "\"basis\":\"\",";
   res += "\"category\":\"\",";
   res += "\"country\":\"\",";
   res += "\"sector_name\":\"\",";
   res += "\"industry_name\":\"\",";
   res += "\"currency_base\":\"" + JsonEscape(SymbolInfoString(symbol, SYMBOL_CURRENCY_BASE)) + "\",";
   res += "\"currency_profit\":\"" + JsonEscape(SymbolInfoString(symbol, SYMBOL_CURRENCY_PROFIT)) + "\",";
   res += "\"currency_margin\":\"" + JsonEscape(SymbolInfoString(symbol, SYMBOL_CURRENCY_MARGIN)) + "\",";
   res += "\"bank\":\"" + JsonEscape(SymbolInfoString(symbol, SYMBOL_BANK)) + "\",";
   res += "\"description\":\"" + JsonEscape(SymbolInfoString(symbol, SYMBOL_DESCRIPTION)) + "\",";
   res += "\"exchange\":\"" + JsonEscape(SymbolInfoString(symbol, SYMBOL_EXCHANGE)) + "\",";
   res += "\"formula\":\"" + JsonEscape(SymbolInfoString(symbol, SYMBOL_FORMULA)) + "\",";
   res += "\"isin\":\"" + JsonEscape(SymbolInfoString(symbol, SYMBOL_ISIN)) + "\",";
   res += "\"name\":\"" + JsonEscape(symbol) + "\",";
   res += "\"page\":\"" + JsonEscape(SymbolInfoString(symbol, SYMBOL_PAGE)) + "\",";
   res += "\"path\":\"" + JsonEscape(SymbolInfoString(symbol, SYMBOL_PATH)) + "\"";
   res += "}";
   return res;
}

string HandleSymbolInfo(string json)
{
   string symbol = ExtractJsonString(json, "symbol");
   if(symbol == "") return "{\"status\":\"error\",\"error\":\"symbol parameter required\"}";
   
   SymbolSelect(symbol, true);
   string data = FormatSymbolInfo(symbol);
   return "{\"status\":\"ok\",\"action\":\"symbol_info\",\"data\":" + data + "}";
}

string HandleSymbolInfoTick(string json)
{
   string symbol = ExtractJsonString(json, "symbol");
   if(symbol == "") return "{\"status\":\"error\",\"error\":\"symbol parameter required\"}";
   
   MqlTick tick;
   if(!SymbolInfoTick(symbol, tick))
      return "{\"status\":\"error\",\"error\":\"Failed to get tick for symbol " + symbol + "\"}";
      
   int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
   string res = "{\"status\":\"ok\",\"action\":\"symbol_info_tick\",\"data\":{";
   res += "\"time\":" + (string)(long)tick.time + ",";
   res += "\"bid\":" + DoubleToString(tick.bid, digits) + ",";
   res += "\"ask\":" + DoubleToString(tick.ask, digits) + ",";
   res += "\"last\":" + DoubleToString(tick.last, digits) + ",";
   res += "\"volume\":" + (string)tick.volume + ",";
   res += "\"time_msc\":" + (string)tick.time_msc + ",";
   res += "\"flags\":" + (string)tick.flags + ",";
   res += "\"volume_real\":" + DoubleToString(tick.volume_real, 2);
   res += "}}";
   return res;
}

string HandleSymbolsGet(string json)
{
   string group = ExtractJsonString(json, "group");
   int total = SymbolsTotal(false);
   string res = "{\"status\":\"ok\",\"action\":\"symbols_get\",\"data\":[";
   int count = 0;
   
   for(int i = 0; i < total; i++)
   {
      string name = SymbolName(i, false);
      if(name == "") continue;
      
      if(group != "" && StringFind(name, group) < 0)
         continue;
         
      if(count > 0) res += ",";
      res += FormatSymbolInfo(name);
      count++;
      if(count >= 500) break; // Limit to 500 symbols per request for memory safety
   }
   res += "]}";
   return res;
}

ENUM_TIMEFRAMES ParseTimeframe(long tf)
{
   switch((int)tf)
   {
      case 1: return PERIOD_M1;
      case 2: return PERIOD_M2;
      case 3: return PERIOD_M3;
      case 4: return PERIOD_M4;
      case 5: return PERIOD_M5;
      case 6: return PERIOD_M6;
      case 10: return PERIOD_M10;
      case 12: return PERIOD_M12;
      case 15: return PERIOD_M15;
      case 20: return PERIOD_M20;
      case 30: return PERIOD_M30;
      case 16385: return PERIOD_H1;
      case 16386: return PERIOD_H2;
      case 16387: return PERIOD_H3;
      case 16388: return PERIOD_H4;
      case 16390: return PERIOD_H6;
      case 16392: return PERIOD_H8;
      case 16396: return PERIOD_H12;
      case 16408: return PERIOD_D1;
      case 32769: return PERIOD_W1;
      case 49153: return PERIOD_MN1;
      default: return PERIOD_H1;
   }
}


string HandleCopyRatesFromPos(string json)
{
   string symbol = ExtractJsonString(json, "symbol");
   long tf_val = ExtractJsonInt(json, "timeframe", 16385);
   long start_pos = ExtractJsonInt(json, "start_pos", 0);
   long count = ExtractJsonInt(json, "count", 100);
   if(count > 50000) count = 50000;
   
   ENUM_TIMEFRAMES tf = ParseTimeframe(tf_val);
   MqlRates rates[];
   ArraySetAsSeries(rates, true);
   int copied = CopyRates(symbol, tf, (int)start_pos, (int)count, rates);
   if(copied <= 0)
      return "{\"status\":\"error\",\"error\":\"CopyRates failed\",\"code\":" + (string)GetLastError() + "}";
      
   int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
   string res = "{\"status\":\"ok\",\"action\":\"copy_rates_from_pos\",\"data\":[";
   for(int i = 0; i < copied; i++)
   {
      if(i > 0) res += ",";
      res += "{\"time\":" + (string)(long)rates[i].time + ",";
      res += "\"open\":" + DoubleToString(rates[i].open, digits) + ",";
      res += "\"high\":" + DoubleToString(rates[i].high, digits) + ",";
      res += "\"low\":" + DoubleToString(rates[i].low, digits) + ",";
      res += "\"close\":" + DoubleToString(rates[i].close, digits) + ",";
      res += "\"tick_volume\":" + (string)rates[i].tick_volume + ",";
      res += "\"spread\":" + (string)rates[i].spread + ",";
      res += "\"real_volume\":" + (string)rates[i].real_volume + "}";
   }
   res += "]}";
   return res;
}

string HandleCopyRatesFrom(string json)
{
   string symbol = ExtractJsonString(json, "symbol");
   long tf_val = ExtractJsonInt(json, "timeframe", 16385);
   long date_from = ExtractJsonInt(json, "date_from", 0);
   long count = ExtractJsonInt(json, "count", 100);
   if(count > 50000) count = 50000;
   
   ENUM_TIMEFRAMES tf = ParseTimeframe(tf_val);
   MqlRates rates[];
   ArraySetAsSeries(rates, true);
   int copied = CopyRates(symbol, tf, (datetime)date_from, (int)count, rates);
   if(copied <= 0)
      return "{\"status\":\"error\",\"error\":\"CopyRates failed\",\"code\":" + (string)GetLastError() + "}";
      
   int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
   string res = "{\"status\":\"ok\",\"action\":\"copy_rates_from\",\"data\":[";
   for(int i = 0; i < copied; i++)
   {
      if(i > 0) res += ",";
      res += "{\"time\":" + (string)(long)rates[i].time + ",";
      res += "\"open\":" + DoubleToString(rates[i].open, digits) + ",";
      res += "\"high\":" + DoubleToString(rates[i].high, digits) + ",";
      res += "\"low\":" + DoubleToString(rates[i].low, digits) + ",";
      res += "\"close\":" + DoubleToString(rates[i].close, digits) + ",";
      res += "\"tick_volume\":" + (string)rates[i].tick_volume + ",";
      res += "\"spread\":" + (string)rates[i].spread + ",";
      res += "\"real_volume\":" + (string)rates[i].real_volume + "}";
   }
   res += "]}";
   return res;
}

string HandleCopyRatesRange(string json)
{
   string symbol = ExtractJsonString(json, "symbol");
   long tf_val = ExtractJsonInt(json, "timeframe", 16385);
   long date_from = ExtractJsonInt(json, "date_from", 0);
   long date_to = ExtractJsonInt(json, "date_to", 0);
   
   ENUM_TIMEFRAMES tf = ParseTimeframe(tf_val);
   MqlRates rates[];
   ArraySetAsSeries(rates, true);
   int copied = CopyRates(symbol, tf, (datetime)date_from, (datetime)date_to, rates);
   if(copied <= 0)
      return "{\"status\":\"error\",\"error\":\"CopyRates failed\",\"code\":" + (string)GetLastError() + "}";
      
   int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
   string res = "{\"status\":\"ok\",\"action\":\"copy_rates_range\",\"data\":[";
   for(int i = 0; i < copied; i++)
   {
      if(i > 0) res += ",";
      res += "{\"time\":" + (string)(long)rates[i].time + ",";
      res += "\"open\":" + DoubleToString(rates[i].open, digits) + ",";
      res += "\"high\":" + DoubleToString(rates[i].high, digits) + ",";
      res += "\"low\":" + DoubleToString(rates[i].low, digits) + ",";
      res += "\"close\":" + DoubleToString(rates[i].close, digits) + ",";
      res += "\"tick_volume\":" + (string)rates[i].tick_volume + ",";
      res += "\"spread\":" + (string)rates[i].spread + ",";
      res += "\"real_volume\":" + (string)rates[i].real_volume + "}";
   }
   res += "]}";
   return res;
}

string HandleCopyTicksFrom(string json)
{
   string symbol = ExtractJsonString(json, "symbol");
   long date_from = ExtractJsonInt(json, "date_from", 0);
   long count = ExtractJsonInt(json, "count", 100);
   uint flags = (uint)ExtractJsonInt(json, "flags", (long)COPY_TICKS_ALL);
   if(count > 50000) count = 50000;
   
   MqlTick ticks[];
   ulong from_msc = (ulong)date_from * 1000;
   int copied = CopyTicks(symbol, ticks, flags, from_msc, (uint)count);
   if(copied <= 0)
      return "{\"status\":\"error\",\"error\":\"CopyTicks failed\",\"code\":" + (string)GetLastError() + "}";
      
   int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
   string res = "{\"status\":\"ok\",\"action\":\"copy_ticks_from\",\"data\":[";
   for(int i = 0; i < copied; i++)
   {
      if(i > 0) res += ",";
      res += "{\"time\":" + (string)(long)ticks[i].time + ",";
      res += "\"bid\":" + DoubleToString(ticks[i].bid, digits) + ",";
      res += "\"ask\":" + DoubleToString(ticks[i].ask, digits) + ",";
      res += "\"last\":" + DoubleToString(ticks[i].last, digits) + ",";
      res += "\"volume\":" + (string)ticks[i].volume + ",";
      res += "\"time_msc\":" + (string)ticks[i].time_msc + ",";
      res += "\"flags\":" + (string)ticks[i].flags + ",";
      res += "\"volume_real\":" + DoubleToString(ticks[i].volume_real, 2) + "}";
   }
   res += "]}";
   return res;
}

string HandleCopyTicksRange(string json)
{
   string symbol = ExtractJsonString(json, "symbol");
   long date_from = ExtractJsonInt(json, "date_from", 0);
   long date_to = ExtractJsonInt(json, "date_to", 0);
   uint flags = (uint)ExtractJsonInt(json, "flags", (long)COPY_TICKS_ALL);
   
   MqlTick ticks[];
   ulong from_msc = (ulong)date_from * 1000;
   ulong to_msc = (ulong)date_to * 1000;
   int copied = CopyTicksRange(symbol, ticks, flags, from_msc, to_msc);
   if(copied <= 0)
      return "{\"status\":\"error\",\"error\":\"CopyTicksRange failed\",\"code\":" + (string)GetLastError() + "}";
      
   int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
   string res = "{\"status\":\"ok\",\"action\":\"copy_ticks_range\",\"data\":[";
   for(int i = 0; i < copied; i++)
   {
      if(i > 0) res += ",";
      res += "{\"time\":" + (string)(long)ticks[i].time + ",";
      res += "\"bid\":" + DoubleToString(ticks[i].bid, digits) + ",";
      res += "\"ask\":" + DoubleToString(ticks[i].ask, digits) + ",";
      res += "\"last\":" + DoubleToString(ticks[i].last, digits) + ",";
      res += "\"volume\":" + (string)ticks[i].volume + ",";
      res += "\"time_msc\":" + (string)ticks[i].time_msc + ",";
      res += "\"flags\":" + (string)ticks[i].flags + ",";
      res += "\"volume_real\":" + DoubleToString(ticks[i].volume_real, 2) + "}";
   }
   res += "]}";
   return res;
}

string HandlePositionsGet(string json)
{
   string symbol = ExtractJsonString(json, "symbol");
   string group = ExtractJsonString(json, "group");
   long ticket = ExtractJsonInt(json, "ticket", 0);
   
   int total = PositionsTotal();
   string res = "{\"status\":\"ok\",\"action\":\"positions_get\",\"data\":[";
   int count = 0;
   
   for(int i = 0; i < total; i++)
   {
      ulong pos_ticket = PositionGetTicket(i);
      if(pos_ticket <= 0) continue;
      
      if(ticket > 0 && (long)pos_ticket != ticket)
         continue;
         
      string pos_symbol = PositionGetString(POSITION_SYMBOL);
      if(symbol != "" && pos_symbol != symbol)
         continue;
         
      if(group != "" && StringFind(pos_symbol, group) < 0)
         continue;
         
      int digits = (int)SymbolInfoInteger(pos_symbol, SYMBOL_DIGITS);
      if(count > 0) res += ",";
      res += "{";
      res += "\"ticket\":" + (string)pos_ticket + ",";
      res += "\"time\":" + (string)PositionGetInteger(POSITION_TIME) + ",";
      res += "\"time_msc\":" + (string)PositionGetInteger(POSITION_TIME_MSC) + ",";
      res += "\"time_update\":" + (string)PositionGetInteger(POSITION_TIME_UPDATE) + ",";
      res += "\"time_update_msc\":" + (string)PositionGetInteger(POSITION_TIME_UPDATE_MSC) + ",";
      res += "\"type\":" + (string)PositionGetInteger(POSITION_TYPE) + ",";
      res += "\"magic\":" + (string)PositionGetInteger(POSITION_MAGIC) + ",";
      res += "\"identifier\":" + (string)PositionGetInteger(POSITION_IDENTIFIER) + ",";
      res += "\"reason\":" + (string)PositionGetInteger(POSITION_REASON) + ",";
      res += "\"volume\":" + DoubleToString(PositionGetDouble(POSITION_VOLUME), 2) + ",";
      res += "\"price_open\":" + DoubleToString(PositionGetDouble(POSITION_PRICE_OPEN), digits) + ",";
      res += "\"sl\":" + DoubleToString(PositionGetDouble(POSITION_SL), digits) + ",";
      res += "\"tp\":" + DoubleToString(PositionGetDouble(POSITION_TP), digits) + ",";
      res += "\"price_current\":" + DoubleToString(PositionGetDouble(POSITION_PRICE_CURRENT), digits) + ",";
      res += "\"swap\":" + DoubleToString(PositionGetDouble(POSITION_SWAP), 2) + ",";
      res += "\"profit\":" + DoubleToString(PositionGetDouble(POSITION_PROFIT), 2) + ",";
      res += "\"symbol\":\"" + JsonEscape(pos_symbol) + "\",";
      res += "\"comment\":\"" + JsonEscape(PositionGetString(POSITION_COMMENT)) + "\",";
      res += "\"external_id\":\"" + JsonEscape(PositionGetString(POSITION_EXTERNAL_ID)) + "\"";
      res += "}";
      count++;
   }
   res += "]}";
   return res;
}

string HandleOrdersGet(string json)
{
   string symbol = ExtractJsonString(json, "symbol");
   string group = ExtractJsonString(json, "group");
   long ticket = ExtractJsonInt(json, "ticket", 0);
   
   int total = OrdersTotal();
   string res = "{\"status\":\"ok\",\"action\":\"orders_get\",\"data\":[";
   int count = 0;
   
   for(int i = 0; i < total; i++)
   {
      ulong ord_ticket = OrderGetTicket(i);
      if(ord_ticket <= 0) continue;
      
      if(ticket > 0 && (long)ord_ticket != ticket)
         continue;
         
      string ord_symbol = OrderGetString(ORDER_SYMBOL);
      if(symbol != "" && ord_symbol != symbol)
         continue;
         
      if(group != "" && StringFind(ord_symbol, group) < 0)
         continue;
         
      int digits = (int)SymbolInfoInteger(ord_symbol, SYMBOL_DIGITS);
      if(count > 0) res += ",";
      res += "{";
      res += "\"ticket\":" + (string)ord_ticket + ",";
      res += "\"time_setup\":" + (string)OrderGetInteger(ORDER_TIME_SETUP) + ",";
      res += "\"time_setup_msc\":" + (string)OrderGetInteger(ORDER_TIME_SETUP_MSC) + ",";
      res += "\"time_done\":" + (string)OrderGetInteger(ORDER_TIME_DONE) + ",";
      res += "\"time_done_msc\":" + (string)OrderGetInteger(ORDER_TIME_DONE_MSC) + ",";
      res += "\"time_expiration\":" + (string)OrderGetInteger(ORDER_TIME_EXPIRATION) + ",";
      res += "\"type\":" + (string)OrderGetInteger(ORDER_TYPE) + ",";
      res += "\"type_time\":" + (string)OrderGetInteger(ORDER_TYPE_TIME) + ",";
      res += "\"type_filling\":" + (string)OrderGetInteger(ORDER_TYPE_FILLING) + ",";
      res += "\"state\":" + (string)OrderGetInteger(ORDER_STATE) + ",";
      res += "\"magic\":" + (string)OrderGetInteger(ORDER_MAGIC) + ",";
      res += "\"position_id\":" + (string)OrderGetInteger(ORDER_POSITION_ID) + ",";
      res += "\"position_by_id\":" + (string)OrderGetInteger(ORDER_POSITION_BY_ID) + ",";
      res += "\"reason\":" + (string)OrderGetInteger(ORDER_REASON) + ",";
      res += "\"volume_initial\":" + DoubleToString(OrderGetDouble(ORDER_VOLUME_INITIAL), 2) + ",";
      res += "\"volume_current\":" + DoubleToString(OrderGetDouble(ORDER_VOLUME_CURRENT), 2) + ",";
      res += "\"price_open\":" + DoubleToString(OrderGetDouble(ORDER_PRICE_OPEN), digits) + ",";
      res += "\"sl\":" + DoubleToString(OrderGetDouble(ORDER_SL), digits) + ",";
      res += "\"tp\":" + DoubleToString(OrderGetDouble(ORDER_TP), digits) + ",";
      res += "\"price_current\":" + DoubleToString(OrderGetDouble(ORDER_PRICE_CURRENT), digits) + ",";
      res += "\"price_stoplimit\":" + DoubleToString(OrderGetDouble(ORDER_PRICE_STOPLIMIT), digits) + ",";
      res += "\"symbol\":\"" + JsonEscape(ord_symbol) + "\",";
      res += "\"comment\":\"" + JsonEscape(OrderGetString(ORDER_COMMENT)) + "\",";
      res += "\"external_id\":\"" + JsonEscape(OrderGetString(ORDER_EXTERNAL_ID)) + "\"";
      res += "}";
      count++;
   }
   res += "]}";
   return res;
}

string HandleOrderSend(string json)
{
   MqlTradeRequest request = {};
   MqlTradeResult result = {};
   
   request.action = (ENUM_TRADE_REQUEST_ACTIONS)ExtractJsonInt(json, "trade_action", ExtractJsonInt(json, "action", TRADE_ACTION_DEAL));
   request.magic = (ulong)ExtractJsonInt(json, "magic", 0);
   request.order = (ulong)ExtractJsonInt(json, "order", 0);
   request.symbol = ExtractJsonString(json, "symbol");
   request.volume = ExtractJsonDouble(json, "volume", 0.0);
   request.price = ExtractJsonDouble(json, "price", 0.0);
   request.stoplimit = ExtractJsonDouble(json, "stoplimit", 0.0);
   request.sl = ExtractJsonDouble(json, "sl", 0.0);
   request.tp = ExtractJsonDouble(json, "tp", 0.0);
   request.deviation = (ulong)ExtractJsonInt(json, "deviation", 0);
   request.type = (ENUM_ORDER_TYPE)ExtractJsonInt(json, "type", 0);
   request.type_filling = (ENUM_ORDER_TYPE_FILLING)ExtractJsonInt(json, "type_filling", ORDER_FILLING_FOK);
   request.type_time = (ENUM_ORDER_TYPE_TIME)ExtractJsonInt(json, "type_time", ORDER_TIME_GTC);
   request.expiration = (datetime)ExtractJsonInt(json, "expiration", 0);
   request.comment = ExtractJsonString(json, "comment");
   request.position = (ulong)ExtractJsonInt(json, "position", 0);
   request.position_by = (ulong)ExtractJsonInt(json, "position_by", 0);
   
   ResetLastError();
   OrderSend(request, result);
   if(result.retcode == 0)
   {
      result.retcode = (uint)GetLastError();
   }
   
   string res = "{\"status\":\"ok\",\"action\":\"order_send\",\"data\":{";
   res += "\"retcode\":" + (string)result.retcode + ",";
   res += "\"deal\":" + (string)result.deal + ",";
   res += "\"order\":" + (string)result.order + ",";
   res += "\"volume\":" + DoubleToString(result.volume, 2) + ",";
   res += "\"price\":" + DoubleToString(result.price, 5) + ",";
   res += "\"bid\":" + DoubleToString(result.bid, 5) + ",";
   res += "\"ask\":" + DoubleToString(result.ask, 5) + ",";
   res += "\"comment\":\"" + JsonEscape(result.comment != "" ? result.comment : (string)result.retcode) + "\",";
   res += "\"request_id\":" + (string)result.request_id + ",";
   res += "\"retcode_external\":" + (string)result.retcode_external;
   res += "}}";
   return res;
}

string HandleOrderCheck(string json)
{
   MqlTradeRequest request = {};
   MqlTradeCheckResult result = {};
   
   request.action = (ENUM_TRADE_REQUEST_ACTIONS)ExtractJsonInt(json, "trade_action", ExtractJsonInt(json, "action", TRADE_ACTION_DEAL));
   request.magic = (ulong)ExtractJsonInt(json, "magic", 0);
   request.order = (ulong)ExtractJsonInt(json, "order", 0);
   request.symbol = ExtractJsonString(json, "symbol");
   request.volume = ExtractJsonDouble(json, "volume", 0.0);
   request.price = ExtractJsonDouble(json, "price", 0.0);
   request.stoplimit = ExtractJsonDouble(json, "stoplimit", 0.0);
   request.sl = ExtractJsonDouble(json, "sl", 0.0);
   request.tp = ExtractJsonDouble(json, "tp", 0.0);
   request.deviation = (ulong)ExtractJsonInt(json, "deviation", 0);
   request.type = (ENUM_ORDER_TYPE)ExtractJsonInt(json, "type", 0);
   request.type_filling = (ENUM_ORDER_TYPE_FILLING)ExtractJsonInt(json, "type_filling", ORDER_FILLING_FOK);
   request.type_time = (ENUM_ORDER_TYPE_TIME)ExtractJsonInt(json, "type_time", ORDER_TIME_GTC);
   request.expiration = (datetime)ExtractJsonInt(json, "expiration", 0);
   request.comment = ExtractJsonString(json, "comment");
   request.position = (ulong)ExtractJsonInt(json, "position", 0);
   request.position_by = (ulong)ExtractJsonInt(json, "position_by", 0);
   
   ResetLastError();
   OrderCheck(request, result);
   if(result.retcode == 0)
   {
      result.retcode = (uint)GetLastError();
   }
   
   string res = "{\"status\":\"ok\",\"action\":\"order_check\",\"data\":{";
   res += "\"retcode\":" + (string)result.retcode + ",";
   res += "\"balance\":" + DoubleToString(result.balance, 2) + ",";
   res += "\"equity\":" + DoubleToString(result.equity, 2) + ",";
   res += "\"profit\":" + DoubleToString(result.profit, 2) + ",";
   res += "\"margin\":" + DoubleToString(result.margin, 2) + ",";
   res += "\"margin_free\":" + DoubleToString(result.margin_free, 2) + ",";
   res += "\"margin_level\":" + DoubleToString(result.margin_level, 2) + ",";
   res += "\"comment\":\"" + JsonEscape(result.comment) + "\"";
   res += "}}";
   return res;
}

string HandleOrderCalcMargin(string json)
{
   ENUM_ORDER_TYPE action = (ENUM_ORDER_TYPE)ExtractJsonInt(json, "order_type", ExtractJsonInt(json, "trade_action", ORDER_TYPE_BUY));
   string symbol = ExtractJsonString(json, "symbol");
   double volume = ExtractJsonDouble(json, "volume", 1.0);
   double price = ExtractJsonDouble(json, "price", 0.0);
   
   double margin = 0.0;
   bool ok = OrderCalcMargin(action, symbol, volume, price, margin);
   if(!ok)
      return "{\"status\":\"error\",\"error\":\"OrderCalcMargin failed\",\"code\":" + (string)GetLastError() + "}";
      
   return "{\"status\":\"ok\",\"action\":\"order_calc_margin\",\"data\":{\"margin\":" + DoubleToString(margin, 2) + "}}";
}

string HandleOrderCalcProfit(string json)
{
   ENUM_ORDER_TYPE action = (ENUM_ORDER_TYPE)ExtractJsonInt(json, "order_type", ExtractJsonInt(json, "trade_action", ORDER_TYPE_BUY));
   string symbol = ExtractJsonString(json, "symbol");
   double volume = ExtractJsonDouble(json, "volume", 1.0);
   double price_open = ExtractJsonDouble(json, "price_open", 0.0);
   double price_close = ExtractJsonDouble(json, "price_close", 0.0);
   
   double profit = 0.0;
   bool ok = OrderCalcProfit(action, symbol, volume, price_open, price_close, profit);
   if(!ok)
      return "{\"status\":\"error\",\"error\":\"OrderCalcProfit failed\",\"code\":" + (string)GetLastError() + "}";
      
   return "{\"status\":\"ok\",\"action\":\"order_calc_profit\",\"data\":{\"profit\":" + DoubleToString(profit, 2) + "}}";
}

string HandleHistoryOrdersGet(string json)
{
   long date_from = ExtractJsonInt(json, "date_from", 0);
   long date_to = ExtractJsonInt(json, "date_to", 0);
   string symbol = ExtractJsonString(json, "symbol");
   string group = ExtractJsonString(json, "group");
   long ticket = ExtractJsonInt(json, "ticket", 0);
   
   if(date_from > 0 && date_to > 0)
      HistorySelect((datetime)date_from, (datetime)date_to);
   else
      HistorySelect(0, TimeCurrent());
      
   int total = HistoryOrdersTotal();
   string res = "{\"status\":\"ok\",\"action\":\"history_orders_get\",\"data\":[";
   int count = 0;
   
   for(int i = 0; i < total; i++)
   {
      ulong ord_ticket = HistoryOrderGetTicket(i);
      if(ord_ticket <= 0) continue;
      
      if(ticket > 0 && (long)ord_ticket != ticket)
         continue;
         
      string ord_symbol = HistoryOrderGetString(ord_ticket, ORDER_SYMBOL);
      if(symbol != "" && ord_symbol != symbol)
         continue;
         
      if(group != "" && StringFind(ord_symbol, group) < 0)
         continue;
         
      int digits = (int)SymbolInfoInteger(ord_symbol, SYMBOL_DIGITS);
      if(count > 0) res += ",";
      res += "{";
      res += "\"ticket\":" + (string)ord_ticket + ",";
      res += "\"time_setup\":" + (string)HistoryOrderGetInteger(ord_ticket, ORDER_TIME_SETUP) + ",";
      res += "\"time_setup_msc\":" + (string)HistoryOrderGetInteger(ord_ticket, ORDER_TIME_SETUP_MSC) + ",";
      res += "\"time_done\":" + (string)HistoryOrderGetInteger(ord_ticket, ORDER_TIME_DONE) + ",";
      res += "\"time_done_msc\":" + (string)HistoryOrderGetInteger(ord_ticket, ORDER_TIME_DONE_MSC) + ",";
      res += "\"time_expiration\":" + (string)HistoryOrderGetInteger(ord_ticket, ORDER_TIME_EXPIRATION) + ",";
      res += "\"type\":" + (string)HistoryOrderGetInteger(ord_ticket, ORDER_TYPE) + ",";
      res += "\"type_time\":" + (string)HistoryOrderGetInteger(ord_ticket, ORDER_TYPE_TIME) + ",";
      res += "\"type_filling\":" + (string)HistoryOrderGetInteger(ord_ticket, ORDER_TYPE_FILLING) + ",";
      res += "\"state\":" + (string)HistoryOrderGetInteger(ord_ticket, ORDER_STATE) + ",";
      res += "\"magic\":" + (string)HistoryOrderGetInteger(ord_ticket, ORDER_MAGIC) + ",";
      res += "\"position_id\":" + (string)HistoryOrderGetInteger(ord_ticket, ORDER_POSITION_ID) + ",";
      res += "\"position_by_id\":" + (string)HistoryOrderGetInteger(ord_ticket, ORDER_POSITION_BY_ID) + ",";
      res += "\"reason\":" + (string)HistoryOrderGetInteger(ord_ticket, ORDER_REASON) + ",";
      res += "\"volume_initial\":" + DoubleToString(HistoryOrderGetDouble(ord_ticket, ORDER_VOLUME_INITIAL), 2) + ",";
      res += "\"volume_current\":" + DoubleToString(HistoryOrderGetDouble(ord_ticket, ORDER_VOLUME_CURRENT), 2) + ",";
      res += "\"price_open\":" + DoubleToString(HistoryOrderGetDouble(ord_ticket, ORDER_PRICE_OPEN), digits) + ",";
      res += "\"sl\":" + DoubleToString(HistoryOrderGetDouble(ord_ticket, ORDER_SL), digits) + ",";
      res += "\"tp\":" + DoubleToString(HistoryOrderGetDouble(ord_ticket, ORDER_TP), digits) + ",";
      res += "\"price_current\":" + DoubleToString(HistoryOrderGetDouble(ord_ticket, ORDER_PRICE_CURRENT), digits) + ",";
      res += "\"price_stoplimit\":" + DoubleToString(HistoryOrderGetDouble(ord_ticket, ORDER_PRICE_STOPLIMIT), digits) + ",";
      res += "\"symbol\":\"" + JsonEscape(ord_symbol) + "\",";
      res += "\"comment\":\"" + JsonEscape(HistoryOrderGetString(ord_ticket, ORDER_COMMENT)) + "\",";
      res += "\"external_id\":\"" + JsonEscape(HistoryOrderGetString(ord_ticket, ORDER_EXTERNAL_ID)) + "\"";
      res += "}";
      count++;
   }
   res += "]}";
   return res;
}

string HandleHistoryDealsGet(string json)
{
   long date_from = ExtractJsonInt(json, "date_from", 0);
   long date_to = ExtractJsonInt(json, "date_to", 0);
   string symbol = ExtractJsonString(json, "symbol");
   string group = ExtractJsonString(json, "group");
   long ticket = ExtractJsonInt(json, "ticket", 0);
   long position = ExtractJsonInt(json, "position", 0);
   
   if(date_from > 0 && date_to > 0)
      HistorySelect((datetime)date_from, (datetime)date_to);
   else
      HistorySelect(0, TimeCurrent());
      
   int total = HistoryDealsTotal();
   string res = "{\"status\":\"ok\",\"action\":\"history_deals_get\",\"data\":[";
   int count = 0;
   
   for(int i = 0; i < total; i++)
   {
      ulong deal_ticket = HistoryDealGetTicket(i);
      if(deal_ticket <= 0) continue;
      
      if(ticket > 0 && (long)deal_ticket != ticket)
         continue;
         
      if(position > 0 && (long)HistoryDealGetInteger(deal_ticket, DEAL_POSITION_ID) != position)
         continue;
         
      string deal_symbol = HistoryDealGetString(deal_ticket, DEAL_SYMBOL);
      if(symbol != "" && deal_symbol != symbol)
         continue;
         
      if(group != "" && StringFind(deal_symbol, group) < 0)
         continue;
         
      int digits = (int)SymbolInfoInteger(deal_symbol, SYMBOL_DIGITS);
      if(count > 0) res += ",";
      res += "{";
      res += "\"ticket\":" + (string)deal_ticket + ",";
      res += "\"order\":" + (string)HistoryDealGetInteger(deal_ticket, DEAL_ORDER) + ",";
      res += "\"time\":" + (string)HistoryDealGetInteger(deal_ticket, DEAL_TIME) + ",";
      res += "\"time_msc\":" + (string)HistoryDealGetInteger(deal_ticket, DEAL_TIME_MSC) + ",";
      res += "\"type\":" + (string)HistoryDealGetInteger(deal_ticket, DEAL_TYPE) + ",";
      res += "\"entry\":" + (string)HistoryDealGetInteger(deal_ticket, DEAL_ENTRY) + ",";
      res += "\"magic\":" + (string)HistoryDealGetInteger(deal_ticket, DEAL_MAGIC) + ",";
      res += "\"reason\":" + (string)HistoryDealGetInteger(deal_ticket, DEAL_REASON) + ",";
      res += "\"position_id\":" + (string)HistoryDealGetInteger(deal_ticket, DEAL_POSITION_ID) + ",";
      res += "\"volume\":" + DoubleToString(HistoryDealGetDouble(deal_ticket, DEAL_VOLUME), 2) + ",";
      res += "\"price\":" + DoubleToString(HistoryDealGetDouble(deal_ticket, DEAL_PRICE), digits) + ",";
      res += "\"commission\":" + DoubleToString(HistoryDealGetDouble(deal_ticket, DEAL_COMMISSION), 2) + ",";
      res += "\"swap\":" + DoubleToString(HistoryDealGetDouble(deal_ticket, DEAL_SWAP), 2) + ",";
      res += "\"profit\":" + DoubleToString(HistoryDealGetDouble(deal_ticket, DEAL_PROFIT), 2) + ",";
      res += "\"fee\":" + DoubleToString(HistoryDealGetDouble(deal_ticket, DEAL_FEE), 2) + ",";
      res += "\"symbol\":\"" + JsonEscape(deal_symbol) + "\",";
      res += "\"comment\":\"" + JsonEscape(HistoryDealGetString(deal_ticket, DEAL_COMMENT)) + "\",";
      res += "\"external_id\":\"" + JsonEscape(HistoryDealGetString(deal_ticket, DEAL_EXTERNAL_ID)) + "\"";
      res += "}";
      count++;
   }
   res += "]}";
   return res;
}

//+------------------------------------------------------------------+
//| Router: Process JSON Request                                     |
//+------------------------------------------------------------------+
string ProcessRequest(string request_json)
{
   string action = ExtractJsonString(request_json, "action");
   if(action == "ping") return HandlePing();
   if(action == "version") return HandleVersion();
   if(action == "terminal_info") return HandleTerminalInfo();
   if(action == "account_info") return HandleAccountInfo();
   if(action == "symbols_total") return HandleSymbolsTotal();
   if(action == "symbol_info") return HandleSymbolInfo(request_json);
   if(action == "symbol_info_tick") return HandleSymbolInfoTick(request_json);
   if(action == "symbols_get") return HandleSymbolsGet(request_json);
   if(action == "copy_rates_from") return HandleCopyRatesFrom(request_json);
   if(action == "copy_rates_from_pos") return HandleCopyRatesFromPos(request_json);
   if(action == "copy_rates_range") return HandleCopyRatesRange(request_json);
   if(action == "copy_ticks_from") return HandleCopyTicksFrom(request_json);
   if(action == "copy_ticks_range") return HandleCopyTicksRange(request_json);
   if(action == "positions_get") return HandlePositionsGet(request_json);
   if(action == "orders_get") return HandleOrdersGet(request_json);
   if(action == "order_send") return HandleOrderSend(request_json);
   if(action == "order_check") return HandleOrderCheck(request_json);
   if(action == "order_calc_margin") return HandleOrderCalcMargin(request_json);
   if(action == "order_calc_profit") return HandleOrderCalcProfit(request_json);
   if(action == "history_orders_get") return HandleHistoryOrdersGet(request_json);
   if(action == "history_deals_get") return HandleHistoryDealsGet(request_json);
   
   return "{\"status\":\"error\",\"error\":\"Unknown action: " + action + "\"}";
}

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("==> [RestGateway] Inicializando Gateway TCP JSON na porta ", InpPort);
   
   uchar wsa_data[];
   ArrayResize(wsa_data, 512);
   ArrayInitialize(wsa_data, 0);
   if(WSAStartup(0x0202, wsa_data) != 0)
   {
      Print("[RestGateway] ERRO WSAStartup: ", WSAGetLastError());
      return INIT_FAILED;
   }
   
   g_server_socket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
   if(g_server_socket == INVALID_SOCKET_VAL)
   {
      Print("[RestGateway] ERRO socket: ", WSAGetLastError());
      WSACleanup();
      return INIT_FAILED;
   }
   
   // Set non-blocking mode on listening socket
   uint non_block = 1;
   ioctlsocket(g_server_socket, FIONBIO, non_block);
   
   // Prepare sockaddr_in (16 bytes)
   uchar saddr[];
   ArrayResize(saddr, 16);
   ArrayInitialize(saddr, 0);
   saddr[0] = 2; // AF_INET = 2
   saddr[1] = 0;
   saddr[2] = (uchar)((InpPort >> 8) & 0xFF); // Port MSB
   saddr[3] = (uchar)(InpPort & 0xFF);        // Port LSB
   saddr[4] = 127;                            // 127.0.0.1
   saddr[5] = 0;
   saddr[6] = 0;
   saddr[7] = 1;
   
   if(bind(g_server_socket, saddr, 16) == SOCKET_ERROR)
   {
      Print("[RestGateway] ERRO bind na porta ", InpPort, ": ", WSAGetLastError());
      closesocket(g_server_socket);
      g_server_socket = INVALID_SOCKET_VAL;
      WSACleanup();
      return INIT_FAILED;
   }
   
   if(listen(g_server_socket, 16) == SOCKET_ERROR)
   {
      Print("[RestGateway] ERRO listen: ", WSAGetLastError());
      closesocket(g_server_socket);
      g_server_socket = INVALID_SOCKET_VAL;
      WSACleanup();
      return INIT_FAILED;
   }
   
   Print("[RestGateway] Servidor TCP ouvindo com sucesso em 127.0.0.1:", InpPort);
   EventSetMillisecondTimer(20); // Poll every 20ms for fast request processing
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   if(g_server_socket != INVALID_SOCKET_VAL)
   {
      closesocket(g_server_socket);
      g_server_socket = INVALID_SOCKET_VAL;
      WSACleanup();
      Print("[RestGateway] Socket do servidor fechado.");
   }
}

//+------------------------------------------------------------------+
//| Timer function: Poll & Handle Incoming Connections               |
//+------------------------------------------------------------------+
void OnTimer()
{
   if(g_server_socket == INVALID_SOCKET_VAL) return;
   
   for(int loop = 0; loop < 10; loop++)
   {
      uchar client_addr[];
      ArrayResize(client_addr, 16);
      int addr_len = 16;
      ArrayInitialize(client_addr, 0);
      
      ulong client_sock = accept(g_server_socket, client_addr, addr_len);
      if(client_sock == INVALID_SOCKET_VAL)
         break; // No pending incoming connection
         
      // Set client socket to blocking mode with 2000ms timeout
      uint non_block = 0;
      ioctlsocket(client_sock, FIONBIO, non_block);
      
      uchar timeout_val[];
      ArrayResize(timeout_val, 4);
      timeout_val[0] = (uchar)(2000 & 0xFF);
      timeout_val[1] = (uchar)((2000 >> 8) & 0xFF);
      timeout_val[2] = 0;
      timeout_val[3] = 0;
      setsockopt(client_sock, SOL_SOCKET_VAL, SO_RCVTIMEO_VAL, timeout_val, 4);
      setsockopt(client_sock, SOL_SOCKET_VAL, SO_SNDTIMEO_VAL, timeout_val, 4);
      
      uchar req_buf[];
      ArrayResize(req_buf, 65536);
      ArrayInitialize(req_buf, 0);
      
      int bytes_read = recv(client_sock, req_buf, 65535, 0);
      if(bytes_read > 0)
      {
         string req_str = CharArrayToString(req_buf, 0, bytes_read);
         string res_str = ProcessRequest(req_str) + "\n";
         
         uchar res_buf[];
         int res_len = StringToCharArray(res_str, res_buf, 0, WHOLE_ARRAY, CP_UTF8);
         if(res_len > 0 && res_buf[res_len - 1] == 0) res_len--;
         
         if(res_len > 0)
         {
            send(client_sock, res_buf, res_len, 0);
         }
      }
      
      closesocket(client_sock);
   }
}

//+------------------------------------------------------------------+
//| Tick function: Fallback loop trigger                             |
//+------------------------------------------------------------------+
void OnTick()
{
   OnTimer();
}


