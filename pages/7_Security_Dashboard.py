import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
from datetime import datetime
import time
import os
import re

# Set page configuration
st.set_page_config(
    page_title="TerraFusion Security Dashboard",
    page_icon="🛡️",
    layout="wide"
)

# Define custom CSS
st.markdown("""
<style>
    /* Dashboard Container */
    .dashboard-container {
        padding: 20px;
        border-radius: 10px;
        background-color: #0e1117;
        margin-bottom: 20px;
    }
    
    /* Dashboard Title */
    .dashboard-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #00e5ff;
        margin-bottom: 10px;
    }
    
    .dashboard-subtitle {
        font-size: 1.1rem;
        color: rgba(255, 255, 255, 0.7);
        margin-bottom: 30px;
    }
    
    /* Metric Container */
    .metric-container {
        background-color: #1a2032;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        height: 100%;
    }
    
    /* Metric Title */
    .metric-title {
        font-size: 0.9rem;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.7);
        margin-bottom: 5px;
    }
    
    /* Metric Value */
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #ffffff;
    }
    
    /* Metric with Critical Color */
    .metric-critical .metric-value {
        color: #ff4d4d;
    }
    
    /* Metric with Warning Color */
    .metric-warning .metric-value {
        color: #ffae00;
    }
    
    /* Metric with Success Color */
    .metric-good .metric-value {
        color: #00d97e;
    }
    
    /* Metric Details */
    .metric-details {
        font-size: 0.8rem;
        color: rgba(255, 255, 255, 0.5);
        margin-top: 5px;
    }
    
    /* Section Container */
    .section-container {
        background-color: #1a2032;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Section Title */
    .section-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #00e5ff;
        margin-bottom: 15px;
        border-bottom: 1px solid rgba(0, 229, 255, 0.3);
        padding-bottom: 5px;
    }
    
    /* Data Table */
    .dataframe {
        width: 100%;
        font-size: 0.9rem;
    }
    
    /* Vulnerability Badge */
    .vuln-badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        text-align: center;
        min-width: 70px;
    }
    
    .vuln-critical {
        background-color: rgba(255, 77, 77, 0.2);
        color: #ff4d4d;
        border: 1px solid rgba(255, 77, 77, 0.3);
    }
    
    .vuln-high {
        background-color: rgba(255, 174, 0, 0.2);
        color: #ffae00;
        border: 1px solid rgba(255, 174, 0, 0.3);
    }
    
    .vuln-medium {
        background-color: rgba(255, 222, 51, 0.2);
        color: #ffde33;
        border: 1px solid rgba(255, 222, 51, 0.3);
    }
    
    .vuln-low {
        background-color: rgba(0, 217, 126, 0.2);
        color: #00d97e;
        border: 1px solid rgba(0, 217, 126, 0.3);
    }
    
    .vuln-info {
        background-color: rgba(0, 174, 255, 0.2);
        color: #00aeff;
        border: 1px solid rgba(0, 174, 255, 0.3);
    }
    
    /* Code Block */
    .code-block {
        background-color: #0e1117;
        border-radius: 5px;
        padding: 10px;
        font-family: monospace;
        overflow-x: auto;
        border: 1px solid rgba(255, 255, 255, 0.1);
        font-size: 0.9rem;
    }
    
    /* Recommendations */
    .recommendation-item {
        background-color: rgba(0, 229, 255, 0.05);
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 4px solid #00e5ff;
    }
    
    .recommendation-title {
        font-size: 1rem;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 5px;
    }
    
    .recommendation-description {
        font-size: 0.9rem;
        color: rgba(255, 255, 255, 0.7);
    }
    
    .recommendation-high {
        border-left-color: #ff4d4d;
    }
    
    .recommendation-medium {
        border-left-color: #ffae00;
    }
    
    .recommendation-low {
        border-left-color: #00d97e;
    }
    
    /* Progress Bar */
    .progress-bar-container {
        width: 100%;
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        height: 8px;
        margin-top: 8px;
        overflow: hidden;
    }
    
    .progress-bar {
        height: 100%;
        border-radius: 10px;
    }
    
    .progress-critical {
        background-color: #ff4d4d;
    }
    
    .progress-high {
        background-color: #ffae00;
    }
    
    .progress-medium {
        background-color: #ffde33;
    }
    
    .progress-low {
        background-color: #00d97e;
    }
    
    /* Scan List Item */
    .scan-list-item {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 5px;
        padding: 12px;
        margin-bottom: 8px;
        cursor: pointer;
        transition: all 0.2s ease-in-out;
    }
    
    .scan-list-item:hover {
        background-color: rgba(255, 255, 255, 0.1);
        transform: translateY(-2px);
    }
    
    .scan-list-item.active {
        background-color: rgba(0, 229, 255, 0.1);
        border-left: 3px solid #00e5ff;
    }
    
    .scan-list-title {
        font-size: 0.9rem;
        font-weight: 600;
        color: #ffffff;
    }
    
    .scan-list-date {
        font-size: 0.75rem;
        color: rgba(255, 255, 255, 0.5);
    }
    
    .scan-list-score {
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    .scan-list-count {
        font-size: 0.8rem;
        color: rgba(255, 255, 255, 0.7);
    }
    
    /* Risk Score Meter */
    .risk-score-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 20px 0;
    }
    
    .risk-score-value {
        font-size: 3.5rem;
        font-weight: 700;
    }
    
    .risk-score-label {
        font-size: 1rem;
        color: rgba(255, 255, 255, 0.7);
        margin-top: 5px;
    }
    
    /* Specific risk colors */
    .risk-critical {
        color: #ff4d4d;
    }
    
    .risk-high {
        color: #ffae00;
    }
    
    .risk-medium {
        color: #ffde33;
    }
    
    .risk-low {
        color: #00d97e;
    }
</style>
""", unsafe_allow_html=True)

