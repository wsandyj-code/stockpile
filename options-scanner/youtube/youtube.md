# YouTube Script: Options Scanner

## Title Ideas

### keep this one
- "Claude Code Finds Mis-Priced Options (Python)"

- "I Built a Free Web App That Finds Mispriced Options"
- "See Which Options Are Overpriced — In One Chart"
- "Click Scan → See the Best Options to Sell (Free Tool)"
- "The Options Screener Your Broker Doesn't Have"
- "Find Overpriced Options in 30 Seconds (Free, Any Ticker)"
- "I Built an Options Scanner with Claude Code — Here's How to
  Use It"

---

## Thumbnail Ideas

**Concept 1 — The Chart IS the Thumbnail** *(recommended)*
Background: the volatility-surface scatter from the web app —
dashed gray fitted curve, a cluster of red dots glowing well
above it, a couple of blue dots below. Big white text overlaid:
- Large: SELL THESE
- Arrow pointing at the reddest dot
- Small: Free Web App — Any Ticker

**Concept 2 — Split Screen**
Left: brokerage option chain — wall of undifferentiated numbers.
Right: the scanner chart — clean curve, one red dot clearly
glowing above it. Text:
- Which one? → THIS one.

**Concept 3 — The Hook**
Dark background, the chart on screen, big number floating next
to a glowing red dot:
- +7.2 pp
- "That option is overpriced. Here's how to spot them."

---

## HOOK (0:00–1:15)

*[SHOW BROKERAGE OPTION CHAIN BRIEFLY — wall of numbers]*

If you sell options — covered calls, cash-secured puts — you've
probably stared at an option chain like this and wondered
which contract is actually the best one to sell.

Same goes for option buyers.

*[BACK TO STREAMLIT — type **ticker**, click Scan]*

I built a free tool with Claude Code in a couple nights
that shows you the best ones, and visualizes it in a chart.

Let me demonstrate:
[Type a ticker. Click Scan. Wait...]

*[SHOW THE VOLATILITY SURFACE CHART — dots and dashed curve]*

This is every long-dated call on NVDA right now. Each dot is one
option. The dashed line is what the rest of the chain says each
strike's implied volatility *should* be — it's a fitted
volatility surface.

*[POINT TO RED DOTS ABOVE THE LINE]*

The red dots are sitting above the line. That means the market
is pricing those options richer than their neighbors. More
premium for the same amount of risk. Those are the calls you
want to sell.

*[POINT TO BLUE DOTS BELOW]*

Blue dots are the opposite — cheap for what they are. If you're
buying calls, you'd look at those.

*[HOVER OVER A RED DOT — tooltip shows strike, IV+pp, delta]*

Hover any dot and you get the strike, the expiration, how many
percentage points it sits above the surface, the delta, and the
open interest. Everything you need to decide whether to sell it.

I'm going to spend this video showing you how the chart works,
what to actually do with it, and how to run it on your own
positions in about five minutes of setup. There's a portfolio
scanner, a rolling-position mode, and more. Let's get into it.

---

## WHAT THE TOOL IS DOING (1:15–2:30)

*[SHOW THE CHART AGAIN — annotate as you talk]*

Quick framing on what you're looking at, because the chart is
doing most of the work.

A stock's option chain should form a smooth surface. Plot
implied volatility against strike, and it traces a shape — the
volatility smile. Higher IV for far out-of-the-money strikes,
smooth transitions between expirations. Market makers keep it
that way.

The dashed line in the chart is that smooth shape, fit to the
chain. When an option's actual IV sits noticeably above the
line, something made it more expensive than its neighbors — a
stale quote, a thin market, event risk that isn't evenly
distributed, or just an inefficiency. That's the option you
want to sell.

*[POINT TO COLOR LEGEND]*

The color tells you the gap, in percentage points, between the
actual IV and the fitted surface. We call it IV-plus-pp. Small
gaps — under three percentage points — mean the chain is
uniformly priced and the ranking is mostly noise. Five or more
points above the line is a genuine signal.

