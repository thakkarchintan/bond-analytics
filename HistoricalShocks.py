"""
Historical Global Shocks — yield and rates dynamics during 12 key market events.
"""
from __future__ import annotations

import pathlib

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data import load_data
from global_macro_data import (
    BREAKEVEN_CACHE, CROSS_ASSET_CACHE, SPREADS_LONG_CACHE,
    load_breakeven, load_cross_asset, load_spreads_long, refresh_spreads_long,
)

_HERE = pathlib.Path(__file__).parent
_CBPOL_CACHE = _HERE / "dbn_cbpol_cache.parquet"

# ── Palette ───────────────────────────────────────────────────────────────────
_T1  = "#f1f5f9"
_T2  = "#94a3b8"
_GRD = "#1e293b"
_BG  = "rgba(0,0,0,0)"

_COLS = [
    "#60a5fa", "#f59e0b", "#34d399", "#f87171",
    "#a78bfa", "#fb923c", "#38bdf8", "#6ee7b7",
]

_DRIVER_STYLE: dict[str, tuple[str, str]] = {
    "Growth Shock":                     ("#1e3a5f", "#60a5fa"),
    "Inflation Shock":                  ("#3b1f00", "#fb923c"),
    "Central Bank Communication":       ("#2d1f4e", "#a78bfa"),
    "Sovereign Credit Risk":            ("#3b0f0f", "#f87171"),
    "Fiscal Policy & Market Structure": ("#2d2008", "#fbbf24"),
}

# ── Event catalogue ───────────────────────────────────────────────────────────