# API base URL
API_BASE_URL = "http://localhost:5001/api"
SECURITY_API_URL = f"{API_BASE_URL}/security"

# Function to fetch security scan data
def fetch_security_scans():
    try:
        response = requests.get(f"{SECURITY_API_URL}/scans")
        if response.status_code == 200:
            return response.json()["data"]
        else:
            st.error(f"Error fetching scan data: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error connecting to API: {e}")
        return []

# Function to fetch a specific scan
def fetch_scan_details(scan_id):
    try:
        response = requests.get(f"{SECURITY_API_URL}/scan/{scan_id}")
        if response.status_code == 200:
            return response.json()["data"]
        else:
            st.error(f"Error fetching scan details: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error connecting to API: {e}")
        return None

# Function to initiate a security scan
def initiate_security_scan(repository_path, languages, scan_depth):
    try:
        payload = {
            "repositoryPath": repository_path,
            "languages": languages,
            "scanDepth": scan_depth
        }
        response = requests.post(f"{SECURITY_API_URL}/scan", json=payload)
        if response.status_code == 202:
            return response.json()["data"]["scanId"]
        else:
            st.error(f"Error initiating scan: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error connecting to API: {e}")
        return None

# Function to check dependencies
def check_dependencies(repository_path, languages):
    try:
        payload = {
            "repositoryPath": repository_path,
            "languages": languages
        }
        response = requests.post(f"{SECURITY_API_URL}/dependencies/check", json=payload)
        if response.status_code == 200:
            return response.json()["data"]
        else:
            st.error(f"Error checking dependencies: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error connecting to API: {e}")
        return None

# Function to detect secrets
def detect_secrets(repository_path):
    try:
        payload = {
            "repositoryPath": repository_path
        }
        response = requests.post(f"{SECURITY_API_URL}/secrets/detect", json=payload)
        if response.status_code == 200:
            return response.json()["data"]
        else:
            st.error(f"Error detecting secrets: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error connecting to API: {e}")
        return None

# Function to format timestamp
def format_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp / 1000 if timestamp > 1e12 else timestamp).strftime("%Y-%m-%d %H:%M:%S")

# Function to get severity badge HTML
def get_severity_badge(severity):
    return f'<span class="vuln-badge vuln-{severity.lower()}">{severity.capitalize()}</span>'

# Function to determine risk color
def get_risk_color(score):
    if score >= 7.0:
        return "critical"
    elif score >= 5.0:
        return "high"
    elif score >= 3.0:
        return "medium"
    else:
        return "low"

# Function to determine metric color class
def get_metric_color_class(value, thresholds):
    if value >= thresholds["critical"]:
        return "metric-critical"
    elif value >= thresholds["warning"]:
        return "metric-warning"
    else:
        return "metric-good"

# Helper function to pluralize words
def pluralize(word, count):
    return word if count == 1 else f"{word}s"

# Initialize session state
if "show_scan_details" not in st.session_state:
    st.session_state.show_scan_details = False

if "current_scan_id" not in st.session_state:
    st.session_state.current_scan_id = None

if "dependency_check_results" not in st.session_state:
    st.session_state.dependency_check_results = None

if "secret_detection_results" not in st.session_state:
    st.session_state.secret_detection_results = None

if "active_tab" not in st.session_state:
    st.session_state.active_tab = "overview"

# Dashboard title
st.markdown('<h1 class="dashboard-title">Security Dashboard 🛡️</h1>', unsafe_allow_html=True)
st.markdown('<p class="dashboard-subtitle">Comprehensive security monitoring and vulnerability management for your codebase</p>', unsafe_allow_html=True)

# Create two columns for layout
col1, col2 = st.columns([3, 1])