*[SCROLL DOWN TO THE TABLES]*

Below the chart there are two tables.

The first is the chain view. It shows every option in the
expiration you have selected in the chart dropdown, sorted by
strike — like reading a real option chain from your broker.
The rows are shaded: green means IV+pp is meaningfully above
the average for that expiration, gray means it's in the noise
floor, red means it's below average.

*[POINT TO ROW SHADING IN CHAIN VIEW]*

This is where you actually pick your strike. The whole
expiration at a glance, shading doing the filtering for you —
you can see in seconds which strikes have genuinely rich
premium and which ones are unremarkable.

*[POINT TO RED BID/ASK CELLS]*

Two other signals in the table. Red Bid and Ask cells mean
the spread is wider than typical for this chain — the gap
between what buyers will pay and sellers will accept. A wide
spread means your real execution price may land meaningfully
worse than the mid suggests. And a red OI cell means open
interest is low — barely past the filter threshold — which
makes it harder to fill at a good price. Hover the question
mark on any column header and it explains exactly what
triggers the color.

*[POINT TO SECOND TABLE — "TOP CANDIDATES — ALL CHAINS"]*

Below that is the top candidates table — the highest-ranked
options by IV+pp pulled from every expiration. The chain view
says "show me everything for January, sorted by strike." This
one says "show me the best ten, regardless of expiration."

*[POINT TO DELTA COLUMN]*

Delta is your approximate probability of being assigned at
expiration. A delta of 0.30 means roughly a thirty percent
chance the stock closes above your strike. Lower delta means
you keep the stock more often — you give up some premium to
get that safety margin.

*[POINT TO ANN% COLUMN]*

Ann% is the annualized yield on the premium you'd collect —
for calls, relative to the stock's current price. For puts,
relative to the strike, which is the capital you'd be putting
at risk. This lets you compare options across different
expirations on the same footing.

*[POINT TO LT CLOSE METRIC AT TOP]*

And up here — LT Close. If you open a short position today and
hold it for three hundred and sixty-six days before closing,
the premium is taxed at the long-term capital gains rate. This
tells you the earliest you could close for that treatment.

---

## A QUICK ASIDE: PERCENTAGE POINTS VS. PERCENT (2:30–3:15)

*[OPTIONAL: SIMPLE TEXT SLIDE WITH THE EXAMPLE NUMBERS]*

This is wonky but an important concept to understand when using
this tool. The IV+pp column you keep seeing — pp stands for
**percentage points**, and that is deliberately different from
percent. They are not the same thing.

Here is why it matters. Implied volatility itself is already a
percentage — forty-five percent, fifty percent, and so on. So
when you talk about the gap between two of those numbers, you
have to be careful. Going from forty-five percent to
forty-eight-and-a-half percent is plus three-and-a-half
**percentage points**. Calling that plus three-and-a-half
**percent** would be wrong — the relative percent change there
is more like plus seven-point-eight percent.

*[SHOW THE NUMBERS ON SCREEN: 45% → 48.5% = +3.5 pp ≠ +7.8%]*

Two practical takeaways from that.

**One.** When you read a plus-five-pp signal in the table or
see a red dot floating five units above the fitted curve,
that's an absolute IV gap. Same unit on every strike and every
expiration, which is what makes the ranking comparable across
the whole chain.

**Two.** Do not confuse IV+pp with a return. A plus-five-pp
option is not paying you five percent. The Ann% column on the
table is your actual annualized yield on the premium — that's
where you check the real return on capital.

So: pp is the language of volatility differences. Once you've
got that distinction, the rest of the tool falls into place.

---

## SELLING COVERED CALLS — THE MAIN USE CASE (3:15–5:15)

*[SHOW STREAMLIT — Single Ticker tab, NVDA loaded]*