_EVENTS: list[dict] = [
    {
        "id":     "dotcom",
        "label":  "1 · Dot-com Bust (2000–02)",
        "period": "March 2000 – October 2002",
        "driver": "Growth Shock",
        "lesson": "Growth fears → bond prices rise → yields fall. The yield curve inverted in 2000, signalling the recession, then steepened aggressively as the Fed cut 550 bp.",
        "window": ("1998-06-01", "2003-06-01"),
        "shade":  ("2000-03-10", "2002-10-09"),
        "keys":   [("2000-03-10", "NASDAQ peak"), ("2001-01-03", "Fed first cut")],
        "writeup": (
            "The S&P 500 peaked on March 24, 2000 and the NASDAQ on March 10 at 5,048 — a level it would "
            "not revisit for 15 years. The bubble was inflated by easy 1990s monetary policy, irrational "
            "valuations in technology, and a wave of speculative IPOs. When it burst, equity markets erased "
            "roughly $8 trillion in market capitalisation.\n\n"
            "The bond market moved exactly as theory predicts. Growth fears and equity wealth destruction drove "
            "a massive rally in safe-haven Treasuries. The Federal Reserve cut rates eleven times — from 6.5 % "
            "in January 2001 to 1.0 % by June 2003 — the most aggressive easing cycle in decades. US 10Y "
            "Treasury yields fell from around 6.5 % to 3.1 %. The yield curve briefly inverted in late 2000 "
            "(2Y yields above 10Y), accurately signalling the impending recession (March–November 2001). As "
            "the Fed front-loaded cuts, the 2Y10Y curve steepened sharply — short rates fall faster than long "
            "rates when the central bank is the buyer. The equity crash pulled money into bonds, not out of them."
        ),
    },
    {
        "id":     "gfc",
        "label":  "2 · Global Financial Crisis (2008–09)",
        "period": "December 2007 – June 2009",
        "driver": "Growth Shock",
        "lesson": "Flight-to-quality dominates everything. Credit spreads explode even while government yields collapse. The two move in opposite directions during systemic crises.",
        "window": ("2006-01-01", "2010-12-01"),
        "shade":  ("2007-12-01", "2009-06-30"),
        "keys":   [("2008-09-15", "Lehman Brothers"), ("2008-12-16", "Fed → 0 %")],
        "writeup": (
            "The Global Financial Crisis was triggered by the collapse of the US subprime mortgage market, "
            "which had been inflated by loose lending standards, complex securitisation (CDOs, MBS) and "
            "excessive leverage. When Lehman Brothers filed Chapter 11 on September 15, 2008, it froze "
            "global interbank lending markets overnight.\n\n"
            "What distinguishes the GFC from a normal recession is the simultaneous explosion of credit "
            "spreads and collapse of safe-haven yields. High-yield OAS spreads blew out to over 1,900 bp "
            "at the peak (December 2008) — nearly 19 percentage points above risk-free rates. Meanwhile, "
            "US 10Y Treasury yields fell from ~4.5 % to ~2 %. The two moved in opposite directions, "
            "illustrating the classic flight-to-quality: investors sold risky assets and bought Treasuries "
            "regardless of yield level.\n\n"
            "The Fed cut rates from 5.25 % to 0–0.25 % in 15 months and launched QE1 ($600 bn in November "
            "2008). The ECB, Bank of England and Bank of Japan all followed with aggressive easing. VIX "
            "hit an all-time record of 80.86 on October 24, 2008 — the highest since the inception of the index."
        ),
    },
    {
        "id":     "eurozone",
        "label":  "3 · European Sovereign Debt Crisis (2010–12)",
        "period": "April 2010 – July 2012",
        "driver": "Sovereign Credit Risk",
        "lesson": "Government bonds are not equally risk-free. Spreads of 500+ bp between eurozone sovereigns proved that credit risk is real even within a shared currency.",
        "window": ("2009-01-01", "2013-06-01"),
        "shade":  ("2010-04-27", "2012-07-25"),
        "keys":   [("2010-04-27", "Greece junk"), ("2011-11-09", "Italy 10Y > 7 %")],
        "writeup": (
            "The European Sovereign Debt Crisis exposed the fundamental flaw in the eurozone's construction: "
            "member states share a currency but retain independent fiscal policy, with no common fiscal backstop "
            "or lender of last resort for sovereigns. When Greece's fiscal deficit was revised from 3.7 % to "
            "12.7 % of GDP in October 2009, markets realised they had mispriced eurozone sovereign risk for "
            "a decade.\n\n"
            "Contagion spread rapidly to Ireland, Portugal, Spain and Italy — the 'PIIGS' acronym entered the "
            "financial lexicon. Italy, with €2 trillion of debt, was the critical domino: its 10Y yield "
            "pierced 7 % on November 9, 2011 — widely regarded as the unsustainable threshold that would "
            "force a bailout. BTP-Bund spreads peaked at ~550 bp.\n\n"
            "German Bund yields fell sharply as the safe-haven within Europe, illustrating that in a currency "
            "union credit risk drives spreads, not absolute yields. France was not immune: OAT-Bund spreads "
            "also widened meaningfully, showing contagion beyond the obvious periphery. The crisis would only "
            "be resolved by Draghi's July 2012 intervention (see the next event)."
        ),
    },
    {
        "id":     "draghi",
        "label":  "4 · ECB 'Whatever It Takes' (2012)",
        "period": "July 26, 2012",
        "driver": "Central Bank Communication",
        "lesson": "Central bank credibility alone can move yields more than actual bond purchases. The OMT programme has never been formally activated — yet it resolved the crisis.",
        "window": ("2012-01-01", "2013-06-01"),
        "shade":  None,
        "keys":   [("2012-07-26", "Draghi: 'whatever it takes'")],
        "writeup": (
            "On July 26, 2012, ECB President Mario Draghi was speaking at the Global Investment Conference "
            "in London when he delivered the most consequential sentence in modern central banking: 'Within "
            "our mandate, the ECB is ready to do whatever it takes to preserve the euro. And believe me, "
            "it will be enough.'\n\n"
            "At that moment Italian 10Y yields were above 6 %, Spanish yields above 7 %, and bond markets "
            "were pricing a non-trivial probability of eurozone break-up. The OMT (Outright Monetary "
            "Transactions) programme — under which the ECB would buy potentially unlimited quantities of "
            "distressed sovereign bonds — had not yet purchased a single bond when peripheral yields collapsed.\n\n"
            "The Italian BTP-Bund 10Y spread fell from ~530 bp at end-July to ~230 bp by year-end. The "
            "entire move happened on the strength of a credible commitment. This episode proved that central "
            "bank commitment functions as an options contract: the 'strike price' at which the central bank "
            "intervenes determines market pricing, not the actual quantity of purchases. The OMT programme "
            "has never formally purchased a single bond."
        ),
    },
    {
        "id":     "taper",
        "label":  "5 · US Taper Tantrum (2013)",
        "period": "May – December 2013",
        "driver": "Central Bank Communication",
        "lesson": "Expectations move markets before policy changes. A hint of QE tapering — with no actual rate change — drove US 10Y yields up ~140 bp in seven months.",
        "window": ("2012-06-01", "2014-06-01"),
        "shade":  ("2013-05-22", "2013-12-31"),
        "keys":   [("2013-05-22", "Bernanke hints taper"), ("2013-12-18", "Taper begins")],
        "writeup": (
            "By early 2013 the Fed had been buying $85 billion of Treasuries and MBS per month under QE3. "
            "Markets had priced perpetual accommodation. When Chairman Bernanke testified before Congress on "
            "May 22, 2013 and suggested the Fed might 'step down' its bond purchases 'in the next few "
            "meetings,' bond markets reacted as if a rate hike had been announced.\n\n"
            "The US 10Y rose from approximately 1.63 % on May 1 to 3.03 % by December 31 — a 140 bp rise "
            "in seven months. The 30Y rose similarly. Crucially, the Federal Funds Rate did not move at all: "
            "it stayed at 0–0.25 % throughout. This illustrates that long-term yields are driven by "
            "expectations of the future path of rates and inflation — not current policy.\n\n"
            "The curve steepened significantly: 2Y yields are anchored by expected near-term policy (which "
            "the Fed said would remain near zero), while 10Y and 30Y embed inflation and term premium "
            "expectations that repriced sharply. Emerging markets suffered most — capital flooded back to "
            "the US as the yield gap narrowed, causing EM currencies and bonds to sell off sharply."
        ),
    },
    {
        "id":     "oil_deflation",
        "label":  "6 · Oil Crash & Deflation Scare (2014–16)",
        "period": "June 2014 – January 2016",
        "driver": "Growth Shock",
        "lesson": "Falling inflation expectations can push nominal yields to historic lows. German 10Y yields went negative — disproving any notion of a natural 'zero lower bound'.",
        "window": ("2013-06-01", "2017-01-01"),
        "shade":  ("2014-06-01", "2016-01-31"),
        "keys":   [("2014-11-28", "OPEC keeps output"), ("2016-07-06", "German 10Y < 0")],
        "writeup": (
            "OPEC's November 27, 2014 decision not to cut production — in the face of surging US shale "
            "output — triggered a collapse in oil prices. WTI crude fell from $107/bbl in June 2014 to "
            "below $26/bbl by February 2016. The crash had broad deflationary implications: energy feeds "
            "directly into CPI through fuel prices, utility bills and transportation costs.\n\n"
            "US TIPS breakeven inflation rates fell from around 2 % to below 1.3 % as oil collapsed. In "
            "Europe, deflation became a genuine risk: eurozone CPI briefly turned negative in early 2015. "
            "The ECB responded by cutting the deposit rate to -0.40 % and launching the PSPP (Public Sector "
            "Purchase Programme) — its first QE programme.\n\n"
            "German 10Y Bund yields fell from ~1.8 % in early 2014 to a historic low of -0.19 % on July 6, "
            "2016. For the first time in centuries of German state finances, the government was paid to "
            "borrow at 10-year maturities. This destroyed the notion that there is a natural 'zero lower "
            "bound' for nominal yields — when expected inflation is sufficiently negative, a negative nominal "
            "yield can still represent a positive real return."
        ),
    },
    {
        "id":     "brexit",
        "label":  "7 · Brexit Referendum (2016)",
        "period": "June 23, 2016",
        "driver": "Fiscal Policy & Market Structure",
        "lesson": "Political uncertainty triggers immediate risk-off demand for government bonds, even the bonds of the country facing the political risk. Currency absorbs the shock first.",
        "window": ("2016-01-01", "2017-03-01"),
        "shade":  None,
        "keys":   [("2016-06-23", "Vote"), ("2016-06-24", "Result: Leave")],
        "writeup": (
            "The UK's June 23, 2016 referendum produced a 51.9 % majority for 'Leave' — defying polls that "
            "had consistently shown 'Remain' ahead. The result was announced at 4:40 am on June 24. Prime "
            "Minister David Cameron resigned the same morning. Sterling fell nearly 10 % overnight — the "
            "largest single-day move for a major currency since the collapse of Bretton Woods.\n\n"
            "Bond markets reacted immediately in risk-off mode: UK gilt yields fell as investors bought "
            "safe-haven assets. Paradoxically, investors bought the gilts of the very country facing the "
            "political risk — illustrating that the immediate reaction to geopolitical shocks is reflexive "
            "risk-off before more nuanced repricing occurs. US Treasuries also rallied, showing the risk-off "
            "was global.\n\n"
            "The UK-Germany spread initially compressed (both gilts and Bunds rallied), then widened as "
            "UK-specific risk was repriced. The FTSE 100, which earns ~75 % of revenues internationally, "
            "actually rose for the year — boosted by the weak pound making overseas earnings worth more in "
            "sterling terms. The Bank of England cut rates to 0.25 % in August 2016 and expanded QE."
        ),
    },
    {
        "id":     "covid",
        "label":  "8 · COVID-19 Pandemic (2020)",
        "period": "February – June 2020",
        "driver": "Growth Shock",
        "lesson": "Extreme uncertainty + aggressive central bank intervention = record-low yields. The US 10Y fell below 0.5 %. Central bank responses have grown faster and larger with each crisis.",
        "window": ("2019-10-01", "2021-09-01"),
        "shade":  ("2020-02-01", "2021-04-30"),
        "keys":   [("2020-03-11", "WHO pandemic"), ("2020-03-15", "Fed → 0 % emergency")],
        "writeup": (
            "COVID-19 was the fastest economic shock in recorded history. From the WHO's pandemic declaration "
            "on March 11, 2020 to the trough of US equity markets (March 23), just 12 days elapsed. The "
            "lockdowns that followed produced the sharpest quarterly GDP contractions since the Great "
            "Depression.\n\n"
            "The bond market response was initially counterintuitive. On March 12–16, both US Treasuries "
            "and equities sold off simultaneously — a 'dash for cash' as institutional investors liquidated "
            "everything to meet redemptions and margin calls. This was one of the few episodes where "
            "Treasuries and equities moved together in the acute crisis phase, requiring the Fed to "
            "intervene directly.\n\n"
            "The Fed cut rates 150 bp in two emergency moves (March 3 and March 15) and launched unlimited "
            "QE. The US 10Y hit 0.54 % on March 9 — the lowest in 230 years of US Treasury market history. "
            "VIX closed at 82.69 on March 16, 2020 — a new all-time record, surpassing the 2008 crisis peak. "
            "All major central banks converged toward the zero lower bound within weeks, and nearly every "
            "central bank expanded its balance sheet aggressively via asset purchases."
        ),
    },
    {
        "id":     "inflation_hike",
        "label":  "9 · Inflation Shock & Hiking Cycle (2022–23)",
        "period": "March 2022 – July 2023",
        "driver": "Inflation Shock",
        "lesson": "When inflation becomes entrenched, it dominates everything. The fastest hiking cycle in 40 years produced the worst bond bear market in a century. Duration risk returned with force.",
        "window": ("2021-01-01", "2024-06-01"),
        "shade":  ("2022-03-16", "2023-07-26"),
        "keys":   [("2022-03-16", "Fed first hike"), ("2023-07-26", "Last hike (+525 bp total)")],
        "writeup": (
            "The post-COVID inflation surge combined multiple shocks: $6 trillion of US fiscal stimulus, "
            "pent-up consumer demand, supply chain bottlenecks (semiconductor shortages, shipping "
            "disruptions), and Russia's February 2022 invasion of Ukraine which drove European energy "
            "prices to record highs. US CPI peaked at 9.1 % YoY in June 2022 — the highest since 1981.\n\n"
            "The Federal Reserve's response was the fastest hiking cycle in 40 years: 525 bp in 17 months "
            "(March 2022 to July 2023), including four consecutive 75 bp moves in June–November 2022. The "
            "ECB hiked 450 bp from a negative base; the Bank of England 515 bp. US 10Y yields rose from "
            "1.51 % (January 3, 2022) to 5.02 % (October 19, 2023) — a 351 bp rise that produced the worst "
            "calendar-year loss for US Treasuries since the Civil War era (-18.1 % total return in 2022).\n\n"
            "The 2Y10Y yield curve inverted sharply — at its deepest (July 3, 2023), 2Y yields were 108 bp "
            "above 10Y yields, the deepest inversion since 1981. This reflects the market pricing aggressive "
            "near-term hikes while pricing eventual easing as the economy slows. TIPS breakeven rates peaked "
            "at 3.6 % (March 2022) then declined as hiking credibility was established. The 5Y real yield "
            "rose from -2 % to +2.5 % — a massive repricing of the risk-free rate."
        ),
    },
    {
        "id":     "uk_ldi",
        "label":  "10 · UK Mini-Budget & LDI Crisis (2022)",
        "period": "September – October 2022",
        "driver": "Fiscal Policy & Market Structure",
        "lesson": "Bond markets can punish fiscal policy within days. Pension leverage (LDI strategies) amplified the gilt sell-off into a systemic spiral requiring emergency BoE intervention.",
        "window": ("2022-07-01", "2023-03-01"),
        "shade":  ("2022-09-23", "2022-10-14"),
        "keys":   [("2022-09-23", "Mini-budget"), ("2022-10-14", "BoE emergency ends")],
        "writeup": (
            "On September 23, 2022, new Chancellor Kwasi Kwarteng announced £45 bn of unfunded tax cuts — "
            "the largest fiscal package in the UK since 1972. The announcement came without an Office for "
            "Budget Responsibility assessment, during a global hiking cycle in which fiscal credibility was "
            "under scrutiny everywhere. Bond markets reacted within hours.\n\n"
            "UK 10Y gilt yields rose from 3.4 % to 4.5 % in five days — a move of over 100 bp. The 30Y "
            "gilt rose from ~3.7 % to above 5 %. The pound fell to $1.03 — an all-time record low. "
            "This was not just a rate repricing: it exposed structural vulnerability in UK pension funds.\n\n"
            "Defined-benefit pension funds had extensively used Liability-Driven Investment (LDI) strategies — "
            "leveraged positions in long-dated gilts to match pension liabilities. As gilt prices fell, these "
            "funds faced margin calls, forcing them to sell gilts to meet them, which drove prices lower "
            "still, triggering more margin calls. The Bank of England estimated the market was within hours "
            "of a self-reinforcing collapse threatening several pension funds. The BoE launched an emergency "
            "£65 bn gilt purchase programme on September 28. Kwarteng was sacked October 14; PM Truss "
            "resigned October 20 — the shortest-serving UK Prime Minister in history."
        ),
    },
    {
        "id":     "trump_reflation",
        "label":  "✧ Trump Reflation Trade (2016)",
        "period": "November 2016",
        "driver": "Fiscal Policy & Market Structure",
        "lesson": "Not all yield rises are bearish. When yields rise on growth/fiscal expectations, equities can rally alongside bonds. The 'why' behind yield moves matters as much as the direction.",
        "window": ("2016-09-01", "2017-06-01"),
        "shade":  None,
        "keys":   [("2016-11-08", "US Election")],
        "writeup": (
            "Donald Trump's unexpected election victory on November 8, 2016 triggered an immediate repricing "
            "of US fiscal policy, growth and inflation expectations. Markets priced a large unfunded fiscal "
            "stimulus (corporate and personal tax cuts, infrastructure spending), deregulation and "
            "protectionist trade policies.\n\n"
            "US 10Y Treasury yields rose from 1.77 % on election day to 2.60 % by December 15 — an 83 bp "
            "move in five weeks. Critically, equities also rose: the S&P 500 gained ~5 % between the "
            "election and year-end. This 'Trump trade' — simultaneous rise in yields and equities — is the "
            "classic reflationary scenario where growth expectations dominate. The 2Y10Y spread steepened "
            "meaningfully as longer maturities priced fiscal expansion risks while 2Y remained anchored to "
            "near-term Fed rate expectations.\n\n"
            "This episode illustrates the critical distinction: yields rising on growth/fiscal expectations "
            "are bullish for equities because they signal higher earnings growth ahead. Yields rising on "
            "inflation fears or credit risk are bearish. The mechanism behind the yield move — not just the "
            "direction — determines how other asset classes respond."
        ),
    },
    {
        "id":     "negative_yields",
        "label":  "✧ Negative Yield Era (2016–2021)",
        "period": "2016 – 2021",
        "driver": "Growth Shock",
        "lesson": "Yield is a market price with no natural floor. $18 trillion of bonds traded at negative yields — driven by central bank purchases, deflation fear, and a global savings glut.",
        "window": ("2014-01-01", "2022-03-01"),
        "shade":  ("2016-07-06", "2021-12-31"),
        "keys":   [("2016-07-06", "German 10Y < 0"), ("2019-08-01", "$17 T negative yield peak")],
        "writeup": (
            "The negative yield era represents the most radical repricing in the history of sovereign bond "
            "markets. German Bund 10Y yields went negative in July 2016 and remained predominantly negative "
            "through December 2021. At the peak in August 2019, approximately $17 trillion of global bonds "
            "traded at negative nominal yields — roughly 25 % of the entire investable bond universe.\n\n"
            "The causes were structural: aggressive central bank asset purchases (ECB PSPP from March 2015, "
            "BoJ Yield Curve Control from September 2016), persistently below-target inflation, a global "
            "savings glut (excess savings relative to investment opportunities), and demographic trends in "
            "ageing economies creating structural demand for fixed-income assets to match long-dated "
            "liabilities.\n\n"
            "Negative yields are not irrational: when expected inflation is also negative, a negative nominal "
            "yield can still be a positive real return. Insurance companies and pension funds with regulatory "
            "requirements to hold government bonds will buy them regardless of yield — capital preservation "
            "matters more than income. The era ended abruptly when US inflation surged in 2021, eventually "
            "dragging European yields higher through global rate contagion. German 10Y yields moved from "
            "-0.50 % in late 2021 to +2.4 % by October 2022 — one of the fastest reversals in Bund history."
        ),
    },
]