with col2:
    # Scan controls
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Security Scan Controls</div>', unsafe_allow_html=True)
    
    repository_path = st.text_input("Repository Path", value="./", help="Path to the code repository to scan")
    
    languages = st.multiselect(
        "Languages to Scan",
        ["javascript", "python", "java", "csharp", "go", "ruby", "php"],
        default=["javascript", "python"],
        help="Select the programming languages to include in the scan"
    )
    
    scan_depth = st.select_slider(
        "Scan Depth",
        options=["quick", "standard", "deep"],
        value="standard",
        help="Deeper scans are more thorough but take longer"
    )
    
    col1_button, col2_button = st.columns(2)
    
    with col1_button:
        if st.button("Run Security Scan", type="primary"):
            with st.spinner("Initiating security scan..."):
                scan_id = initiate_security_scan(repository_path, languages, scan_depth)
                if scan_id:
                    st.success(f"Scan initiated successfully!")
                    st.session_state.current_scan_id = scan_id
                    st.session_state.show_scan_details = True
                    st.rerun()
    
    with col2_button:
        if st.button("Check Dependencies"):
            with st.spinner("Checking dependencies..."):
                results = check_dependencies(repository_path, languages)
                if results:
                    st.session_state.dependency_check_results = results
                    st.session_state.active_tab = "dependencies"
                    st.rerun()
    
    if st.button("Detect Secrets"):
        with st.spinner("Detecting secrets..."):
            results = detect_secrets(repository_path)
            if results:
                st.session_state.secret_detection_results = results
                st.session_state.active_tab = "secrets"
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Recent scans list
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Recent Scans</div>', unsafe_allow_html=True)
    
    scans = fetch_security_scans()
    
    if not scans:
        st.info("No security scans found. Run a scan to get started.")
    else:
        for scan in scans[:10]:  # Show most recent 10 scans
            scan_timestamp = scan.get("timestamp", 0)
            formatted_time = format_timestamp(scan_timestamp)
            scan_id = scan.get("scanId", "")
            vuln_count = scan.get("vulnerabilityCount", 0)
            risk_score = scan.get("riskScore", 0)
            repo_path = scan.get("repositoryPath", "./")
            
            # Generate a truncated repo path
            short_repo = repo_path
            if len(short_repo) > 20:
                short_repo = f"{short_repo[:10]}...{short_repo[-10:]}"
            
            # Generate risk score color
            risk_color = get_risk_color(risk_score)
            
            is_active = scan_id == st.session_state.current_scan_id
            active_class = "active" if is_active else ""
            
            html = f"""
            <div class="scan-list-item {active_class}" onclick="handleScanClick('{scan_id}')">
                <div class="scan-list-title">{short_repo}</div>
                <div class="scan-list-date">{formatted_time}</div>
                <div style="display: flex; justify-content: space-between; margin-top: 5px;">
                    <span class="scan-list-score risk-{risk_color}">Risk: {risk_score:.1f}</span>
                    <span class="scan-list-count">Issues: {vuln_count}</span>
                </div>
            </div>
            """
            
            st.markdown(html, unsafe_allow_html=True)
            
            # Create a button using the scan ID that won't display but will capture clicks
            if st.button(f"Select {scan_id}", key=f"btn_{scan_id}", label_visibility="collapsed"):
                st.session_state.current_scan_id = scan_id
                st.session_state.show_scan_details = True
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