Let's say you own NVDA shares and you want to sell a covered
call. You want LEAPS — options a year or more out — so the
premium qualifies for long-term capital gains when you close.
You also want the call to be genuinely overpriced, not just any
call.

*[POINT TO THE CHART — RED DOTS]*

The chart shows you the candidates at a glance. Anything red
above the curve is a sell candidate. The redder the dot, the
richer the premium relative to its neighbors.

*[POINT TO DELTA SLIDER]*

Up top there's a delta range slider. Default is 0.10 to 0.75 —
a wide range that covers everything from conservative out-of-the-
money strikes to fairly deep in-the-money ones. A lot of covered
call sellers narrow this to 0.25 to 0.40 — enough premium to be
worthwhile, enough strike distance to not get called away every
time the stock moves.

*[DRAG SLIDER TO 0.25–0.40, CLICK SCAN]*

*[SHOW UPDATED CHART AND TABLE]*

Now you're looking at a tighter slice — real candidates for a
covered call that won't keep you up at night.

*[POINT TO EXPIRATION SELECTBOX ABOVE THE CHART]*

Each expiration has its own volatility smile, so the chart shows
one at a time. Use this dropdown to switch between them — you'll
see the surface shape change, and which strikes are rich shifts
with it.

*[SCROLL DOWN — CHAIN VIEW TABLE UPDATES TO MATCH]*

Switching the dropdown also updates the chain view table below.
It always shows the full option chain for whichever expiration
you're looking at, sorted by strike. So the workflow is: pick
an expiration in the dropdown, read the chain view for that
expiration, then check the top candidates below for the best
across all expirations.

*[POINT TO CHAIN VIEW TITLE — EARNINGS DATE]*

The chain view title shows you the expiration date and, if any
earnings event falls before it, the date of the next one and
how many days away it is — something like "Jan 15 '27 — next
earnings Oct 22 (167d)." IV spikes around earnings as the
market prices in uncertainty; a lot of that elevated premium
may evaporate the morning after the announcement whether or
not the stock moves much. Worth factoring in before you
commit.

*[POINT TO EXPIRATION COLUMN IN TOP CANDIDATES TABLE]*

In the top candidates table, the Expiration column uses a
shorthand: `2E` means two earnings events fall before that
expiration.

*[CLICK "DOWNLOAD HTML REPORT" BUTTON]*

If you want to save a report — to share with someone, or come
back to it later — there's a download button. The HTML version
has the same data, sortable by any column. Click to re-rank.

*[OPEN THE DOWNLOADED HTML REPORT]*

That's all the same data, in a single file you can email
yourself or check tomorrow.

**One honest caveat about the data source.** Everything here
comes from Yahoo Finance, which is free and requires no account.
That's a real advantage for getting started. But Yahoo Finance
has limitations worth knowing.

The implied volatility numbers it returns are sometimes stale
— especially on thinly traded strikes where the last trade was
hours or days ago. The Greeks aren't provided at all; delta
here is calculated from Black-Scholes using Yahoo's IV, which
means if the IV is stale, the delta is too. And for LEAPS
specifically, wide bid-ask spreads and low volume mean some of
the IV readings are noise rather than signal.

None of this breaks the tool — it still surfaces real
patterns — but you should treat the output as a starting
point for further research, not a trading signal on its own.
Always verify the bid-ask spread before acting on anything
the scanner surfaces. Stale IV also tends to show up as a
single dot far from its neighbors with no obvious reason — if
something looks too good to be true on the chart, it usually is.

A natural future enhancement would be plugging in a better
data source. Schwab has a developer API — free for account
holders — that returns full option chains with real-time
quotes and proper Greeks: delta, gamma, theta, vega, all
of it. That would make this significantly more accurate,
especially for the IV surface fitting. It's on the roadmap.

---

## MORE FEATURES (5:15–7:15)

*[SHOW STREAMLIT — Single Ticker tab]*

That's the core use case, but there's more here, and it's all
on the same form.

