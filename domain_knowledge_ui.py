"""
Domain Knowledge UI

This module provides Streamlit UI components for interacting with the Domain Knowledge Agent.
"""

import streamlit as st
import os
import sys
import random
import json
import time
import logging
from typing import Dict, Any, List, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def initialize_domain_knowledge_state():
    """Initialize session state for domain knowledge."""
    if 'domain_knowledge_initialized' not in st.session_state:
        st.session_state.domain_knowledge_initialized = False
        st.session_state.property_data = None
        st.session_state.assessment_results = None
        st.session_state.real_estate_results = None
        st.session_state.gis_results = None
        st.session_state.database_recommendations = None
        st.session_state.appraisal_results = None
        st.session_state.market_analysis_results = None
        st.session_state.expert_response = None

def get_domain_knowledge_agent():
    """
    Get the Domain Knowledge Agent.
    
    Returns:
        DomainKnowledgeAgent instance or None
    """
    try:
        from domain_knowledge_agent import DomainKnowledgeAgent
        
        # Create Domain Knowledge Agent
        agent = DomainKnowledgeAgent()
        
        return agent
    except Exception as e:
        logger.error(f"Error loading domain knowledge agent: {str(e)}")
        return None

def render_domain_knowledge_ui():
    """Render the domain knowledge agent UI."""
    # Initialize state
    initialize_domain_knowledge_state()
    
    st.header("🏠 Property Assessment & Market Analysis")
    
    # Load Domain Knowledge Agent if not already loaded
    if 'domain_agent' not in st.session_state:
        with st.spinner("Loading Domain Knowledge Agent..."):
            st.session_state.domain_agent = get_domain_knowledge_agent()
    
    # Check if Domain Knowledge Agent loaded successfully
    if st.session_state.domain_agent is None:
        st.error("Failed to load Domain Knowledge Agent. Please check the logs for details.")
        return
    
    # Create tabs for different analysis types
    tabs = st.tabs([
        "Tax Assessment", 
        "Real Estate Statistics", 
        "GIS Analysis", 
        "Property Appraisal", 
        "Market Analysis",
        "Domain Expert"
    ])
    
    # Tax Assessment Tab
    with tabs[0]:
        render_tax_assessment_tab()
    
    # Real Estate Statistics Tab
    with tabs[1]:
        render_real_estate_statistics_tab()
    
    # GIS Analysis Tab
    with tabs[2]:
        render_gis_analysis_tab()
    
    # Property Appraisal Tab
    with tabs[3]:
        render_property_appraisal_tab()
    
    # Market Analysis Tab
    with tabs[4]:
        render_market_analysis_tab()
    
    # Domain Expert Tab
    with tabs[5]:
        render_domain_expert_tab()