with col1:
    # Define tabs for different security views
    tabs = st.tabs(["Overview", "Vulnerabilities", "Dependencies", "Secrets", "Recommendations"])
    
    with tabs[0]:  # Overview tab
        st.session_state.active_tab = "overview"
        
        if st.session_state.show_scan_details and st.session_state.current_scan_id:
            scan_data = fetch_scan_details(st.session_state.current_scan_id)
            
            if scan_data:
                # Summary metrics
                st.markdown('<div style="display: flex; gap: 20px; margin-bottom: 20px;">', unsafe_allow_html=True)
                
                # Get summary data
                summary = scan_data.get("summary", {})
                risk_score = summary.get("risk_score", 0)
                vuln_count = summary.get("vulnerability_count", 0)
                total_files = summary.get("total_files_scanned", 0)
                severity_counts = summary.get("severity_counts", {})
                
                # Metric columns
                cols = st.columns(4)
                
                # Risk Score Metric
                risk_color = get_risk_color(risk_score)
                with cols[0]:
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-title">Overall Risk Score</div>
                        <div class="risk-score-container">
                            <div class="risk-score-value risk-{risk_color}">{risk_score:.1f}</div>
                            <div class="risk-score-label">out of 10.0</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Vulnerability Count Metric
                vuln_color_class = get_metric_color_class(vuln_count, {"critical": 10, "warning": 5})
                with cols[1]:
                    st.markdown(f"""
                    <div class="metric-container {vuln_color_class}">
                        <div class="metric-title">Vulnerabilities</div>
                        <div class="metric-value">{vuln_count}</div>
                        <div class="metric-details">Across {total_files} files</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Critical Issues Metric
                critical_count = severity_counts.get("critical", 0)
                high_count = severity_counts.get("high", 0)
                critical_color_class = get_metric_color_class(critical_count, {"critical": 1, "warning": 0})
                with cols[2]:
                    st.markdown(f"""
                    <div class="metric-container {critical_color_class}">
                        <div class="metric-title">Critical Issues</div>
                        <div class="metric-value">{critical_count}</div>
                        <div class="metric-details">+ {high_count} high severity</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Scan Timestamp Metric
                timestamp = scan_data.get("timestamp", 0)
                formatted_time = format_timestamp(timestamp)
                with cols[3]:
                    # Format the scan ID appropriately
                    scan_id_display = st.session_state.current_scan_id[:8] + "..." if st.session_state.current_scan_id else "N/A"
                    
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-title">Scan Completed</div>
                        <div class="metric-value" style="font-size: 1.5rem;">{formatted_time}</div>
                        <div class="metric-details">Scan ID: {scan_id_display}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Vulnerability Distribution Chart
                st.markdown('<div class="section-container">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">Vulnerability Distribution</div>', unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Severity distribution
                    severity_data = []
                    for severity, count in severity_counts.items():
                        if count > 0:
                            severity_data.append({"severity": severity.capitalize(), "count": count})
                    
                    if severity_data:
                        df_severity = pd.DataFrame(severity_data)
                        
                        # Customize colors
                        severity_colors = {
                            "Critical": "#ff4d4d",
                            "High": "#ffae00",
                            "Medium": "#ffde33",
                            "Low": "#00d97e",
                            "Info": "#00aeff"
                        }
                        
                        # Create pie chart
                        fig = px.pie(
                            df_severity,
                            values="count",
                            names="severity",
                            title="Vulnerabilities by Severity",
                            color="severity",
                            color_discrete_map=severity_colors,
                            hole=0.4
                        )
                        
                        # Update layout
                        fig.update_layout(
                            showlegend=True,
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=-0.2,
                                xanchor="center",
                                x=0.5
                            ),
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                            font=dict(color="white"),
                            margin=dict(l=20, r=20, t=30, b=0),
                            height=300
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No vulnerability data available for the severity distribution chart.")
                
                with col2:
                    # Get vulnerabilities and group by type
                    vulnerabilities = scan_data.get("vulnerabilities", [])
                    vuln_types = {}
                    
                    for vuln in vulnerabilities:
                        vuln_name = vuln.get("name", "Unknown")
                        # Extract the general type from the name (e.g., "SQL Injection Vulnerability" -> "SQL Injection")
                        vuln_type = re.sub(r"Vulnerability$", "", vuln_name).strip()
                        
                        if vuln_type not in vuln_types:
                            vuln_types[vuln_type] = 0
                        vuln_types[vuln_type] += 1
                    
                    if vuln_types:
                        # Convert to DataFrame
                        df_types = pd.DataFrame([
                            {"type": t, "count": c} for t, c in vuln_types.items()
                        ])
                        
                        # Sort by count
                        df_types = df_types.sort_values("count", ascending=False)
                        
                        # Create bar chart
                        fig = px.bar(
                            df_types,
                            x="count",
                            y="type",
                            title="Vulnerabilities by Type",
                            orientation="h",
                            text="count"
                        )
                        
                        # Update layout
                        fig.update_layout(
                            yaxis=dict(
                                title="",
                                autorange="reversed"
                            ),
                            xaxis=dict(title=""),
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                            font=dict(color="white"),
                            margin=dict(l=20, r=20, t=30, b=0),
                            height=300
                        )
                        
                        # Update traces
                        fig.update_traces(
                            marker_color="#00e5ff",
                            textposition="outside"
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No vulnerability data available for the type distribution chart.")
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Files with Most Vulnerabilities
                st.markdown('<div class="section-container">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">Files with Most Vulnerabilities</div>', unsafe_allow_html=True)
                
                # Group vulnerabilities by file
                file_vulns = {}
                for vuln in vulnerabilities:
                    file_path = vuln.get("file_path", "Unknown")
                    if file_path not in file_vulns:
                        file_vulns[file_path] = {"total": 0, "critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
                    
                    file_vulns[file_path]["total"] += 1
                    severity = vuln.get("severity", "low").lower()
                    file_vulns[file_path][severity] += 1
                
                # Convert to DataFrame
                if file_vulns:
                    df_files = pd.DataFrame([
                        {
                            "file": f,
                            "total": d["total"],
                            "critical": d["critical"],
                            "high": d["high"],
                            "medium": d["medium"],
                            "low": d["low"],
                            "info": d["info"]
                        } for f, d in file_vulns.items()
                    ])
                    
                    # Sort and get top 10
                    df_files = df_files.sort_values("total", ascending=False).head(10)
                    
                    # Shorten file paths for display
                    df_files["display_file"] = df_files["file"].apply(
                        lambda x: f"...{x[-40:]}" if len(x) > 40 else x
                    )
                    
                    # Create a stacked bar chart
                    fig = go.Figure()
                    
                    # Add traces for each severity
                    fig.add_trace(go.Bar(
                        y=df_files["display_file"],
                        x=df_files["critical"],
                        name="Critical",
                        orientation="h",
                        marker=dict(color="#ff4d4d"),
                        hovertemplate="%{y}<br>Critical: %{x}<extra></extra>"
                    ))
                    
                    fig.add_trace(go.Bar(
                        y=df_files["display_file"],
                        x=df_files["high"],
                        name="High",
                        orientation="h",
                        marker=dict(color="#ffae00"),
                        hovertemplate="%{y}<br>High: %{x}<extra></extra>"
                    ))
                    
                    fig.add_trace(go.Bar(
                        y=df_files["display_file"],
                        x=df_files["medium"],
                        name="Medium",
                        orientation="h",
                        marker=dict(color="#ffde33"),
                        hovertemplate="%{y}<br>Medium: %{x}<extra></extra>"
                    ))
                    
                    fig.add_trace(go.Bar(
                        y=df_files["display_file"],
                        x=df_files["low"],
                        name="Low",
                        orientation="h",
                        marker=dict(color="#00d97e"),
                        hovertemplate="%{y}<br>Low: %{x}<extra></extra>"
                    ))
                    
                    fig.add_trace(go.Bar(
                        y=df_files["display_file"],
                        x=df_files["info"],
                        name="Info",
                        orientation="h",
                        marker=dict(color="#00aeff"),
                        hovertemplate="%{y}<br>Info: %{x}<extra></extra>"
                    ))
                    
                    # Update layout
                    fig.update_layout(
                        barmode="stack",
                        title="Top 10 Files by Vulnerability Count",
                        yaxis=dict(
                            title="",
                            autorange="reversed"
                        ),
                        xaxis=dict(title="Vulnerability Count"),
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="center",
                            x=0.5
                        ),
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="white"),
                        margin=dict(l=20, r=20, t=50, b=20),
                        height=500
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No file vulnerability data available for the chart.")
                
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.warning("Failed to load scan details. The scan may still be in progress.")
        else:
            st.info("Select a scan from the list or run a new security scan to view results.")
    
    with tabs[1]:  # Vulnerabilities tab
        st.session_state.active_tab = "vulnerabilities"
        
        if st.session_state.show_scan_details and st.session_state.current_scan_id:
            scan_data = fetch_scan_details(st.session_state.current_scan_id)
            
            if scan_data:
                vulnerabilities = scan_data.get("vulnerabilities", [])
                
                if vulnerabilities:
                    # Filter controls
                    st.markdown('<div class="section-container">', unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        severity_filter = st.multiselect(
                            "Filter by Severity",
                            ["critical", "high", "medium", "low", "info"],
                            default=["critical", "high"],
                            key="vuln_severity_filter"
                        )
                    
                    with col2:
                        # Extract unique vulnerability types
                        vuln_types = sorted(list(set([v.get("name", "Unknown") for v in vulnerabilities])))
                        type_filter = st.multiselect(
                            "Filter by Type",
                            vuln_types,
                            default=[],
                            key="vuln_type_filter"
                        )
                    
                    with col3:
                        # Extract unique file extensions
                        file_exts = []
                        for vuln in vulnerabilities:
                            file_path = vuln.get("file_path", "")
                            _, ext = os.path.splitext(file_path)
                            if ext and ext not in file_exts:
                                file_exts.append(ext)
                        
                        file_exts.sort()
                        ext_filter = st.multiselect(
                            "Filter by File Extension",
                            file_exts,
                            default=[],
                            key="vuln_ext_filter"
                        )
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Apply filters
                    filtered_vulns = vulnerabilities
                    
                    if severity_filter:
                        filtered_vulns = [v for v in filtered_vulns if v.get("severity", "").lower() in severity_filter]
                    
                    if type_filter:
                        filtered_vulns = [v for v in filtered_vulns if v.get("name", "") in type_filter]
                    
                    if ext_filter:
                        filtered_vulns = [v for v in filtered_vulns if os.path.splitext(v.get("file_path", ""))[1] in ext_filter]
                    
                    # Display vulnerability table
                    st.markdown('<div class="section-container">', unsafe_allow_html=True)
                    st.markdown(f'<div class="section-title">Vulnerabilities ({len(filtered_vulns)} of {len(vulnerabilities)})</div>', unsafe_allow_html=True)
                    
                    if filtered_vulns:
                        # Create a DataFrame for display
                        vuln_data = []
                        for v in filtered_vulns:
                            file_path = v.get("file_path", "Unknown")
                            file_name = os.path.basename(file_path)
                            
                            vuln_data.append({
                                "Severity": v.get("severity", "Unknown").capitalize(),
                                "Type": v.get("name", "Unknown"),
                                "File": file_name,
                                "Line": v.get("line_number", "N/A"),
                                "CWE": v.get("cwe_id", "N/A"),
                                "Details": f"{v.get('description', 'No description available')[:100]}..."
                            })
                        
                        df_vulns = pd.DataFrame(vuln_data)
                        
                        # Function to color severity
                        def color_severity(val):
                            if val == "Critical":
                                return f'<span class="vuln-badge vuln-critical">{val}</span>'
                            elif val == "High":
                                return f'<span class="vuln-badge vuln-high">{val}</span>'
                            elif val == "Medium":
                                return f'<span class="vuln-badge vuln-medium">{val}</span>'
                            elif val == "Low":
                                return f'<span class="vuln-badge vuln-low">{val}</span>'
                            else:
                                return f'<span class="vuln-badge vuln-info">{val}</span>'
                        
                        # Apply styling
                        df_styled = df_vulns.style.format({
                            "Severity": lambda x: color_severity(x)
                        })
                        
                        st.write(df_styled.to_html(escape=False), unsafe_allow_html=True)
                        
                        # Detailed view for selected vulnerability
                        st.markdown('<div class="section-title" style="margin-top: 20px;">Vulnerability Details</div>', unsafe_allow_html=True)
                        
                        selected_idx = st.selectbox(
                            "Select vulnerability to view details",
                            range(len(filtered_vulns)),
                            format_func=lambda i: f"{filtered_vulns[i].get('severity', 'Unknown').capitalize()} - {filtered_vulns[i].get('name', 'Unknown')} in {os.path.basename(filtered_vulns[i].get('file_path', 'Unknown'))}"
                        )
                        
                        selected_vuln = filtered_vulns[selected_idx]
                        
                        # Display detailed information
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            severity = selected_vuln.get("severity", "Unknown").lower()
                            st.markdown(f"""
                            <div style="margin-bottom: 15px;">
                                <span style="font-weight: 600;">Severity:</span> {get_severity_badge(severity)}
                            </div>
                            <div style="margin-bottom: 15px;">
                                <span style="font-weight: 600;">Vulnerability:</span> {selected_vuln.get("name", "Unknown")}
                            </div>
                            <div style="margin-bottom: 15px;">
                                <span style="font-weight: 600;">File:</span> {selected_vuln.get("file_path", "Unknown")}
                            </div>
                            <div style="margin-bottom: 15px;">
                                <span style="font-weight: 600;">Line:</span> {selected_vuln.get("line_number", "N/A")}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if selected_vuln.get("cwe_id"):
                                st.markdown(f"""
                                <div style="margin-bottom: 15px;">
                                    <span style="font-weight: 600;">CWE:</span> {selected_vuln.get("cwe_id", "N/A")}
                                </div>
                                """, unsafe_allow_html=True)
                        
                        with col2:
                            st.markdown(f"""
                            <div style="margin-bottom: 15px;">
                                <span style="font-weight: 600;">Description:</span>
                                <div style="margin-top: 5px;">{selected_vuln.get("description", "No description available")}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if selected_vuln.get("recommendation"):
                                st.markdown(f"""
                                <div style="margin-bottom: 15px;">
                                    <span style="font-weight: 600;">Recommendation:</span>
                                    <div style="margin-top: 5px;">{selected_vuln.get("recommendation", "")}</div>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # Code snippet
                        if selected_vuln.get("code_snippet"):
                            st.markdown('<span style="font-weight: 600;">Code Snippet:</span>', unsafe_allow_html=True)
                            st.markdown(f"""
                            <div class="code-block">
                            {selected_vuln.get("code_snippet", "").replace("\n", "<br>").replace(" ", "&nbsp;")}
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # References
                        if selected_vuln.get("references"):
                            st.markdown('<span style="font-weight: 600;">References:</span>', unsafe_allow_html=True)
                            for ref in selected_vuln.get("references", []):
                                st.markdown(f"- [{ref}]({ref})", unsafe_allow_html=True)
                    else:
                        st.info("No vulnerabilities match the current filters.")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.success("No vulnerabilities found in this scan.")
            else:
                st.warning("Failed to load scan details. The scan may still be in progress.")
        else:
            st.info("Select a scan from the list or run a new security scan to view results.")
    
    with tabs[2]:  # Dependencies tab
        st.session_state.active_tab = "dependencies"
        
        # Check if we have dependency results
        if st.session_state.dependency_check_results:
            dependency_data = st.session_state.dependency_check_results
            
            # Summary metrics
            st.markdown('<div style="display: flex; gap: 20px; margin-bottom: 20px;">', unsafe_allow_html=True)
            
            summary = dependency_data.get("summary", {})
            vulnerable_deps = dependency_data.get("vulnerable_dependencies", [])
            dep_files = dependency_data.get("dependency_files_found", [])
            sev_dist = summary.get("severity_distribution", {})
            
            # Metric columns
            cols = st.columns(4)
            
            # Total Vulnerable Dependencies
            vuln_count = len(vulnerable_deps)
            vuln_color_class = get_metric_color_class(vuln_count, {"critical": 5, "warning": 1})
            with cols[0]:
                st.markdown(f"""
                <div class="metric-container {vuln_color_class}">
                    <div class="metric-title">Vulnerable Dependencies</div>
                    <div class="metric-value">{vuln_count}</div>
                    <div class="metric-details">In {len(dep_files)} dependency files</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Critical/High Dependencies
            critical_count = sev_dist.get("critical", 0)
            high_count = sev_dist.get("high", 0)
            critical_color_class = get_metric_color_class(critical_count + high_count, {"critical": 3, "warning": 1})
            with cols[1]:
                st.markdown(f"""
                <div class="metric-container {critical_color_class}">
                    <div class="metric-title">Critical/High Severity</div>
                    <div class="metric-value">{critical_count + high_count}</div>
                    <div class="metric-details">Dependencies requiring immediate action</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Languages Checked
            languages = dependency_data.get("languages_checked", [])
            languages_str = ", ".join(languages)
            with cols[2]:
                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-title">Languages Checked</div>
                    <div class="metric-value" style="font-size: 1.5rem;">{languages_str}</div>
                    <div class="metric-details">{len(languages)} languages in total</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Timestamp
            timestamp = dependency_data.get("timestamp", 0)
            formatted_time = format_timestamp(timestamp)
            with cols[3]:
                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-title">Check Completed</div>
                    <div class="metric-value" style="font-size: 1.5rem;">{formatted_time}</div>
                    <div class="metric-details">Dependency check results</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Vulnerable Dependencies Table
            st.markdown('<div class="section-container">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Vulnerable Dependencies</div>', unsafe_allow_html=True)
            
            if vulnerable_deps:
                # Create DataFrame
                dep_data = []
                for dep in vulnerable_deps:
                    dep_data.append({
                        "Name": dep.get("name", "Unknown"),
                        "Version": dep.get("version", "Unknown"),
                        "Language": dep.get("language", "Unknown").capitalize(),
                        "Severity": dep.get("severity", "Unknown").capitalize(),
                        "File": os.path.basename(dep.get("file_path", "Unknown")),
                        "Vulnerability": dep.get("vulnerability", "Unknown"),
                        "Recommendation": dep.get("recommendation", "Update to the latest version")
                    })
                
                df_deps = pd.DataFrame(dep_data)
                
                # Function to color severity
                def color_severity_dep(val):
                    if val == "Critical":
                        return f'<span class="vuln-badge vuln-critical">{val}</span>'
                    elif val == "High":
                        return f'<span class="vuln-badge vuln-high">{val}</span>'
                    elif val == "Medium":
                        return f'<span class="vuln-badge vuln-medium">{val}</span>'
                    elif val == "Low":
                        return f'<span class="vuln-badge vuln-low">{val}</span>'
                    else:
                        return val
                
                # Apply styling
                df_styled = df_deps.style.format({
                    "Severity": lambda x: color_severity_dep(x)
                })
                
                st.write(df_styled.to_html(escape=False), unsafe_allow_html=True)
            else:
                st.success("No vulnerable dependencies found.")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Dependency Files
            st.markdown('<div class="section-container">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Scanned Dependency Files</div>', unsafe_allow_html=True)
            
            if dep_files:
                # Create DataFrame
                file_data = []
                for file in dep_files:
                    file_data.append({
                        "File Path": file.get("file_path", "Unknown"),
                        "File Type": file.get("file_type", "Unknown"),
                        "Language": file.get("language", "Unknown").capitalize()
                    })
                
                st.table(pd.DataFrame(file_data))
            else:
                st.info("No dependency files found.")
            
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Run a dependency check to view results.")
    
    with tabs[3]:  # Secrets tab
        st.session_state.active_tab = "secrets"
        
        # Check if we have secret detection results
        if st.session_state.secret_detection_results:
            secrets_data = st.session_state.secret_detection_results
            
            # Summary metrics
            st.markdown('<div style="display: flex; gap: 20px; margin-bottom: 20px;">', unsafe_allow_html=True)
            
            summary = secrets_data.get("summary", {})
            secrets_found = secrets_data.get("secrets_found", [])
            
            # Metric columns
            cols = st.columns(3)
            
            # Total Secrets
            secrets_count = len(secrets_found)
            secrets_color_class = get_metric_color_class(secrets_count, {"critical": 5, "warning": 1})
            with cols[0]:
                st.markdown(f"""
                <div class="metric-container {secrets_color_class}">
                    <div class="metric-title">Secrets Found</div>
                    <div class="metric-value">{secrets_count}</div>
                    <div class="metric-details">Potential credential leaks</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Files with Secrets
            files_count = summary.get("files_with_secrets", 0)
            files_color_class = get_metric_color_class(files_count, {"critical": 3, "warning": 1})
            with cols[1]:
                st.markdown(f"""
                <div class="metric-container {files_color_class}">
                    <div class="metric-title">Files with Secrets</div>
                    <div class="metric-value">{files_count}</div>
                    <div class="metric-details">Files containing credentials</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Timestamp
            timestamp = secrets_data.get("timestamp", 0)
            formatted_time = format_timestamp(timestamp)
            with cols[2]:
                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-title">Detection Completed</div>
                    <div class="metric-value" style="font-size: 1.5rem;">{formatted_time}</div>
                    <div class="metric-details">Secret detection results</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Secret Types Distribution
            st.markdown('<div class="section-container">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Secret Types Distribution</div>', unsafe_allow_html=True)
            
            type_dist = summary.get("type_distribution", {})
            
            if type_dist:
                # Convert to DataFrame
                type_data = []
                for secret_type, count in type_dist.items():
                    type_data.append({
                        "Type": secret_type.replace("_", " ").title(),
                        "Count": count
                    })
                
                df_types = pd.DataFrame(type_data)
                
                # Create bar chart
                fig = px.bar(
                    df_types,
                    x="Type",
                    y="Count",
                    text="Count",
                    color_discrete_sequence=["#00e5ff"]
                )
                
                # Update layout
                fig.update_layout(
                    xaxis=dict(title=""),
                    yaxis=dict(title="Number of Secrets"),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="white"),
                    margin=dict(l=20, r=20, t=30, b=20),
                    height=300
                )
                
                # Update traces
                fig.update_traces(
                    textposition="outside"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No secret type distribution data available.")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Secrets Found Table
            st.markdown('<div class="section-container">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Detected Secrets</div>', unsafe_allow_html=True)
            
            if secrets_found:
                # Create DataFrame
                secret_data = []
                for secret in secrets_found:
                    secret_data.append({
                        "Type": secret.get("type", "Unknown").replace("_", " ").title(),
                        "File": os.path.basename(secret.get("file_path", "Unknown")),
                        "Line": secret.get("line_number", "N/A"),
                        "Masked Value": secret.get("masked_value", "****"),
                        "Severity": secret.get("severity", "Unknown").capitalize()
                    })
                
                df_secrets = pd.DataFrame(secret_data)
                
                # Function to color severity
                def color_severity_secret(val):
                    if val == "Critical":
                        return f'<span class="vuln-badge vuln-critical">{val}</span>'
                    elif val == "High":
                        return f'<span class="vuln-badge vuln-high">{val}</span>'
                    elif val == "Medium":
                        return f'<span class="vuln-badge vuln-medium">{val}</span>'
                    elif val == "Low":
                        return f'<span class="vuln-badge vuln-low">{val}</span>'
                    else:
                        return val
                
                # Apply styling
                df_styled = df_secrets.style.format({
                    "Severity": lambda x: color_severity_secret(x)
                })
                
                st.write(df_styled.to_html(escape=False), unsafe_allow_html=True)
                
                # Secret details
                st.markdown('<div class="section-title" style="margin-top: 20px;">Secret Details</div>', unsafe_allow_html=True)
                
                selected_idx = st.selectbox(
                    "Select a secret to view details",
                    range(len(secrets_found)),
                    format_func=lambda i: f"{secrets_found[i].get('type', 'Unknown').replace('_', ' ').title()} in {os.path.basename(secrets_found[i].get('file_path', 'Unknown'))}"
                )
                
                selected_secret = secrets_found[selected_idx]
                
                # Display code snippet with the secret
                st.markdown(f"""
                <div style="margin-bottom: 15px;">
                    <span style="font-weight: 600;">File:</span> {selected_secret.get("file_path", "Unknown")}
                </div>
                <div style="margin-bottom: 15px;">
                    <span style="font-weight: 600;">Line:</span> {selected_secret.get("line_number", "N/A")}
                </div>
                <div style="margin-bottom: 15px;">
                    <span style="font-weight: 600;">Secret Type:</span> {selected_secret.get("type", "Unknown").replace("_", " ").title()}
                </div>
                <div style="margin-bottom: 15px;">
                    <span style="font-weight: 600;">Severity:</span> {get_severity_badge(selected_secret.get("severity", "high"))}
                </div>
                <div style="margin-bottom: 15px;">
                    <span style="font-weight: 600;">Line Content:</span>
                    <div class="code-block">
                    {selected_secret.get("line_content", "").replace("<", "&lt;").replace(">", "&gt;")}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Display recommendations
                st.markdown("""
                <div class="recommendation-item recommendation-high">
                    <div class="recommendation-title">Security Recommendation</div>
                    <div class="recommendation-description">
                    Remove hardcoded secrets from source code. Use environment variables, secret management services, or configuration files that are not checked into source control.
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            else:
                st.success("No secrets found in the code.")
            
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Run a secret detection scan to view results.")
    
    with tabs[4]:  # Recommendations tab
        st.session_state.active_tab = "recommendations"
        
        if st.session_state.show_scan_details and st.session_state.current_scan_id:
            scan_data = fetch_scan_details(st.session_state.current_scan_id)
            
            if scan_data:
                # Extract recommendations
                vulnerabilities = scan_data.get("vulnerabilities", [])
                
                if vulnerabilities:
                    # Group vulnerabilities by type to generate recommendations
                    vuln_types = {}
                    for vuln in vulnerabilities:
                        vuln_type = vuln.get("name", "Unknown")
                        severity = vuln.get("severity", "low")
                        recommendation = vuln.get("recommendation", "")
                        
                        if vuln_type not in vuln_types:
                            vuln_types[vuln_type] = {
                                "count": 0,
                                "severity": severity,
                                "recommendation": recommendation
                            }
                        
                        vuln_types[vuln_type]["count"] += 1
                        
                        # Upgrade severity if higher
                        sev_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
                        if sev_rank.get(severity, 0) > sev_rank.get(vuln_types[vuln_type]["severity"], 0):
                            vuln_types[vuln_type]["severity"] = severity
                    
                    # Sort by severity and count
                    sorted_types = sorted(
                        vuln_types.items(),
                        key=lambda x: (
                            {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}.get(x[1]["severity"], 0),
                            x[1]["count"]
                        ),
                        reverse=True
                    )
                    
                    # Display recommendations
                    st.markdown('<div class="section-container">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">Security Recommendations</div>', unsafe_allow_html=True)
                    
                    for vuln_type, data in sorted_types:
                        severity = data["severity"]
                        count = data["count"]
                        recommendation = data["recommendation"]
                        
                        st.markdown(f"""
                        <div class="recommendation-item recommendation-{severity}">
                            <div class="recommendation-title">
                                {get_severity_badge(severity)} {vuln_type} ({count} {pluralize("instance", count)})
                            </div>
                            <div class="recommendation-description">
                                {recommendation}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # General security recommendations
                    st.markdown('<div class="section-container">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">General Security Best Practices</div>', unsafe_allow_html=True)
                    
                    general_recs = [
                        {
                            "title": "Implement a Secure Development Lifecycle (SDLC)",
                            "description": "Establish a formal secure development lifecycle process that includes security training, threat modeling, and security testing at each phase of development.",
                            "severity": "medium"
                        },
                        {
                            "title": "Conduct Regular Security Training",
                            "description": "Provide regular security training for all developers to create awareness of common vulnerabilities and secure coding practices.",
                            "severity": "medium"
                        },
                        {
                            "title": "Use Static Code Analysis Tools",
                            "description": "Integrate static code analysis tools into your CI/CD pipeline to automatically detect security issues early in the development process.",
                            "severity": "high"
                        },
                        {
                            "title": "Implement Security Headers",
                            "description": "Add security headers to your web applications to prevent common attacks like XSS, clickjacking, and MIME sniffing.",
                            "severity": "medium"
                        },
                        {
                            "title": "Keep Dependencies Updated",
                            "description": "Regularly update your dependencies to patch known vulnerabilities. Use tools like npm audit or Dependabot to automate this process.",
                            "severity": "high"
                        }
                    ]
                    
                    for rec in general_recs:
                        st.markdown(f"""
                        <div class="recommendation-item recommendation-{rec['severity']}">
                            <div class="recommendation-title">
                                {rec['title']}
                            </div>
                            <div class="recommendation-description">
                                {rec['description']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.success("No vulnerabilities found. Your code is looking secure!")
            else:
                st.warning("Failed to load scan details. The scan may still be in progress.")
        else:
            st.info("Select a scan from the list or run a new security scan to view recommendations.")