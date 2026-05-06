"""Merrill Edge CSV parser.

Handles the Merrill Edge all-transactions CSV export as well as the PDF-
converted CSV produced by tools/extract_merrill_pdf.py. Both share the
same column layout; only the encoding differs (utf-8-sig vs utf-8).

Merrill option symbol format: TICKER#MONTH_CODE DAY2 YEAR2 SIZE_CODE STRIKE6
  e.g. ETSY#C1927D750000 = ETSY Mar 19 2027 Call $75.00
  Call months: A=Jan … L=Dec
  Put  months: M=Jan … X=Dec
  Size code C → strike = value / 1000  (strike ≥ 100)
  Size code D → strike = value / 10000 (strike < 100)
"""

import re
import csv
from collections import defaultdict

_MERRILL_OPT_RE = re.compile(r"^([A-Z0-9]+)#([A-Z])(\d{2})(\d{2})([CD])(\d+)$")
_CALL_MONTH = dict(zip("ABCDEFGHIJKL", range(1, 13)))
_PUT_MONTH  = dict(zip("MNOPQRSTUVWX", range(1, 13)))
_TICKER_RE  = re.compile(r"^[A-Z]{1,6}(\.[A-Z]{1,2})?$")

# Rows whose descriptions start with these prefixes carry no position data
# (money-market fund activity, ADR fees, DRIP bookkeeping, symbol changes).
_SKIP_DESC = (
    "Interest ",
    "Depository Bank",
    "Reinvestment Program",
    "Reinvestment Share",
    "Subscription ",
    "Redemption ",
    "Exchange ",
    "Dividend BLF",
)

# Money-market symbols to exclude entirely
_SKIP_SYMS = {"TFDXX", "IIAXX"}

_STOCK_ACTIONS = {"Purchase", "Sale", "Sale-Option Assigned"}
_OPT_ACTIONS   = {"Option Sale", "Option Purchase", "Option Expired", "Option Assigned"}


def parse_dollar(s):
    if not s:
        return None
    s = re.sub(r"[$,\s]", "", s)
    try:
        return float(s)
    except ValueError:
        return None


def _parse_option_symbol(sym):
    """ETSY#C1927D750000 → (ticker, expiration MM/DD/YYYY, strike, opt_type, schwab_symbol)
    Returns None for unrecognised / adjusted-strike symbols.
    """
    m = _MERRILL_OPT_RE.match(sym)
    if not m:
        return None
    ticker, mc, day_s, yr_s, size, strike_s = m.groups()

    if mc in _CALL_MONTH:
        mm, opt_type = _CALL_MONTH[mc], "Call"
    elif mc in _PUT_MONTH:
        mm, opt_type = _PUT_MONTH[mc], "Put"
    else:
        return None

    strike = int(strike_s) / (1000.0 if size == "C" else 10000.0)
    year = 2000 + int(yr_s)
    expiration = f"{mm:02d}/{int(day_s):02d}/{year}"
    cp = "C" if opt_type == "Call" else "P"
    schwab_symbol = f"{ticker} {expiration} {strike:.2f} {cp}"
    return ticker, expiration, strike, opt_type, schwab_symbol


def _map_action(desc, signed_qty):
    """Return internal action name from description text and raw signed quantity."""
    if desc.startswith("Option Sale"):
        return "Sell to Open" if signed_qty <= 0 else "Sell to Close"
    if desc.startswith("Option Purchase"):
        return "Buy to Close" if signed_qty >= 0 else "Buy to Open"
    if desc.startswith("Option Expired"):
        return "Expired"
    if desc.startswith("Option Assigned"):
        return "Assigned"
    if desc.startswith("Purchase"):
        return "Buy"
    if desc.startswith("Sale"):      # covers "Sale" and "Sale-Option Assigned"
        return "Sell"
    if desc.startswith("Dividend") or desc.startswith("Foreign Dividend"):
        return "Dividend"
    return None