**Selling puts.** Flip the Option Type radio from Calls to Puts
and click Scan. Same chart, same ranking, but now you're looking
at the put side of the chain. For puts, Ann% is calculated
relative to the strike price, not the stock price, because
that's the capital you'd be committing if assigned.

*[CLICK "PUTS", SCAN, SHOW CHART]*

**Rolling an existing position.** You have a call expiring in a
few months and want to roll it out. Check the "Rolling an
existing position?" box.

*[CHECK THE ROLL BOX — FIELDS APPEAR]*

Fields appear for your current strike and expiration. Fill them
in, scan, and a Net Credit column appears in the table — the
net credit you'd receive after paying to close the old position.
Positive means you'd collect cash on the roll. Negative is a
debit.

*[FILL IN ROLL FIELDS, SCAN, POINT TO NetCr COLUMN]*

The candidates are still ranked by IV excess, so the top row is
the new contract where you'd collect the most excess premium —
not just the most raw premium.

**Short-dated options.** The default is LEAPS — one year or
more. But you can change the Min and Max DTE inputs to look at
shorter expirations. Useful if you're scanning for near-term
premium or want to see the full picture across timeframes.

*[CHANGE MIN DTE TO 30, MAX DTE TO 90, SCAN]*

**Buy mode.** Flip the Action radio from Sell to Buy. Same
surface fit, but now the ranking inverts — you're looking for
the most underpriced options, the dots farthest *below* the
curve. The chart's blue dots are now the candidates.

*[CLICK BUY MODE, SHOW CHART WITH BLUE DOTS HIGHLIGHTED]*

---

## PORTFOLIO SCAN (7:15–8:30)

*[SWITCH TO PORTFOLIO TAB]*

Here's my favorite feature if you have more than one or two
positions. Drop in your brokerage CSV — Schwab, Robinhood,
Fidelity, or Merrill — and the tool scans every position you own.

*[DRAG-AND-DROP A REDACTED CSV INTO THE UPLOADER]*

Pick the brokerage, click Scan Portfolio. There's a progress
bar while it fetches each ticker.

*[SHOW PROGRESS BAR FILLING IN]*

It figures out every ticker where you currently hold shares,
detects which ones already have a covered call open against
them, and scans each position automatically.

*[SHOW EXPANDABLE SECTIONS — ONE PER TICKER]*

Each position is its own expandable section. For uncovered
positions — shares with no call against them — it shows the
best calls to sell. For covered positions, it shows the roll
candidates with a Net Credit column — what you'd collect net
if you closed your existing call and opened each of these
instead.

*[CLICK "DOWNLOAD PORTFOLIO REPORT"]*

One download button gives you an HTML report covering your
whole account — summary table up top, every ticker's
candidates below.

Instead of scanning ticker by ticker, you upload one CSV and
get a full report.

---

## A QUICK NOTE ON THE TERMINAL (8:30–9:00)

*[BRIEFLY SHOW TERMINAL — `uv run options-scanner/run_scanner.py NVDA --calls`]*

If you prefer the command line — or you want to script this
into a cron job, pipe the output, automate around it — there's
a CLI version that does everything the web UI does. Same data,
same ranking, just text output instead of a chart.

```
uv run options-scanner/run_scanner.py NVDA --calls
```

The README has the full flag reference. If you don't want to
touch the terminal, you don't have to — the web UI is the
recommended way to use this.

---

## HOW I BUILT THIS — AND HOW LONG IT TOOK (9:00–10:30)

*[SHOW CLAUDE CODE TERMINAL OR SIDE-BY-SIDE: CHAT ON LEFT,
CODE ON RIGHT]*

Let me show you what it actually took to build this, because
I think it might surprise you.

*[SHOW CONVERSATION SUMMARY OR SCROLL THROUGH PROMPT LIST]*