def render_tax_assessment_tab():
    """Render the tax assessment tab."""
    st.subheader("Tax Assessment Analysis")
    st.markdown("""
    This tab allows you to analyze property tax assessments using various methodologies.
    """)
    
    # Sample Property Selection
    st.markdown("### Select a property for assessment")
    
    property_types = [
        "Select a property...",
        "Single Family Home (Suburban)",
        "Luxury Condo (Downtown)",
        "Commercial Office Building",
        "Mixed-Use Development",
        "Industrial Warehouse"
    ]
    
    selected_property = st.selectbox("Property Type", property_types)
    
    # Sample property data
    property_data = {}
    if selected_property == "Single Family Home (Suburban)":
        property_data = {
            "property_type": "residential",
            "subtype": "single_family",
            "location": {"city": "Springfield", "zip": "12345", "neighborhood": "Oak Hills"},
            "lot_size_sqft": 10000,
            "building_size_sqft": 2200,
            "year_built": 1995,
            "bedrooms": 4,
            "bathrooms": 2.5,
            "recent_sale_price": 350000,
            "recent_sale_date": "2023-08-15",
            "estimated_value": 375000,
            "is_primary_residence": True,
            "owner_age": 45,
            "land_value": 120000,
            "improvement_value": 230000,
            "depreciation": 0.15,
            "annual_income": 0,
            "annual_expenses": 0
        }
    elif selected_property == "Luxury Condo (Downtown)":
        property_data = {
            "property_type": "residential",
            "subtype": "condo",
            "location": {"city": "Springfield", "zip": "12340", "neighborhood": "Downtown"},
            "lot_size_sqft": 0,
            "building_size_sqft": 1800,
            "year_built": 2015,
            "bedrooms": 2,
            "bathrooms": 2,
            "recent_sale_price": 450000,
            "recent_sale_date": "2023-11-10",
            "estimated_value": 475000,
            "is_primary_residence": True,
            "owner_age": 35,
            "land_value": 0,
            "improvement_value": 450000,
            "depreciation": 0.05,
            "annual_income": 0,
            "annual_expenses": 0
        }
    elif selected_property == "Commercial Office Building":
        property_data = {
            "property_type": "commercial",
            "subtype": "office",
            "location": {"city": "Springfield", "zip": "12345", "neighborhood": "Business District"},
            "lot_size_sqft": 15000,
            "building_size_sqft": 25000,
            "year_built": 2005,
            "recent_sale_price": 2750000,
            "recent_sale_date": "2022-06-30",
            "estimated_value": 3000000,
            "is_primary_residence": False,
            "land_value": 750000,
            "improvement_value": 2250000,
            "depreciation": 0.12,
            "annual_income": 275000,
            "annual_expenses": 120000
        }
    elif selected_property == "Mixed-Use Development":
        property_data = {
            "property_type": "mixed_use",
            "subtype": "retail_residential",
            "location": {"city": "Springfield", "zip": "12342", "neighborhood": "Gateway"},
            "lot_size_sqft": 20000,
            "building_size_sqft": 40000,
            "year_built": 2010,
            "recent_sale_price": 4250000,
            "recent_sale_date": "2022-02-15",
            "estimated_value": 4500000,
            "is_primary_residence": False,
            "land_value": 1250000,
            "improvement_value": 3250000,
            "depreciation": 0.08,
            "annual_income": 425000,
            "annual_expenses": 180000
        }
    elif selected_property == "Industrial Warehouse":
        property_data = {
            "property_type": "industrial",
            "subtype": "warehouse",
            "location": {"city": "Springfield", "zip": "12347", "neighborhood": "Industrial Park"},
            "lot_size_sqft": 50000,
            "building_size_sqft": 75000,
            "year_built": 1985,
            "recent_sale_price": 3200000,
            "recent_sale_date": "2021-10-05",
            "estimated_value": 3500000,
            "is_primary_residence": False,
            "land_value": 1500000,
            "improvement_value": 2000000,
            "depreciation": 0.25,
            "annual_income": 300000,
            "annual_expenses": 125000
        }
    
    if selected_property != "Select a property...":
        st.session_state.property_data = property_data
        
        with st.expander("Property Details", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Property Type:** {property_data['property_type'].title()} - {property_data['subtype'].replace('_', ' ').title()}")
                st.write(f"**Location:** {property_data['location']['neighborhood']}, {property_data['location']['city']}")
                st.write(f"**Size:** {property_data['building_size_sqft']:,} sqft (building)")
                if property_data['lot_size_sqft'] > 0:
                    st.write(f"**Lot Size:** {property_data['lot_size_sqft']:,} sqft")
                st.write(f"**Year Built:** {property_data['year_built']}")
            
            with col2:
                st.write(f"**Recent Sale Price:** ${property_data['recent_sale_price']:,}")
                st.write(f"**Recent Sale Date:** {property_data['recent_sale_date']}")
                st.write(f"**Estimated Value:** ${property_data['estimated_value']:,}")
                if property_data['property_type'] == 'residential':
                    st.write(f"**Bedrooms:** {property_data['bedrooms']}")
                    st.write(f"**Bathrooms:** {property_data['bathrooms']}")
        
        st.markdown("### Choose Assessment Methodology")
        
        methodologies = [
            "Market Value Approach",
            "Income Approach",
            "Cost Approach"
        ]
        
        selected_methodology = st.radio("Methodology", methodologies)
        
        methodology_map = {
            "Market Value Approach": "market_value",
            "Income Approach": "income_approach",
            "Cost Approach": "cost_approach"
        }
        
        if st.button("Calculate Assessment"):
            with st.spinner("Calculating tax assessment..."):
                # Call the domain knowledge agent to perform tax assessment
                assessment_task = {
                    "type": "tax_assessment_analysis",
                    "property_data": property_data,
                    "methodology": methodology_map[selected_methodology]
                }
                
                result = st.session_state.domain_agent._execute_task(assessment_task)
                
                if result.get("status") == "success":
                    st.session_state.assessment_results = result
                else:
                    st.error(f"Assessment failed: {result.get('message', 'Unknown error')}")
        
        # Display assessment results if available
        if st.session_state.assessment_results:
            result = st.session_state.assessment_results
            
            st.markdown("### Assessment Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Assessed Value", f"${result['assessment_value']:,.2f}")
                st.metric("Net Assessed Value", f"${result['net_assessed_value']:,.2f}")
                st.write(f"**Confidence Level:** {result['confidence']:.2f}")
                st.write(f"**Methodology:** {result['methodology_used'].replace('_', ' ').title()}")
            
            with col2:
                if result.get('exemption_value', 0) > 0:
                    st.metric("Exemption Value", f"${result['exemption_value']:,.2f}")
                    st.write("**Applicable Exemptions:**")
                    for exemption in result.get('applicable_exemptions', []):
                        st.write(f"- {exemption} Exemption")
                
                st.write("**Factors Considered:**")
                for factor in result.get('factors_considered', []):
                    st.write(f"- {factor}")
            
            # Appeal options
            st.markdown("### Appeal Options")
            st.write("If you disagree with this assessment, you have the following appeal options:")
            for i, option in enumerate(result.get('appeal_options', [])):
                st.write(f"{i+1}. {option}")

def render_real_estate_statistics_tab():
    """Render the real estate statistics tab."""
    st.subheader("Real Estate Market Statistics")
    st.markdown("""
    This tab provides real estate market statistics for different locations and property types.
    """)
    
    # Location selection
    st.markdown("### Select Location")
    
    locations = [
        "Springfield Metro Area",
        "Downtown Springfield",
        "Oak Hills (Suburban)",
        "Riverside District",
        "Gateway (Mixed-Use District)"
    ]
    
    selected_location = st.selectbox("Location", locations)
    
    # Property type selection
    st.markdown("### Select Property Type")
    
    property_types = [
        "Residential",
        "Commercial",
        "Industrial",
        "Multi-Family"
    ]
    
    selected_property_type = st.selectbox("Property Type", property_types)
    
    # Time period selection
    st.markdown("### Select Time Period")
    
    time_periods = [
        "Last Quarter",
        "Last Year",
        "Last 3 Years",
        "Last 5 Years"
    ]
    
    selected_time_period = st.selectbox("Time Period", time_periods)
    
    # Process the selections
    if st.button("Analyze Market Statistics"):
        with st.spinner("Analyzing real estate market statistics..."):
            location_data = {
                "name": selected_location, 
                "type": "neighborhood" if "District" in selected_location or "Hills" in selected_location else "city"
            }
            
            # Call the domain knowledge agent
            task = {
                "type": "real_estate_statistics",
                "location": location_data,
                "property_type": selected_property_type.lower(),
                "time_period": selected_time_period.lower().replace(" ", "_")
            }
            
            result = st.session_state.domain_agent._execute_task(task)
            
            if result.get("status") == "success":
                st.session_state.real_estate_results = result
            else:
                st.error(f"Analysis failed: {result.get('message', 'Unknown error')}")
    
    # Display results if available
    if st.session_state.real_estate_results:
        result = st.session_state.real_estate_results
        
        st.markdown("### Market Statistics Results")
        
        # Key metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Average Price", f"${result['average_price']:,.2f}")
            st.metric("Price per Sq.Ft.", f"${result['price_per_sqft']:,.2f}")
        
        with col2:
            st.metric("Median Price", f"${result['median_price']:,.2f}")
            st.metric("Days on Market", f"{result['days_on_market']} days")
        
        with col3:
            st.metric("Price Change", f"{result['price_change_percent']*100:+.2f}%")
            st.metric("Inventory", f"{result['months_of_inventory']:.1f} months")
        
        # Market condition
        st.markdown("### Market Condition")
        condition = result.get('market_condition', 'Neutral')
        trend = result.get('trending_direction', 'Stable')
        
        # Create a styled box for market condition
        bg_color = "#E8F4F9" if condition == "Buyer's Market" else "#F9F3E8"
        text_color = "#2C6E9B" if condition == "Buyer's Market" else "#9B6E2C"
        
        st.markdown(f"""
        <div style="background-color: {bg_color}; 
                    padding: 20px; border-radius: 10px; margin: 10px 0;">
            <h4 style="margin: 0; color: {text_color};">
                {condition}
            </h4>
            <p style="margin: 5px 0;">
                The market is currently <strong>{trend.lower()}</strong> with {result['months_of_inventory']:.1f} months of inventory.
            </p>
            <p>
                List-to-Sale Ratio: {result['list_to_sale_ratio']*100:.1f}%
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Tracked indicators
        st.markdown("### Tracked Market Indicators")
        indicators = result.get('market_indicators_tracked', [])
        
        st.write("The following market indicators are being tracked:")
        cols = st.columns(len(indicators))
        for i, indicator in enumerate(indicators):
            with cols[i]:
                st.markdown(f"""
                <div style="text-align: center; padding: 10px; margin: 5px; 
                            background-color: #F5F5F5; border-radius: 5px;">
                    <p style="margin: 0; font-weight: bold;">{indicator}</p>
                </div>
                """, unsafe_allow_html=True)

def render_gis_analysis_tab():
    """Render the GIS analysis tab."""
    st.subheader("GIS Data Analysis")
    st.markdown("""
    This tab allows you to perform Geographic Information System (GIS) analysis on property locations.
    """)
    
    # Analysis type selection
    st.markdown("### Select Analysis Type")
    
    analysis_types = [
        "Proximity Analysis",
        "Overlay Analysis",
        "Network Analysis"
    ]
    
    selected_analysis = st.selectbox("Analysis Type", analysis_types)
    
    # Location selection
    st.markdown("### Select Location")
    
    locations = [
        "Downtown Springfield",
        "Oak Hills Neighborhood",
        "Riverside District",
        "Business Park",
        "Industrial Zone"
    ]
    
    selected_location = st.selectbox("Location", locations)
    
    # Analysis parameters
    st.markdown("### Analysis Parameters")
    
    if selected_analysis == "Proximity Analysis":
        col1, col2 = st.columns(2)
        
        with col1:
            poi_types = ["Schools", "Parks", "Shopping", "Transit", "Healthcare"]
            selected_poi = st.selectbox("Points of Interest", poi_types)
        
        with col2:
            radius = st.slider("Radius (miles)", 0.1, 5.0, 1.0, 0.1)
        
        parameters = {
            "poi_type": selected_poi.lower(),
            "radius": radius
        }
    
    elif selected_analysis == "Overlay Analysis":
        col1, col2 = st.columns(2)
        
        with col1:
            layer_options = ["Zoning", "Flood Zones", "School Districts", "Tax Districts", "Land Use"]
            selected_layers = st.multiselect("Map Layers", layer_options, default=["Zoning", "Flood Zones"])
        
        parameters = {
            "layers": [layer.lower().replace(" ", "_") for layer in selected_layers]
        }
    
    else:  # Network Analysis
        col1, col2 = st.columns(2)
        
        with col1:
            analysis_subtypes = ["Route Analysis", "Service Area", "Closest Facility"]
            selected_subtype = st.selectbox("Network Analysis Type", analysis_subtypes)
        
        with col2:
            travel_mode = st.selectbox("Travel Mode", ["Driving", "Walking", "Transit"])
        
        parameters = {
            "subtype": selected_subtype.lower().replace(" ", "_"),
            "travel_mode": travel_mode.lower()
        }
    
    # Location data
    location_data = {
        "name": selected_location,
        "coordinates": {"lat": 40.7128, "lng": -74.0060}  # Sample coordinates
    }
    
    # Process the analysis
    if st.button("Perform Analysis"):
        with st.spinner(f"Performing {selected_analysis}..."):
            # Call the domain knowledge agent
            task = {
                "type": "gis_data_analysis",
                "location": location_data,
                "analysis_type": selected_analysis.lower().split()[0],  # 'proximity', 'overlay', or 'network'
                "parameters": parameters
            }
            
            result = st.session_state.domain_agent._execute_task(task)
            
            if result.get("status") == "success":
                st.session_state.gis_results = result
            else:
                st.error(f"Analysis failed: {result.get('message', 'Unknown error')}")
    
    # Display results if available
    if st.session_state.gis_results:
        result = st.session_state.gis_results
        
        st.markdown(f"### {selected_analysis} Results")
        
        if result.get("analysis_type") == "proximity":
            # Display proximity analysis results
            st.write(f"**Location:** {result['location']['name']}")
            st.write(f"**Radius:** {result['radius_miles']} miles")
            st.write(f"**POI Type:** {result['poi_type'].title()}")
            
            st.markdown("#### Results")
            poi_results = result.get("results", {})
            
            st.write(f"Found **{poi_results.get('count', 0)}** points of interest")
            st.write(f"Nearest distance: **{poi_results.get('nearest_distance', 0):.2f}** miles")
            st.write(f"Average distance: **{poi_results.get('average_distance', 0):.2f}** miles")
            
            # Display points of interest
            if poi_results.get("points_of_interest"):
                st.markdown("#### Points of Interest")
                
                for poi in poi_results["points_of_interest"]:
                    st.markdown(f"""
                    <div style="background-color: #F5F5F5; padding: 10px; border-radius: 5px; margin-bottom: 5px;">
                        <strong>{poi['name']}</strong><br/>
                        Distance: {poi['distance']:.2f} miles<br/>
                        Rating: {poi['rating']:.1f}/5.0
                    </div>
                    """, unsafe_allow_html=True)
            
            # Map placeholder (in a real app, this would be an actual map)
            st.markdown("#### Location Map")
            st.markdown("""
            <div style="background-color: #E8E8E8; height: 300px; border-radius: 5px; 
                        display: flex; align-items: center; justify-content: center;">
                <p style="color: #666;">Map visualization would appear here</p>
            </div>
            """, unsafe_allow_html=True)
        
        elif result.get("analysis_type") == "overlay":
            # Display overlay analysis results
            st.write(f"**Location:** {result['location']['name']}")
            st.write(f"**Layers Analyzed:** {', '.join([l.replace('_', ' ').title() for l in result['layers_analyzed']])}")
            
            overlay_results = result.get("results", {})
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Zoning Information")
                st.write(f"**Zone Type:** {overlay_results.get('zone_type', 'Unknown')}")
                
                if "overlay_results" in overlay_results:
                    st.write(f"**Area:** {overlay_results['overlay_results'].get('area_sqft', 0):,} sq.ft.")
                    st.write(f"**Commercial %:** {overlay_results['overlay_results'].get('percent_commercial_zoned', 0)*100:.1f}%")
            
            with col2:
                st.markdown("#### Flood Risk")
                st.write(f"**Risk Level:** {overlay_results.get('flood_risk', 'Unknown')}")
                
                if "overlay_results" in overlay_results:
                    st.write(f"**% in Flood Zone:** {overlay_results['overlay_results'].get('percent_in_flood_zone', 0)*100:.1f}%")
            
            # Map placeholder
            st.markdown("#### Overlay Map")
            st.markdown("""
            <div style="background-color: #E8E8E8; height: 300px; border-radius: 5px; 
                        display: flex; align-items: center; justify-content: center;">
                <p style="color: #666;">Overlay map visualization would appear here</p>
            </div>
            """, unsafe_allow_html=True)
        
        else:  # General results
            st.write(f"**Available Operations:** {', '.join(result.get('available_operations', []))}")
            st.write(f"**Available Layers:** {', '.join(result.get('available_layers', []))}")
            st.write(f"**Recommended Analysis:** {result.get('recommended_analysis', 'None')}")

def render_property_appraisal_tab():
    """Render the property appraisal tab."""
    st.subheader("Property Appraisal")
    st.markdown("""
    This tab provides property appraisal analysis using different methodologies.
    """)
    
    # Use the same property selection as in the tax assessment tab
    if 'property_data' not in st.session_state or st.session_state.property_data is None:
        st.warning("Please select a property in the Tax Assessment tab first.")
        return
    
    property_data = st.session_state.property_data
    
    # Display selected property
    st.markdown("### Selected Property")
    st.write(f"**{property_data['property_type'].title()} - {property_data['subtype'].replace('_', ' ').title()}**")
    st.write(f"**Location:** {property_data['location']['neighborhood']}, {property_data['location']['city']}")
    st.write(f"**Size:** {property_data['building_size_sqft']:,} sqft")
    st.write(f"**Year Built:** {property_data['year_built']}")
    
    # Appraisal method selection
    st.markdown("### Appraisal Method")
    
    methods = [
        "Sales Comparison Approach",
        "Income Approach",
        "Cost Approach"
    ]
    
    selected_method = st.radio("Select Appraisal Method", methods)
    
    method_map = {
        "Sales Comparison Approach": "sales_comparison",
        "Income Approach": "income_approach",
        "Cost Approach": "cost_approach"
    }
    
    # Process appraisal
    if st.button("Generate Appraisal"):
        with st.spinner(f"Generating appraisal using {selected_method}..."):
            # Call the domain knowledge agent
            task = {
                "type": "appraisal_insights",
                "property_data": property_data,
                "appraisal_method": method_map[selected_method]
            }
            
            result = st.session_state.domain_agent._execute_task(task)
            
            if result.get("status") == "success":
                st.session_state.appraisal_results = result
            else:
                st.error(f"Appraisal failed: {result.get('message', 'Unknown error')}")
    
    # Display results if available
    if st.session_state.appraisal_results:
        result = st.session_state.appraisal_results
        
        st.markdown("### Appraisal Results")
        
        # Display estimated value prominently
        st.markdown(f"""
        <div style="background-color: #F8F8F8; padding: 20px; border-radius: 10px; text-align: center; margin: 20px 0;">
            <h3 style="margin: 0; color: #333;">Estimated Value</h3>
            <h2 style="margin: 10px 0; color: #2C6E9B;">${result['estimated_value']:,.2f}</h2>
            <p style="margin: 0;">Confidence Level: {result['confidence_level']:.2f}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Display method-specific results
        if "appraisal_method" in result and result["appraisal_method"] == "sales_comparison":
            st.markdown("#### Comparable Properties")
            
            for i, comp in enumerate(result.get("comparable_properties", [])):
                st.markdown(f"""
                <div style="background-color: #F5F5F5; padding: 15px; border-radius: 5px; margin-bottom: 10px;">
                    <h4 style="margin: 0;">Comparable #{i+1}</h4>
                    <p style="margin: 5px 0;">Sale Price: <strong>${comp['sale_price']:,.2f}</strong></p>
                    <p style="margin: 5px 0;">Sale Date: {comp['sale_date']}</p>
                    <p style="margin: 5px 0;">Adjusted Price: <strong>${comp['adjusted_price']:,.2f}</strong></p>
                    <hr style="margin: 10px 0;">
                    <p style="margin: 5px 0;">Adjustments:</p>
                    <ul style="margin: 5px 0; padding-left: 20px;">
                """, unsafe_allow_html=True)
                
                for factor, adjustment in comp.get("adjustments", {}).items():
                    st.markdown(f"""
                    <li>{factor.replace('_', ' ').title()}: {adjustment*100:+.1f}%</li>
                    """, unsafe_allow_html=True)
                
                st.markdown("</ul></div>", unsafe_allow_html=True)
            
            # Display value range
            if "value_range" in result:
                st.markdown("#### Value Range")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Low Estimate", f"${result['value_range']['low']:,.2f}")
                
                with col2:
                    st.metric("High Estimate", f"${result['value_range']['high']:,.2f}")
            
            # Display market conditions
            st.write(f"**Market Conditions:** {result.get('market_conditions', 'Stable')}")
            
        elif "appraisal_method" in result and result["appraisal_method"] == "income_approach":
            # Display income analysis
            if "income_analysis" in result:
                income = result["income_analysis"]
                
                st.markdown("#### Income Analysis")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Potential Gross Income", f"${income['potential_gross_income']:,.2f}")
                    st.metric("Effective Gross Income", f"${income['effective_gross_income']:,.2f}")
                    st.metric("Net Operating Income", f"${income['net_operating_income']:,.2f}")
                
                with col2:
                    st.metric("Vacancy Rate", f"{income['vacancy_rate']*100:.1f}%")
                    st.metric("Operating Expenses", f"${income['operating_expenses']:,.2f}")
                    st.metric("Capitalization Rate", f"{income['capitalization_rate']*100:.2f}%")
                
                # Display capitalization rate context
                st.markdown("#### Market Capitalization Rates")
                st.write(f"**Min:** {income['market_cap_rates']['min']*100:.2f}%")
                st.write(f"**Typical:** {income['market_cap_rates']['typical']*100:.2f}%")
                st.write(f"**Max:** {income['market_cap_rates']['max']*100:.2f}%")

def render_market_analysis_tab():
    """Render the market analysis tab."""
    st.subheader("Local Market Analysis")
    st.markdown("""
    This tab provides analysis of local market factors affecting property values.
    """)
    
    # Location selection
    st.markdown("### Select Location")
    
    locations = [
        "Downtown Springfield",
        "Oak Hills Neighborhood",
        "Riverside District",
        "Business Park",
        "Industrial Zone"
    ]
    
    selected_location = st.selectbox("Location", locations, key="market_location")
    
    # Market factor selection
    st.markdown("### Select Market Factors to Analyze")
    
    factor_options = [
        "School Quality",
        "Crime Rates",
        "Walkability",
        "Transit Access",
        "Population Growth",
        "Income Levels",
        "Employment Centers"
    ]
    
    selected_factors = st.multiselect("Market Factors", factor_options, 
                                     default=["School Quality", "Walkability", "Population Growth"])
    
    # Process the analysis
    if st.button("Analyze Market Factors"):
        with st.spinner("Analyzing local market factors..."):
            location_data = {
                "name": selected_location,
                "type": "neighborhood"
            }
            
            # Call the domain knowledge agent
            task = {
                "type": "local_market_analysis",
                "location": location_data,
                "market_factors": [f.lower().replace(" ", "_") for f in selected_factors] if selected_factors else ["all"]
            }
            
            result = st.session_state.domain_agent._execute_task(task)
            
            if result.get("status") == "success":
                st.session_state.market_analysis_results = result
            else:
                st.error(f"Analysis failed: {result.get('message', 'Unknown error')}")
    
    # Display results if available
    if st.session_state.market_analysis_results:
        result = st.session_state.market_analysis_results
        
        st.markdown("### Market Analysis Results")
        
        # Display market summary
        if "market_summary" in result:
            summary = result["market_summary"]
            
            st.markdown(f"""
            <div style="background-color: #F8F8F8; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <h3 style="margin: 0; color: #333;">Market Summary</h3>
                <h4 style="margin: 10px 0; color: #2C6E9B;">
                    {summary['strength']} {summary['direction']} Market
                </h4>
                <p style="margin: 5px 0;">
                    <strong>Price Forecast:</strong> {summary['price_forecast']}
                </p>
                <p style="margin: 5px 0;">
                    <strong>Opportunity Level:</strong> {summary['opportunity_level']*10:.1f}/10
                </p>
                <p style="margin: 5px 0;">
                    <strong>Risk Level:</strong> {summary['risk_level']*10:.1f}/10
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        # Display factor analysis
        if "factor_analysis" in result:
            st.markdown("### Factor Analysis")
            
            factor_analysis = result["factor_analysis"]
            
            # Create expandable sections for each factor
            for factor, analysis in factor_analysis.items():
                with st.expander(factor.replace("_", " ").title(), expanded=True):
                    if "rating" in analysis:
                        st.write(f"**Rating:** {analysis['rating']:.1f}/10")
                    if "score" in analysis:
                        st.write(f"**Score:** {analysis['score']:.1f}/10")
                    if "percentile" in analysis:
                        st.write(f"**Percentile:** {analysis['percentile']*100:.1f}%")
                    if "impact_on_value" in analysis:
                        impact = analysis["impact_on_value"] * 100
                        st.write(f"**Impact on Value:** {impact:+.1f}%")
                    if "trend" in analysis:
                        st.write(f"**Trend:** {analysis['trend']}")
                    
                    # Display factor-specific information
                    if factor == "school_quality":
                        st.progress(analysis.get("rating", 5)/10)
                    elif factor == "crime_rates":
                        # Invert the progress bar (higher is worse for crime)
                        safe_rating = 1 - (analysis.get("rating", 5)/10)
                        st.progress(safe_rating)
                    elif factor == "walkability":
                        st.progress(analysis.get("score", 50)/100)
                        if "notable_amenities" in analysis:
                            st.write("**Notable Amenities Nearby:**")
                            st.write(", ".join(analysis["notable_amenities"]))
                    elif factor == "population_growth":
                        growth = analysis.get("annual_rate", 0) * 100
                        st.metric("Annual Growth Rate", f"{growth:+.2f}%")
                        st.write(f"**Forecast:** {analysis.get('forecast', 0)*100:+.2f}% annually")
                    elif factor == "income_levels":
                        st.metric("Median Household Income", f"${analysis.get('median_household', 0):,}")
                        st.write(f"**Comparison to Metro:** {analysis.get('comparison_to_metro', 1)*100:.1f}% of metro average")

def render_domain_expert_tab():
    """Render the domain expert tab."""
    st.subheader("Domain Expert")
    st.markdown("""
    Ask questions about tax assessment, real estate statistics, GIS, appraisal, 
    or local market factors to get expert insights.
    """)
    
    # Domain selection
    st.markdown("### Select Knowledge Domain")
    
    domains = [
        "Tax Assessment",
        "Real Estate Market",
        "GIS & Spatial Analysis",
        "Property Appraisal",
        "Local Market Factors",
        "Database Optimization"
    ]
    
    selected_domain = st.selectbox("Domain", domains)
    
    domain_map = {
        "Tax Assessment": "tax_assessment",
        "Real Estate Market": "real_estate",
        "GIS & Spatial Analysis": "gis",
        "Property Appraisal": "appraisal",
        "Local Market Factors": "local_market",
        "Database Optimization": "database"
    }
    
    # Model selection
    st.markdown("### Select AI Model(s)")
    
    # Get available models
    available_models = []
    try:
        if hasattr(st.session_state.domain_agent, 'model_interface') and st.session_state.domain_agent.model_interface:
            available_models = st.session_state.domain_agent.model_interface.get_available_models()
    except Exception as e:
        logger.error(f"Error getting available models: {str(e)}")
    
    # Create model groups
    model_groups = {
        "OpenAI": [m for m in available_models if "gpt" in m.lower()],
        "Anthropic": [m for m in available_models if "claude" in m.lower()],
        "Perplexity": [m for m in available_models if "perplexity" in m.lower()],
        "DeepSeek": [m for m in available_models if "deepseek" in m.lower()],
        "Google": [m for m in available_models if "gemini" in m.lower()]
    }
    
    # Add mode selection (single model or comparison)
    model_mode = st.radio(
        "Model Selection Mode",
        ["Single Model", "Compare Models"],
        help="Select a single model or compare multiple models"
    )
    
    if model_mode == "Single Model":
        # Create model selection UI for single model
        col1, col2 = st.columns(2)
        
        with col1:
            model_provider = st.selectbox(
                "Model Provider", 
                ["Auto-select (Recommended)"] + list(model_groups.keys()),
                help="Select a model provider or let the system choose the best model for your domain"
            )
        
        with col2:
            if model_provider == "Auto-select (Recommended)":
                selected_model = None
            else:
                provider_models = model_groups.get(model_provider, [])
                if provider_models:
                    selected_model = st.selectbox("Specific Model", provider_models)
                else:
                    st.info(f"No {model_provider} models available. Using default.")
                    selected_model = None
        
        # Set comparison models to None
        comparison_models = None
    else:
        # Create UI for model comparison
        st.write("Select models to compare:")
        
        # Get one representative model from each available provider
        comparison_models = []
        
        # Create checkboxes for each provider's recommended model
        cols = st.columns(len(model_groups))
        for i, (provider, models) in enumerate(model_groups.items()):
            if models:  # Only show providers with available models
                with cols[i % len(cols)]:
                    # Get the first/best model for this provider
                    provider_model = models[0]
                    if st.checkbox(f"{provider}", value=(i < 2), key=f"compare_{provider}"):
                        comparison_models.append(provider_model)
        
        selected_model = None  # Not used in comparison mode
    
    # Question input
    st.markdown("### Ask a Question")
    
    question = st.text_area("Your Question", height=100, 
                            placeholder="Enter your question about property assessment, real estate market, GIS analysis, etc.")
    
    # Sample questions
    st.markdown("### Sample Questions")
    
    sample_questions = {
        "Tax Assessment": [
            "What factors influence property tax assessments?",
            "How do exemptions affect my property tax bill?",
            "What is the difference between assessed value and market value?"
        ],
        "Real Estate Market": [
            "What are the key indicators of a buyer's vs. seller's market?",
            "How do interest rates impact property values?",
            "What metrics are most important for real estate investment analysis?"
        ],
        "GIS & Spatial Analysis": [
            "How does proximity to schools affect residential property values?",
            "What GIS layers are most important for flood risk assessment?",
            "How can spatial analysis help identify undervalued properties?"
        ],
        "Property Appraisal": [
            "When should the income approach be used instead of sales comparison?",
            "What adjustments are most important in the sales comparison approach?",
            "How is economic obsolescence calculated in the cost approach?"
        ],
        "Local Market Factors": [
            "How do school ratings impact property values?",
            "What demographic trends most strongly predict neighborhood appreciation?",
            "How does walkability affect urban property values?"
        ],
        "Database Optimization": [
            "What indexes improve property database query performance?",
            "How should spatial data be stored for optimal GIS queries?",
            "What are best practices for modeling property relationships in a database?"
        ]
    }
    
    selected_samples = sample_questions.get(selected_domain, [])
    
    col1, col2 = st.columns(2)
    
    # Only show sample questions if there are any for the selected domain
    if selected_samples:
        with col1:
            if st.button(selected_samples[0]):
                question = selected_samples[0]
                st.session_state.expert_question = question
        
        with col2:
            if st.button(selected_samples[1]):
                question = selected_samples[1]
                st.session_state.expert_question = question
        
        if len(selected_samples) > 2:
            if st.button(selected_samples[2]):
                question = selected_samples[2]
                st.session_state.expert_question = question
    
    # Update text area with selected sample question if applicable
    if 'expert_question' in st.session_state:
        question = st.session_state.expert_question
    
    # Process the query
    if question and st.button("Get Expert Insight"):
        with st.spinner("Consulting domain knowledge..."):
            # Call the domain knowledge agent
            task = {
                "type": "query_domain_knowledge",
                "query": question,
                "domain": domain_map[selected_domain],
                "context": {
                    "user_expertise": "novice",
                    "query_type": "informational"
                }
            }
            
            # Add model selection based on the mode
            if model_mode == "Single Model":
                task["model"] = selected_model
            else:
                task["comparison_models"] = comparison_models
            
            result = st.session_state.domain_agent._execute_task(task)
            
            if result.get("status") == "success":
                st.session_state.expert_response = result
            else:
                st.error(f"Query failed: {result.get('message', 'Unknown error')}")
    
    # Display results if available
    if st.session_state.expert_response:
        result = st.session_state.expert_response
        
        # Check if this is a model comparison result
        if result.get('model_comparison'):
            st.markdown("### Model Comparison Results")
            
            comparison_results = result.get('comparison_results', {})
            if comparison_results:
                # Create tabs for each model
                model_names = list(comparison_results.keys())
                model_tabs = st.tabs(model_names)
                
                # Show results for each model in a tab
                for i, model_name in enumerate(model_names):
                    with model_tabs[i]:
                        model_result = comparison_results[model_name]
                        
                        # Get model provider for display
                        provider = "AI"
                        if "gpt" in model_name.lower():
                            provider = "OpenAI"
                        elif "claude" in model_name.lower():
                            provider = "Anthropic"
                        elif "gemini" in model_name.lower():
                            provider = "Google"
                        elif "perplexity" in model_name.lower():
                            provider = "Perplexity"
                        elif "deepseek" in model_name.lower():
                            provider = "DeepSeek"
                        
                        st.markdown(f"""
                        <div style="background-color: #F8F8F8; padding: 20px; border-radius: 10px; margin: 20px 0;">
                            <h4 style="margin: 0 0 15px 0; color: #2C6E9B;">{model_name} ({provider})</h4>
                            <p style="margin: 0; white-space: pre-line;">{model_result.get('text', 'No response generated')}</p>
                            <p style="margin: 5px 0 0 0; font-style: italic; font-size: 0.7em; color: #888;">
                                Response time: {model_result.get('latency', 0):.2f}s
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Add model comparison analysis
                st.markdown("### Model Response Analysis")
                st.info("""
                Compare the model responses to see differences in:
                - Answer depth and specificity
                - Technical accuracy
                - Explanation clarity
                - Response style
                """)
                
                # Provide metrics if available
                metrics_cols = st.columns(len(model_names))
                for i, model_name in enumerate(model_names):
                    with metrics_cols[i]:
                        model_result = comparison_results[model_name]
                        latency = model_result.get('latency', 0)
                        token_count = model_result.get('token_count', 0)
                        st.metric(
                            label=f"{model_name}", 
                            value=f"{latency:.2f}s",
                            delta=f"{token_count} tokens" if token_count else None,
                            delta_color="off"
                        )
                
            else:
                st.warning("No comparison results available")
        else:
            # Standard single model response
            st.markdown("### Expert Response")
            
            # Create a clean, card-like container for the response
            st.markdown(f"""
            <div style="background-color: #F8F8F8; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <h4 style="margin: 0 0 15px 0; color: #2C6E9B;">Response to your question:</h4>
                <p style="margin: 0; white-space: pre-line;">{result['response']}</p>
                <p style="margin: 10px 0 0 0; font-style: italic; font-size: 0.8em; color: #666;">
                    Source: {result.get('source', 'Domain Knowledge Model')} 
                    ({result.get('provider', 'AI')})
                </p>
                <p style="margin: 5px 0 0 0; font-style: italic; font-size: 0.7em; color: #888;">
                    Response time: {result.get('latency', 0):.2f}s | Generated: {result.get('timestamp', '')}
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        # Add model comparison option
        if 'domain_agent' in st.session_state and hasattr(st.session_state.domain_agent, 'model_interface'):
            st.markdown("### Compare With Other Models")
            if st.button("Compare responses across different models"):
                with st.spinner("Generating responses from multiple models..."):
                    try:
                        model_interface = st.session_state.domain_agent.model_interface
                        available_models = model_interface.get_available_models()
                        
                        # Select up to 3 different models for comparison
                        comparison_models = []
                        for provider in ["OpenAI", "Anthropic", "Perplexity", "Google", "DeepSeek"]:
                            provider_models = [m for m in available_models if 
                                              (provider.lower() in m.lower() or 
                                               (provider == "OpenAI" and "gpt" in m.lower()) or
                                               (provider == "Anthropic" and "claude" in m.lower()) or 
                                               (provider == "Google" and "gemini" in m.lower()))]
                            if provider_models and len(comparison_models) < 3:
                                # Avoid adding the same model used for the original response
                                if provider_models[0] != result.get('source'):
                                    comparison_models.append(provider_models[0])
                        
                        # Generate comparison responses
                        if comparison_models:
                            st.subheader("Model Comparisons")
                            
                            # Create tabs for each model
                            comparison_tabs = st.tabs(comparison_models)
                            
                            # Generate responses from each model
                            for i, model in enumerate(comparison_models):
                                with comparison_tabs[i]:
                                    with st.spinner(f"Generating response from {model}..."):
                                        task = {
                                            "type": "query_domain_knowledge",
                                            "query": question,
                                            "domain": domain_map[selected_domain],
                                            "model": model,
                                            "context": {
                                                "user_expertise": "novice",
                                                "query_type": "informational"
                                            }
                                        }
                                        
                                        comp_result = st.session_state.domain_agent._execute_task(task)
                                        
                                        if comp_result.get("status") == "success":
                                            st.markdown(f"""
                                            <div style="background-color: #F5F8FA; padding: 15px; border-radius: 10px; margin: 10px 0;">
                                                <p style="margin: 0; white-space: pre-line;">{comp_result['response']}</p>
                                                <p style="margin: 10px 0 0 0; font-style: italic; font-size: 0.8em; color: #666;">
                                                    Response time: {comp_result.get('latency', 0):.2f}s
                                                </p>
                                            </div>
                                            """, unsafe_allow_html=True)
                                        else:
                                            st.error(f"Failed to generate comparison from {model}")
                        else:
                            st.info("No additional models available for comparison.")
                    except Exception as e:
                        st.error(f"Error comparing models: {str(e)}")