_EVENT_BY_ID = {e["id"]: e for e in _EVENTS}


# ── Chart helpers ─────────────────────────────────────────────────────────────

def _clip(df: pd.DataFrame, date_col: str, start: str, end: str) -> pd.DataFrame:
    return df[
        (df[date_col] >= pd.Timestamp(start)) &
        (df[date_col] <= pd.Timestamp(end))
    ].copy()


def _decorate(fig: go.Figure, ev: dict) -> go.Figure:
    if ev.get("shade"):
        fig.add_vrect(
            x0=ev["shade"][0], x1=ev["shade"][1],
            fillcolor="rgba(100,110,130,0.13)", line_width=0,
        )
    for date, label in (ev.get("keys") or []):
        fig.add_shape(
            type="line", x0=date, x1=date, y0=0, y1=1,
            xref="x", yref="paper",
            line=dict(color="#f59e0b", width=1.5, dash="dot"),
        )
        fig.add_annotation(
            x=date, y=0.98, xref="x", yref="paper",
            text=label, showarrow=False,
            xanchor="left", yanchor="top",
            font=dict(size=9, color="#f59e0b"),
            bgcolor="rgba(0,0,0,0)",
        )
    return fig


def _base(title: str, y_label: str = "", h: int = 310) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=_BG, plot_bgcolor=_BG,
        font=dict(size=11, color=_T2),
        title=dict(text=title, font=dict(size=13, color=_T1), x=0),
        xaxis=dict(gridcolor=_GRD, zeroline=False),
        yaxis=dict(gridcolor=_GRD, zeroline=False, title=y_label),
        margin=dict(l=0, r=0, t=38, b=0),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, x=0,
            font=dict(size=11, color=_T1),
            bgcolor="rgba(0,0,0,0)",
        ),
        height=h,
        hovermode="x unified",
    )
    return fig


