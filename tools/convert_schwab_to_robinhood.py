"""One-off script: convert schwabIRA_b4_robinhood-migration.csv to Robinhood CSV format."""

import csv
import re
import sys
from pathlib import Path

INPUT = Path("input/schwabIRA_b4_robinhood-migration.csv")
OUTPUT = Path("input/schwabIRA_b4_robinhood-migration_rh.csv")

RH_HEADERS = [
    "Activity Date", "Process Date", "Settle Date",
    "Instrument", "Description", "Trans Code", "Quantity", "Price", "Amount",
]

CUSIP_RE = re.compile(r"^[0-9A-Z]{9}$")
OPT_SYM_RE = re.compile(r"^([A-Z]+\d*)\s+(\d{2}/\d{2}/\d{4})\s+([\d.]+)\s+([CP])$")


def schwab_date_to_rh(d):
    """MM/DD/YYYY → M/D/YYYY (no leading zeros).
    Also handles 'MM/DD/YYYY as of MM/DD/YYYY' — takes the first date.
    """
    match = re.search(r"(\d{2})/(\d{2})/(\d{4})", d)
    if not match:
        return d.strip()
    return f"{int(match.group(1))}/{int(match.group(2))}/{match.group(3)}"


def schwab_amount_to_rh(s):
    """'$1,234.56' → '$1,234.56'; '-$1,234.56' → '($1,234.56)'; '' → ''."""
    s = s.strip()
    if not s:
        return ""
    if s.startswith("-$"):
        return f"({s[1:]})"
    return s


def schwab_price_to_rh(s):
    """Already '$X.XX' or '' — pass through."""
    return s.strip()


def parse_opt_symbol(sym):
    """'BBY 01/17/2025 95.00 C' → (ticker, 'M/D/YYYY', strike_str, 'Call'/'Put')"""
    m = OPT_SYM_RE.match(sym.strip())
    if not m:
        return None
    ticker, exp_mmddyyyy, strike, cp = m.groups()
    exp_rh = schwab_date_to_rh(exp_mmddyyyy)
    opt_type = "Call" if cp == "C" else "Put"
    strike_str = strike.rstrip("0").rstrip(".")  # 95.00 → 95, 7.50 → 7.5
    return ticker, exp_rh, strike_str, opt_type


def build_opt_description(ticker, exp_rh, strike_str, opt_type, expired=False):
    base = f"{ticker} {exp_rh} {opt_type} ${strike_str}"
    return f"Option Expiration for {base}" if expired else base


def qty_str(raw, *, absolute=False, short=False):
    """Clean a quantity string; optionally abs it and/or append 'S'."""
    raw = raw.strip().replace(",", "")
    if not raw or not re.search(r"\d", raw):
        return ""
    val = abs(int(float(raw))) if absolute else int(float(raw))
    s = str(val)
    return s + "S" if short else s


def is_swvxx(row):
    return "SWVXX" in row["Symbol"] or "SWVXX" in row["Description"]


def is_cusip(sym):
    return bool(CUSIP_RE.match(sym)) if sym else False


def convert(row):
    """Return a Robinhood row dict, or None to skip."""
    action = row["Action"].strip()
    sym = row["Symbol"].strip()
    desc = row["Description"].strip()
    raw_date = row["Date"].strip()
    qty_raw = row["Quantity"].strip()
    price_raw = row["Price"].strip()
    amount_raw = row["Amount"].strip()

    if not raw_date or not action:
        return None

    date_rh = schwab_date_to_rh(raw_date)
    price_rh = schwab_price_to_rh(price_raw)
    amount_rh = schwab_amount_to_rh(amount_raw)

    def row_out(instrument, description, code, quantity):
        return {
            "Activity Date": date_rh,
            "Process Date": date_rh,
            "Settle Date": date_rh,
            "Instrument": instrument,
            "Description": description,
            "Trans Code": code,
            "Quantity": quantity,
            "Price": price_rh,
            "Amount": amount_rh,
        }

    # ── Skip categories ───────────────────────────────────────────────────────
    if is_swvxx(row):
        return None
    if is_cusip(sym):
        return None
    if action in ("Journaled Shares", "Journal"):
        return None
    if action in ("Bank Interest", "Bond Interest"):
        return None
    if action in ("Full Redemption", "Full Redemption Adj"):
        return None
    if action in ("Qual Div Reinvest", "Reinvest Dividend", "Reinvest Shares"):
        return None

    # ── Options ───────────────────────────────────────────────────────────────
    opt = parse_opt_symbol(sym) if sym else None

    if action in ("Sell to Open", "Buy to Open", "Buy to Close", "Sell to Close",
                  "Expired", "Assigned"):
        if not opt:
            return None
        ticker, exp_rh, strike_str, opt_type = opt
        code_map = {
            "Sell to Open": "STO", "Buy to Open": "BTO",
            "Buy to Close": "BTC", "Sell to Close": "STC",
            "Expired": "OEXP", "Assigned": "OASGN",
        }
        code = code_map[action]
        opt_desc = build_opt_description(ticker, exp_rh, strike_str, opt_type,
                                         expired=(action == "Expired"))
        return row_out(ticker, opt_desc, code, qty_str(qty_raw, absolute=True))

    # ── Stocks ────────────────────────────────────────────────────────────────
    if action in ("Buy", "Sell"):
        if not sym or is_cusip(sym):
            return None
        code = action  # "Buy" or "Sell"
        return row_out(sym, desc, code, qty_str(qty_raw, absolute=True))

    # ── Dividends ─────────────────────────────────────────────────────────────
    if action in ("Qualified Dividend", "Cash Dividend"):
        if not sym:
            return None
        return row_out(sym, desc, "CDIV", "")

    # ── Security Transfer / Internal Transfer → skip (no cash amount) ────────
    if action in ("Security Transfer", "Internal Transfer"):
        return None

    # ── Internal Transfer (TDA → Schwab, Nov 2023) ───────────────────────────
    if action == "Internal Transfer":
        if not sym or not re.search(r"\d", qty_raw):
            return None
    return None  # unhandled action → skip


def main():
    with open(INPUT, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    out_rows = []
    skipped = {}
    for row in rows:
        result = convert(row)
        if result:
            out_rows.append(result)
        else:
            a = row["Action"].strip()
            skipped[a] = skipped.get(a, 0) + 1

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=RH_HEADERS, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Wrote {len(out_rows)} rows -> {OUTPUT}")
    if skipped:
        print("Skipped:")
        for a, n in sorted(skipped.items()):
            print(f"  {n:4d}  {a}")


if __name__ == "__main__":
    main()
