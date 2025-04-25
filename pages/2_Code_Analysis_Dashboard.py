import streamlit as st
import time
import pandas as pd
import numpy as np
import plotly.express as px
from model_interface import ModelInterface
import os
import json

# Set page configuration
st.set_page_config(
    page_title="Code Analysis Dashboard",
    page_icon="📊",
    layout="wide"
)

# Define custom CSS
st.markdown("""
<style>
    .analysis-card {
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 15px;
        border: 1px solid #ddd;
        background-color: #f8f9fa;
    }
    .analysis-header {
        font-size: 18px;
        font-weight: bold;
        color: #333;
        margin-bottom: 10px;
    }
    .issue-card {
        padding: 10px;
        margin-bottom: 10px;
        border-radius: 5px;
        background-color: #fff8e1;
        border-left: 4px solid #ffc107;
    }
    .issue-title {
        font-weight: bold;
        color: #333;
    }
    .score-circle {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto;
        font-size: 24px;
        font-weight: bold;
        color: white;
    }
    .code-block {
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 15px;
        background-color: #f5f5f5;
        font-family: monospace;
        overflow-x: auto;
        white-space: pre-wrap;
    }
    .insights-panel {
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 15px;
        background-color: #e8f5e9;
        border-left: 4px solid #4caf50;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'model_interface' not in st.session_state:
    st.session_state.model_interface = ModelInterface()
    
if 'code_analysis_history' not in st.session_state:
    st.session_state.code_analysis_history = []
    
if 'current_analysis' not in st.session_state:
    st.session_state.current_analysis = None

# Helper function to get a color for quality scores
def get_score_color(score):
    """Get color for quality score"""
    if score >= 8:
        return "#4caf50"  # Green
    elif score >= 6:
        return "#ffc107"  # Yellow
    elif score >= 4:
        return "#ff9800"  # Orange
    else:
        return "#f44336"  # Red

# Sidebar
st.sidebar.title("Code Analysis Controls")

# Analysis Type
analysis_type = st.sidebar.selectbox(
    "Analysis Type",
    ["Code Quality", "Architecture", "Performance", "Security"]
)

# Sample code or upload
code_source = st.sidebar.radio(
    "Code Source",
    ["Sample Code", "Custom Code"]
)

language_options = [
    "Python", "JavaScript", "TypeScript", "Java", 
    "C#", "Go", "Ruby", "PHP", "Swift", "SQL"
]

selected_language = st.sidebar.selectbox("Programming Language", language_options)

# Sample code for different languages
sample_code = {
    "Python": """def calculate_factorial(n):
    \"\"\"Calculate the factorial of a number.\"\"\"
    if n < 0:
        return None
    if n == 0:
        return 1
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result

def find_fibonacci(n):
    \"\"\"Return the nth Fibonacci number.\"\"\"
    if n <= 0:
        return 0
    if n == 1:
        return 1
    return find_fibonacci(n - 1) + find_fibonacci(n - 2)
""",
    "JavaScript": """function calculateFactorial(n) {
  // Calculate the factorial of a number
  if (n < 0) {
    return null;
  }
  if (n === 0) {
    return 1;
  }
  let result = 1;
  for (let i = 1; i <= n; i++) {
    result *= i;
  }
  return result;
}

function findFibonacci(n) {
  // Return the nth Fibonacci number
  if (n <= 0) {
    return 0;
  }
  if (n === 1) {
    return 1;
  }
  return findFibonacci(n - 1) + findFibonacci(n - 2);
}""",
    "TypeScript": """function calculateFactorial(n: number): number | null {
  // Calculate the factorial of a number
  if (n < 0) {
    return null;
  }
  if (n === 0) {
    return 1;
  }
  let result = 1;
  for (let i = 1; i <= n; i++) {
    result *= i;
  }
  return result;
}

function findFibonacci(n: number): number {
  // Return the nth Fibonacci number
  if (n <= 0) {
    return 0;
  }
  if (n === 1) {
    return 1;
  }
  return findFibonacci(n - 1) + findFibonacci(n - 2);
}""",
    "Java": """public class MathFunctions {
    /**
     * Calculate the factorial of a number.
     */
    public static Long calculateFactorial(int n) {
        if (n < 0) {
            return null;
        }
        if (n == 0) {
            return 1L;
        }
        long result = 1;
        for (int i = 1; i <= n; i++) {
            result *= i;
        }
        return result;
    }

    /**
     * Return the nth Fibonacci number.
     */
    public static int findFibonacci(int n) {
        if (n <= 0) {
            return 0;
        }
        if (n == 1) {
            return 1;
        }
        return findFibonacci(n - 1) + findFibonacci(n - 2);
    }
}""",
    "C#": """public class MathFunctions 
{
    /// <summary>
    /// Calculate the factorial of a number.
    /// </summary>
    public static long? CalculateFactorial(int n) 
    {
        if (n < 0)
        {
            return null;
        }
        if (n == 0)
        {
            return 1;
        }
        long result = 1;
        for (int i = 1; i <= n; i++)
        {
            result *= i;
        }
        return result;
    }

    /// <summary>
    /// Return the nth Fibonacci number.
    /// </summary>
    public static int FindFibonacci(int n)
    {
        if (n <= 0)
        {
            return 0;
        }
        if (n == 1)
        {
            return 1;
        }
        return FindFibonacci(n - 1) + FindFibonacci(n - 2);
    }
}""",
    "Go": """package mathfunctions

// CalculateFactorial calculates the factorial of a number.
func CalculateFactorial(n int) int {
    if n < 0 {
        return -1 // Go doesn't have null, using -1 to indicate error
    }
    if n == 0 {
        return 1
    }
    result := 1
    for i := 1; i <= n; i++ {
        result *= i
    }
    return result
}

// FindFibonacci returns the nth Fibonacci number.
func FindFibonacci(n int) int {
    if n <= 0 {
        return 0
    }
    if n == 1 {
        return 1
    }
    return FindFibonacci(n-1) + FindFibonacci(n-2)
}""",
    "Ruby": """# Calculate the factorial of a number.
def calculate_factorial(n)
  if n < 0
    return nil
  end
  if n == 0
    return 1
  end
  result = 1
  (1..n).each do |i|
    result *= i
  end
  return result
end

# Return the nth Fibonacci number.
def find_fibonacci(n)
  if n <= 0
    return 0
  end
  if n == 1
    return 1
  end
  return find_fibonacci(n - 1) + find_fibonacci(n - 2)
end""",
    "PHP": """<?php
/**
 * Calculate the factorial of a number.
 */
function calculateFactorial($n) {
    if ($n < 0) {
        return null;
    }
    if ($n == 0) {
        return 1;
    }
    $result = 1;
    for ($i = 1; $i <= $n; $i++) {
        $result *= $i;
    }
    return $result;
}

/**
 * Return the nth Fibonacci number.
 */
function findFibonacci($n) {
    if ($n <= 0) {
        return 0;
    }
    if ($n == 1) {
        return 1;
    }
    return findFibonacci($n - 1) + findFibonacci($n - 2);
}
?>""",
    "Swift": """// Calculate the factorial of a number.
func calculateFactorial(n: Int) -> Int? {
    if n < 0 {
        return nil
    }
    if n == 0 {
        return 1
    }
    var result = 1
    for i in 1...n {
        result *= i
    }
    return result
}

// Return the nth Fibonacci number.
func findFibonacci(n: Int) -> Int {
    if n <= 0 {
        return 0
    }
    if n == 1 {
        return 1
    }
    return findFibonacci(n: n - 1) + findFibonacci(n: n - 2)
}""",
    "SQL": """-- Create a table for employee data
CREATE TABLE employees (
    employee_id INT PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    hire_date DATE,
    salary DECIMAL(10, 2),
    department_id INT
);

-- Function to calculate years of service
CREATE OR REPLACE FUNCTION calculate_years_of_service(hire_date DATE) 
RETURNS INT AS $$
BEGIN
    RETURN EXTRACT(YEAR FROM AGE(CURRENT_DATE, hire_date));
END;
$$ LANGUAGE plpgsql;

-- Query to find employees with high salaries by department
SELECT 
    department_id,
    AVG(salary) as avg_salary,
    MAX(salary) as max_salary,
    COUNT(*) as employee_count
FROM 
    employees
GROUP BY 
    department_id
HAVING 
    AVG(salary) > 50000
ORDER BY 
    avg_salary DESC;"""
}

# Custom code area
if code_source == "Sample Code":
    code_to_analyze = sample_code.get(selected_language, "# Sample code not available for this language")
    st.sidebar.text_area("Sample Code", code_to_analyze, height=200, disabled=True)
    custom_code = False
else:
    code_to_analyze = st.sidebar.text_area("Enter Code to Analyze", "", height=300)
    custom_code = True

# Analysis focus
if analysis_type == "Code Quality":
    analysis_focus = st.sidebar.selectbox(
        "Analysis Focus",
        ["Overall Quality", "Readability", "Maintainability", "Complexity", "Documentation"]
    )
    
    query_templates = {
        "Overall Quality": "Provide a comprehensive quality analysis of this code, focusing on readability, maintainability, and best practices.",
        "Readability": "Analyze the readability of this code. How easy is it to understand? What could improve its clarity?",
        "Maintainability": "Assess the maintainability of this code. How easy would it be to modify or extend?",
        "Complexity": "Evaluate the complexity of this code. Are there overly complex parts that could be simplified?",
        "Documentation": "Review the documentation of this code. Is it well-documented? What's missing?"
    }
    
    query = query_templates.get(analysis_focus, query_templates["Overall Quality"])
    
elif analysis_type == "Architecture":
    analysis_focus = st.sidebar.selectbox(
        "Analysis Focus",
        ["Design Patterns", "Component Structure", "Dependencies", "Architectural Quality"]
    )
    
    query_templates = {
        "Design Patterns": "Identify any design patterns used in this code. Are they implemented correctly? Suggest improvements.",
        "Component Structure": "Analyze the component structure of this code. Is it well-organized?",
        "Dependencies": "Evaluate the dependencies in this code. Are there tight couplings or circular dependencies?",
        "Architectural Quality": "Assess the overall architectural quality of this code. What are its strengths and weaknesses?"
    }
    
    query = query_templates.get(analysis_focus, query_templates["Architectural Quality"])
    
elif analysis_type == "Performance":
    analysis_focus = st.sidebar.selectbox(
        "Analysis Focus",
        ["Efficiency", "Resource Usage", "Optimization Opportunities", "Bottlenecks"]
    )
    
    query_templates = {
        "Efficiency": "Analyze the efficiency of this code. Are there any inefficient algorithms or operations?",
        "Resource Usage": "Evaluate the resource usage of this code. Could it use less memory or CPU?",
        "Optimization Opportunities": "Identify optimization opportunities in this code. How could it be made faster?",
        "Bottlenecks": "Find potential bottlenecks in this code. What parts might cause performance issues?"
    }
    
    query = query_templates.get(analysis_focus, query_templates["Optimization Opportunities"])
    
else:  # Security
    analysis_focus = st.sidebar.selectbox(
        "Analysis Focus",
        ["Vulnerabilities", "Input Validation", "Error Handling", "Secure Coding Practices"]
    )
    
    query_templates = {
        "Vulnerabilities": "Identify any security vulnerabilities in this code. How could they be exploited and fixed?",
        "Input Validation": "Analyze the input validation in this code. Is it sufficient to prevent attacks?",
        "Error Handling": "Evaluate the error handling in this code. Could errors expose sensitive information?",
        "Secure Coding Practices": "Assess this code against secure coding practices. What improvements are needed?"
    }
    
    query = query_templates.get(analysis_focus, query_templates["Vulnerabilities"])

# Custom query option
custom_query = st.sidebar.checkbox("Custom Analysis Query")
if custom_query:
    query = st.sidebar.text_area("Enter your analysis query", query, height=100)

# Run analysis button
if st.sidebar.button("Run Analysis"):
    if not code_to_analyze.strip():
        st.sidebar.error("Please enter code to analyze")
    else:
        with st.spinner("Analyzing code..."):
            try:
                # Get model availability
                openai_available = st.session_state.model_interface.check_openai_status()
                anthropic_available = st.session_state.model_interface.check_anthropic_status()
                
                if not (openai_available or anthropic_available):
                    st.sidebar.error("No AI models available. Please check API keys.")
                else:
                    # Run analysis using available model
                    provider = "openai" if openai_available else "anthropic"
                    analysis_result = st.session_state.model_interface.analyze_code(
                        code=code_to_analyze,
                        language=selected_language.lower(),
                        query=query
                    )
                    
                    # Store the analysis result
                    st.session_state.current_analysis = {
                        "code": code_to_analyze,
                        "language": selected_language,
                        "query": query,
                        "result": analysis_result,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "type": analysis_type,
                        "focus": analysis_focus
                    }
                    
                    # Add to history
                    st.session_state.code_analysis_history.append(st.session_state.current_analysis)
                    
                    st.sidebar.success("Analysis completed successfully!")
            except Exception as e:
                st.sidebar.error(f"Error analyzing code: {str(e)}")

# Add navigation back to homepage
if st.sidebar.button("Back to Home"):
    st.switch_page("app.py")

# Main content
st.title("Code Analysis & Optimization Dashboard")

if st.session_state.current_analysis:
    analysis = st.session_state.current_analysis
    result = analysis["result"]
    
    # Analysis overview
    st.header("Analysis Overview")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown(f"**Analysis Type:** {analysis['type']} - {analysis['focus']}")
        st.markdown(f"**Language:** {analysis['language']}")
        st.markdown(f"**Timestamp:** {analysis['timestamp']}")
    
    with col2:
        quality_score = result.get("quality_score", 0)
        st.markdown("<div style='text-align: center'>Quality Score</div>", unsafe_allow_html=True)
        score_color = get_score_color(quality_score)
        st.markdown(
            f"<div class='score-circle' style='background-color: {score_color}'>{quality_score}/10</div>",
            unsafe_allow_html=True
        )
    
    with col3:
        if "issues" in result:
            issue_count = len(result["issues"])
            st.metric("Issues Identified", issue_count)
    
    # Code summary
    st.subheader("Code Summary")
    st.markdown(f"<div class='insights-panel'>{result.get('summary', 'No summary available')}</div>", unsafe_allow_html=True)
    
    # Tabs for different analysis aspects
    tab1, tab2, tab3 = st.tabs(["Detailed Analysis", "Issues & Recommendations", "Original Code"])
    
    with tab1:
        st.markdown("### Detailed Analysis")
        st.markdown(f"<div class='analysis-card'>{result.get('query_response', 'No detailed analysis available')}</div>", unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### Issues & Recommendations")
        
        if "issues" in result and result["issues"]:
            for i, issue in enumerate(result["issues"]):
                st.markdown(
                    f"<div class='issue-card'>"
                    f"<div class='issue-title'>Issue {i+1}</div>"
                    f"<p>{issue}</p>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        else:
            st.info("No issues identified.")
    
    with tab3:
        st.markdown("### Original Code")
        st.markdown(f"```{analysis['language'].lower()}\n{analysis['code']}\n```")
    
else:
    # Welcome message when no analysis has been run
    st.info("Welcome to the Code Analysis Dashboard! Use the sidebar to configure and run an analysis.")
    
    st.markdown("""
    ### Getting Started
    
    1. Select an **Analysis Type** from the sidebar
    2. Choose a **Code Source** (sample or custom)
    3. Select the **Programming Language**
    4. Choose an **Analysis Focus** area
    5. Click **Run Analysis** to start
    
    The AI-powered analysis engine will evaluate your code and provide insights, recommendations, and quality metrics.
    """)