def _pchrt(fig: go.Figure, caption: str = "") -> None:
    """Render a plotly chart with an optional caption."""
    st.plotly_chart(fig, use_container_width=True)
    if caption:
        st.caption(caption)


# ── Chart functions ───────────────────────────────────────────────────────────

def _yields(df: pd.DataFrame, ev: dict,
            cols: list[str], names: list[str],
            title: str, y_label: str = "Yield (%)") -> go.Figure:
    d = _clip(df, "Date", *ev["window"])
    fig = _base(title, y_label)
    for i, (col, name) in enumerate(zip(cols, names)):
        if col not in d.columns:
            continue
        s = d[["Date", col]].dropna()
        fig.add_trace(go.Scatter(
            x=s["Date"], y=s[col], name=name,
            line=dict(color=_COLS[i % len(_COLS)], width=1.8),
        ))
    return _decorate(fig, ev)


def _spread(df: pd.DataFrame, ev: dict,
            c1: str, c2: str, name: str,
            title: str, y_label: str = "bp",
            color: str = "#f87171", scale: float = 100.0) -> go.Figure:
    d = _clip(df, "Date", *ev["window"])
    fig = _base(title, y_label)
    if c1 in d.columns and c2 in d.columns:
        s = (d[c1] - d[c2]) * scale
        fig.add_trace(go.Scatter(
            x=d["Date"], y=s, name=name,
            line=dict(color=color, width=1.8),
        ))
        fig.add_hline(y=0, line_color="#475569", line_dash="dot", line_width=1)
    return _decorate(fig, ev)


