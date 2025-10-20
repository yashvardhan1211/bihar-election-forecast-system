"""
Shared constituency details component for both ECI and Advanced dashboard styles
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

class ConstituencyDetailsComponent:
    """Shared component for constituency details across dashboard styles"""
    
    def __init__(self, style="advanced"):
        self.style = style  # "eci" or "advanced"
    
    def render_constituency_selector(self, constituency_analyzer):
        """Render constituency selection interface"""
        try:
            all_constituencies = list(constituency_analyzer.constituencies.keys())
            all_constituencies.sort()
            
            if self.style == "eci":
                st.markdown("""
                <div style="background: #f8f9fa; border: 2px solid #1f4e79; border-radius: 8px; padding: 1rem; margin: 1rem 0;">
                    <h3 style="color: #1f4e79; margin: 0 0 1rem 0;">Select Constituency for Detailed Analysis</h3>
                </div>
                """, unsafe_allow_html=True)
                
                selected_const = st.selectbox(
                    "Choose Constituency:",
                    all_constituencies,
                    index=0 if all_constituencies else 0,
                    key=f"{self.style}_constituency_select"
                )
            else:
                # Advanced style selector
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    selected_const = st.selectbox(
                        "🔍 Select Constituency for Detailed Analysis",
                        all_constituencies,
                        index=0 if all_constituencies else 0,
                        help="Choose any of the 243 Bihar constituencies for detailed candidate analysis",
                        key=f"{self.style}_constituency_select"
                    )
                
                with col2:
                    st.metric("Total Constituencies", len(all_constituencies))
                    st.metric("Available Analysis", "243 Complete")
            
            return selected_const
            
        except Exception as e:
            st.error(f"Error loading constituencies: {e}")
            return None
    
    def render_constituency_header(self, selected_const, matchup):
        """Render constituency header based on style"""
        if self.style == "eci":
            # ECI official style header
            st.markdown(f"""
            <div class="eci-table">
                <div class="eci-table-header">
                    {selected_const.upper()} - CANDIDATE ANALYSIS
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # ECI-style metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="eci-summary-box">
                    <strong>Constituency Code</strong><br>
                    {matchup['constituency_code']}
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="eci-summary-box">
                    <strong>Region</strong><br>
                    {matchup['region']}
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="eci-summary-box">
                    <strong>Total Candidates</strong><br>
                    {matchup['total_candidates']}
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class="eci-summary-box">
                    <strong>Contest Type</strong><br>
                    {matchup['battle_type']}
                </div>
                """, unsafe_allow_html=True)
        
        else:
            # Advanced style header
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #4CAF50 0%, #45A049 100%); 
                        color: white; padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                <h2 style="margin: 0; text-align: center;">🏛️ {selected_const.upper()}</h2>
                <p style="margin: 0.5rem 0 0 0; text-align: center; font-size: 1.1rem;">
                    {matchup['region']} Region • {matchup['battle_type']} • {matchup['key_contest']}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Advanced style metrics
            col1, col2, col3, col4 = st.columns(4)
            
            metrics = [
                (matchup['constituency_code'], "Constituency Code", "#4CAF50"),
                (matchup['region'], "Region", "#FF9800"),
                (matchup['total_candidates'], "Total Candidates", "#2196F3"),
                (matchup['battle_type'], "Battle Type", "#E91E63")
            ]
            
            for i, (value, label, color) in enumerate(metrics):
                with [col1, col2, col3, col4][i]:
                    st.markdown(f"""
                    <div style="background: {color}20; border: 2px solid {color}; border-radius: 8px; padding: 1rem; text-align: center;">
                        <h3 style="color: {color}; margin: 0;">{value}</h3>
                        <p style="color: {color}; margin: 0;">{label}</p>
                    </div>
                    """, unsafe_allow_html=True)
    
    def render_candidates(self, matchup):
        """Render candidate information based on style"""
        if self.style == "eci":
            # ECI official table style
            st.markdown("""
            <div class="eci-table" style="margin-top: 2rem;">
                <div class="eci-table-header">
                    CANDIDATE WISE RESULTS
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            for i, candidate in enumerate(matchup['candidates']):
                # Determine status styling
                if i == 0:
                    status_class = 'status-leading'
                    status_text = 'LEADING'
                    status_icon = '🥇'
                elif i == 1:
                    status_class = 'status-competitive'
                    status_text = 'CHALLENGER'
                    status_icon = '🥈'
                else:
                    status_class = 'status-trailing'
                    status_text = 'TRAILING'
                    status_icon = '🥉'
                
                st.markdown(f"""
                <div class="eci-party-row">
                    <div>
                        <div class="eci-party-name">
                            {status_icon} {candidate['name']}
                        </div>
                        <div style="font-size: 0.9rem; color: #666;">
                            {candidate['party_name']} ({candidate['party_code']}) • {candidate['alliance']} Alliance
                        </div>
                        <div style="font-size: 0.8rem; color: #888; margin-top: 0.3rem;">
                            Age: {candidate['age']} • Education: {candidate['education']} • Assets: {candidate['assets']}
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div class="eci-percentage">{candidate['winning_chances']:.1f}%</div>
                        <div class="{status_class}">{status_text}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        else:
            # Advanced style with enhanced cards
            st.markdown("""
            <div style="background: #F3E5F5; border: 2px solid #9C27B0; border-radius: 8px; padding: 1rem; margin: 2rem 0 1rem 0;">
                <h2 style="color: #6A1B9A; margin: 0;">👥 CANDIDATE vs CANDIDATE ANALYSIS</h2>
                <p style="color: #7B1FA2; margin: 0.5rem 0 0 0;">Complete head-to-head comparison with winning chances</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Enhanced candidate cards
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
            
            # Also show comparison table
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
    
    def render_historical_context(self, matchup):
        """Render historical context and demographics"""
        hist_context = matchup['historical_context']
        demographics = matchup['demographics']
        
        if self.style == "eci":
            # ECI official style
            st.markdown("""
            <div class="eci-table" style="margin-top: 2rem;">
                <div class="eci-table-header">
                    HISTORICAL RESULTS & DEMOGRAPHICS
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                <div class="eci-summary-box">
                    <h4 style="color: #1f4e79; margin: 0 0 0.5rem 0;">Previous Election (2020)</h4>
                    <strong>Winner:</strong> {hist_context['last_winner']}<br>
                    <strong>Party:</strong> {hist_context['last_party']}<br>
                    <strong>Margin:</strong> {hist_context['last_margin']:,} votes<br>
                    <strong>Trend:</strong> {hist_context['trend']}
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="eci-summary-box">
                    <h4 style="color: #1f4e79; margin: 0 0 0.5rem 0;">Voter Demographics</h4>
                    <strong>Total Voters:</strong> {demographics['total_voters']:,}<br>
                    <strong>Male:</strong> {demographics['male_voters']:,} • <strong>Female:</strong> {demographics['female_voters']:,}<br>
                    <strong>Urban:</strong> {demographics['urban_percentage']:.1f}% • <strong>Literacy:</strong> {demographics['literacy_rate']:.1f}%
                </div>
                """, unsafe_allow_html=True)
        
        else:
            # Advanced style
            st.markdown("""
            <div style="background: #FFF8E1; border: 2px solid #FFC107; border-radius: 8px; padding: 1rem; margin: 2rem 0 1rem 0;">
                <h2 style="color: #F57F17; margin: 0;">📊 HISTORICAL CONTEXT & DEMOGRAPHICS</h2>
                <p style="color: #FF8F00; margin: 0.5rem 0 0 0;">Past election results and voter composition analysis</p>
            </div>
            """, unsafe_allow_html=True)
            
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
    
    def render_complete_analysis(self, const_prob_df):
        """Render complete constituency details analysis"""
        # Import candidate data
        try:
            from src.data.constituency_candidates import constituency_analyzer
        except ImportError:
            if self.style == "eci":
                st.markdown("""
                <div class="eci-party-row">
                    <div style="text-align: center; color: #dc3545;">
                        <strong>Candidate data not available</strong>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error("Candidate data not available")
            return
        
        if const_prob_df.empty:
            if self.style == "eci":
                st.markdown("""
                <div class="eci-party-row">
                    <div style="text-align: center; color: #ffc107;">
                        <strong>No constituency data available</strong>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("No constituency data available")
            return
        
        # Render constituency selector
        selected_const = self.render_constituency_selector(constituency_analyzer)
        
        if selected_const:
            matchup = constituency_analyzer.get_candidate_matchup(selected_const)
            
            if matchup:
                # Render all components
                self.render_constituency_header(selected_const, matchup)
                self.render_candidates(matchup)
                self.render_historical_context(matchup)