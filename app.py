"""
Cyber Advisory Search Application

This is the main entry point for the Streamlit application. It provides a web interface
for users to search for cyber threat intelligence.

The application features:
1.  **Search Interface:** A clean, "Spotlight Search" style input for queries.
2.  **RAG Pipeline Integration:** Connects to the backend search (`src.search`) and answer generation (`src.answerer`) modules.
3.  **Custom UI:** A "Dark Mode" theme with teal accents, styled using custom CSS.
4.  **Progress Tracking:** Displays operation details and logs for transparency.

Usage:
    Run this application using streamlit:
    $ streamlit run app.py
"""

import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.search import search
from src.answerer import generate_answer
from src.logger import get_logger, progress_tracker

# Initialize logger for the frontend
logger = get_logger("app")

# -----------------------------------------------------------------------------
# 1. Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Cyber Advisory Search",
    page_icon="🛡️",
    layout="centered", # Centered layout mimics a search engine
    initial_sidebar_state="collapsed"
)

# -----------------------------------------------------------------------------
# 2. Custom CSS Styling
# -----------------------------------------------------------------------------
# Applies a "Dark Mode" theme with Teal (#00D9D9) accents.
st.markdown("""
<style>
    /* GLOBAL FONTS & BACKGROUND */
    .stApp {
        background-color: #000000;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* TYPOGRAPHY */
    h1, h2, h3 {
        color: #00D9D9 !important; /* TEAL HEADERS */
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    p, li, div {
        color: #E5E5E5; /* Off-white for readability (Professional Standard) */
        font-weight: 400;
    }

    /* REMOVE DEFAULT STREAMLIT CHROME */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* INPUT FIELD - The "Spotlight Search" Look */
    .stTextInput > div > div > input {
        background-color: #1C1C1E; /* Apple Dark Gray */
        color: #00D9D9;
        border: 1px solid #333333;
        border-radius: 12px;
        padding: 16px;
        font-size: 16px;
        transition: all 0.3s ease;
    }
    
    /* Input Focus State - Teal Glow */
    .stTextInput > div > div > input:focus {
        border-color: #00D9D9;
        box-shadow: 0 0 15px rgba(0, 217, 217, 0.3); /* Soft Neon Glow */
    }

    /* BUTTON STYLING */
    .stButton > button {
        background: linear-gradient(135deg, #00D9D9 0%, #00B8B8 100%);
        color: #000000;
        border: none;
        border-radius: 12px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        width: 100%;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0, 217, 217, 0.4);
    }

    /* RESULT CARD - "Glassmorphism" Effect */
    .result-card {
        background-color: #111111;
        border: 1px solid #333333;
        border-radius: 16px;
        padding: 30px;
        margin-top: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    
    /* EXPANDER STYLING */
    div[data-testid="stExpander"] {
        background-color: #111111;
        border: 1px solid #333;
        border-radius: 8px;
    }
    
    /* CUSTOM SCROLLBAR FOR CHROME */
    ::-webkit-scrollbar {
        width: 10px;
        background: #000;
    }
    ::-webkit-scrollbar-thumb {
        background: #333;
        border-radius: 5px;
    }

</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. UI Layout & Components
# -----------------------------------------------------------------------------

# Spacer for vertical alignment
st.write("") 
st.write("") 

# Main Header
st.markdown("<h1 style='text-align: center; margin-bottom: 10px;'>Cyber Advisory Search</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666; font-size: 14px; margin-bottom: 40px;'>INTELLIGENCE POWERED BY RAG</p>", unsafe_allow_html=True)

# Search Input Field
query = st.text_input("Search", placeholder="Search for CVEs, threat actors, or IOCs...", label_visibility="collapsed")

# Search Button (Centered using columns)
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    search_clicked = st.button("Initialize Search")

# -----------------------------------------------------------------------------
# 4. Search & Results Logic
# -----------------------------------------------------------------------------
if search_clicked and query:
    logger.info(f"🚀 User initiated search for query: '{query}'")
    
    # Create a container for progress updates to keep UI clean
    progress_container = st.container()
    
    with progress_container:
        # Step 1: Retrieve Documents
        with st.spinner("🔍 Searching database..."):
            try:
                logger.debug("Calling search backend")
                hits = search(query)
                logger.info(f"✓ Search returned {len(hits)} results")
            except Exception as e:
                logger.error(f"✗ Search failed: {e}")
                st.error(f"❌ Search Error: {e}")
                hits = {}

    if not hits:
        logger.warning("Search returned no results")
        st.warning("⚠️ No intelligence found.")
    else:
        # Step 2: Generate Answer
        with progress_container:
            with st.spinner("🧠 Analyzing with LLM..."):
                try:
                    logger.debug("Calling answer generation")
                    answer = generate_answer(query, hits)
                    logger.info("✓ Answer generation complete")
                except Exception as e:
                    logger.error(f"✗ Answer generation failed: {e}")
                    st.error(f"❌ Answer Generation Error: {e}")
                    answer = None

        # Step 3: Display Results
        if answer:
            # Render the "Intel Summary" Card
            st.markdown(f"""
            <div class="result-card">
                <h3 style="color: #00D9D9; margin-top: 0;">Intel Summary</h3>
                <div style="color: #E0E0E0; line-height: 1.6; font-size: 16px;">
                    {answer}
                </div>
                <br>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 20px; padding-top: 15px; border-top: 1px solid #333;">
                    <span style="color: #666; font-size: 12px;">📊 CONFIDENCE: HIGH</span>
                    <span style="color: #00D9D9; font-size: 12px; font-weight: bold;">✅ LIVE ADVISORY</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Show technical details in an expander
            with st.expander("📊 Operation Details"):
                summary = progress_tracker.get_summary()
                st.code(summary, language="text")
            
            logger.info("✓ Results displayed successfully")
        else:
            logger.error("Answer was None after generation")
            st.warning("Unable to generate answer")