This entire tool — the scanner, the IV surface model, the roll
mode, the portfolio scan, the HTML reports, the Streamlit web
UI, and the YouTube script you're watching — was built in about
twenty-two back-and-forth messages with Claude Code. Here's a
rough summary of what those conversations looked like:

- "Thinking of building a tool to look at an option chain and
  help me pick the best option to sell."
- "I want to target LEAPS for long-term capital gains on the
  premium. Note earnings dates."
- "Yeah let's build it."
- "How do I run it?"
- "I like both ideas — add earnings fallback and delta range
  filters."
- "Go ahead and implement HTML output, buy mode, and
  short-dated options."
- "Build the portfolio scanner and a Streamlit UI. Don't stop
  to ask me anything — just do it."

That's the gist. No architecture meetings, no tickets, no
planning documents. I described what I wanted, Claude built it,
I tested it, I asked for changes.

*[SHOW GIT LOG OR FILE DIFF]*

The result: just under nineteen hundred lines of Python across
ten source files. Chain fetching, IV surface fitting, earnings
detection, terminal output, HTML report generation, portfolio
parsing, and the Streamlit app.

*[SHOW COMMIT HISTORY IF AVAILABLE, OR FILE TREE]*

All of it written part-time in the evenings over two nights.
Not two weeks. Two nights.

I'm going to make a claim here that I can't prove precisely,
but I believe is in the right ballpark: this took roughly
one hundredth of the effort it would have taken me before
Claude. BC — Before Claude. Not one tenth. One hundredth.

Think about what "before Claude" looks like for a project
like this. You'd spend an evening just researching the right
library for IV surface fitting, reading documentation, looking
at Stack Overflow answers that are three years old and half
wrong. Another evening getting the option chain data into a
usable shape. A weekend on the HTML report. Another session
on the Streamlit UI. You'd hit walls, debug things that
shouldn't be broken, context-switch back to the docs, lose
the thread.

I didn't do any of that. I described what I wanted. Claude
knew what libraries to use, knew the right mathematical
approach, wrote the boilerplate, and kept all the context
in its head across sessions. My effort was deciding what I
wanted — not figuring out how to build it.

That's the shift. The bottleneck used to be implementation.
Now it's just knowing what to ask for.

*[SHOW A SPECIFIC INTERESTING PROMPT-AND-RESPONSE EXCHANGE —
e.g. the IV surface fitting suggestion]*

Here's the one that stuck with me. I described the problem —
I want to find options that are priced differently from what
you'd theoretically expect from the rest of the chain. I didn't
know how to formalize that. Claude suggested fitting a
two-dimensional polynomial in log-moneyness and the square root
of time to expiration. That's a simplified version of a model
called SVI that professional volatility desks actually use. I
wouldn't have known to look for that. Claude did.

That's the real value proposition here — not just that Claude
writes the code faster than I can, but that it brings knowledge
I don't have into the conversation.

*[SHOW CLAUDE CODE TERMINAL — BRIEF DEMO OF ASKING FOR A
SMALL CHANGE]*

And extending it works exactly the same way. I've done it
several times since the initial build — adding a full chain
view table sorted by strike with green-gray-red IV+pp row
shading, flagging wide bid-ask spreads and low open interest
with red cell highlights, putting the next earnings date right
in the table title with a days-to-go count. Each of those was
a short conversation. Describe what you want, Claude builds it.
No documentation to read, no library to learn.

The whole thing is open source. Every line is on GitHub. You
can read it, fork it, change it, or just use it as-is.

---

## WHAT YOU NEED — SETUP (10:30–12:00)

*[SHOW GITHUB REPO]*

Let's walk through everything you'd need to do to run this
yourself.

**Step 1 — Get the code.**

Go to the GitHub repository linked in the description. Either
download the zip or clone it:

```
git clone https://github.com/medloh/stockpile.git
cd stockpile
```

You'll need Git installed — git-scm.com has installers for
Windows and Mac.

*[SHOW PYTHON.ORG]*

