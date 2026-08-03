CHANGELOG = [
    {
        "id": 1,
        "version": "1.1",
        "timestamp": "03 Aug 2026, 10:46 IST",
        "category": "Refactor",
        "title": "Initial refactor — shared utilities, dead code removal, changelog added",
        "description": [
            "Extracted shared Firebase formula CRUD (get/add/delete) into firebase_utils.py — was copy-pasted across GridTab, CustomTab, and HeatmapTab; any future fix now in one place",
            "Extracted shared load_data() into data.py — was defined separately in all 4 tabs reading the same Final.xlsx; now a single @st.cache_data call app-wide",
            "Fixed instrument column inconsistency — HeatmapTab sliced df.columns[1:32] (31 cols), CustomTab sliced df.columns[1:34] (33 cols); unified to df.columns[1:] so all instruments are included dynamically",
            "Replaced unsafe eval() in CustomTab with df.eval() — matches GridTab's existing approach; removes Python builtins escape vector in custom formula evaluation",
            "Fixed deprecated st.experimental_rerun() → st.rerun() in portfolio_rebalance.py — would raise AttributeError on Streamlit ≥1.28",
            "Removed debug print('Saved Formulas', ...) in GridTab.py — was logging each user's saved formulas to stdout on every render",
            "Removed unused imports in CustomTab.py — authenticator, firebase_admin, credentials, get_app, initialize_app were imported but never referenced",
            "Removed dead commented-out code from stream.py (old home_page implementation) and portfolio_rebalance.py (commented file upload block)",
            "Added admin-only Changelog tab visible to professionalbuzz@gmail.com (requires ADMINS env var on Render to include this email)",
        ],
    },
]