def _multi_spreads(df: pd.DataFrame, ev: dict,
                   pairs: list[tuple],
                   title: str, y_label: str = "bp") -> go.Figure:
    d = _clip(df, "Date", *ev["window"])
    fig = _base(title, y_label)
    for c1, c2, name, color in pairs:
        if c1 in d.columns and c2 in d.columns:
            s = (d[c1] - d[c2]) * 100
            fig.add_trace(go.Scatter(
                x=d["Date"], y=s, name=name,
                line=dict(color=color, width=1.8),
            ))
    fig.add_hline(y=0, line_color="#475569", line_dash="dot", line_width=1)
    return _decorate(fig, ev)


def _cb_rates(df_cbpol: pd.DataFrame, ev: dict,
              countries: list[str], names: list[str],
              title: str) -> go.Figure:
    fig = _base(title, "Rate (%)")
    start, end = ev["window"]
    for i, (country, name) in enumerate(zip(countries, names)):
        d = df_cbpol[df_cbpol["Country"] == country].copy()
        d = _clip(d, "Date", start, end).sort_values("Date")
        if d.empty:
            continue
        fig.add_trace(go.Scatter(
            x=d["Date"], y=d["Rate"], name=name,
            line=dict(color=_COLS[i % len(_COLS)], width=1.8, shape="hv"),
        ))
    return _decorate(fig, ev)


def _single_cross(df_cross: pd.DataFrame, ev: dict,
                  series: str, title: str,
                  y_label: str = "", color: str = "#60a5fa") -> go.Figure:
    d = df_cross[df_cross["Series"] == series].copy()
    d = _clip(d, "Date", *ev["window"]).sort_values("Date")
    fig = _base(title, y_label)
    if not d.empty:
        fig.add_trace(go.Scatter(
            x=d["Date"], y=d["Value"], name=series,
            line=dict(color=color, width=1.8),
        ))
    return _decorate(fig, ev)


def _breakeven_chart(df_be: pd.DataFrame, ev: dict,
                     series: list[str], title: str) -> go.Figure:
    fig = _base(title, "Rate (%)")
    for i, s in enumerate(series):
        d = df_be[df_be["Series"] == s].copy()
        d = _clip(d, "Date", *ev["window"]).sort_values("Date")
        if d.empty:
            continue
        fig.add_trace(go.Scatter(
            x=d["Date"], y=d["Value"], name=s,
            line=dict(color=_COLS[i % len(_COLS)], width=1.8),
        ))
    fig.add_hline(y=2.0, line_color="#475569", line_dash="dot", line_width=1,
                  annotation_text="2 % target", annotation_font=dict(size=9, color=_T2))
    return _decorate(fig, ev)


def _oas_chart(df_sl: pd.DataFrame, ev: dict,
               series: list[str], title: str) -> go.Figure:
    fig = _base(title, "OAS (%)")
    for i, s in enumerate(series):
        d = df_sl[df_sl["Series"] == s].copy()
        d = _clip(d, "Date", *ev["window"]).sort_values("Date")
        if d.empty:
            continue
        fig.add_trace(go.Scatter(
            x=d["Date"], y=d["OAS_Pct"], name=s,
            line=dict(color=_COLS[i % len(_COLS)], width=1.8),
        ))
    return _decorate(fig, ev)


# ── Event renderers ───────────────────────────────────────────────────────────

def _render_dotcom(ev, df, cbpol, cross, be, sl):
    c1, c2, c3 = st.columns(3)
    with c1:
        _pchrt(_yields(df, ev, ["US2Y", "US10Y", "US30Y"],
                       ["US 2Y Treasury", "US 10Y Treasury", "US 30Y Treasury"],
                       "US Treasury Yields (%)"),
               "Fed cut rates 11× from 6.5 % to 1.0 % (2001–03). US 10Y fell from ~6.5 % to 3.1 %. "
               "Flight to safety drove the bond rally as equities collapsed.")
    with c2:
        _pchrt(_spread(df, ev, "US10Y", "US2Y", "10Y minus 2Y",
                       "US 2Y10Y Yield Curve Slope (bp)", color="#34d399"),
               "The 2Y10Y spread inverted briefly in 2000 — a classic recession warning signal — "
               "then steepened sharply as the Fed cut short rates faster than long rates fell.")
    with c3:
        _pchrt(_single_cross(cross, ev, "S&P 500", "S&P 500 Index (Level)", "Level", "#34d399"),
               "S&P 500 lost ~49 % from the March 2000 peak to the October 2002 trough. "
               "Equity wealth destruction of ~$8 trillion drove the flight into Treasuries.")


def _render_gfc(ev, df, cbpol, cross, be, sl):
    has_spreads = not sl.empty
    n = 4 if has_spreads else 3
    cols = st.columns(n)
    with cols[0]:
        _pchrt(_yields(df, ev, ["US2Y", "US10Y"],
                       ["US 2Y Treasury", "US 10Y Treasury"],
                       "US Treasury Yields (%)"),
               "10Y Treasury fell from ~4.5 % to ~2 % as flight-to-quality dominated. "
               "Even at historic lows, Treasuries were bought because everything else was far worse.")
    with cols[1]:
        _pchrt(_cb_rates(cbpol, ev,
                         ["United States", "Euro Area", "United Kingdom", "Japan"],
                         ["Fed (US)", "ECB (Euro Area)", "BoE (UK)", "BoJ (Japan)"],
                         "Central Bank Policy Rates (%)"),
               "Fed cut 525 bp in 15 months to 0–0.25 % and launched QE1 ($600 bn). "
               "ECB, BoE and BoJ all followed with aggressive easing cycles.")
    with cols[2]:
        _pchrt(_single_cross(cross, ev, "VIX", "VIX Volatility Index", "", "#f87171"),
               "VIX hit 80.86 on October 24, 2008 — an all-time record at the time. "
               "Elevated VIX signals extreme uncertainty and forced liquidation of risk assets.")
    if has_spreads:
        with cols[3]:
            _pchrt(_oas_chart(sl, ev, ["HY", "BBB"],
                              "US Credit Spreads — OAS (%)"),
                   "HY OAS blew out to ~19 % in December 2008 — unprecedented. "
                   "Even BBB (lower investment-grade) spreads exceeded 7 %. Credit markets effectively froze.")


