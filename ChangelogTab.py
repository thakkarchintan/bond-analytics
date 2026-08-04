import streamlit as st
from changelog import CHANGELOG


_CATEGORY_STYLES = {
    "Feature":     ("#eff6ff", "#1e40af"),
    "Fix":         ("#fef2f2", "#991b1b"),
    "Refactor":    ("#f0fdf4", "#166534"),
    "Security":    ("#fff7ed", "#9a3412"),
    "Performance": ("#f5f3ff", "#5b21b6"),
    "Config":      ("#f0f9ff", "#0c4a6e"),
    "UI":          ("#fdf4ff", "#7e22ce"),
}


def _category_badge(category: str) -> str:
    bg, fg = _CATEGORY_STYLES.get(category, ("#f8fafc", "#334155"))
    return (
        f'<span style="background:{bg}; color:{fg}; padding:2px 10px; '
        f'border-radius:4px; font-size:11px; font-weight:600;">{category}</span>'
    )


def changelog_tab():
    st.markdown(
        """
        <style>
        .cl-header { font-size: 22px; font-weight: 700; color: #0f172a; margin-bottom: 4px; }
        .cl-sub    { font-size: 13px; color: #64748b; margin-bottom: 24px; }
        .cl-card   {
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 18px 20px;
            margin-bottom: 14px;
            background: #ffffff;
        }
        .cl-version { font-family: monospace; font-size: 12px; font-weight: 700;
                      background: #1e3a8a; color: white; padding: 2px 8px;
                      border-radius: 4px; margin-right: 8px; }
        .cl-title   { font-size: 15px; font-weight: 600; color: #0f172a; }
        .cl-ts      { font-family: monospace; font-size: 12px; color: #94a3b8; margin-top: 6px; }
        .cl-bullet  { font-size: 13px; color: #374151; margin: 3px 0 3px 12px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="cl-header">Changelog — Bond Analytics</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="cl-sub">Admin view · {len(CHANGELOG)} deployment{"s" if len(CHANGELOG) != 1 else ""} tracked</div>',
        unsafe_allow_html=True,
    )

    for entry in CHANGELOG:
        bullets_html = "".join(
            f'<div class="cl-bullet">• {b}</div>' for b in entry["description"]
        )
        st.markdown(
            f"""
            <div class="cl-card">
                <div>
                    <span class="cl-version">v{entry["version"]}</span>
                    <span class="cl-title">{entry["title"]}</span>
                    &nbsp;&nbsp;{_category_badge(entry["category"])}
                </div>
                <div class="cl-ts">🕐 {entry["timestamp"]}</div>
                <hr style="border:none; border-top:1px solid #f1f5f9; margin:12px 0 10px;">
                {bullets_html}
            </div>
            """,
            unsafe_allow_html=True,
        )
