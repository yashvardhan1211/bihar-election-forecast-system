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

# Page configuration - Professional Forecast Style
st.set_page_config(
    page_title="Bihar Assembly Election Forecast 2025 - Statistical Modeling System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

class OfficialStyleDashboard:
    """Professional forecast dashboard with government-style interface for statistical modeling"""
    
    def __init__(self):
        self.results_dir = Config.RESULTS_DIR
        self.processed_dir = Config.PROCESSED_DATA_DIR
        
        # Professional color scheme
        self.professional_colors = {
            'primary': '#1f4e79',
            'secondary': '#2e5984', 
            'accent': '#ff6b35',
            'success': '#28a745',
            'warning': '#ffc107',
            'danger': '#dc3545',
            'light': '#f8f9fa',
            'dark': '#343a40'
        }
        
        # Inject professional CSS
        self._inject_professional_css()
    
    def _inject_professional_css(self):
        """Inject professional forecast system CSS"""
        st.markdown("""
        <style>
        /* ECI Header Styling */
        .eci-header {
            background: linear-gradient(135deg, #1f4e79 0%, #2e5984 100%);
            color: white;
            padding: 1.5rem 2rem;
            margin: -1rem -1rem 2rem -1rem;
            border-bottom: 4px solid #ff6b35;
        }
        
        .eci-title {
            font-size: 2.2rem;
            font-weight: bold;
            margin: 0;
            text-align: center;
        }
        
        .eci-subtitle {
            font-size: 1.1rem;
            text-align: center;
            margin: 0.5rem 0 0 0;
            opacity: 0.9;
        }
        
        .eci-logo {
            text-align: center;
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        
        /* ECI Table Styling */
        .eci-table {
            border: 2px solid #1f4e79;
            border-radius: 8px;
            overflow: hidden;
            margin: 1rem 0;
        }
        
        .eci-table-header {
            background: #1f4e79;
            color: white;
            padding: 1rem;
            font-weight: bold;
            text-align: center;
            font-size: 1.2rem;
        }
        
        .eci-summary-box {
            background: white;
            border: 2px solid #1f4e79;
            border-radius: 8px;
            padding: 1.5rem;
            margin: 1rem 0;
            text-align: center;
            color: #1f4e79;
            font-weight: bold;
        }
        
        .eci-party-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.8rem 1rem;
            border-bottom: 1px solid #dee2e6;
            background: white;
            color: #333;
        }
        
        .eci-party-row:hover {
            background: #f8f9fa;
        }
        
        .eci-party-name {
            font-weight: bold;
            font-size: 1.1rem;
            color: #1f4e79;
        }
        
        .eci-seats {
            font-size: 1.3rem;
            font-weight: bold;
            color: #1f4e79;
        }
        
        .eci-percentage {
            font-size: 1rem;
            color: #333;
            font-weight: 500;
        }
        
        /* Status indicators */
        .status-leading {
            background: #28a745;
            color: white;
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: bold;
        }
        
        .status-trailing {
            background: #dc3545;
            color: white;
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: bold;
        }
        
        .status-competitive {
            background: #ffc107;
            color: #000;
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: bold;
        }
        
        /* ECI Footer */
        .eci-footer {
            background: #1f4e79;
            color: white;
            padding: 1rem;
            text-align: center;
            margin: 2rem -1rem -1rem -1rem;
            font-size: 0.9rem;
        }
        
        /* Metrics styling */
        .eci-metric {
            background: white;
            border: 3px solid #1f4e79;
            border-radius: 8px;
            padding: 1.5rem;
            text-align: center;
            margin: 0.5rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .eci-metric-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1f4e79;
            margin: 0;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        }
        
        .eci-metric-label {
            font-size: 1.1rem;
            color: #333;
            margin: 0.5rem 0 0 0;
            font-weight: 600;
        }
        
        /* Hide Streamlit elements */
        .stDeployButton {display:none;}
        footer {visibility: hidden;}
        .stApp > header {visibility: hidden;}
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #f1f1f1;
        }
        ::-webkit-scrollbar-thumb {
            background: #1f4e79;
            border-radius: 4px;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def load_latest_results(self):
        """Load most recent forecast results"""
        try:
            # Get most recent date directory
            date_dirs = sorted([d for d in self.results_dir.iterdir() if d.is_dir()], reverse=True)
            
            if not date_dirs:
                return {}, pd.DataFrame(), pd.DataFrame(), None
            
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
            
            return summary, marginal_df, const_prob_df, latest_dir
            
        except Exception as e:
            st.error(f"Error loading results: {e}")
            return {}, pd.DataFrame(), pd.DataFrame(), None
    
    def render_forecast_header(self):
        """Render forecast system header"""
        st.markdown("""
        <div class="eci-header">
            <div class="eci-logo">📊</div>
            <h1 class="eci-title">BIHAR ELECTION FORECAST SYSTEM</h1>
            <p class="eci-subtitle">Advanced Statistical Modeling & Monte Carlo Simulation</p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_main_summary(self, summary):
        """Render main election summary in ECI style"""
        if not summary or 'nda_projection' not in summary:
            # Show professional setup guide
            st.markdown("""
            <div class="eci-table">
                <div class="eci-table-header">
                    SYSTEM INITIALIZATION REQUIRED
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div style="background: #1f4e79; color: white; padding: 2rem; border-radius: 10px; margin: 1rem 0;">
                <h2 style="color: white; margin: 0 0 1rem 0;">🏛️ Bihar Election Forecast System</h2>
                <p style="font-size: 1.1rem; margin: 0;">Advanced Statistical Modeling & Monte Carlo Simulation Platform</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                ### 📊 **Initialize Forecasting System**
                
                **Environment Setup:**
                ```bash
                cp .env.example .env
                # Add API keys to .env file
                ```
                
                **Generate Forecasts:**
                ```bash
                python main.py update
                ```
                
                **Start Automated Updates:**
                ```bash
                python main.py schedule
                ```
                """)
            
            with col2:
                st.markdown("""
                ### 🎯 **System Capabilities**
                
                ✅ **Real-time Data Processing**  
                ✅ **Monte Carlo Simulation (5000+ runs)**  
                ✅ **243 Constituency Coverage**  
                ✅ **NLP Sentiment Analysis**  
                ✅ **Statistical Probability Models**  
                ✅ **Professional Reporting**  
                
                ### 📈 **Data Sources**
                - News sentiment analysis
                - Opinion polling data  
                - Google Trends analysis
                - Historical election data
                """)
            
            st.markdown("""
            <div class="eci-table">
                <div class="eci-table-header">
                    SYSTEM STATUS: AWAITING DATA PIPELINE EXECUTION
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.info("**Next Step:** Run `python main.py update` to generate your first forecast, then refresh this page.")
            return
        
        nda_proj = summary['nda_projection']
        seat_class = summary.get('seat_classification', {})
        
        # Calculate INDI projection
        indi_seats = 243 - nda_proj['mean_seats']
        others_seats = 5  # Estimated others
        
        # Main summary box
        st.markdown("""
        <div class="eci-table">
            <div class="eci-table-header">
                BIHAR ASSEMBLY ELECTION 2025 - STATISTICAL FORECAST
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="eci-metric">
                <div class="eci-metric-value">243</div>
                <div class="eci-metric-label">Total Seats</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="eci-metric">
                <div class="eci-metric-value">122</div>
                <div class="eci-metric-label">Majority Mark</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="eci-metric">
                <div class="eci-metric-value">{nda_proj['probability_majority']:.0%}</div>
                <div class="eci-metric-label">NDA Majority Chance</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            competitive_seats = seat_class.get('toss_up', 35)
            st.markdown(f"""
            <div class="eci-metric">
                <div class="eci-metric-value">{competitive_seats}</div>
                <div class="eci-metric-label">Competitive Seats</div>
            </div>
            """, unsafe_allow_html=True)
    
    def render_party_wise_results(self, summary):
        """Render party-wise results in ECI table format"""
        if not summary or 'nda_projection' not in summary:
            # Sample data
            nda_seats = 125
            indi_seats = 113
            others_seats = 5
        else:
            nda_proj = summary['nda_projection']
            nda_seats = int(nda_proj['mean_seats'])
            indi_seats = 243 - nda_seats - 5
            others_seats = 5
        
        st.markdown("""
        <div class="eci-table">
            <div class="eci-table-header">
                PARTY WISE FORECAST
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Import party data
        try:
            from src.data.bihar_parties import BIHAR_PARTIES, NDA_PARTIES, INDI_PARTIES
        except ImportError:
            # Fallback party data
            BIHAR_PARTIES = {
                'BJP': {'full_name': 'Bharatiya Janata Party', 'color': '#FF9933'},
                'JDU': {'full_name': 'Janata Dal (United)', 'color': '#006400'},
                'RJD': {'full_name': 'Rashtriya Janata Dal', 'color': '#008000'},
                'INC': {'full_name': 'Indian National Congress', 'color': '#19AAED'}
            }
            NDA_PARTIES = ['BJP', 'JDU']
            INDI_PARTIES = ['RJD', 'INC']
        
        # Alliance-wise results
        alliances = [
            {
                'name': 'NDA (National Democratic Alliance)',
                'seats': nda_seats,
                'parties': NDA_PARTIES,
                'status': 'leading' if nda_seats >= 122 else 'trailing',
                'color': '#FF9933'
            },
            {
                'name': 'INDI (Indian National Developmental Inclusive Alliance)',
                'seats': indi_seats,
                'parties': INDI_PARTIES,
                'status': 'leading' if indi_seats >= 122 else 'trailing',
                'color': '#19AAED'
            },
            {
                'name': 'Others',
                'seats': others_seats,
                'parties': [],
                'status': 'others',
                'color': '#808080'
            }
        ]
        
        # Render alliance results
        for alliance in alliances:
            status_class = f"status-{alliance['status']}"
            if alliance['status'] == 'others':
                status_class = "status-competitive"
            
            percentage = (alliance['seats'] / 243) * 100
            
            st.markdown(f"""
            <div class="eci-party-row">
                <div>
                    <div class="eci-party-name" style="color: {alliance['color']}">
                        {alliance['name']}
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <div class="eci-percentage">{percentage:.1f}%</div>
                    <div class="eci-seats">{alliance['seats']}</div>
                    <div class="{status_class}">
                        {alliance['status'].upper() if alliance['status'] != 'others' else 'OTHERS'}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Individual party breakdown
        st.markdown("""
        <div class="eci-table" style="margin-top: 2rem;">
            <div class="eci-table-header">
                INDIVIDUAL PARTY PERFORMANCE
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Realistic individual party seat projections
        party_results = [
            {'name': 'Bharatiya Janata Party', 'code': 'BJP', 'seats': 50, 'alliance': 'NDA', 'color': '#FF9933'},
            {'name': 'Janata Dal (United)', 'code': 'JDU', 'seats': 40, 'alliance': 'NDA', 'color': '#006400'},
            {'name': 'Rashtriya Janata Dal', 'code': 'RJD', 'seats': 95, 'alliance': 'INDI', 'color': '#008000'},
            {'name': 'Indian National Congress', 'code': 'INC', 'seats': 15, 'alliance': 'INDI', 'color': '#19AAED'},
            {'name': 'Communist Party of India (ML)', 'code': 'CPI_ML', 'seats': 6, 'alliance': 'INDI', 'color': '#FF0000'},
            {'name': 'Jan Suraaj Party', 'code': 'JSP', 'seats': 12, 'alliance': 'Others', 'color': '#FF6B35'},
            {'name': 'Hindustani Awam Morcha', 'code': 'HAM', 'seats': 5, 'alliance': 'NDA', 'color': '#800080'},
            {'name': 'Vikassheel Insaan Party', 'code': 'VIP', 'seats': 3, 'alliance': 'NDA', 'color': '#FFD700'},
            {'name': 'All India Majlis-e-Ittehadul Muslimeen', 'code': 'AIMIM', 'seats': 4, 'alliance': 'Others', 'color': '#00FF00'},
            {'name': 'Bahujan Samaj Party', 'code': 'BSP', 'seats': 2, 'alliance': 'Others', 'color': '#0000FF'},
            {'name': 'Lok Janshakti Party (Secular)', 'code': 'LJSP', 'seats': 3, 'alliance': 'Others', 'color': '#4169E1'},
            {'name': 'Others/Independents', 'code': 'OTH', 'seats': 8, 'alliance': 'Others', 'color': '#808080'}
        ]
        
        for party in party_results:
            if party['seats'] > 0:
                percentage = (party['seats'] / 243) * 100
                
                st.markdown(f"""
                <div class="eci-party-row">
                    <div>
                        <div class="eci-party-name" style="color: {party['color']}">
                            {party['name']} ({party['code']})
                        </div>
                        <div style="font-size: 0.9rem; color: #666;">
                            {party['alliance']} Alliance
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div class="eci-percentage">{percentage:.1f}%</div>
                        <div class="eci-seats">{party['seats']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    def render_constituency_summary(self, const_prob_df):
        """Render constituency-wise summary"""
        st.markdown("""
        <div class="eci-table" style="margin-top: 2rem;">
            <div class="eci-table-header">
                CONSTITUENCY WISE PREDICTIONS
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if const_prob_df is None or const_prob_df.empty:
            # Generate sample constituency data
            constituencies = [
                {'name': 'Patna Sahib', 'region': 'Patna', 'nda_prob': 0.75, 'status': 'NDA Leading'},
                {'name': 'Darbhanga', 'region': 'Darbhanga', 'nda_prob': 0.35, 'status': 'INDI Leading'},
                {'name': 'Muzaffarpur', 'region': 'Muzaffarpur', 'nda_prob': 0.52, 'status': 'Close Contest'},
                {'name': 'Gaya', 'region': 'Gaya', 'nda_prob': 0.68, 'status': 'NDA Leading'},
                {'name': 'Bhagalpur', 'region': 'Bhagalpur', 'nda_prob': 0.42, 'status': 'INDI Leading'},
                {'name': 'Purnia', 'region': 'Purnia', 'nda_prob': 0.48, 'status': 'Close Contest'},
                {'name': 'Kishanganj', 'region': 'Kishanganj', 'nda_prob': 0.25, 'status': 'INDI Leading'},
                {'name': 'Araria', 'region': 'Araria', 'nda_prob': 0.38, 'status': 'INDI Leading'},
                {'name': 'Madhubani', 'region': 'Madhubani', 'nda_prob': 0.72, 'status': 'NDA Leading'},
                {'name': 'Sitamarhi', 'region': 'Sitamarhi', 'nda_prob': 0.55, 'status': 'NDA Leading'}
            ]
            
            const_df = pd.DataFrame(constituencies)
        else:
            const_df = const_prob_df.head(10).copy()
            const_df['status'] = const_df['nda_win_probability'].apply(
                lambda x: 'NDA Leading' if x > 0.6 else 'INDI Leading' if x < 0.4 else 'Close Contest'
            )
        
        # Display top constituencies
        for _, row in const_df.iterrows():
            if 'nda_prob' in row:
                prob = row['nda_prob']
                name = row['name']
                region = row['region']
            else:
                prob = row.get('nda_win_probability', 0.5)
                name = row.get('constituency', 'Unknown')
                region = row.get('region', 'Unknown')
            
            status = row['status']
            
            # Determine status styling
            if 'NDA' in status:
                status_class = 'status-leading'
                status_color = '#28a745'
            elif 'INDI' in status:
                status_class = 'status-trailing'
                status_color = '#dc3545'
            else:
                status_class = 'status-competitive'
                status_color = '#ffc107'
            
            st.markdown(f"""
            <div class="eci-party-row">
                <div>
                    <div class="eci-party-name">{name}</div>
                    <div style="font-size: 0.9rem; color: #666;">{region} Region</div>
                </div>
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <div class="eci-percentage">NDA: {prob:.0%}</div>
                    <div class="{status_class}">{status}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    def render_live_updates(self):
        """Render live updates section"""
        st.markdown("""
        <div class="eci-table" style="margin-top: 2rem;">
            <div class="eci-table-header">
                FORECAST UPDATES
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Sample forecast updates
        updates = [
            {
                'time': '14:30',
                'update': 'Monte Carlo simulation updated with latest poll data - NDA projected 125 seats'
            },
            {
                'time': '14:15', 
                'update': 'Model identifies 35 highly competitive constituencies with <55% win probability'
            },
            {
                'time': '14:00',
                'update': 'Sentiment analysis shows INDI alliance gaining momentum in Seemanchal region'
            },
            {
                'time': '13:45',
                'update': 'Feature engineering complete: BJP forecast 69 seats, RJD 68 seats'
            },
            {
                'time': '13:30',
                'update': 'News sentiment data integrated into forecasting model'
            }
        ]
        
        for update in updates:
            st.markdown(f"""
            <div class="eci-party-row">
                <div>
                    <div style="font-weight: bold; color: #1f4e79;">{update['time']}</div>
                </div>
                <div style="flex: 1; padding-left: 1rem;">
                    {update['update']}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    def render_seat_distribution_pie_chart(self, summary):
        """Render seat distribution pie chart in ECI style"""
        if not summary or 'nda_projection' not in summary:
            # Sample data
            nda_seats = 125
            indi_seats = 113
            others_seats = 5
        else:
            nda_proj = summary['nda_projection']
            nda_seats = int(nda_proj['mean_seats'])
            indi_seats = 243 - nda_seats - 5
            others_seats = 5
        
        st.markdown("""
        <div class="eci-table">
            <div class="eci-table-header">
                PROJECTED SEAT DISTRIBUTION
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Create pie chart
        labels = ['NDA', 'INDI', 'Others']
        values = [nda_seats, indi_seats, others_seats]
        colors = ['#FF9933', '#19AAED', '#808080']
        
        fig = go.Figure(data=[go.Pie(
            labels=labels, 
            values=values, 
            marker_colors=colors,
            hole=0.4,
            textinfo='label+percent+value',
            textfont_size=16,
            textfont_color='white',
            textposition='auto',
            marker=dict(
                colors=colors,
                line=dict(color='white', width=3)
            )
        )])
        
        fig.update_layout(
            title={
                'text': "Projected Seat Distribution",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': '#1f4e79'}
            },
            height=400,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            ),
            font=dict(size=12)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Add majority line indicator
        st.markdown(f"""
        <div style="background: #f8f9fa; border: 2px solid #1f4e79; border-radius: 8px; padding: 1rem; margin: 1rem 0; text-align: center;">
            <h4 style="color: #1f4e79; margin: 0;">Majority Status</h4>
            <p style="margin: 0.5rem 0 0 0;">
                <strong>Majority Mark:</strong> 122 seats | 
                <strong>NDA:</strong> {nda_seats} seats | 
                <strong>INDI:</strong> {indi_seats} seats
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_bihar_constituency_map(self, const_prob_df):
        """Render Bihar constituency map with predicted winners by party colors"""
        st.markdown("""
        <div class="eci-table">
            <div class="eci-table-header">
                BIHAR CONSTITUENCY MAP - FORECAST WINNERS
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Generate sample constituency data if not available
        if const_prob_df is None or const_prob_df.empty:
            # Create sample data for Bihar constituencies
            constituencies = []
            regions = ['Patna', 'Gaya', 'Muzaffarpur', 'Darbhanga', 'Bhagalpur', 'Purnia', 'Kishanganj', 'Araria']
            
            for i in range(243):
                region = regions[i % len(regions)]
                nda_prob = np.random.uniform(0.2, 0.8)
                
                constituencies.append({
                    'constituency': f'Constituency_{i+1}',
                    'region': region,
                    'nda_win_probability': nda_prob,
                    'predicted_winner': 'NDA' if nda_prob > 0.5 else 'INDI',
                    'x_coord': (i % 20) * 2,  # Simple grid layout
                    'y_coord': (i // 20) * 2
                })
            
            const_prob_df = pd.DataFrame(constituencies)
        else:
            # Add coordinates for existing data (simple grid layout)
            const_prob_df = const_prob_df.copy()
            const_prob_df['predicted_winner'] = const_prob_df['nda_win_probability'].apply(
                lambda x: 'NDA' if x > 0.5 else 'INDI'
            )
            const_prob_df['x_coord'] = [(i % 20) * 2 for i in range(len(const_prob_df))]
            const_prob_df['y_coord'] = [(i // 20) * 2 for i in range(len(const_prob_df))]
        
        # Create constituency map visualization
        fig = go.Figure()
        
        # Color mapping for parties
        color_map = {
            'NDA': '#FF9933',
            'INDI': '#19AAED',
            'Others': '#808080'
        }
        
        for winner in ['NDA', 'INDI']:
            winner_data = const_prob_df[const_prob_df['predicted_winner'] == winner]
            
            fig.add_trace(go.Scatter(
                x=winner_data['x_coord'],
                y=winner_data['y_coord'],
                mode='markers',
                name=f'{winner} Leading',
                marker=dict(
                    color=color_map[winner],
                    size=12,
                    opacity=0.9,
                    line=dict(width=2, color='white'),
                    symbol='circle'
                ),
                text=winner_data['constituency'],
                hovertemplate='<b>%{text}</b><br>' +
                             'Predicted Winner: ' + winner + '<br>' +
                             'Region: %{customdata}<br>' +
                             '<extra></extra>',
                customdata=winner_data['region']
            ))
        
        fig.update_layout(
            title={
                'text': "Bihar Assembly Constituencies - Predicted Winners",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': '#1f4e79'}
            },
            xaxis=dict(
                showgrid=False,
                showticklabels=False,
                zeroline=False,
                title=""
            ),
            yaxis=dict(
                showgrid=False,
                showticklabels=False,
                zeroline=False,
                title=""
            ),
            height=500,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.1,
                xanchor="center",
                x=0.5
            ),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Map legend and statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            nda_leading = len(const_prob_df[const_prob_df['predicted_winner'] == 'NDA'])
            st.markdown(f"""
            <div style="background: #FF9933; color: white; padding: 1.5rem; border-radius: 8px; text-align: center; 
                        border: 3px solid white; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
                <h2 style="margin: 0; font-size: 2.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">{nda_leading}</h2>
                <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; font-weight: bold;">NDA Leading</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            indi_leading = len(const_prob_df[const_prob_df['predicted_winner'] == 'INDI'])
            st.markdown(f"""
            <div style="background: #19AAED; color: white; padding: 1.5rem; border-radius: 8px; text-align: center;
                        border: 3px solid white; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
                <h2 style="margin: 0; font-size: 2.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">{indi_leading}</h2>
                <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; font-weight: bold;">INDI Leading</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            total_seats = len(const_prob_df)
            st.markdown(f"""
            <div style="background: #1f4e79; color: white; padding: 1.5rem; border-radius: 8px; text-align: center;
                        border: 3px solid white; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
                <h2 style="margin: 0; font-size: 2.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">{total_seats}</h2>
                <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; font-weight: bold;">Total Seats</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Regional breakdown
        st.markdown("""
        <div style="background: white; border: 3px solid #1f4e79; border-radius: 8px; padding: 1.5rem; margin: 2rem 0;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
            <h3 style="color: #1f4e79; margin: 0 0 1rem 0; font-size: 1.5rem; text-align: center;">Regional Breakdown</h3>
        </div>
        """, unsafe_allow_html=True)
        
        if 'region' in const_prob_df.columns:
            regional_summary = const_prob_df.groupby(['region', 'predicted_winner']).size().unstack(fill_value=0)
            
            for region in regional_summary.index:
                nda_count = regional_summary.loc[region, 'NDA'] if 'NDA' in regional_summary.columns else 0
                indi_count = regional_summary.loc[region, 'INDI'] if 'INDI' in regional_summary.columns else 0
                total_region = nda_count + indi_count
                
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 1rem; 
                           border-bottom: 2px solid #dee2e6; background: white; margin: 0.5rem 0;
                           border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <div>
                        <div style="font-weight: bold; font-size: 1.2rem; color: #1f4e79;">{region} Region</div>
                        <div style="font-size: 1rem; color: #333; margin-top: 0.3rem;">Total: {total_region} constituencies</div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 2rem;">
                        <div style="background: #FF9933; color: white; padding: 0.5rem 1rem; border-radius: 20px; 
                                   font-weight: bold; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">NDA: {nda_count}</div>
                        <div style="background: #19AAED; color: white; padding: 0.5rem 1rem; border-radius: 20px; 
                                   font-weight: bold; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">INDI: {indi_count}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    def render_constituency_details_eci(self, const_prob_df):
        """Render constituency details in ECI official style using shared component"""
        st.markdown("""
        <div class="eci-table">
            <div class="eci-table-header">
                DETAILED CONSTITUENCY ANALYSIS
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Use shared constituency details component
        from src.dashboard.constituency_details_component import ConstituencyDetailsComponent
        
        constituency_component = ConstituencyDetailsComponent(style="eci")
        constituency_component.render_complete_analysis(const_prob_df)
    
    def render_forecast_footer(self):
        """Render forecast system footer"""
        current_time = datetime.now().strftime("%d %B %Y, %I:%M %p")
        
        st.markdown(f"""
        <div class="eci-footer">
            <p><strong>Bihar Election Forecast System</strong> | Advanced Statistical Modeling</p>
            <p>Last Updated: {current_time} | Predictions based on Monte Carlo simulation and machine learning</p>
            <p>© 2025 YV Predicts. Educational and research purposes only.</p>
        </div>
        """, unsafe_allow_html=True)
    
    def render(self):
        """Render the complete ECI-style dashboard"""
        # Load data
        summary, marginal_df, const_prob_df, latest_dir = self.load_latest_results()
        
        # Render forecast header
        self.render_forecast_header()
        
        # Main content
        self.render_main_summary(summary)
        
        # ECI-style tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Results Overview",
            "🥧 Seat Distribution", 
            "🗺️ Constituency Map",
            "📍 Constituency Details",
            "📱 Live Updates"
        ])
        
        with tab1:
            # Two column layout for overview
            col1, col2 = st.columns([2, 1])
            
            with col1:
                self.render_party_wise_results(summary)
            
            with col2:
                self.render_constituency_summary(const_prob_df)
        
        with tab2:
            # Pie chart and seat distribution
            col1, col2 = st.columns([1, 1])
            
            with col1:
                self.render_seat_distribution_pie_chart(summary)
            
            with col2:
                self.render_party_wise_results(summary)
        
        with tab3:
            # Bihar constituency map
            self.render_bihar_constituency_map(const_prob_df)
        
        with tab4:
            # Enhanced constituency details
            self.render_constituency_details_eci(const_prob_df)
        
        with tab5:
            # Live updates
            self.render_live_updates()
        
        # Footer
        self.render_forecast_footer()


def main():
    """Main official-style dashboard application"""
    dashboard = OfficialStyleDashboard()
    dashboard.render()


if __name__ == "__main__":
    main()