def _render_eurozone(ev, df, cbpol, cross, be, sl):
    c1, c2, c3 = st.columns(3)
    with c1:
        _pchrt(_spread(df, ev, "FBTPY", "FGBLY", "Italy 10Y minus Germany 10Y",
                       "Italy – Germany 10Y Spread (bp)", color="#f87171"),
               "BTP-Bund spread peaked at ~550 bp in November 2011 when Italy's 10Y yield "
               "crossed 7 % — the threshold widely considered unsustainable for €2 trillion of debt.")
    with c2:
        _pchrt(_multi_spreads(df, ev,
                              [("FOATY", "FGBLY", "France – Germany 10Y", "#c084fc"),
                               ("UK10Y",  "FGBLY", "UK – Germany 10Y",    "#fb923c")],
                              "Contagion Spreads vs German Bund (bp)"),
               "French OAT and UK Gilt spreads over Germany also widened, showing contagion "
               "beyond the obvious PIIGS. No eurozone sovereign was fully immune.")
    with c3:
        _pchrt(_yields(df, ev, ["FGBLY"], ["German 10Y Bund"],
                       "German 10Y Bund — Safe Haven Within Europe (%)"),
               "German Bund yields fell sharply as the safe-haven within Europe. "
               "Within a currency union, credit risk drives spreads; Bunds played the role "
               "that Treasuries play globally.")


def _render_draghi(ev, df, cbpol, cross, be, sl):
    c1, c2, c3 = st.columns(3)
    with c1:
        _pchrt(_spread(df, ev, "FBTPY", "FGBLY", "Italy 10Y minus Germany 10Y",
                       "Italy – Germany 10Y Spread (bp)", color="#f87171"),
               "BTP-Bund spread fell from ~530 bp (late July 2012) to ~230 bp by year-end — "
               "on Draghi's words alone. The OMT programme never formally purchased a single bond.")
    with c2:
        _pchrt(_multi_spreads(df, ev,
                              [("FOATY", "FGBLY", "France – Germany 10Y", "#c084fc"),
                               ("FBTSY", "FGBSY", "Italy – Germany 2Y",   "#f87171")],
                              "Contagion Spreads — Speech Impact (bp)"),
               "French 10Y and Italian 2Y spreads also collapsed immediately after the speech. "
               "Short-dated spreads fell fastest — markets repriced near-term break-up risk to near zero.")
    with c3:
        _pchrt(_cb_rates(cbpol, ev, ["Euro Area"], ["ECB Policy Rate"],
                         "ECB Policy Rate (%)"),
               "The ECB rate was at 0.75 % at the time of the speech. The real tool was the OMT "
               "backstop — an unlimited, conditional commitment to buy peripheral sovereign bonds.")


def _render_taper(ev, df, cbpol, cross, be, sl):
    c1, c2, c3 = st.columns(3)
    with c1:
        _pchrt(_yields(df, ev, ["US10Y", "US30Y"],
                       ["US 10Y Treasury", "US 30Y Treasury"],
                       "US Treasury Yields — The Tantrum (%)"),
               "US 10Y rose ~140 bp in 7 months on a hint — not an actual rate change. "
               "Bernanke merely suggested slowing bond purchases; the market repriced the entire long end.")
    with c2:
        _pchrt(_spread(df, ev, "US10Y", "US2Y", "10Y minus 2Y",
                       "US Yield Curve — Steepening on Taper Expectations (bp)", color="#34d399"),
               "The 2Y10Y spread steepened significantly. 2Y yields were anchored near zero "
               "(Fed held rates steady); 10Y and 30Y repriced future inflation and term premium.")
    with c3:
        _pchrt(_cb_rates(cbpol, ev, ["United States"], ["Federal Funds Rate"],
                         "Federal Funds Rate — Held at 0 % Throughout (%)"),
               "The Fed did not raise rates once in 2013. Long-term yields can move 100+ bp "
               "while the policy rate is frozen — expectations are the transmission mechanism.")


def _render_oil_deflation(ev, df, cbpol, cross, be, sl):
    c1, c2, c3 = st.columns(3)
    with c1:
        _pchrt(_single_cross(cross, ev, "WTI Crude",
                             "WTI Crude Oil — The Deflationary Driver (USD/bbl)",
                             "USD / bbl", "#fb923c"),
               "WTI fell from $107/bbl (June 2014) to below $26/bbl (February 2016). "
               "OPEC's November 2014 decision to maintain output despite surging US shale triggered the crash.")
    with c2:
        _pchrt(_breakeven_chart(be, ev, ["5Y Breakeven", "10Y Breakeven"],
                                "US Inflation Expectations — Falling Toward Deflation (%)"),
               "US 5Y breakeven inflation fell from ~2 % to ~1.1 % as oil collapsed. "
               "Markets priced sustained deflation risk; the Fed's 2 % target became a distant goal.")
    with c3:
        _pchrt(_yields(df, ev, ["FGBLY", "US10Y"],
                       ["German 10Y Bund", "US 10Y Treasury"],
                       "Nominal Yields Fall — German Bund Goes Negative (%)"),
               "German 10Y Bund yield crossed zero on July 6, 2016 — a historic first. "
               "When expected inflation is negative, a negative nominal yield can still be a "
               "positive real return.")


def _render_brexit(ev, df, cbpol, cross, be, sl):
    c1, c2, c3 = st.columns(3)
    with c1:
        _pchrt(_yields(df, ev,
                       ["UK10Y", "FGBLY", "US10Y"],
                       ["UK 10Y Gilt", "German 10Y Bund", "US 10Y Treasury"],
                       "10Y Government Yields — Risk-Off Rally (%)"),
               "UK Gilt yields fell on the vote result — investors bought gilts of the very "
               "country facing political risk. Reflex risk-off dominated before more nuanced repricing.")
    with c2:
        _pchrt(_multi_spreads(df, ev,
                              [("UK10Y", "FGBLY", "UK Gilt – German Bund 10Y", "#fb923c"),
                               ("US10Y", "FGBLY", "US Treasury – German Bund 10Y", "#60a5fa")],
                              "10Y Spreads vs German Bund (bp)"),
               "UK–Germany spread initially compressed (both gilts and Bunds rallied in risk-off), "
               "then widened as markets repriced UK-specific growth and political uncertainty risk.")
    with c3:
        _pchrt(_single_cross(cross, ev, "S&P 500",
                             "S&P 500 — Rapid Recovery (Level)", "Level", "#34d399"),
               "US equities fell initially but recovered within days — markets quickly concluded "
               "Brexit was a UK-specific shock, not a global one. FTSE 100 rose on sterling weakness.")


