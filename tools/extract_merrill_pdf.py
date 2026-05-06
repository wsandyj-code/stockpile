"""Extract Merrill Edge IRA PDF statements and write to Merrill CSV format.

Reads merrill2023.pdf (all of 2023) and merrill2024.pdf (all of 2024),
extracts transactions before the existing CSV cutoff (2024-05-06), and
writes input/merrill_2023_2024_missing.csv in Merrill CSV format.
"""

import re
import csv
from datetime import date
from pathlib import Path
import pdfplumber

INPUT_PDFS = ["input/merrill2023.pdf", "input/merrill2024.pdf"]
OUTPUT = Path("input/merrill_2023_2024_missing.csv")
CSV_CUTOFF = date(2024, 5, 6)   # first date in existing CSV — exclude this and later
ACCOUNT = "IRA-Edge 6B1-50X02"

OPT_BOILERPLATE = (
    "CLIENT ENTERED. ML ACTED AS AGENT. ORDERS MAY BE ROUTED TO A MERRILL "
    "LYNCH AFFILIATE WHO MAY EXECUTE SUCH ORDERS AS PRINCIPAL OR AGENT OR "
    "ROUTE ORDERS TO OTHER MARKET CENTERS FOR EXECUTION. "
    "SECURITY IS AN EXCHANGE LISTED OPTION."
)
STK_BOILERPLATE = (
    "CLIENT ENTERED. ORDERS MAY BE ROUTED TO A MERRILL LYNCH AFFILIATE WHO "
    "MAY EXECUTE SUCH ORDERS AS PRINCIPAL OR AGENT OR ROUTE ORDERS TO OTHER "
    "MARKET CENTERS FOR EXECUTION."
)

MERRILL_HEADERS = [
    "Trade Date ", "Settlement Date ", "Account ", "Description ",
    "Type ", "Symbol/ CUSIP ", "Quantity ", "Price ", "Amount ", " "
]

CALL_MONTHS = dict(zip(range(1, 13), "ABCDEFGHIJKL"))
PUT_MONTHS  = dict(zip(range(1, 13), "MNOPQRSTUVWX"))

MONTH_NAMES = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12,
}

PERIOD_RE = re.compile(
    r"(January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+(\d{1,2}),\s+(20\d{2})\s+-\s+"
    r"(January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+(\d{1,2}),\s+(20\d{2})"
)

# Date at start of line; tolerates OCR artefacts like "1 2 . /29"
DATE_START_RE = re.compile(r"^(\d[\d\s\.]{0,4}/\d{2})\s+(.*)", re.DOTALL)

# Option line 1 — fixed qty pattern ([-\d.]+) so it doesn't eat the amounts
OPT_LINE1_RE = re.compile(
    r"^(CALL|PUT)\s+(\S+)\s+([\d.]+)\s+"
    r"(Option (?:Purchase|Sale|Expired|Assigned))\s+"
    r"([-\d.]+)"                                       # qty (no spaces)
    r"(?:\s+([\d,.()]+)\s+([\d,.()]+)\s+([\d,.()]+))?"  # amount fees credit
)

