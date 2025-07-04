def news_app():
    import streamlit as st
    import requests
    import cohere
    import nltk
    import json
    import os
    from datetime import datetime, timedelta
    from sumy.parsers.plaintext import PlaintextParser
    from sumy.nlp.tokenizers import Tokenizer
    from sumy.summarizers.text_rank import TextRankSummarizer
    from bs4 import BeautifulSoup
    from dotenv import load_dotenv
    from pathlib import Path

    env_path = Path(__file__).resolve().parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)
    COHERE_API_KEY = os.getenv("COHERE_API_KEY")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    NEWS_API_KEY = os.getenv("NEWS_API_KEY")
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SOURCE_FILE = os.path.join(BASE_DIR, "news_summary_source.txt")

    co = cohere.Client(COHERE_API_KEY)
    nltk.download("punkt", quiet=True)

    # --- Load Source Preferences ---
    def load_source_prefs():
        if os.path.exists(SOURCE_FILE):
            with open(SOURCE_FILE, "r") as f:
                data = json.load(f)
                return set(data.get("whitelist", [])), set(data.get("blacklist", []))
        return set(), set()

    # --- Save Source Preferences ---
    def save_source_prefs():
        with open(SOURCE_FILE, "w") as f:
            json.dump({
                "whitelist": list(st.session_state.whitelist),
                "blacklist": list(st.session_state.blacklist)
            }, f, indent=2)

    # --- Session State Init ---
    if "whitelist" not in st.session_state or "blacklist" not in st.session_state:
        whitelist, blacklist = load_source_prefs()
        st.session_state.whitelist = whitelist
        st.session_state.blacklist = blacklist

    # --- DeepSeek Summarizer ---
    def summarize_with_deepseek(text):
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": f"Summarize the following in 2-3 lines:\n{text}"}
            ]
        }
        try:
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            res.raise_for_status()
            return res.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"DeepSeek failed: {e}")
            return None

    # --- Fallback Summarizer ---
    def summarize_text(text, fallback_sentences=5):
        summary = summarize_with_deepseek(text)
        if summary:
            return summary
        try:
            response = co.summarize(
                text=text,
                length='medium',
                format='paragraph',
                model='command',
                extractiveness='low',
                temperature=0.3
            )
            return response.summary.strip()
        except Exception as e:
            print(f"Cohere failed: {e}")
            try:
                parser = PlaintextParser.from_string(text, Tokenizer("english"))
                summarizer = TextRankSummarizer()
                summary_sentences = summarizer(parser.document, fallback_sentences)
                return " ".join(str(sentence) for sentence in summary_sentences)
            except Exception as e:
                return f"[Summarization failed: {e}]"

    # --- Clean Article Content ---
    def clean_html(text):
        soup = BeautifulSoup(text, "html.parser")
        return soup.get_text()

    # --- Extract Full Text from URL ---
    def extract_full_article(url):
        try:
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")
            paragraphs = soup.find_all('p')
            full_text = " ".join(p.get_text() for p in paragraphs)
            return full_text.strip()
        except Exception as e:
            print(f"Failed to fetch full article: {e}")
            return ""

    # --- Feedback Tracking ---
    def add_to_whitelist(source):
        st.session_state.whitelist.add(source)
        st.session_state.blacklist.discard(source)
        save_source_prefs()

    def add_to_blacklist(source):
        st.session_state.blacklist.add(source)
        st.session_state.whitelist.discard(source)
        save_source_prefs()

    # --- Fetch News ---
    @st.cache_data(ttl=3600)
    def get_news(query):
        url = f"https://newsapi.org/v2/everything?q={query}&from={(datetime.now() - timedelta(days=7)).date()}&sortBy=publishedAt&language=en&apiKey={NEWS_API_KEY}"
        res = requests.get(url)
        return res.json().get("articles", [])

    # --- Streamlit UI ---
    # st.set_page_config(page_title="Headline News Summarizer", layout="wide")
    st.sidebar.title("News Search")
    query = st.sidebar.text_input("Enter topic/keyword:", "")

    if st.sidebar.checkbox("Settings"):
        st.sidebar.markdown("### Source Trust Settings")
        st.sidebar.markdown("**Trusted Sources**")
        for src in sorted(st.session_state.whitelist):
            st.sidebar.text(src)
        st.sidebar.markdown("**Avoided Sources**")
        for src in sorted(st.session_state.blacklist):
            st.sidebar.text(src)

    if query:
        with st.spinner("Fetching and summarizing news..."):
            articles = get_news(query)

            for i, art in enumerate(articles[:15]):
                source = art.get("source", {}).get("name", "Unknown Source")
                if source in st.session_state.blacklist:
                    continue  # Skip blacklisted sources

                title = art.get("title")
                url = art.get("url")
                published_at = art.get("publishedAt", "")[:10]

                st.markdown(f"### [{title}]({url})")
                st.markdown(f"**Published on:** {published_at} | **Source:** {source}")

                key = f"summarize_{i}"
                if st.button("📄 Summarize Full Article", key=key):
                    full_article = extract_full_article(url)
                    if full_article:
                        summary = summarize_text(full_article)
                        st.markdown(summary)
                    else:
                        st.markdown("❗ Could not retrieve full article.")

                if source in st.session_state.whitelist:
                    st.markdown("✅ **Trusted Source**")
                else:
                    col1, col2 = st.columns(2)
                    if col1.button("👍 Trust", key=f"up_{i}"):
                        add_to_whitelist(source)
                    if col2.button("👎 Avoid", key=f"down_{i}"):
                        add_to_blacklist(source)

                st.markdown("---")
