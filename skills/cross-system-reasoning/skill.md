---
name: cross-system-reasoning
description: Trace one user goal across specialist systems instead of checking only the first visible component.
keywords: cross system trace signal tradingview telegram make crm mt5 crosstrade tradovate binance lifecycle
---
# Cross System Reasoning
1. Start from the user-visible symptom and identify every hop that can affect the outcome.
2. FOREX example: TradingView/signal -> transport/router -> risk/series EA -> MT5 order/fill -> lifecycle/CRM/Telegram.
3. FUTURES example: signal -> Make/router -> firm/account selector -> CrossTrade -> Tradovate -> fill/SL/TP -> lifecycle.
4. STOCKS/CRYPTO follow equivalent ingress -> guard -> broker/exchange -> fill -> persistence -> alert chains.
5. Use correlation IDs/timestamps across hops and stop at the first proven break rather than guessing downstream causes.
