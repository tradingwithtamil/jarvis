---
name: darkflow-trading-core
description: Apply BOSS's Dark Flow trading logic consistently across Forex, Futures, Stocks and Crypto.
keywords: dark flow, dft, fvg, bos, mss, choch, no wick, breakout, ms-rr, the great
---
# Dark Flow Trading Core
1. Dark Flow Theory uses HTF FVG plus 2/2 fractal structure and the 50% level from the last opposite fractal swing.
2. SELL: bearish FVG at or above 50%. BUY: bullish FVG at or below 50%. Exact 50% is valid.
3. FVG mitigation is first tap with candle close; mitigated zones stop at the mitigation candle, unmitigated zones extend.
4. Keep only the last valid FVG for the active setup.
5. Entry confirmation is the next 1m MSS/BOS in the same direction after the HTF FVG tap; never confirm before the tap.
6. Structure sequence focus: CHOCH, BOS, BOS. One active signal/trade at a time unless BOSS explicitly changes it.
7. Probability is HP when the parent swing is intact or 50% is touched; LP otherwise. A valid tap before the break can lock HP.
8. Default display/logic: RR 1:2, last 5 signals, small arrows, LOSS/PROFIT only, alerts ENTRY/SL_HIT/TP_HIT.
9. No-Wick mode: displacement logic, swing SL, RR choices 1:1/1:2/1:3, BE after 1:1, pending expiry 15 candles.
10. MS-RR mode: enter around 50% of BOS/CHOCH move, SL at structure high/low, TP external liquidity or configured RR.
11. Breakout mode tracks WR, sequence and recent performance; do not mix its entry state with DFT state.
12. The Great supports EN1/EN2, risk USD/fixed lot/fixed qty, TP1..TP5, reverse, pending expiry, WR/sequence and Cash Mode.
13. Never invent a signal, fill, SL/TP or result. Use live source evidence when reporting current trades.