def _render_covid(ev, df, cbpol, cross, be, sl):
    c1, c2, c3 = st.columns(3)
    with c1:
        _pchrt(_yields(df, ev,
                       ["US2Y", "US10Y", "US30Y"],
                       ["US 2Y Treasury", "US 10Y Treasury", "US 30Y Treasury"],
                       "US Treasury Yields — Historic Lows (%)"),
               "US 10Y hit 0.54 % on March 9, 2020 — the lowest in 230 years of US Treasury history. "
               "The entire US curve traded below 1 % simultaneously for the first time ever.")
    with c2:
        _pchrt(_cb_rates(cbpol, ev,
                         ["United States", "Euro Area", "United Kingdom", "Japan"],
                         ["Fed (US)", "ECB (Euro Area)", "BoE (UK)", "BoJ (Japan)"],
                         "Central Bank Policy Rates — Emergency Cuts (%)"),
               "Fed cut 150 bp in two emergency moves in March 2020 and launched unlimited QE. "
               "All major central banks converged to the zero lower bound within weeks.")
    with c3:
        _pchrt(_single_cross(cross, ev, "VIX",
                             "VIX — All-Time Record High", "", "#f87171"),
               "VIX hit 82.69 on March 16, 2020 — a new all-time record. "
               "The speed of the shock (lockdowns in 12 days from WHO pandemic declaration) "
               "was unprecedented in modern financial history.")


def _render_inflation_hike(ev, df, cbpol, cross, be, sl):
    r1c1, r1c2 = st.columns(2)
    r2c1, r2c2 = st.columns(2)
    with r1c1:
        _pchrt(_cb_rates(cbpol, ev,
                         ["United States", "Euro Area", "United Kingdom", "Japan", "Canada"],
                         ["Fed (US)", "ECB (Euro Area)", "BoE (UK)", "BoJ (Japan)", "BoC (Canada)"],
                         "Central Bank Policy Rates — Fastest Hike in 40 Years (%)"),
               "Fed hiked 525 bp in 17 months — the fastest cycle since Volcker (1980). "
               "ECB hiked 450 bp from a negative base rate. Four consecutive 75 bp Fed moves in H2 2022.")
    with r1c2:
        _pchrt(_yields(df, ev,
                       ["US2Y", "US10Y", "US30Y"],
                       ["US 2Y Treasury", "US 10Y Treasury", "US 30Y Treasury"],
                       "US Treasury Yields — Worst Bond Bear Market in a Century (%)"),
               "US 10Y rose from 1.5 % (Jan 2022) to 5.0 % (Oct 2023) — a 351 bp rise. "
               "US Treasuries returned -18 % in 2022, the worst calendar year since the Civil War era.")
    with r2c1:
        _pchrt(_spread(df, ev, "US10Y", "US2Y", "10Y minus 2Y",
                       "US 2Y10Y Slope — Historic Inversion (bp)", color="#f87171"),
               "2Y10Y inverted to -108 bp in July 2023 — deepest since 1981. "
               "Inverted curves reliably precede recessions: near-term hikes priced in, future cuts expected.")
    with r2c2:
        _pchrt(_breakeven_chart(be, ev,
                                ["5Y Breakeven", "10Y Breakeven", "5Y Real Yield"],
                                "US Inflation & Real Yield Repricing (%)"),
               "5Y breakeven peaked at 3.6 % (March 2022) then declined as hike credibility built. "
               "5Y real yield rose from -2 % to +2.5 % — a massive repricing of the risk-free rate.")


def _render_uk_ldi(ev, df, cbpol, cross, be, sl):
    c1, c2, c3 = st.columns(3)
    with c1:
        _pchrt(_yields(df, ev,
                       ["UK10Y", "FGBXY"],
                       ["UK 10Y Gilt", "German 30Y Buxl"],
                       "Long-End Yields — The LDI Spike (%)"),
               "UK 10Y rose 110 bp in 5 days after the mini-budget. The 30Y gilt "
               "— the key LDI instrument for pension funds — spiked even more dramatically.")
    with c2:
        _pchrt(_multi_spreads(df, ev,
                              [("UK10Y", "FGBLY", "UK Gilt – German Bund 10Y", "#fb923c"),
                               ("UK10Y", "US10Y", "UK Gilt – US Treasury 10Y", "#a78bfa")],
                              "UK Gilt Spreads — Fiscal Credibility Premium (bp)"),
               "UK–Germany and UK–US spreads blew out sharply — this was UK-specific, not a global move. "
               "Bond markets priced a fiscal credibility premium for the first time in modern UK history.")
    with c3:
        _pchrt(_cb_rates(cbpol, ev,
                         ["United Kingdom", "United States", "Euro Area"],
                         ["BoE (UK)", "Fed (US)", "ECB (Euro Area)"],
                         "Policy Rates — BoE Conflict: Hike or Intervene? (%)"),
               "The BoE was already hiking to combat 11 % UK CPI when the mini-budget hit. "
               "It faced a conflict: tighten to fight inflation, or intervene to prevent a pension "
               "fund collapse. It ultimately did both — hike and launch emergency gilt purchases.")


def _render_trump_reflation(ev, df, cbpol, cross, be, sl):
    c1, c2, c3 = st.columns(3)
    with c1:
        _pchrt(_yields(df, ev,
                       ["US2Y", "US10Y", "US30Y"],
                       ["US 2Y Treasury", "US 10Y Treasury", "US 30Y Treasury"],
                       "US Treasury Yields — Reflationary Jump (%)"),
               "US 10Y rose 83 bp in 5 weeks post-election. Unlike most yield spikes, "
               "equity markets rallied simultaneously — markets priced higher growth, not just higher "
               "inflation.")
    with c2:
        _pchrt(_spread(df, ev, "US10Y", "US2Y", "10Y minus 2Y",
                       "US Curve — Steepening on Fiscal Expansion Expectations (bp)",
                       color="#34d399"),
               "The 2Y10Y spread steepened sharply. Longer maturities repriced fiscal expansion "
               "and inflation risks; 2Y remained anchored to near-term Fed rate expectations.")
    with c3:
        _pchrt(_single_cross(cross, ev, "S&P 500",
                             "S&P 500 — Equities and Yields Rise Together (Level)",
                             "Level", "#34d399"),
               "S&P 500 rose ~5 % alongside bond yields. The 'Trump trade' — yields and equities "
               "rising together — is the classic reflationary scenario driven by growth expectations.")


