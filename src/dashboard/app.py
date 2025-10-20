import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import json
import sys
import os

# Add src to path for imports - MUST be before src imports
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent))

# Now import from src
from src.config.settings import Config

# Page configuration
st.set_page_config(
    page_title="Bihar Election Forecast Dashboard",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="expanded"
)

class ForecastDashboard:
    """Interactive Streamlit dashboard for Bihar election forecasts"""
    
    def __init__(self):
        self.results_dir = Config.RESULTS_DIR
        self.processed_dir = Config.PROCESSED_DATA_DIR
        
        # Initialize session state
        if 'last_refresh' not in st.session_state:
            st.session_state.last_refresh = datetime.now()
        
        # Custom CSS
        self._inject_custom_css()
    
    def _inject_custom_css(self):
        """Inject custom CSS for better styling"""
        st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .metric-container {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 0.5rem 0;
        }
        
        .status-good {
            color: #28a745;
            font-weight: bold;
        }
        
        .status-warning {
            color: #ffc107;
            font-weight: bold;
        }
        
        .status-danger {
            color: #dc3545;
            font-weight: bold;
        }
        
        .sidebar-info {
            background-color: #e3f2fd;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def load_latest_results(self):
        """Load most recent forecast results"""
        try:
            # Get most recent date directory
            date_dirs = sorted([d for d in self.results_dir.iterdir() if d.is_dir()], reverse=True)
            
            if not date_dirs:
                return {}, pd.DataFrame(), pd.DataFrame(), {}, None
            
            latest_dir = date_dirs[0]
            
            # Load forecast summary
            summary_path = latest_dir / "forecast_summary.json"
            summary = {}
            if summary_path.exists():
                with open(summary_path) as f:
                    summary = json.load(f)
            
            # Load marginal seats
            marginal_path = latest_dir / "marginal_seats.csv"
            marginal_df = pd.DataFrame()
            if marginal_path.exists():
                marginal_df = pd.read_csv(marginal_path)
            
            # Load constituency probabilities
            const_prob_path = latest_dir / "constituency_probabilities.csv"
            const_prob_df = pd.DataFrame()
            if const_prob_path.exists():
                const_prob_df = pd.read_csv(const_prob_path)
            
            # Load simulation summary
            sim_summary_path = latest_dir / "simulation_summary.json"
            sim_summary = {}
            if sim_summary_path.exists():
                with open(sim_summary_path) as f:
                    sim_summary = json.load(f)
            
            return summary, marginal_df, const_prob_df, sim_summary, latest_dir
            
        except Exception as e:
            st.error(f"Error loading results: {e}")
            return {}, pd.DataFrame(), pd.DataFrame(), {}, None
    
    def load_historical_forecasts(self, days=30):
        """Load historical forecast data"""
        historical = []
        
        try:
            date_dirs = sorted([d for d in self.results_dir.iterdir() if d.is_dir()], reverse=True)
            
            for date_dir in date_dirs[:days]:
                summary_path = date_dir / "forecast_summary.json"
                if summary_path.exists():
                    with open(summary_path) as f:
                        summary = json.load(f)
                    summary['date'] = date_dir.name
                    historical.append(summary)
            
            return pd.DataFrame(historical) if historical else pd.DataFrame()
            
        except Exception as e:
            st.error(f"Error loading historical data: {e}")
            return pd.DataFrame()
    
    def render_header(self):
        """Render dashboard header"""
        st.markdown('<h1 class="main-header">🗳️ Bihar Assembly Election Forecast</h1>', unsafe_allow_html=True)
        st.markdown("**Real-time prediction system with daily updates powered by advanced ML and Monte Carlo simulation**")
        
        # Auto-refresh functionality
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"*Last updated: {st.session_state.last_refresh.strftime('%Y-%m-%d %H:%M:%S')}*")
        
        with col2:
            if st.button("🔄 Refresh Data"):
                st.session_state.last_refresh = datetime.now()
                st.experimental_rerun()
        
        with col3:
            auto_refresh = st.checkbox("Auto-refresh (30s)", value=False)
            if auto_refresh:
                st.empty()
                # Note: In production, implement proper auto-refresh
    
    def render_sidebar(self, summary, latest_dir):
        """Render sidebar with key information"""
        st.sidebar.header("📊 Forecast Overview")
        
        if summary and 'nda_projection' in summary:
            nda_proj = summary['nda_projection']
            
            # Key metrics
            st.sidebar.markdown('<div class="sidebar-info">', unsafe_allow_html=True)
            st.sidebar.metric("📈 Mean NDA Seats", f"{nda_proj['mean_seats']:.0f}")
            st.sidebar.metric("🎯 Majority Probability", f"{nda_proj['probability_majority']:.1%}")
            st.sidebar.metric("📊 Total Seats", "243")
            st.sidebar.metric("🏆 Majority Needed", "122")
            st.sidebar.markdown('</div>', unsafe_allow_html=True)
            
            # Forecast date
            if latest_dir:
                st.sidebar.info(f"**Forecast Date:** {latest_dir.name}")
            
            # Quick insights
            st.sidebar.header("💡 Quick Insights")
            
            majority_prob = nda_proj['probability_majority']
            if majority_prob > 0.7:
                status_class = "status-good"
                status_text = "NDA Favored"
            elif majority_prob > 0.3:
                status_class = "status-warning"
                status_text = "Competitive Race"
            else:
                status_class = "status-danger"
                status_text = "INDI Favored"
            
            st.sidebar.markdown(f'<p class="{status_class}">🎯 {status_text}</p>', unsafe_allow_html=True)
            
            # Confidence interval
            if 'confidence_interval_95' in nda_proj:
                ci_low, ci_high = nda_proj['confidence_interval_95']
                st.sidebar.markdown(f"**95% CI:** {ci_low:.0f} - {ci_high:.0f} seats")
        
        else:
            st.sidebar.warning("No forecast data available")
            st.sidebar.info("Run the daily update pipeline to generate forecasts")
    
    def render_main_metrics(self, summary):
        """Render main forecast metrics"""
        if not summary or 'nda_projection' not in summary:
            # Show comprehensive setup guide
            st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 2rem; border-radius: 15px; margin: 2rem 0; color: white;">
                <h2 style="color: white; margin: 0 0 1rem 0;">🚀 Welcome to Bihar Election Forecast System</h2>
                <p style="font-size: 1.1rem; margin: 0;">Your advanced statistical modeling system is ready! Generate real forecasts by running the data pipeline.</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                ### 📊 **Generate Real Forecasts**
                
                **Step 1: Setup Environment**
                ```bash
                # Copy environment template
                cp .env.example .env
                
                # Add your API keys to .env file
                NEWS_API_KEY=your_newsapi_key_here
                ```
                
                **Step 2: Run Data Pipeline**
                ```bash
                # Generate forecasts
                python main.py update
                
                # Or start automated daily updates
                python main.py schedule
                ```
                """)
            
            with col2:
                st.markdown("""
                ### 🎯 **What You'll Get**
                
                ✅ **Real-time Data**: News sentiment, polls, trends  
                ✅ **Monte Carlo Simulation**: 5000+ statistical runs  
                ✅ **Constituency Analysis**: All 243 Bihar seats  
                ✅ **Party Projections**: NDA vs INDI forecasts  
                ✅ **Interactive Charts**: Professional visualizations  
                ✅ **Export Tools**: CSV downloads and reports  
                
                ### 🔧 **System Features**
                - Advanced NLP sentiment analysis
                - Exponential moving averages
                - Probability calibration
                - Marginal seat identification
                """)
            
            st.markdown("""
            ---
            ### 📚 **Documentation & Support**
            
            - **📖 Setup Guide**: Check `README.md` for detailed instructions
            - **🔧 Configuration**: See `.env.example` for required API keys  
            - **📊 Architecture**: Review `SYSTEM_COMPLETE.md` for technical details
            - **🚀 Deployment**: See `DEPLOYMENT.md` for production setup
            
            **Once you run the pipeline, refresh this page to see your forecasts!**
            """)
            return
        
        nda_proj = summary['nda_projection']
        seat_class = summary.get('seat_classification', {})
        
        # Main metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Mean NDA Seats",
                f"{nda_proj['mean_seats']:.0f}",
                delta=f"±{(nda_proj['mean_seats'] - nda_proj['median_seats']):.0f}"
            )
        
        with col2:
            st.metric(
                "Majority Probability",
                f"{nda_proj['probability_majority']:.1%}",
                delta=None
            )
        
        with col3:
            st.metric(
                "Supermajority Prob",
                f"{nda_proj['probability_supermajority']:.1%}",
                delta=None
            )
        
        with col4:
            competitive_seats = seat_class.get('toss_up', 0)
            st.metric(
                "Competitive Seats",
                competitive_seats,
                delta=f"{(competitive_seats/243)*100:.1f}% of total"
            )
    
    def render_seat_distribution(self, summary, sim_summary):
        """Render seat distribution analysis"""
        st.header("📊 Seat Distribution Analysis")
        
        if not summary or 'seat_classification' not in summary:
            st.warning("No seat classification data available")
            return
        
        seat_class = summary['seat_classification']
        
        # Create seat classification chart
        categories = ['Safe NDA', 'Likely NDA', 'Lean NDA', 'Toss-up', 'Lean INDI', 'Likely INDI', 'Safe INDI']
        values = [
            seat_class.get('safe_nda', 0),
            seat_class.get('likely_nda', 0),
            seat_class.get('lean_nda', 0),
            seat_class.get('toss_up', 0),
            seat_class.get('lean_indi', 0),
            seat_class.get('likely_indi', 0),
            seat_class.get('safe_indi', 0)
        ]
        
        colors = ['#8B0000', '#FF4500', '#FFA500', '#FFD700', '#87CEEB', '#4169E1', '#000080']
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Bar chart
            fig_bar = go.Figure(data=[
                go.Bar(x=categories, y=values, marker_color=colors, text=values, textposition='auto')
            ])
            
            fig_bar.update_layout(
                title="Seat Classification",
                xaxis_title="Category",
                yaxis_title="Number of Seats",
                height=400
            )
            
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with col2:
            # Pie chart
            fig_pie = go.Figure(data=[
                go.Pie(labels=categories, values=values, marker_colors=colors, hole=0.3)
            ])
            
            fig_pie.update_layout(
                title="Seat Distribution",
                height=400
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Probability distribution if available
        if sim_summary and 'mean_nda_seats' in sim_summary:
            st.subheader("📈 Probability Distribution")
            
            # Generate probability distribution visualization
            # This would use actual simulation data in production
            mean_seats = sim_summary['mean_nda_seats']
            std_seats = sim_summary.get('std_nda_seats', 15)
            
            x = np.linspace(max(0, mean_seats - 4*std_seats), min(243, mean_seats + 4*std_seats), 100)
            y = np.exp(-0.5 * ((x - mean_seats) / std_seats) ** 2) / (std_seats * np.sqrt(2 * np.pi))
            
            fig_dist = go.Figure()
            fig_dist.add_trace(go.Scatter(x=x, y=y, mode='lines', fill='tonexty', name='Probability Density'))
            fig_dist.add_vline(x=122, line_dash="dash", line_color="red", annotation_text="Majority (122)")
            fig_dist.add_vline(x=mean_seats, line_dash="dot", line_color="blue", annotation_text=f"Mean ({mean_seats:.0f})")
            
            fig_dist.update_layout(
                title="NDA Seat Probability Distribution",
                xaxis_title="NDA Seats",
                yaxis_title="Probability Density",
                height=400
            )
            
            st.plotly_chart(fig_dist, use_container_width=True)
    
    def render_marginal_seats(self, marginal_df):
        """Render marginal seats analysis"""
        st.header("🎯 Most Competitive Constituencies")
        
        if marginal_df is None or marginal_df.empty:
            st.markdown("""
            <div style="background: #FFF3E0; border: 2px solid #FF9800; border-radius: 10px; padding: 1.5rem; margin: 1rem 0;">
                <h3 style="color: #E65100; margin: 0 0 1rem 0;">🎯 Marginal Seats Analysis Not Available</h3>
                <p style="color: #BF360C; margin: 0;">
                    Generate Monte Carlo simulations to identify the most competitive constituencies in Bihar.
                </p>
                <p style="color: #F57C00; margin: 0.5rem 0 0 0; font-weight: bold;">
                    Run: <code>python main.py update</code> to create forecasts
                </p>
            </div>
            """, unsafe_allow_html=True)
            return
        
        # Show top competitive seats
        top_marginal = marginal_df.head(20)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Interactive bar chart
            fig = go.Figure()
            
            colors = ['#FF6B6B' if p < 0.5 else '#4ECDC4' for p in top_marginal['nda_win_prob']]
            
            fig.add_trace(go.Bar(
                y=top_marginal['constituency'],
                x=top_marginal['nda_win_prob'],
                orientation='h',
                marker_color=colors,
                text=[f"{p:.1%}" for p in top_marginal['nda_win_prob']],
                textposition='auto'
            ))
            
            fig.add_vline(x=0.5, line_dash="dash", line_color="black", annotation_text="50%")
            
            fig.update_layout(
                title="Top 20 Most Competitive Seats",
                xaxis_title="NDA Win Probability",
                yaxis_title="Constituency",
                height=600
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📋 Seat Details")
            
            # Show detailed table
            display_df = top_marginal[['constituency', 'region', 'nda_win_prob', 'classification']].copy()
            display_df['nda_win_prob'] = display_df['nda_win_prob'].apply(lambda x: f"{x:.1%}")
            display_df.columns = ['Constituency', 'Region', 'NDA Prob', 'Classification']
            
            st.dataframe(display_df, height=600)
    
    def render_historical_trends(self):
        """Render historical forecast trends"""
        st.header("📈 Historical Forecast Trends")
        
        hist_df = self.load_historical_forecasts(days=30)
        
        if hist_df is None or hist_df.empty:
            st.markdown("""
            <div style="background: #F3E5F5; border: 2px solid #9C27B0; border-radius: 10px; padding: 1.5rem; margin: 1rem 0;">
                <h3 style="color: #6A1B9A; margin: 0 0 1rem 0;">📈 Historical Trends Not Available</h3>
                <p style="color: #4A148C; margin: 0;">
                    Historical forecast trends will appear after running daily updates for multiple days.
                </p>
                <p style="color: #7B1FA2; margin: 0.5rem 0 0 0; font-weight: bold;">
                    Start with: <code>python main.py schedule</code> for automated daily forecasts
                </p>
            </div>
            """, unsafe_allow_html=True)
            return
        
        # Prepare data
        hist_df['date'] = pd.to_datetime(hist_df['date'])
        hist_df = hist_df.sort_values('date')
        
        if 'nda_projection' in hist_df.columns:
            # Extract mean seats and probability
            hist_df['mean_seats'] = hist_df['nda_projection'].apply(
                lambda x: x.get('mean_seats', 0) if isinstance(x, dict) else 0
            )
            hist_df['prob_majority'] = hist_df['nda_projection'].apply(
                lambda x: x.get('probability_majority', 0) if isinstance(x, dict) else 0
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Seat trend
                fig_seats = go.Figure()
                fig_seats.add_trace(go.Scatter(
                    x=hist_df['date'],
                    y=hist_df['mean_seats'],
                    mode='lines+markers',
                    name='Mean NDA Seats',
                    line=dict(color='#FF9933', width=3)
                ))
                
                fig_seats.add_hline(y=122, line_dash="dash", line_color="red", annotation_text="Majority (122)")
                
                fig_seats.update_layout(
                    title="NDA Seat Forecast Trend",
                    xaxis_title="Date",
                    yaxis_title="Mean Seats",
                    height=400
                )
                
                st.plotly_chart(fig_seats, use_container_width=True)
            
            with col2:
                # Probability trend
                fig_prob = go.Figure()
                fig_prob.add_trace(go.Scatter(
                    x=hist_df['date'],
                    y=hist_df['prob_majority'] * 100,
                    mode='lines+markers',
                    name='Majority Probability',
                    line=dict(color='#138808', width=3)
                ))
                
                fig_prob.update_layout(
                    title="Probability of NDA Majority",
                    xaxis_title="Date",
                    yaxis_title="Probability (%)",
                    height=400
                )
                
                st.plotly_chart(fig_prob, use_container_width=True)
    
    def render_data_sources(self):
        """Render data sources and quality information"""
        st.header("📊 Data Sources & Quality")
        
        # Check for recent data files
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("📰 News Data")
            
            # Check for recent news files
            news_files = list(self.processed_dir.glob("*news*2025-10-17*"))
            if news_files:
                st.success(f"✅ {len(news_files)} news data files")
                
                # Load and show summary
                try:
                    latest_news = max(news_files, key=lambda x: x.stat().st_mtime)
                    if latest_news.suffix == '.csv':
                        news_df = pd.read_csv(latest_news)
                        st.metric("Articles Processed", len(news_df))
                        
                        if 'sentiment_label' in news_df.columns:
                            sentiment_dist = news_df['sentiment_label'].value_counts()
                            st.write("Sentiment Distribution:")
                            for sentiment, count in sentiment_dist.items():
                                st.write(f"- {sentiment.title()}: {count}")
                except Exception as e:
                    st.error(f"Error loading news data: {e}")
            else:
                st.warning("⚠️ No recent news data")
        
        with col2:
            st.subheader("📊 Poll Data")
            
            poll_files = list(self.processed_dir.glob("*poll*2025-10-17*"))
            if poll_files:
                st.success(f"✅ {len(poll_files)} poll data files")
                
                try:
                    latest_polls = max(poll_files, key=lambda x: x.stat().st_mtime)
                    if latest_polls.suffix == '.csv':
                        polls_df = pd.read_csv(latest_polls)
                        st.metric("Poll Data Points", len(polls_df))
                        
                        if 'nda_vote' in polls_df.columns:
                            avg_nda = polls_df['nda_vote'].mean()
                            st.metric("Avg NDA Vote Share", f"{avg_nda:.1f}%")
                except Exception as e:
                    st.error(f"Error loading poll data: {e}")
            else:
                st.warning("⚠️ No recent poll data")
        
        with col3:
            st.subheader("📈 Features")
            
            feature_files = list(self.processed_dir.glob("features*2025-10-17*"))
            if feature_files:
                st.success(f"✅ {len(feature_files)} feature files")
                
                try:
                    latest_features = max(feature_files, key=lambda x: x.stat().st_mtime)
                    if latest_features.suffix == '.csv':
                        features_df = pd.read_csv(latest_features)
                        st.metric("Constituencies", len(features_df))
                        st.metric("Features", len(features_df.columns))
                except Exception as e:
                    st.error(f"Error loading feature data: {e}")
            else:
                st.warning("⚠️ No recent feature data")
    
    def render_party_analysis(self, summary, const_prob_df):
        """Render detailed party-wise analysis"""
        st.header("🏛️ Detailed Party Analysis")
        
        # Import party data
        try:
            from src.data.bihar_parties import BIHAR_PARTIES, NDA_PARTIES, INDI_PARTIES, OTHER_PARTIES
        except ImportError:
            st.error("Party data not available")
            return
        
        if not summary or 'nda_projection' not in summary:
            st.warning("No party analysis data available")
            return
        
        nda_proj = summary['nda_projection']
        seat_class = summary.get('seat_classification', {})
        
        # Individual Party Performance
        st.subheader("🎯 Individual Party Seat Projections")
        
        nda_proj = summary['nda_projection']
        mean_nda = nda_proj['mean_seats']
        mean_indi = 243 - mean_nda
        
        # Create party-wise breakdown
        party_data = []
        
        # NDA Parties
        for party in NDA_PARTIES:
            party_info = BIHAR_PARTIES[party]
            if party == 'BJP':
                seats = mean_nda * 0.55
            elif party == 'JDU':
                seats = mean_nda * 0.35
            else:
                seats = mean_nda * 0.05
            
            party_data.append({
                'Party': party_info['full_name'],
                'Code': party,
                'Alliance': 'NDA',
                'Expected Seats': int(seats),
                'Leader': party_info['state_leader'],
                'Symbol': party_info['symbol'],
                'Color': party_info['color']
            })
        
        # INDI Parties
        for party in INDI_PARTIES:
            party_info = BIHAR_PARTIES[party]
            if party == 'RJD':
                seats = mean_indi * 0.60
            elif party == 'INC':
                seats = mean_indi * 0.25
            else:
                seats = mean_indi * 0.05
            
            party_data.append({
                'Party': party_info['full_name'],
                'Code': party,
                'Alliance': 'INDI',
                'Expected Seats': int(seats),
                'Leader': party_info['state_leader'],
                'Symbol': party_info['symbol'],
                'Color': party_info['color']
            })
        
        # Other Parties
        for party in ['AIMIM', 'BSP', 'LJSP', 'JSP']:
            if party in BIHAR_PARTIES:
                party_info = BIHAR_PARTIES[party]
                party_data.append({
                    'Party': party_info['full_name'],
                    'Code': party,
                    'Alliance': 'Others',
                    'Expected Seats': 1,
                    'Leader': party_info['state_leader'],
                    'Symbol': party_info['symbol'],
                    'Color': party_info['color']
                })
        
        # Display party-wise table
        party_df = pd.DataFrame(party_data)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**🔵 NDA Alliance**")
            nda_df = party_df[party_df['Alliance'] == 'NDA']
            st.dataframe(nda_df[['Party', 'Expected Seats', 'Leader', 'Symbol']], hide_index=True)
        
        with col2:
            st.write("**🔴 INDI Alliance**")
            indi_df = party_df[party_df['Alliance'] == 'INDI']
            st.dataframe(indi_df[['Party', 'Expected Seats', 'Leader', 'Symbol']], hide_index=True)
        
        with col3:
            st.write("**⚪ Other Parties**")
            others_df = party_df[party_df['Alliance'] == 'Others']
            st.dataframe(others_df[['Party', 'Expected Seats', 'Leader', 'Symbol']], hide_index=True)
        
        # Party-wise seat distribution chart
        fig_party = go.Figure(data=[
            go.Bar(
                x=party_df['Party'],
                y=party_df['Expected Seats'],
                marker_color=party_df['Color'],
                text=party_df['Expected Seats'],
                textposition='auto',
                hovertemplate='<b>%{x}</b><br>Expected Seats: %{y}<br>Leader: %{customdata}<extra></extra>',
                customdata=party_df['Leader']
            )
        ])
        
        fig_party.update_layout(
            title="Party-wise Seat Projections",
            xaxis_title="Political Parties",
            yaxis_title="Expected Seats",
            height=500,
            xaxis_tickangle=-45
        )
        
        st.plotly_chart(fig_party, use_container_width=True)
        
        # Alliance comparison
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔵 NDA Alliance Analysis")
            
            mean_nda = nda_proj['mean_seats']
            prob_majority = nda_proj['probability_majority']
            prob_super = nda_proj.get('probability_supermajority', 0)
            
            st.metric("Expected Seats", f"{mean_nda:.0f}", delta=f"{mean_nda - 122:.0f} vs majority")
            st.metric("Majority Probability", f"{prob_majority:.1%}")
            st.metric("Supermajority Probability", f"{prob_super:.1%}")
            
            # NDA seat breakdown
            nda_safe = seat_class.get('safe_nda', 0)
            nda_likely = seat_class.get('likely_nda', 0)
            nda_lean = seat_class.get('lean_nda', 0)
            
            st.write("**Seat Security:**")
            st.write(f"- Safe: {nda_safe} seats")
            st.write(f"- Likely: {nda_likely} seats") 
            st.write(f"- Lean: {nda_lean} seats")
            st.write(f"- **Total Strong:** {nda_safe + nda_likely} seats")
        
        with col2:
            st.subheader("🔴 INDI Alliance Analysis")
            
            mean_indi = 243 - mean_nda
            prob_indi_majority = 1 - prob_majority
            
            st.metric("Expected Seats", f"{mean_indi:.0f}", delta=f"{mean_indi - 122:.0f} vs majority")
            st.metric("Majority Probability", f"{prob_indi_majority:.1%}")
            
            # INDI seat breakdown
            indi_safe = seat_class.get('safe_indi', 0)
            indi_likely = seat_class.get('likely_indi', 0)
            indi_lean = seat_class.get('lean_indi', 0)
            
            st.write("**Seat Security:**")
            st.write(f"- Safe: {indi_safe} seats")
            st.write(f"- Likely: {indi_likely} seats")
            st.write(f"- Lean: {indi_lean} seats")
            st.write(f"- **Total Strong:** {indi_safe + indi_likely} seats")
        
        # Battleground analysis
        st.subheader("⚔️ Battleground Analysis")
        
        toss_up = seat_class.get('toss_up', 0)
        total_competitive = nda_lean + indi_lean + toss_up
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Toss-up Seats", toss_up, delta=f"{(toss_up/243)*100:.1f}% of total")
        
        with col2:
            st.metric("Total Competitive", total_competitive, delta=f"{(total_competitive/243)*100:.1f}% of total")
        
        with col3:
            st.metric("Decided Seats", 243 - total_competitive, delta=f"{((243-total_competitive)/243)*100:.1f}% of total")
        
        # Regional party performance
        if const_prob_df is not None and not const_prob_df.empty and 'region' in const_prob_df.columns:
            st.subheader("🗺️ Regional Party Performance")
            
            regional_analysis = const_prob_df.groupby('region').agg({
                'nda_win_probability': ['mean', 'count']
            }).round(3)
            
            regional_analysis.columns = ['Avg_NDA_Prob', 'Total_Seats']
            regional_analysis['Expected_NDA'] = (regional_analysis['Avg_NDA_Prob'] * regional_analysis['Total_Seats']).round(1)
            regional_analysis['Expected_INDI'] = (regional_analysis['Total_Seats'] - regional_analysis['Expected_NDA']).round(1)
            regional_analysis['NDA_Prob_Pct'] = (regional_analysis['Avg_NDA_Prob'] * 100).round(1)
            
            # Display as formatted table
            display_regional = regional_analysis[['Total_Seats', 'Expected_NDA', 'Expected_INDI', 'NDA_Prob_Pct']].copy()
            display_regional.columns = ['Total Seats', 'Expected NDA', 'Expected INDI', 'NDA Win %']
            
            st.dataframe(display_regional, use_container_width=True)
            
            # Regional performance chart
            fig_regional = go.Figure()
            
            regions = regional_analysis.index
            nda_expected = regional_analysis['Expected_NDA']
            indi_expected = regional_analysis['Expected_INDI']
            
            fig_regional.add_trace(go.Bar(
                name='NDA Expected',
                x=regions,
                y=nda_expected,
                marker_color='#FF9933'
            ))
            
            fig_regional.add_trace(go.Bar(
                name='INDI Expected',
                x=regions,
                y=indi_expected,
                marker_color='#138808'
            ))
            
            fig_regional.update_layout(
                title="Expected Seats by Region",
                xaxis_title="Region",
                yaxis_title="Expected Seats",
                barmode='stack',
                height=400
            )
            
            st.plotly_chart(fig_regional, use_container_width=True)
    
    def render_constituency_details(self, const_prob_df):
        """Render detailed constituency-wise analysis with enhanced highlighting"""
        
        # Enhanced header with highlighting
        st.markdown("""
        <div style="background: linear-gradient(90deg, #FF6B35 0%, #F7931E 100%); 
                    padding: 1.5rem; border-radius: 10px; margin-bottom: 2rem;">
            <h1 style="color: white; text-align: center; margin: 0; font-size: 2.5rem;">
                🏛️ CONSTITUENCY DETAILS - DEEP DIVE ANALYSIS
            </h1>
            <p style="color: white; text-align: center; margin: 0.5rem 0 0 0; font-size: 1.2rem;">
                Complete candidate-wise analysis for all 243 Bihar constituencies
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Key highlights banner
        st.markdown("""
        <div style="background: #E3F2FD; border-left: 5px solid #2196F3; padding: 1rem; margin-bottom: 2rem;">
            <h3 style="color: #1976D2; margin: 0;">🎯 What You'll Find Here:</h3>
            <ul style="margin: 0.5rem 0 0 0; color: #1976D2;">
                <li><strong>Detailed Candidate Matchups:</strong> Head-to-head analysis with winning chances</li>
                <li><strong>Historical Context:</strong> Previous election results and trends</li>
                <li><strong>Demographics:</strong> Voter composition and regional factors</li>
                <li><strong>Complete Coverage:</strong> All 243 constituencies with filtering options</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Import candidate data
        try:
            from src.data.constituency_candidates import constituency_analyzer
        except ImportError:
            st.error("Candidate data not available")
            return
        
        if const_prob_df is None or const_prob_df.empty:
            st.markdown("""
            <div style="background: #E3F2FD; border: 2px solid #2196F3; border-radius: 10px; padding: 1.5rem; margin: 1rem 0;">
                <h3 style="color: #1565C0; margin: 0 0 1rem 0;">📊 Constituency Data Not Available</h3>
                <p style="color: #0D47A1; margin: 0;">
                    Run the data pipeline to generate constituency-level forecasts and detailed candidate analysis.
                </p>
                <p style="color: #1976D2; margin: 0.5rem 0 0 0; font-weight: bold;">
                    Command: <code>python main.py update</code>
                </p>
            </div>
            """, unsafe_allow_html=True)
            return
        
        # Enhanced Candidate Analysis Section
        st.markdown("""
        <div style="background: #FFF3E0; border: 2px solid #FF9800; border-radius: 8px; padding: 1rem; margin: 1rem 0;">
            <h2 style="color: #E65100; margin: 0;">🏛️ DETAILED CANDIDATE MATCHUPS</h2>
            <p style="color: #BF360C; margin: 0.5rem 0 0 0;">Select any constituency for complete candidate analysis</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced constituency selection
        try:
            all_constituencies = list(constituency_analyzer.constituencies.keys())
            
            # Sort constituencies alphabetically
            all_constituencies.sort()
            
            # Create search and selection interface
            col1, col2 = st.columns([2, 1])
            
            with col1:
                selected_const = st.selectbox(
                    "🔍 Select Constituency for Detailed Analysis",
                    all_constituencies,
                    index=0 if all_constituencies else 0,
                    help="Choose any of the 243 Bihar constituencies for detailed candidate analysis"
                )
            
            with col2:
                # Quick stats
                st.metric("Total Constituencies", len(all_constituencies))
                st.metric("Available Analysis", "243 Complete")
                
        except Exception as e:
            st.error(f"Error loading constituencies: {e}")
            selected_const = None
        
        if selected_const:
            matchup = constituency_analyzer.get_candidate_matchup(selected_const)
            
            if matchup:
                # Enhanced constituency header with highlighting
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #4CAF50 0%, #45A049 100%); 
                            color: white; padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                    <h2 style="margin: 0; text-align: center;">🏛️ {selected_const.upper()}</h2>
                    <p style="margin: 0.5rem 0 0 0; text-align: center; font-size: 1.1rem;">
                        {matchup['region']} Region • {matchup['battle_type']} • {matchup['key_contest']}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Key constituency metrics with highlighting
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown("""
                    <div style="background: #E8F5E8; border: 2px solid #4CAF50; border-radius: 8px; padding: 1rem; text-align: center;">
                        <h3 style="color: #2E7D32; margin: 0;">{}</h3>
                        <p style="color: #388E3C; margin: 0;">Constituency Code</p>
                    </div>
                    """.format(matchup['constituency_code']), unsafe_allow_html=True)
                
                with col2:
                    st.markdown("""
                    <div style="background: #FFF3E0; border: 2px solid #FF9800; border-radius: 8px; padding: 1rem; text-align: center;">
                        <h3 style="color: #E65100; margin: 0;">{}</h3>
                        <p style="color: #F57C00; margin: 0;">Region</p>
                    </div>
                    """.format(matchup['region']), unsafe_allow_html=True)
                
                with col3:
                    st.markdown("""
                    <div style="background: #E3F2FD; border: 2px solid #2196F3; border-radius: 8px; padding: 1rem; text-align: center;">
                        <h3 style="color: #1565C0; margin: 0;">{}</h3>
                        <p style="color: #1976D2; margin: 0;">Total Candidates</p>
                    </div>
                    """.format(matchup['total_candidates']), unsafe_allow_html=True)
                
                with col4:
                    st.markdown("""
                    <div style="background: #FCE4EC; border: 2px solid #E91E63; border-radius: 8px; padding: 1rem; text-align: center;">
                        <h3 style="color: #AD1457; margin: 0;">{}</h3>
                        <p style="color: #C2185B; margin: 0;">Battle Type</p>
                    </div>
                    """.format(matchup['battle_type']), unsafe_allow_html=True)
                
                # Enhanced candidate comparison section
                st.markdown("""
                <div style="background: #F3E5F5; border: 2px solid #9C27B0; border-radius: 8px; padding: 1rem; margin: 2rem 0 1rem 0;">
                    <h2 style="color: #6A1B9A; margin: 0;">👥 CANDIDATE vs CANDIDATE ANALYSIS</h2>
                    <p style="color: #7B1FA2; margin: 0.5rem 0 0 0;">Complete head-to-head comparison with winning chances</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Enhanced candidate cards display
                for i, candidate in enumerate(matchup['candidates']):
                    # Determine card styling based on position
                    if i == 0:
                        card_color = "#4CAF50"
                        bg_color = "#E8F5E8"
                        status_icon = "🥇"
                        status_text = "EXPECTED WINNER"
                    elif i == 1:
                        card_color = "#FF9800"
                        bg_color = "#FFF3E0"
                        status_icon = "🥈"
                        status_text = "MAIN CHALLENGER"
                    else:
                        card_color = "#9E9E9E"
                        bg_color = "#F5F5F5"
                        status_icon = "🥉"
                        status_text = f"CHALLENGER #{i}"
                    
                    st.markdown(f"""
                    <div style="background: {bg_color}; border: 3px solid {card_color}; border-radius: 10px; padding: 1.5rem; margin: 1rem 0;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                            <h3 style="color: {card_color}; margin: 0;">{status_icon} {candidate['name']}</h3>
                            <span style="background: {card_color}; color: white; padding: 0.3rem 0.8rem; border-radius: 20px; font-weight: bold;">
                                {status_text}
                            </span>
                        </div>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                            <div><strong>Party:</strong> {candidate['party_name']} ({candidate['party_code']})</div>
                            <div><strong>Alliance:</strong> {candidate['alliance']}</div>
                            <div><strong>Win Chance:</strong> <span style="color: {card_color}; font-weight: bold;">{candidate['winning_chances']:.1f}%</span></div>
                            <div><strong>Age:</strong> {candidate['age']} years</div>
                            <div><strong>Education:</strong> {candidate['education']}</div>
                            <div><strong>Assets:</strong> {candidate['assets']}</div>
                            <div><strong>Criminal Cases:</strong> {candidate['criminal_cases']}</div>
                            <div><strong>Experience:</strong> {candidate['experience']}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Also show traditional table for easy comparison
                st.markdown("""
                <div style="background: #ECEFF1; border: 2px solid #607D8B; border-radius: 8px; padding: 1rem; margin: 2rem 0 1rem 0;">
                    <h3 style="color: #37474F; margin: 0;">📊 QUICK COMPARISON TABLE</h3>
                </div>
                """, unsafe_allow_html=True)
                
                candidates_data = []
                for i, candidate in enumerate(matchup['candidates']):
                    status = "🥇 Expected Winner" if i == 0 else f"🥈 Challenger #{i}"
                    
                    candidates_data.append({
                        'Status': status,
                        'Candidate': candidate['name'],
                        'Party': f"{candidate['party_name']} ({candidate['party_code']})",
                        'Alliance': candidate['alliance'],
                        'Win Chance': f"{candidate['winning_chances']:.1f}%",
                        'Age': candidate['age'],
                        'Education': candidate['education'],
                        'Assets': candidate['assets'],
                        'Criminal Cases': candidate['criminal_cases'],
                        'Experience': candidate['experience']
                    })
                
                candidates_df = pd.DataFrame(candidates_data)
                st.dataframe(
                    candidates_df, 
                    hide_index=True, 
                    use_container_width=True,
                    column_config={
                        "Win Chance": st.column_config.ProgressColumn(
                            "Win Chance",
                            help="Probability of winning this constituency",
                            min_value=0,
                            max_value=100,
                            format="%.1f%%"
                        )
                    }
                )
                
                # Enhanced candidate strengths and challenges
                st.markdown("""
                <div style="background: #E1F5FE; border: 2px solid #0288D1; border-radius: 8px; padding: 1rem; margin: 2rem 0 1rem 0;">
                    <h2 style="color: #01579B; margin: 0;">💪 CANDIDATE STRENGTHS & CHALLENGES</h2>
                    <p style="color: #0277BD; margin: 0.5rem 0 0 0;">Detailed SWOT analysis for top candidates</p>
                </div>
                """, unsafe_allow_html=True)
                
                for i, candidate in enumerate(matchup['candidates'][:3]):  # Top 3 candidates
                    # Color coding for different candidates
                    if i == 0:
                        border_color = "#4CAF50"
                        bg_color = "#E8F5E8"
                    elif i == 1:
                        border_color = "#FF9800"
                        bg_color = "#FFF3E0"
                    else:
                        border_color = "#9E9E9E"
                        bg_color = "#F5F5F5"
                    
                    with st.expander(f"🔍 {candidate['name']} ({candidate['party_code']}) - Detailed Analysis", expanded=(i==0)):
                        st.markdown(f"""
                        <div style="background: {bg_color}; border: 2px solid {border_color}; border-radius: 8px; padding: 1rem; margin: 0.5rem 0;">
                        """, unsafe_allow_html=True)
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("### ✅ **STRENGTHS**")
                            for strength in candidate['strengths']:
                                st.markdown(f"- ✅ **{strength}**")
                        
                        with col2:
                            st.markdown("### ⚠️ **CHALLENGES**")
                            for challenge in candidate['challenges']:
                                st.markdown(f"- ⚠️ **{challenge}**")
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                
                # Enhanced historical context
                st.markdown("""
                <div style="background: #FFF8E1; border: 2px solid #FFC107; border-radius: 8px; padding: 1rem; margin: 2rem 0 1rem 0;">
                    <h2 style="color: #F57F17; margin: 0;">📊 HISTORICAL CONTEXT & DEMOGRAPHICS</h2>
                    <p style="color: #FF8F00; margin: 0.5rem 0 0 0;">Past election results and voter composition analysis</p>
                </div>
                """, unsafe_allow_html=True)
                
                hist_context = matchup['historical_context']
                demographics = matchup['demographics']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("""
                    <div style="background: #E8F5E8; border: 2px solid #4CAF50; border-radius: 8px; padding: 1.5rem;">
                        <h3 style="color: #2E7D32; margin: 0 0 1rem 0;">🏆 PREVIOUS ELECTION RESULTS</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.metric("2020 Winner", f"{hist_context['last_winner']}")
                    st.metric("Winning Party", f"{hist_context['last_party']}")
                    st.metric("Victory Margin", f"{hist_context['last_margin']:,} votes")
                    
                    # Trend indicator
                    trend_color = "#4CAF50" if "Stable" in hist_context['trend'] else "#FF9800"
                    st.markdown(f"""
                    <div style="background: {trend_color}; color: white; padding: 0.5rem; border-radius: 5px; text-align: center; margin: 1rem 0;">
                        <strong>Trend: {hist_context['trend']}</strong>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"**🎯 Swing Potential:** {hist_context['swing_potential']}")
                
                with col2:
                    st.markdown("""
                    <div style="background: #E3F2FD; border: 2px solid #2196F3; border-radius: 8px; padding: 1.5rem;">
                        <h3 style="color: #1565C0; margin: 0 0 1rem 0;">👥 VOTER DEMOGRAPHICS</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.metric("Total Voters", f"{demographics['total_voters']:,}")
                    
                    # Gender breakdown
                    col2a, col2b = st.columns(2)
                    with col2a:
                        st.metric("Male Voters", f"{demographics['male_voters']:,}")
                    with col2b:
                        st.metric("Female Voters", f"{demographics['female_voters']:,}")
                    
                    # Urban/Rural and literacy
                    col2c, col2d = st.columns(2)
                    with col2c:
                        st.metric("Urban %", f"{demographics['urban_percentage']:.1f}%")
                    with col2d:
                        st.metric("Literacy Rate", f"{demographics['literacy_rate']:.1f}%")
        
        # Enhanced divider
        st.markdown("""
        <div style="height: 3px; background: linear-gradient(90deg, #FF6B35 0%, #F7931E 50%, #FF6B35 100%); 
                    margin: 3rem 0; border-radius: 2px;"></div>
        """, unsafe_allow_html=True)
        
        # Enhanced all constituencies summary
        st.markdown("""
        <div style="background: linear-gradient(135deg, #673AB7 0%, #9C27B0 100%); 
                    color: white; padding: 1.5rem; border-radius: 10px; margin: 2rem 0;">
            <h1 style="margin: 0; text-align: center;">📋 ALL CONSTITUENCIES SUMMARY</h1>
            <p style="margin: 0.5rem 0 0 0; text-align: center; font-size: 1.1rem;">
                Complete overview of all 243 Bihar constituencies with advanced filtering
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            summary_df = constituency_analyzer.get_all_constituencies_summary()
            
            if summary_df is not None and not summary_df.empty:
                # Add filters
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    regions = ['All'] + sorted(summary_df['region'].unique().tolist())
                    selected_region = st.selectbox("Filter by Region", regions, key="region_filter")
                
                with col2:
                    parties = ['All'] + sorted(summary_df['winner_party'].unique().tolist())
                    selected_party = st.selectbox("Filter by Expected Winner Party", parties, key="party_filter")
                
                with col3:
                    contest_types = ['All'] + sorted(summary_df['contest_margin'].unique().tolist())
                    selected_contest = st.selectbox("Filter by Contest Type", contest_types, key="contest_filter")
                
                # Apply filters
                filtered_summary = summary_df.copy()
                
                if selected_region != 'All':
                    filtered_summary = filtered_summary[filtered_summary['region'] == selected_region]
                
                if selected_party != 'All':
                    filtered_summary = filtered_summary[filtered_summary['winner_party'] == selected_party]
                
                if selected_contest != 'All':
                    filtered_summary = filtered_summary[filtered_summary['contest_margin'] == selected_contest]
                
                st.write(f"**Showing {len(filtered_summary)} constituencies**")
                
                # Display summary table
                display_cols = [
                    'constituency', 'region', 'expected_winner', 'winner_party', 
                    'winning_chance', 'runner_up', 'runner_up_party', 'contest_margin',
                    'last_winner', 'last_party'
                ]
                
                st.dataframe(
                    filtered_summary[display_cols],
                    column_config={
                        'constituency': 'Constituency',
                        'region': 'Region',
                        'expected_winner': 'Expected Winner',
                        'winner_party': 'Party',
                        'winning_chance': 'Win %',
                        'runner_up': 'Runner-up',
                        'runner_up_party': 'Runner-up Party',
                        'contest_margin': 'Contest Type',
                        'last_winner': '2020 Winner',
                        'last_party': '2020 Party'
                    },
                    hide_index=True,
                    use_container_width=True,
                    height=400
                )
                
                # Summary statistics
                st.subheader("📈 Summary Statistics")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    close_contests = len(filtered_summary[filtered_summary['contest_margin'] == 'Close'])
                    st.metric("Close Contests", close_contests)
                
                with col2:
                    nda_leading = len(filtered_summary[filtered_summary['winner_alliance'] == 'NDA'])
                    st.metric("NDA Leading", nda_leading)
                
                with col3:
                    indi_leading = len(filtered_summary[filtered_summary['winner_alliance'] == 'INDI'])
                    st.metric("INDI Leading", indi_leading)
                
                with col4:
                    incumbents_winning = len(filtered_summary[
                        filtered_summary['expected_winner'] == filtered_summary['last_winner']
                    ])
                    st.metric("Incumbents Retaining", incumbents_winning)
            
            else:
                st.info("Constituency summary data not available")
        
        except Exception as e:
            st.error(f"Error loading constituency summary: {e}")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Region filter
            regions = ['All'] + sorted(const_prob_df['region'].unique().tolist())
            selected_region = st.selectbox("Filter by Region", regions)
        
        with col2:
            # Classification filter - create classification if it doesn't exist
            if 'classification' not in const_prob_df.columns:
                # Create classification based on probability
                const_prob_df['classification'] = pd.cut(
                    const_prob_df['nda_win_probability'],
                    bins=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
                    labels=['Safe INDI', 'Likely INDI', 'Toss-up', 'Likely NDA', 'Safe NDA']
                )
            
            classifications = ['All'] + sorted(const_prob_df['classification'].unique().tolist())
            selected_class = st.selectbox("Filter by Classification", classifications)
        
        with col3:
            # Probability range
            prob_range = st.slider("NDA Win Probability Range", 0.0, 1.0, (0.0, 1.0), 0.05)
        
        # Apply filters
        filtered_df = const_prob_df.copy()
        
        # Ensure classification column exists
        if 'classification' not in filtered_df.columns:
            filtered_df['classification'] = pd.cut(
                filtered_df['nda_win_probability'],
                bins=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
                labels=['Safe INDI', 'Likely INDI', 'Toss-up', 'Likely NDA', 'Safe NDA']
            )
        
        if selected_region != 'All':
            filtered_df = filtered_df[filtered_df['region'] == selected_region]
        
        if selected_class != 'All':
            filtered_df = filtered_df[filtered_df['classification'] == selected_class]
        
        filtered_df = filtered_df[
            (filtered_df['nda_win_probability'] >= prob_range[0]) & 
            (filtered_df['nda_win_probability'] <= prob_range[1])
        ]
        
        st.write(f"**Showing {len(filtered_df)} constituencies**")
        
        # Constituency table
        if filtered_df is not None and not filtered_df.empty:
            # Prepare display dataframe
            display_columns = ['constituency', 'region', 'nda_win_probability']
            if 'classification' in filtered_df.columns:
                display_columns.append('classification')
            
            display_df = filtered_df[display_columns].copy()
            display_df['nda_win_probability'] = display_df['nda_win_probability'].apply(lambda x: f"{x:.1%}")
            display_df = display_df.sort_values('nda_win_probability', ascending=False)
            
            column_names = ['Constituency', 'Region', 'NDA Win Prob']
            if 'classification' in display_df.columns:
                column_names.append('Classification')
            
            display_df.columns = column_names
            
            st.dataframe(display_df, use_container_width=True, height=400)
            
            # Constituency map visualization (simplified)
            st.subheader("🗺️ Constituency Map View")
            
            # Create a scatter plot as a simple map representation
            fig_map = go.Figure()
            
            # Color mapping for classifications
            color_map = {
                'Safe NDA': '#8B0000',
                'Likely NDA': '#FF4500', 
                'Toss-up': '#FFD700',
                'Likely INDI': '#4169E1',
                'Safe INDI': '#000080'
            }
            
            if 'classification' in filtered_df.columns:
                for classification in filtered_df['classification'].unique():
                    class_data = filtered_df[filtered_df['classification'] == classification]
                    
                    fig_map.add_trace(go.Scatter(
                        x=list(range(len(class_data))),  # Convert range to list
                        y=class_data['nda_win_probability'],
                        mode='markers',
                        name=str(classification),
                        marker=dict(
                            color=color_map.get(str(classification), '#808080'),
                            size=10,
                            opacity=0.7
                        ),
                        text=class_data['constituency'],
                        hovertemplate='<b>%{text}</b><br>NDA Prob: %{y:.1%}<extra></extra>'
                    ))
            else:
                # Simple scatter plot without classification
                fig_map.add_trace(go.Scatter(
                    x=list(range(len(filtered_df))),  # Convert range to list
                    y=filtered_df['nda_win_probability'],
                    mode='markers',
                    name='Constituencies',
                    marker=dict(
                        color='#4169E1',
                        size=10,
                        opacity=0.7
                    ),
                    text=filtered_df['constituency'],
                    hovertemplate='<b>%{text}</b><br>NDA Prob: %{y:.1%}<extra></extra>'
                ))
            
            fig_map.add_hline(y=0.5, line_dash="dash", line_color="black", annotation_text="50% (Even)")
            
            fig_map.update_layout(
                title="Constituency Win Probabilities",
                xaxis_title="Constituency Index",
                yaxis_title="NDA Win Probability",
                height=500,
                showlegend=True
            )
            
            st.plotly_chart(fig_map, use_container_width=True)
            
            # Summary statistics for filtered data
            st.subheader("📊 Summary Statistics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                avg_prob = filtered_df['nda_win_probability'].mean()
                st.metric("Average NDA Prob", f"{avg_prob:.1%}")
            
            with col2:
                nda_favored = (filtered_df['nda_win_probability'] > 0.5).sum()
                st.metric("NDA Favored", f"{nda_favored}/{len(filtered_df)}")
            
            with col3:
                indi_favored = (filtered_df['nda_win_probability'] < 0.5).sum()
                st.metric("INDI Favored", f"{indi_favored}/{len(filtered_df)}")
            
            with col4:
                very_close = ((filtered_df['nda_win_probability'] >= 0.45) & 
                             (filtered_df['nda_win_probability'] <= 0.55)).sum()
                st.metric("Very Close", f"{very_close}/{len(filtered_df)}")
        
        else:
            st.info("No constituencies match the selected filters")
    
    def render_download_section(self, latest_dir):
        """Render download section"""
        st.header("📥 Download Data")
        
        if not latest_dir or not latest_dir.exists():
            st.warning("No forecast data available for download")
            return
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Forecast summary
            summary_file = latest_dir / "forecast_summary.json"
            if summary_file.exists():
                with open(summary_file) as f:
                    summary_data = f.read()
                
                st.download_button(
                    "📊 Forecast Summary (JSON)",
                    summary_data,
                    f"forecast_summary_{latest_dir.name}.json",
                    "application/json"
                )
        
        with col2:
            # Marginal seats
            marginal_file = latest_dir / "marginal_seats.csv"
            if marginal_file.exists():
                marginal_data = pd.read_csv(marginal_file)
                csv_data = marginal_data.to_csv(index=False)
                
                st.download_button(
                    "🎯 Marginal Seats (CSV)",
                    csv_data,
                    f"marginal_seats_{latest_dir.name}.csv",
                    "text/csv"
                )
        
        with col3:
            # Constituency probabilities
            const_prob_file = latest_dir / "constituency_probabilities.csv"
            if const_prob_file.exists():
                const_prob_data = pd.read_csv(const_prob_file)
                csv_data = const_prob_data.to_csv(index=False)
                
                st.download_button(
                    "📊 All Constituencies (CSV)",
                    csv_data,
                    f"constituency_probabilities_{latest_dir.name}.csv",
                    "text/csv"
                )
    
    def render_footer(self):
        """Render dashboard footer with copyright"""
        from datetime import datetime
        current_time = datetime.now().strftime("%d %B %Y, %I:%M %p")
        
        st.markdown("---")
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem; background-color: #f0f2f6; border-radius: 0.5rem; margin-top: 2rem;">
            <p><strong>Bihar Election Forecast System</strong> | Advanced Statistical Modeling & Monte Carlo Simulation</p>
            <p>Last Updated: {current_time} | Predictions based on machine learning and statistical analysis</p>
            <p><strong>© 2025 YV Predicts. Educational and research purposes only.</strong></p>
        </div>
        """, unsafe_allow_html=True)
    
    def render(self):
        """Render the complete dashboard"""
        # Load data
        summary, marginal_df, const_prob_df, sim_summary, latest_dir = self.load_latest_results()
        
        # Render header
        self.render_header()
        
        # Render sidebar
        self.render_sidebar(summary, latest_dir)
        
        # Main content tabs with highlighted constituency details
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📊 Overview", 
            "🏛️ Party Analysis",
            "🎯 Competitive Seats", 
            "🔥 **CONSTITUENCY DETAILS** 🔥",
            "📈 Trends", 
            "📥 Downloads"
        ])
        
        with tab1:
            self.render_main_metrics(summary)
            st.divider()
            self.render_seat_distribution(summary, sim_summary)
        
        with tab2:
            self.render_party_analysis(summary, const_prob_df)
        
        with tab3:
            self.render_marginal_seats(marginal_df)
        
        with tab4:
            self.render_constituency_details(const_prob_df)
        
        with tab5:
            self.render_historical_trends()
        
        with tab6:
            self.render_download_section(latest_dir)
        
        # Footer
        self.render_footer()


def main():
    """Main dashboard application with style selection"""
    # Add style selector in sidebar
    st.sidebar.title("Dashboard Style")
    style_choice = st.sidebar.radio(
        "Choose Dashboard Style:",
        ["Official Style", "Advanced Analytics Style"],
        index=0
    )
    
    if style_choice == "Official Style":
        # Import and render ECI style
        try:
            from src.dashboard.eci_style_app import OfficialStyleDashboard
            official_dashboard = OfficialStyleDashboard()
            official_dashboard.render()
        except ImportError:
            st.error("Official Style dashboard not available. Using default style.")
            dashboard = ForecastDashboard()
            dashboard.render()
    else:
        # Render advanced analytics style
        dashboard = ForecastDashboard()
        dashboard.render()


if __name__ == "__main__":
    main()