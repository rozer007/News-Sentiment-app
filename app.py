import streamlit as st
import os
import base64
import pandas as pd
import requests
from datetime import datetime
import plotly.graph_objects as go

# API Configuration
API_URL = "http://localhost:8000"  # URL for the FastAPI service
USE_API = True  # Set to False to use direct file access instead of API

# Set page configuration
st.set_page_config(
    page_title="News Sentiment Analysis",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
    }
    .company-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .last-updated {
        font-size: 0.8rem;
        color: #666;
        font-style: italic;
    }
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .sentiment-badge {
        padding: 0.3rem 0.8rem;
        border-radius: 2rem;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 1rem;
    }
    .sentiment-badge.positive {
        background-color: #d4edda;
        color: #155724;
    }
    .sentiment-badge.negative {
        background-color: #f8d7da;
        color: #721c24;
    }
    .sentiment-badge.neutral {
        background-color: #e2e3e5;
        color: #383d41;
    }
    .sentiment-badge.mixed {
        background-color: #fff3cd;
        color: #856404;
    }
    .sentiment-value {
        font-size: 1.5rem;
        font-weight: bold;
    }
    .article-card {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border: 1px solid #e0e0e0;
    }
    .article-title {
        font-weight: bold;
        font-size: 1.1rem;
    }
    hr {
        margin-top: 2rem;
        margin-bottom: 2rem;
    }
    .tab-content {
        padding: 1rem;
    }
    .stMetric {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
if 'analysis_running' not in st.session_state:
    st.session_state.analysis_running = False
if 'api_available' not in st.session_state:
    st.session_state.api_available = False


# Check API availability
@st.cache_data(ttl=60)
def check_api_availability():
    """Check if the API is available"""
    if not USE_API:
        return False

    try:
        response = requests.get(f"{API_URL}/", timeout=2)
        return response.status_code == 200
    except:
        return False


# Load company list
@st.cache_data(ttl=600)
def load_company_list():
    """Load the list of companies from API or local CSV"""
    if USE_API and check_api_availability():
        try:
            response = requests.get(f"{API_URL}/companies", timeout=5)
            if response.status_code == 200:
                companies = response.json().get("companies", [])
                return pd.DataFrame(companies)
        except Exception as e:
            st.error(f"Error fetching company list from API: {e}")

    # Fallback to local file
    try:
        csv_path = os.path.join('data', 'company_list.csv')
        if os.path.exists(csv_path):
            return pd.read_csv(csv_path)
        else:
            st.error(f"Company list file not found at {csv_path}")
            return pd.DataFrame(columns=['name', 'ticker'])
    except Exception as e:
        st.error(f"Error loading company list: {e}")
        return pd.DataFrame(columns=['name', 'ticker'])


# Load sentiment data
@st.cache_data(ttl=300)
def load_sentiment_data(company_name):
    """Load sentiment data for a specific company from API or local pickle"""
    if USE_API and check_api_availability():
        try:
            response = requests.get(
                f"{API_URL}/sentiment/{company_name}",
                params={"generate_tts":True},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                st.warning(f"API error: {response.text}. Falling back to local files.")
        except Exception as e:
            st.warning(f"Could not fetch data from API, falling back to local files: {e}")

    # Fallback to local file
    try:
        file_path = os.path.join('data', 'output', f"{company_name.lower().replace(' ', '_')}.pkl")
        if not os.path.exists(file_path):
            return None

        with open(file_path, 'rb') as f:
            import pickle
            return pickle.load(f)
    except Exception as e:
        st.error(f"Error loading sentiment data: {e}")
        return None


# Get audio content
def get_audio_content(company_name):
    """Get audio content for a company from API or local file"""
    if USE_API and check_api_availability():
        try:
            response = requests.get(f"{API_URL}/audio/{company_name}", stream=True)
            if response.status_code == 200:
                return response.content
        except Exception as e:
            st.warning(f"Error fetching audio from API: {e}. Trying local file.")

    # Fallback to local file
    sentiment_data = load_sentiment_data(company_name)
    if sentiment_data and "Audio_Path" in sentiment_data:
        audio_path = sentiment_data["Audio_Path"]
        if os.path.exists(audio_path):
            with open(audio_path, 'rb') as f:
                return f.read()

    return None


# Run analysis (immediate, synchronous)
def run_analysis(company_name):
    """Refresh data for a company by forcibly fetching from the latest pickle file"""
    if not USE_API or not check_api_availability():
        st.error("API is not available. Please start the API server.")
        return None

    try:
        with st.spinner(f"Fetching data for {company_name}..."):
            response = requests.get(
                f"{API_URL}/sentiment/{company_name}",
                params={"generate_tts":True},
                timeout=10
            )

            if response.status_code == 200:
                st.success("Data loaded successfully!")
                # Clear cache to ensure fresh data is loaded
                load_sentiment_data.clear()
                return response.json()
            elif response.status_code == 404:
                st.error(f"No data found for {company_name}.")
                return None
            else:
                st.error(f"API Error: {response.text}")
                return None
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None
    finally:
        st.session_state.analysis_running = False


# Format timestamp
def format_timestamp(timestamp_str):
    """Format timestamp for display"""
    if not timestamp_str:
        return "Unknown"

    try:
        dt = datetime.fromisoformat(timestamp_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp_str


# Generate HTML for audio playback
def get_audio_html(audio_content):
    """Generate HTML for audio playback"""
    if not audio_content:
        return None

    audio_b64 = base64.b64encode(audio_content).decode()
    return f"""
    <audio controls>
      <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
      Your browser does not support the audio element.
    </audio>
    """



def main():
    """Main Streamlit application"""

    # Check API availability on startup
    check_api_availability()
    st.session_state.api_available = check_api_availability()
    sentiment_data={}

    # Sidebar
    with st.sidebar:
        st.title("News Sentiment Analysis")

        # API status indicator
        if USE_API:
            if st.session_state.api_available:
                st.success("API is connected")
            # else:
            #     st.error("API is not available")
            #     st.info("Please start the API server with: `python api.py`")

        # Load company list
        companies_df = load_company_list()

        if companies_df.empty:
            st.warning("No companies found. Please check your data/company_list.csv file.")
            return

        # Company selection
        st.subheader("Select Company")
        company_names = companies_df['name'].tolist()

        company_name = st.selectbox("Company", company_names)
        # Load the data with freshness controls

        if st.button("Get Analysis", type="primary"):
            data_loading = st.empty()
            data_loading.info("Loading sentiment data...")
            result = load_sentiment_data(
                company_name
            )
            if result:
                sentiment_data = result
                data_loading.empty()
                # st.rerun()
            else:
                st.error("No data files found for this company.")

    # Main content area
    st.markdown('<div class="main-header">News Sentiment Analysis Dashboard</div>', unsafe_allow_html=True)

    # Create tabs for the entire content area
    main_tabs = st.tabs(["Company Analysis"])

    with main_tabs[0]:
        # Load data for selected company
        if 'company_name' in locals() and company_name:
            # Show loading message
            data_loading = st.empty()
            data_loading.info("Loading sentiment data...")

            # Load the data with freshness controls
            # sentiment_data = load_sentiment_data(
            #     company_name
            # )

            # Clear the loading message
            data_loading.empty()

            if sentiment_data:
                # print(sentiment_data)
                # Display company header with ticker
                st.markdown(f'<div class="company-header">{company_name}</div>', unsafe_allow_html=True)


                # Create tabs for different views
                tabs = st.tabs(["Overall Sentiment", "News Articles", "Comparative Analysis"])

                # Tab 1: Overall Sentiment
                with tabs[0]:
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        # Display final sentiment analysis
                        st.subheader("Final Sentiment Analysis")
                        final_sentiment = sentiment_data.get("Final Sentiment Analysis",
                                                             "No sentiment analysis available")
                        st.info(final_sentiment)

                        # Display Hindi translation if available
                        if "Hindi_Translation" in sentiment_data and sentiment_data["Hindi_Translation"]:
                            st.subheader("Hindi Translation")
                            st.write(sentiment_data["Hindi_Translation"])

                        # Display audio if available
                        st.subheader("Audio Summary (Hindi)")
                        audio_content = get_audio_content(company_name)
                        if audio_content:
                            audio_html = get_audio_html(audio_content)
                            if audio_html:
                                st.markdown(audio_html, unsafe_allow_html=True)
                        else:
                            st.warning("Audio not available.")

                    with col2:
                        # Display sentiment distribution chart
                        st.subheader("Sentiment Distribution")
                        dist = sentiment_data.get("Comparative Sentiment Score", {}).get("Sentiment Distribution", {})

                        if dist:
                            # Create pie chart
                            fig = go.Figure(data=[go.Pie(
                                labels=list(dist.keys()),
                                values=list(dist.values()),
                                hole=.3,
                                # marker_colors=['#28a745', '#dc3545', '#6c757d']
                            )])
                            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
                            st.plotly_chart(fig, use_container_width=True)

                            # Show counts
                            total = sum(dist.values())
                            if total > 0:
                                pos_pct = dist.get('Positive', 0) / total * 100 if total > 0 else 0
                                neg_pct = dist.get('Negative', 0) / total * 100 if total > 0 else 0
                                neu_pct = dist.get('Neutral', 0) / total * 100 if total > 0 else 0

                                col1, col2, col3 = st.columns(3)

                                # col1.metric("Temperature", "70 °F", "1.2 °F")
                                # col1.metric(st.markdown("Positive"), dist.get('Positive', 0),f"{pos_pct:.1f}%")
                                # col2.metric("Negative", dist.get('Negative', 0), f"{neg_pct:.1f}%")
                                # col3.metric("Neutral", dist.get('Neutral', 0), f"{neu_pct:.1f}%")

                # Tab 2: News Articles
                with tabs[1]:
                    st.subheader("News Articles")
                    articles = sentiment_data.get("Articles", [])

                    if articles:
                        for i, article in enumerate(articles):
                            with st.expander(f"{i + 1}. {article.get('Title', 'No Title')}"):
                                # Display sentiment badge
                                st.markdown(
                                    article.get('Sentiment', 'Unknown'),
                                    unsafe_allow_html=True
                                )

                                # Display summary
                                if 'Summary' in article:
                                    st.markdown("**Summary:**")
                                    st.markdown(article['Summary'])

                                # Display topics
                                if 'Topics' in article and article['Topics']:
                                    st.markdown("**Topics:**")
                                    topics_html = " ".join(
                                        [f'<span class="sentiment-badge neutral">{topic}</span>' for topic in
                                         article['Topics']])
                                    st.markdown(topics_html, unsafe_allow_html=True)

                                # Display URL if available
                                if 'URL' in article and article['URL']:
                                    st.markdown(f"[Read original article]({article['URL']})")
                    else:
                        st.info("No news articles available for this company.")

                # Tab 3: Comparative Analysis
                with tabs[2]:
                    st.subheader("Comparative Analysis")
                    comparative = sentiment_data.get("Comparative Sentiment Score", {})

                    if comparative:
                        # Topic overlap
                        st.subheader("Topic Overlap")
                        topic_overlap = comparative.get("Topic Overlap", {})

                        if topic_overlap:
                            # Common topics
                            common_topics = topic_overlap.get("Common Topics", [])
                            if common_topics:
                                st.markdown("**Common Topics Across Articles:**")
                                common_html = " ".join(
                                    [f'<span class="sentiment-badge positive">{topic}</span>' for topic in
                                     common_topics])
                                st.markdown(common_html, unsafe_allow_html=True)
                            else:
                                st.markdown("No common topics found across articles.")

                            # Get all unique topics by article
                            st.markdown("**Unique Topics by Article:**")
                            unique_topics = {k: v for k, v in topic_overlap.items() if k != "Common_Topics"}
                            if unique_topics:
                                for article, topics in unique_topics.items():
                                    if topics:
                                        st.markdown(f"**{article}:**")
                                        topics_html = " ".join(
                                            [f'<span class="sentiment-badge neutral">{topic}</span>' for topic in
                                             topics])
                                        st.markdown(topics_html, unsafe_allow_html=True)

                        # Coverage differences
                        st.subheader("Coverage Differences")
                        differences = comparative.get("Coverage Differences", [])
                        if differences:
                            for diff in differences:
                                st.markdown("""> Comparision""")
                                st.markdown(""" ->  """f"**{diff.get('Comparison', '')}**")
                                st.markdown("""> Impact""")
                                st.markdown(""" ->  """f"**{diff.get('Impact', '')}**")
                        else:
                            st.markdown("No significant coverage differences detected.")
                    else:
                        st.info("No comparative analysis available for this company.")
            else:
                st.warning(f"Please run an analysis first to show sentiment data available for {company_name}")
        else:
            st.info("Please select a company from the sidebar to view sentiment analysis.")


if __name__ == "__main__":
    main() 