# Option line 2 with OPEN/CLOSE TRAN (normal buy/sell)
OPT_TRAN_LINE2_RE = re.compile(
    r"^(.+?)\s+EXP\s+(\d{2}-\d{2}-\d{2})\s+(OPEN|CLOSE)\s+TRAN"
    r"\s+\S+\s+(\w{3})\s+([\d.]+)\s+PRICE\s+[\d.]+\s+UNIT PRICE\s+([\d.]+)"
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def normalize_mmdd(raw):
    cleaned = re.sub(r"[\s.]", "", raw)
    m = re.match(r"^(\d{1,2})/(\d{2})$", cleaned)
    return f"{int(m.group(1)):02d}/{int(m.group(2)):02d}" if m else None


def infer_year(month, period_start, period_end):
    if period_start.year == period_end.year:
        return period_start.year
    return period_start.year if month >= period_start.month else period_end.year


def make_date(mmdd, period_start, period_end):
    m = re.match(r"(\d{2})/(\d{2})", mmdd)
    if not m:
        return None
    mm, dd = int(m.group(1)), int(m.group(2))
    year = infer_year(mm, period_start, period_end)
    try:
        return date(year, mm, dd)
    except ValueError:
        return None


def fmt_amount(pdf_str):
    s = pdf_str.strip()
    if not s:
        return ""
    negative = s.startswith("(") and s.endswith(")")
    try:
        val = float(re.sub(r"[(),\s]", "", s))
    except ValueError:
        return ""
    return f"-${val:,.2f}" if negative else f"${val:,.2f}"


def fmt_price(s):
    s = s.strip()
    if not s:
        return ""
    try:
        return f"${float(s):,.2f}"
    except ValueError:
        return ""


def build_merrill_symbol(ticker, exp_mmddyy, opt_type, strike_f):
    m = re.match(r"(\d{2})-(\d{2})-(\d{2})", exp_mmddyy)
    if not m:
        return ticker
    mm, dd, yy = int(m.group(1)), int(m.group(2)), m.group(3)
    mc = CALL_MONTHS[mm] if opt_type == "CALL" else PUT_MONTHS[mm]
    if strike_f >= 100:
        code = "C"
        sval = int(round(strike_f * 1000))
    else:
        code = "D"
        sval = int(round(strike_f * 10000))
    return f"{ticker}#{mc}{dd:02d}{yy}{code}{sval:06d}"


def build_strike_label(strike_f):
    return f"{int(strike_f):05d}"


# ── PDF line extraction ────────────────────────────────────────────────────────

_SKIP_LINE_RE = re.compile(
    r"^(Subtotal|NET TOTAL|TOTAL |TOTAL$|\+\+|\d{3}\s+\d+\s+of\s+\d+|"
    r"Settlement\s+Transaction|Date\s+Description|"
    r"Commissions/|Tax-Exempt\s+(Interest|Dividends)|"
    r"Fees Included|DOCUMENT PREFERENCES)",
    re.IGNORECASE,
)


def _is_skip(line):
    return not line.strip() or bool(_SKIP_LINE_RE.match(line))


def extract_lines(filepath):
    """Return list of (period_start, period_end, line_text) for every useful line."""
    result = []
    current = (None, None)
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pm = PERIOD_RE.search(text)
            if pm:
                s = date(int(pm.group(3)), MONTH_NAMES[pm.group(1)], int(pm.group(2)))
                e = date(int(pm.group(6)), MONTH_NAMES[pm.group(4)], int(pm.group(5)))
                current = (s, e)
            if current[0] is None:
                continue
            for line in text.splitlines():
                stripped = line.strip()
                if stripped:
                    result.append((*current, stripped))
    return result


# ── Transaction parser ─────────────────────────────────────────────────────────

def build_company_map(lines, company_ticker):
    """Pre-pass: populate company_ticker from option TRAN lines and holdings."""
    for _, _, line in lines:
        tran_m = re.search(
            r"(.+?)\s+EXP\s+\d{2}-\d{2}-\d{2}\s+(?:OPEN|CLOSE)\s+TRAN\s+(\S+)", line
        )
        if tran_m:
            comp = tran_m.group(1).strip()
            tkr  = tran_m.group(2).strip()
            if comp and tkr and re.match(r"^[A-Z]{1,6}$", tkr):
                company_ticker[comp] = tkr
        hold_m = re.match(
            r"^([A-Z][A-Z0-9 &.,/]+?)\s{2,}([A-Z]{1,6})\s+([\d,]+\.\d{4})", line
        )
        if hold_m:
            company_ticker[hold_m.group(1).strip()] = hold_m.group(2).strip()


def parse_lines(lines, company_ticker):
    """Parse flat list of (period_start, period_end, line) into transaction dicts."""
    transactions = []
    section = None
    i = 0

    while i < len(lines):
        period_start, period_end, line = lines[i]
        i += 1

        if _is_skip(line):
            continue

        lu = line.upper()

        # Section detection
        if "DIVIDENDS/INTEREST INCOME TRANSACTIONS" in lu:
            section = "div"; continue
        if "YOUR RETIREMENT ACCOUNT TRANSACTIONS" in lu:
            section = None; continue       # reset; sub-section follows
        if "SECURITY TRANSACTIONS" in lu and "REALIZED" not in lu:
            section = "purchases"; continue
        if lu == "PURCHASES":
            section = "purchases"; continue
        if lu == "SALES":
            section = "sales"; continue
        if "OTHER SECURITY TRANSACTIONS" in lu:
            section = "other"; continue
        if "REALIZED GAINS" in lu or "REALIZED LOSS" in lu:
            section = "skip"; continue

        if section == "skip":
            continue

        # Build company→ticker map from option continuation lines and holdings
        if section is None:
            tran_m = re.search(
                r"(.+?)\s+EXP\s+\d{2}-\d{2}-\d{2}\s+(?:OPEN|CLOSE)\s+TRAN\s+(\S+)", line
            )
            if tran_m:
                comp = tran_m.group(1).strip()
                tkr  = tran_m.group(2).strip()
                if comp and tkr and re.match(r"^[A-Z]{1,6}$", tkr):
                    company_ticker[comp] = tkr
            # Holdings section: "COMPANY NAME  TICKER  1,234.0000 ..."
            hold_m = re.match(
                r"^([A-Z][A-Z0-9 &.,/]+?)\s{2,}([A-Z]{1,6})\s+([\d,]+\.\d{4})", line
            )
            if hold_m:
                company_ticker[hold_m.group(1).strip()] = hold_m.group(2).strip()
            continue

        # Peek ahead for the next non-skip, non-date line (continuation)
        def peek_continuation():
            j = i
            while j < len(lines):
                _, _, nxt = lines[j]
                j += 1
                if _is_skip(nxt):
                    continue
                if DATE_START_RE.match(nxt):
                    break
                return nxt
            return ""

        # ── Dividend / Interest ───────────────────────────────────────────
        if section == "div":
            div_m = re.match(
                r"^(\d[\d\s\.]{0,4}/\d{2})\s+(.+?)\s+\*\s+(Dividend|Foreign Dividend)\s+([\d.,]+)$",
                line
            )
            int_m = re.match(
                r"^(\d[\d\s\.]{0,4}/\d{2})\s+(.+?)\s+(Interest)\s+([\d.]+)$",
                line
            )
            m_obj = div_m or int_m
            if m_obj:
                raw_date = m_obj.group(1)
                company  = m_obj.group(2).strip()
                trans    = m_obj.group(3)
                amount_s = m_obj.group(4)

                mmdd = normalize_mmdd(raw_date)
                if not mmdd:
                    continue
                tx_date = make_date(mmdd, period_start, period_end)
                if not tx_date:
                    continue
                date_str = tx_date.strftime("%m/%d/%Y")

                cont = peek_continuation()
                holding_qty = ""
                pay_date = date_str
                hm = re.match(r"HOLDING\s+([\d,.]+)\s+PAY DATE\s+(\d{2}/\d{2}/\d{4})", cont)
                if hm:
                    holding_qty = hm.group(1)
                    pay_date = hm.group(2)

                ticker = company_ticker.get(company, "")
                try:
                    amt_val = float(amount_s.replace(",", ""))
                except ValueError:
                    amt_val = 0.0

                if trans == "Interest":
                    desc = f"Interest {company} {amount_s} DIV/INT REINVEST PAY DATE {pay_date}"
                    symbol = "IIAXX"
                else:
                    if holding_qty:
                        desc = f"{trans} {company} HOLDING {holding_qty} PAY DATE {pay_date}"
                    else:
                        desc = f"{trans} {company} PAY DATE {pay_date}"
                    symbol = ticker

                transactions.append({
                    "Trade Date ": date_str,
                    "Settlement Date ": date_str,
                    "Account ": ACCOUNT,
                    "Description ": desc,
                    "Type ": "",
                    "Symbol/ CUSIP ": symbol,
                    "Quantity ": "",
                    "Price ": "",
                    "Amount ": f"${amt_val:,.2f}",
                    " ": "",
                    "_date": tx_date,
                })
            continue

        # ── Security transactions ─────────────────────────────────────────
        dm = DATE_START_RE.match(line)
        if not dm:
            # Continuation: update company map
            tran_m = re.search(
                r"(.+?)\s+EXP\s+\d{2}-\d{2}-\d{2}\s+(?:OPEN|CLOSE)\s+TRAN\s+(\S+)", line
            )
            if tran_m:
                comp = tran_m.group(1).strip()
                tkr  = tran_m.group(2).strip()
                if comp and tkr and re.match(r"^[A-Z]{1,6}$", tkr):
                    company_ticker[comp] = tkr
            continue

        raw_date = dm.group(1)
        rest = dm.group(2)
        mmdd = normalize_mmdd(raw_date)
        if not mmdd:
            continue
        tx_date = make_date(mmdd, period_start, period_end)
        if not tx_date:
            continue
        date_str = tx_date.strftime("%m/%d/%Y")

        cont = peek_continuation()

        # ── Option transaction ────────────────────────────────────────────
        opt_m = OPT_LINE1_RE.match(rest)
        if opt_m:
            opt_type  = opt_m.group(1)
            ticker    = opt_m.group(2)
            strike_f  = float(opt_m.group(3))
            trans     = opt_m.group(4)
            qty_s     = opt_m.group(5)
            credit_s  = opt_m.group(8) or ""
            # If only 2 amount groups, group(7) is credit for expired (no fees col)
            if not credit_s and opt_m.group(7):
                credit_s = opt_m.group(7)

            try:
                qty_int = int(float(qty_s))
            except ValueError:
                qty_int = 0

            exp_date   = ""
            unit_price = ""
            company    = ""
            month_abbr = ""
            strike_long = f"{strike_f:.5f}"

            # Parse continuation
            c2 = OPT_TRAN_LINE2_RE.match(cont) if cont else None
            if c2:
                company    = c2.group(1).strip()
                exp_date   = c2.group(2)
                month_abbr = c2.group(4)
                strike_long = f"{float(c2.group(5)):.5f}"
                unit_price  = c2.group(6)
                if company:
                    company_ticker[company] = ticker
            else:
                # Expired/Assigned style: optional "COMPANY " then "EXP MM-DD-YY NOCC"
                nocc_m = re.search(r"EXP\s+(\d{2}-\d{2}-\d{2})\s+NOCC", cont) if cont else None
                if nocc_m:
                    exp_date = nocc_m.group(1)
                    comp_part = cont[:nocc_m.start()].strip()
                    if comp_part:
                        company = comp_part
                        company_ticker[company] = ticker

            symbol = build_merrill_symbol(ticker, exp_date, opt_type, strike_f) if exp_date else ticker
            strike_label = build_strike_label(strike_f)

            if trans == "Option Expired":
                desc = f"Option Expired {opt_type} {ticker} {strike_label} {company} EXP {exp_date or '?'}"
            elif trans == "Option Assigned":
                desc = f"Option Assigned {opt_type} {ticker} {strike_label} {company} EXP {exp_date or '?'}"
            else:
                action = "Sale" if "Sale" in trans else "Purchase"
                month_part = f"{ticker} {month_abbr} " if month_abbr else f"{ticker} "
                desc = (
                    f"Option {action}  {opt_type} {ticker} {strike_label} {company} "
                    f"EXP {exp_date} {month_part}{strike_long} {OPT_BOILERPLATE}"
                )

            transactions.append({
                "Trade Date ": date_str,
                "Settlement Date ": date_str,
                "Account ": ACCOUNT,
                "Description ": desc,
                "Type ": "",
                "Symbol/ CUSIP ": symbol,
                "Quantity ": str(qty_int),
                "Price ": fmt_price(unit_price),
                "Amount ": fmt_amount(credit_s) if credit_s else "$0.00",
                " ": "",
                "_date": tx_date,
            })
            continue

        # ── Stock Purchase / Sale ─────────────────────────────────────────
        stk_m = re.match(
            r"^(.+?)\s+(Purchase|Sale)\s+([-\d,.]+)\s+"
            r"([\d,.()]+)(?:\s+([\d,.()]+))?\s+([\d,.()]+)$",
            rest
        )
        if stk_m:
            company  = stk_m.group(1).strip()
            action   = stk_m.group(2)
            qty_s    = stk_m.group(3).strip()
            credit_s = stk_m.group(6)

            ticker = company_ticker.get(company, "")

            unit_price = ""
            cup_m = re.match(r"CUS NO\s+\S+\s+UNIT PRICE\s+([\d.]+)", cont) if cont else None
            if cup_m:
                unit_price = cup_m.group(1)

            try:
                qty_int = int(float(qty_s.replace(",", "")))
            except ValueError:
                qty_int = 0

            desc = f"{action}  {company} {STK_BOILERPLATE}"
            transactions.append({
                "Trade Date ": date_str,
                "Settlement Date ": date_str,
                "Account ": ACCOUNT,
                "Description ": desc,
                "Type ": "",
                "Symbol/ CUSIP ": ticker,
                "Quantity ": str(qty_int),
                "Price ": fmt_price(unit_price),
                "Amount ": fmt_amount(credit_s),
                " ": "",
                "_date": tx_date,
            })

    return transactions


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    company_ticker = {}
    all_rows = []
    seen = set()

    for pdf_path in INPUT_PDFS:
        print(f"Parsing {pdf_path}...")
        lines = extract_lines(pdf_path)
        build_company_map(lines, company_ticker)
        txns = parse_lines(lines, company_ticker)
        print(f"  {len(txns)} transactions found")
        kept = 0
        for t in txns:
            if t["_date"] >= CSV_CUTOFF:
                continue
            key = (t["Trade Date "], t["Description "][:60], t["Amount "])
            if key in seen:
                continue
            seen.add(key)
            all_rows.append(t)
            kept += 1
        print(f"  {kept} before cutoff")

    all_rows.sort(key=lambda r: r["_date"])

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=MERRILL_HEADERS,
            extrasaction="ignore", quoting=csv.QUOTE_ALL
        )
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\nWrote {len(all_rows)} rows -> {OUTPUT}")

    from collections import Counter
    types = Counter()
    for r in all_rows:
        d = r["Description "]
        for prefix in ["Option Sale", "Option Purchase", "Option Expired",
                       "Option Assigned", "Purchase", "Sale", "Dividend",
                       "Foreign Dividend", "Interest"]:
            if d.startswith(prefix):
                types[prefix] += 1
                break
        else:
            types[d[:25]] += 1
    for k, v in sorted(types.items()):
        print(f"  {v:4d}  {k}")


if __name__ == "__main__":
    main()