def _render_negative_yields(ev, df, cbpol, cross, be, sl):
    c1, c2, c3 = st.columns(3)
    with c1:
        _pchrt(_yields(df, ev,
                       ["FGBLY", "FGBMY", "FGBXY"],
                       ["German 10Y Bund", "German 5Y Bobl", "German 30Y Buxl"],
                       "German Sovereign Yields — Into Negative Territory (%)"),
               "German 10Y went negative in July 2016 and stayed negative through 2021. "
               "At the peak, all German maturities out to 10 years traded below zero simultaneously.")
    with c2:
        _pchrt(_cb_rates(cbpol, ev, ["Euro Area", "Japan"],
                         ["ECB (Euro Area)", "BoJ (Japan)"],
                         "ECB and BoJ — Negative Rate Pioneers (%)"),
               "ECB deposit rate cut to -0.40 % by March 2016. BoJ implemented Yield Curve Control "
               "in September 2016, explicitly targeting a 0 % 10Y yield via unlimited bond purchases.")
    with c3:
        _pchrt(_breakeven_chart(be, ev, ["5Y Breakeven", "10Y Breakeven"],
                                "US Inflation Expectations — Deflation Fear (%)"),
               "US inflation expectations also drifted lower, though never as far as European equivalents. "
               "The era ended abruptly in 2021 when US inflation surged, eventually pulling European "
               "yields higher through global rate contagion.")


_RENDERERS = {
    "dotcom":          _render_dotcom,
    "gfc":             _render_gfc,
    "eurozone":        _render_eurozone,
    "draghi":          _render_draghi,
    "taper":           _render_taper,
    "oil_deflation":   _render_oil_deflation,
    "brexit":          _render_brexit,
    "covid":           _render_covid,
    "inflation_hike":  _render_inflation_hike,
    "uk_ldi":          _render_uk_ldi,
    "trump_reflation": _render_trump_reflation,
    "negative_yields": _render_negative_yields,
}


# ── Render helpers ────────────────────────────────────────────────────────────

_CSS = """
<style>
.shock-header { font-size:22px; font-weight:700; color:#f1f5f9; margin-bottom:2px; }
.shock-sub    { font-size:13px; color:#64748b; margin-bottom:18px; }
.shock-card   { border:1px solid #1e293b; border-radius:10px; padding:14px 18px 12px;
                margin-bottom:10px; background:#0f172a; }
.shock-period { font-size:12px; color:#94a3b8; margin-bottom:6px; }
.shock-badge  { display:inline-block; padding:2px 10px; border-radius:4px;
                font-size:11px; font-weight:600; margin-bottom:8px; }
.shock-lesson { font-size:13px; color:#94a3b8; line-height:1.6; margin-top:4px; }
.shock-writeup-label { font-size:10px; font-weight:700; letter-spacing:.08em;
                       text-transform:uppercase; color:#475569; margin-top:14px; margin-bottom:6px; }
.shock-writeup { font-size:13px; color:#cbd5e1; line-height:1.75; white-space:pre-wrap; }
</style>
"""


def _event_card(ev: dict) -> None:
    bg, fg = _DRIVER_STYLE.get(ev["driver"], ("#1e293b", "#94a3b8"))
    writeup_html = ev.get("writeup", "").replace("\n\n", "<br><br>")
    st.markdown(
        f"""
        <div class="shock-card">
          <div class="shock-period">📅 {ev["period"]}</div>
          <span class="shock-badge" style="background:{bg};color:{fg};">{ev["driver"]}</span>
          <div class="shock-lesson"><b>Core lesson:</b> {ev["lesson"]}</div>
          <div class="shock-writeup-label">Background &amp; Analysis</div>
          <div class="shock-writeup">{writeup_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Main entry point ──────────────────────────────────────────────────────────

def historical_shocks() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown('<div class="shock-header">Historical Global Shocks</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="shock-sub">Yield and rates dynamics across 12 key market events · '
        'Each chart labelled with what is shown and why it moved</div>',
        unsafe_allow_html=True,
    )

    # ── Sidebar ───────────────────────────────────────────────────────────────
    ev_labels = [e["label"] for e in _EVENTS]
    sel_label = st.sidebar.selectbox("Select event", ev_labels, key="shock_event")
    ev = next(e for e in _EVENTS if e["label"] == sel_label)

    st.sidebar.markdown("---")
    refresh_oas = st.sidebar.button(
        "🔄 Refresh Credit Spreads", key="shock_refresh_oas",
        help="Fetch HY/BBB OAS history from FRED (1996–present). Adds a credit spread panel to GFC.",
    )
    st.sidebar.caption("HY & BBB OAS from FRED. Adds a 4th chart panel to the GFC event.")

    # ── Load data ─────────────────────────────────────────────────────────────
    df_bond = load_data()

    if _CBPOL_CACHE.exists():
        df_cbpol = pd.read_parquet(_CBPOL_CACHE)
        df_cbpol["Date"] = pd.to_datetime(df_cbpol["Date"])
    else:
        df_cbpol = pd.DataFrame(columns=["Date", "Country", "Rate"])

    df_cross = load_cross_asset() if CROSS_ASSET_CACHE.exists() else pd.DataFrame()
    if not df_cross.empty:
        df_cross["Date"] = pd.to_datetime(df_cross["Date"])

    df_be = load_breakeven() if BREAKEVEN_CACHE.exists() else pd.DataFrame()
    if not df_be.empty:
        df_be["Date"] = pd.to_datetime(df_be["Date"])

    if refresh_oas:
        with st.spinner("Fetching historical OAS from FRED…"):
            df_sl = refresh_spreads_long()
    else:
        df_sl = load_spreads_long() if SPREADS_LONG_CACHE.exists() else pd.DataFrame()
    if not df_sl.empty:
        df_sl["Date"] = pd.to_datetime(df_sl["Date"])

    # ── Event card (metadata + write-up) ─────────────────────────────────────
    _event_card(ev)

    # ── Charts ────────────────────────────────────────────────────────────────
    render_fn = _RENDERERS.get(ev["id"])
    if render_fn:
        render_fn(ev, df_bond, df_cbpol, df_cross, df_be, df_sl)
    else:
        st.info("Renderer not yet defined for this event.")

    # ── Data sources note ─────────────────────────────────────────────────────
    with st.expander("Data sources", expanded=False):
        for src, detail in [
            ("Yield curves & equity indices", "Final.xlsx — daily from April 1994"),
            ("CB policy rates",               "BIS WS_CBPOL via DBnomics — daily from 1946"),
            ("VIX · WTI · S&P 500",           "FRED — daily from 2000"),
            ("TIPS breakeven / real yields",  "FRED — daily from 2003"),
            ("HY & BBB OAS credit spreads",   "FRED OAS series — daily from 1996–97 (click Refresh above)"),
        ]:
            st.markdown(f"**{src}** — {detail}")