def _parse_rows_to_transactions(rows):
    """Convert a list of cleaned Merrill row dicts to 11-element transaction lists."""
    transactions = []
    for row in rows:
        date_str = row.get("Trade Date", "").strip()
        desc     = row.get("Description", "").strip()
        sym      = row.get("Symbol/ CUSIP", "").strip()
        qty_s    = row.get("Quantity", "").strip().replace(",", "")
        price_s  = row.get("Price", "").strip()
        amount_s = row.get("Amount", "").strip()

        if not date_str or not desc:
            continue
        if any(desc.startswith(p) for p in _SKIP_DESC):
            continue
        if sym in _SKIP_SYMS:
            continue

        try:
            signed_qty = int(float(qty_s)) if qty_s and re.search(r"\d", qty_s) else 0
        except ValueError:
            signed_qty = 0

        action = _map_action(desc, signed_qty)
        if action is None:
            continue

        price  = parse_dollar(price_s)
        amount = parse_dollar(amount_s)
        qty    = abs(signed_qty) if signed_qty else ""

        if "#" in sym:
            parsed = _parse_option_symbol(sym)
            if not parsed:
                continue
            ticker, expiration, strike, opt_type, schwab_sym = parsed
            transactions.append([
                date_str, action, opt_type, schwab_sym,
                strike, expiration, qty,
                "" if price is None else price,
                "",
                "" if amount is None else amount,
                "",
            ])
            # Merrill omits the stock purchase row for put assignments.
            # Synthesize it so share counts and cost basis are correct.
            if action == "Assigned" and opt_type == "Put" and qty != "":
                shares = int(qty) * 100
                buy_amount = -(shares * strike)
                transactions.append([
                    date_str, "Buy", "Stock", ticker,
                    "", "", shares, strike, "", buy_amount, "",
                ])
        elif action == "Dividend":
            transactions.append([
                date_str, action, "Dividend", sym,
                "", "", "", "", "",
                "" if amount is None else amount,
                "",
            ])
        else:
            transactions.append([
                date_str, action, "Stock", sym,
                "", "", qty,
                "" if price is None else price,
                "",
                "" if amount is None else amount,
                "",
            ])

    transactions.sort(key=lambda r: (r[0][6:], r[0][:2], r[0][3:5]))
    return transactions


def parse_all_transactions(filepath):
    """Parse a Merrill Edge all-transactions CSV.

    Returns (ticker_transactions, other_rows):
    - ticker_transactions: dict {ticker: [transaction rows]}
    - other_rows: list of raw row dicts that don't belong to any position
    """
    raw_rows = []
    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cleaned = {
                k.strip(): (v or "").strip()
                for k, v in row.items()
                if k and k.strip()
            }
            if any(cleaned.values()):
                raw_rows.append(cleaned)

    # Pass 1: collect tickers that have real stock / option positions
    position_tickers = set()
    for row in raw_rows:
        desc = row.get("Description", "")
        sym  = row.get("Symbol/ CUSIP", "")
        if not sym or not desc:
            continue
        if "#" in sym:
            parsed = _parse_option_symbol(sym)
            if parsed:
                position_tickers.add(parsed[0])
        elif any(desc.startswith(a) for a in _STOCK_ACTIONS) and _TICKER_RE.match(sym):
            position_tickers.add(sym)

    # Pass 2: assign rows to tickers or other_rows
    ticker_raw = defaultdict(list)
    other_rows = []
    for row in raw_rows:
        desc = row.get("Description", "")
        sym  = row.get("Symbol/ CUSIP", "")
        if not desc:
            continue

        if sym in _SKIP_SYMS:
            continue

        if "#" in sym:
            parsed = _parse_option_symbol(sym)
            if parsed:
                ticker_raw[parsed[0]].append(row)
            else:
                other_rows.append(row)
        elif any(desc.startswith(a) for a in _STOCK_ACTIONS) and sym and _TICKER_RE.match(sym):
            ticker_raw[sym].append(row)
        elif desc.startswith(("Dividend", "Foreign Dividend")) and sym in position_tickers:
            ticker_raw[sym].append(row)
        elif sym and sym not in _SKIP_SYMS:
            other_rows.append(row)

    ticker_transactions = {
        t: _parse_rows_to_transactions(rows)
        for t, rows in ticker_raw.items()
    }
    return ticker_transactions, other_rows