**Step 2 — Install Python.**

You'll need Python 3.12 or newer. Go to python.org, download
the installer for your platform. On Windows, check the box that
says "Add Python to PATH" during installation — that's the one
people miss.

*[SHOW TERMINAL]*

**Step 3 — Install uv.**

This project uses uv, which is a fast Python package manager.
One command installs it:

On Mac or Linux:
```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

On Windows, open PowerShell and run:
```
powershell -ExecutionPolicy Bypass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

If you really don't want to install uv, you can use plain pip
instead — but uv is much faster and handles the workspace
structure this project uses.

*[SHOW TERMINAL — RUN uv sync]*

**Step 4 — Install dependencies.**

From the stockpile folder:

```
uv sync
```

This installs everything — yfinance, numpy, streamlit, tabulate,
all of it. Takes about thirty seconds the first time.

*[SHOW TERMINAL — RUN THE WEB UI COMMAND]*

**Step 5 — Start the web app.**

From the stockpile folder, one command:

```
uv run streamlit run options-scanner/run_app.py
```

That opens the app in your browser at localhost:8501. From here
on, you don't need the terminal — type a ticker, hit Scan.

*[SHOW BROWSER OPENING TO STREAMLIT]*

If you'd rather use the command-line scanner directly:

```
uv run options-scanner/run_scanner.py NVDA --calls
```

Or scan your portfolio from the CLI — export your transaction
history from your brokerage, drop it in the input folder:

```
uv run options-scanner/run_portfolio.py \
    --csv input/your_export.csv --html
```

The README in the options-scanner folder has the full flag
reference. Everything in this video is documented there.

**One important thing.** This tool reads public option chain
data from Yahoo Finance — no account needed, no API key, free.
Your brokerage CSV, if you use the portfolio scanner, stays on
your machine. It never leaves. No Anthropic server sees it.

---

## OUTRO (12:00–12:30)

*[ON CAMERA OR BROWSER]*

That's the options scanner. A free web app that finds LEAPS
calls and puts ranked by how overpriced the premium is, shown
on a chart so you can see at a glance which strikes are rich.
Roll an existing position for maximum net credit. Scan your
whole portfolio at once from a brokerage export. CLI also
available if you want it.

Link to the repo is in the description. If you hit a snag
setting it up, drop a comment — I check them.

The biggest thing on the roadmap is replacing the Yahoo Finance
data source with the Schwab developer API — real-time quotes,
proper Greeks, no stale IV. If that's something you'd use,
let me know in the comments, it'll move up the priority list.

If this was useful, like and subscribe. The previous episode
in this series — building position charts that show your real
adjusted cost basis — should be appearing somewhere around
here.

---

## DESCRIPTION

Free Options Scanner Web App — Find Overpriced Calls and Puts
to Sell

I built an open-source option chain scanner with Claude Code.
It's a free web app that ranks every LEAPS call or put by how
overpriced it is relative to a fitted volatility surface, and
shows the result on a chart so you can see the rich strikes at
a glance. Useful for selling covered calls, cash-secured puts,
and rolling existing positions.

**What it does:**
- Browser-based UI — no terminal required to use it
- Volatility-surface chart: every option as a dot, fitted curve
  overlaid, red dots = overpriced, blue dots = underpriced
- Fetches the full option chain from Yahoo Finance (free,
  no API key)
- Fits a 2-D volatility surface to find options priced above
  where they should be
- Ranks by IV excess — the gap between actual and expected
  implied volatility
- Per-expiration chain view sorted by strike: row shading
  shows which strikes are rich, average, or weak at a glance
- Flags wide bid-ask spreads and low open interest with red
  cell highlights so you spot execution risk before acting
- Earnings dates shown in chain title with days-to-go count
- Filters by delta (default 0.10–0.75), open interest, DTE
- Roll mode: shows net credit for rolling an existing position
- Portfolio scan: drag-and-drop your brokerage CSV and scan
  every open position automatically
- CLI also available for scripting and automation

**What you need:**
- Python 3.12+
- uv (free, one-command install)
- The repo (free on GitHub, link below)
- Optional: a brokerage CSV export for the portfolio scan

**Steps covered:**
0:00 Hook — scanning NVDA in the web app
1:15 How the volatility surface chart works
2:30 Why pp, not % — a wonky but important detail
3:15 Selling covered calls — the main use case
5:15 More features: puts, rolling, buy mode, short-dated
7:15 Portfolio scan — drag in your brokerage CSV
8:30 CLI mode for scripting and power users
9:00 How I built it — 22 prompts, 2 evenings, ~1900 lines
10:30 Setup — Python, uv, cloning the repo, running it

**Links:**
GitHub repo: https://github.com/medloh/stockpile
Claude Code: https://claude.ai/code
Previous episode (cost basis charts): [link]
Previous episode (Google Sheets tracker): [link]

Your brokerage data stays on your machine. This tool only
calls Yahoo Finance's public API — no accounts, no keys, no
data leaves your computer.

If you hit a snag, drop a comment — I check them.

#options #coveredcalls #python #claudecode #optionstrading
#thetagang #leaps #stockmarket #investing #cashsecuredputs

---

## PRODUCTION NOTES

### Before Recording
- **Commit the options-scanner work to git first.** The "how
  I built this" section references the git log and file count —
  you need those to be real and visible on screen. Run:
  `git add options-scanner && git commit -m "Add options-scanner tool"`
  Then use `git log --oneline` and `git diff HEAD~1 --stat` to
  show the scope of what was added in one commit.
- **Have the Streamlit app running before you hit record.** The
  hook depends on it being up the moment you switch to the
  browser. Startup takes 3–4 seconds — don't make viewers wait.
- **Pick a ticker with a visible spread on the chart.** The
  whole hook fails if every dot is sitting on the curve. Before
  recording, scan NVDA, AAPL, TSLA, and 2–3 others — pick the
  one with the most clearly red/blue dots away from the line.
  A volatile day or a day before earnings helps.
- If no ticker has a strong spread that day, acknowledge it on
  camera — "today's chains are uniformly priced, which itself
  is useful information; here's what it looks like when there
  IS a signal" — then show a screenshot from a previous day.
- For the chart hook, zoom the browser to ~125% so the dots
  read clearly on a phone screen.
- Pre-generate the HTML report so you can cut straight to it
  without waiting for the download.
- Have a real brokerage CSV ready for the portfolio scan demo
  — redact or blur any sensitive position sizes if needed.
- For the "how I built this" section, decide whether to show
  the actual Claude Code conversation transcript scrolling, or
  just read the prompt summary bullets on screen. The transcript
  is more compelling but harder to read on camera.

### Sections that need strong pacing
- Hook: keep it under 75 seconds — the chart speaks for itself,
  don't over-narrate. The reveal moment is the chart appearing
  with red dots above the curve; let it land.
- Setup section: this will be the hardest for non-technical
  viewers — go slowly, show every keystroke, mention that
  the README has written instructions they can follow at
  their own pace. The payoff is the web app opening — make
  sure that moment is on screen.

### Before Publishing
- Add chapters (timestamps in description)
- Thumbnail set before publishing
- First two lines of description are visible before "show
  more" — make sure they're compelling
- Add cards at 40% and 70% of runtime pointing to the
  Google Sheets and cost basis chart episodes

### After Publishing
- Share to r/thetagang, r/options, r/learnpython,
  r/investing — lead with the scanner output, not the setup
- Pin a comment with the repo link and a prompt:
  "What other signals would make this more useful?"
- Reply to every comment in the first 48 hours
- Add this video to the exit screens of the previous two
  episodes

### Exit Screens
Add to exit screen of:
- Cost basis charts episode
- Google Sheets tracker episode
