import streamlit as st
import pandas as pd
import numpy as np
import networkx as nx
import plotly.graph_objects as go
import plotly.express as px
import time
import re
import json
from model_interface import ModelInterface
import random
from io import StringIO

# Set page configuration
st.set_page_config(
    page_title="Workflow Visualization",
    page_icon="📊",
    layout="wide"
)

# Define custom CSS
st.markdown("""
<style>
    .workflow-card {
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 15px;
        border: 1px solid #ddd;
        background-color: #f8f9fa;
    }
    .step-card {
        padding: 10px;
        margin-bottom: 10px;
        border-radius: 5px;
        background-color: #e8f5e9;
        border-left: 4px solid #4caf50;
    }
    .step-title {
        font-weight: bold;
        color: #333;
    }
    .step-info {
        font-size: 0.9em;
        color: #666;
    }
    .metric-card {
        text-align: center;
        border-radius: 5px;
        padding: 15px;
        background-color: #f0f0f0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        height: 100%;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #333;
        margin: 10px 0;
    }
    .metric-label {
        font-size: 14px;
        color: #666;
    }
    .node-tooltip {
        font-size: 12px;
        padding: 5px;
        background-color: #f5f5f5;
        border-radius: 3px;
        border: 1px solid #ddd;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'model_interface' not in st.session_state:
    st.session_state.model_interface = ModelInterface()
    
if 'workflow_data' not in st.session_state:
    st.session_state.workflow_data = None
    
if 'analyzed_code' not in st.session_state:
    st.session_state.analyzed_code = None
    
if 'workflow_details' not in st.session_state:
    st.session_state.workflow_details = None

# Helper functions
def create_graph_from_workflow(workflow_data):
    """Create a NetworkX graph from workflow data"""
    G = nx.DiGraph()
    
    # Add nodes
    for step in workflow_data["steps"]:
        node_id = step["id"]
        G.add_node(
            node_id,
            name=step["name"],
            type=step.get("type", "task"),
            duration=step.get("duration", 0),
            status=step.get("status", "pending")
        )
    
    # Add edges
    for step in workflow_data["steps"]:
        node_id = step["id"]
        dependencies = step.get("depends_on", [])
        
        for dep in dependencies:
            G.add_edge(dep, node_id)
    
    return G

def identify_critical_path(G):
    """Identify the critical path in the workflow graph"""
    # Calculate longest path (critical path)
    # This is a simplified approach for a DAG
    topo_order = list(nx.topological_sort(G))
    
    # Initialize distances
    dist = {node: 0 for node in G.nodes()}
    
    # Calculate longest path from source to each node
    for node in topo_order:
        for successor in G.successors(node):
            weight = G.nodes[node].get("duration", 0)
            if dist[successor] < dist[node] + weight:
                dist[successor] = dist[node] + weight
    
    # Find the node with maximum distance (end of critical path)
    if not topo_order:
        return []
        
    sink_nodes = [node for node in G.nodes() if G.out_degree(node) == 0]
    if not sink_nodes:
        end_node = topo_order[-1]
    else:
        end_node = max(sink_nodes, key=lambda x: dist[x])
    
    # Trace back to find the critical path
    path = [end_node]
    current = end_node
    
    while G.in_degree(current) > 0:
        predecessors = list(G.predecessors(current))
        current = max(predecessors, key=lambda x: dist[x])
        path.append(current)
    
    return list(reversed(path))

def plot_workflow_graph(G, critical_path=None):
    """Create a Plotly graph visualization of the workflow"""
    # Create positions for nodes using Spring layout
    try:
        pos = nx.nx_pydot.pydot_layout(G, prog="dot")
    except:
        pos = nx.spring_layout(G, seed=42)
    
    # Convert positions to x, y lists
    node_x = []
    node_y = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
    
    # Create node trace
    status_colors = {
        "completed": "#4CAF50",  # Green
        "in_progress": "#2196F3", # Blue
        "pending": "#9E9E9E",    # Grey
        "failed": "#F44336"      # Red
    }
    
    node_colors = []
    node_sizes = []
    
    for node in G.nodes():
        status = G.nodes[node].get("status", "pending")
        duration = G.nodes[node].get("duration", 1)
        node_colors.append(status_colors.get(status, "#9E9E9E"))
        node_sizes.append(10 + min(duration * 2, 30))  # Scale size by duration
    
    # Create a graph trace for nodes
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            color=node_colors,
            size=node_sizes,
            line=dict(width=2, color='#333')
        ),
        text=[G.nodes[node].get("name", node) for node in G.nodes()],
        name='Tasks'
    )
    
    # Create edge traces
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1.5, color='#888'),
        hoverinfo='none',
        mode='lines',
        name='Dependencies'
    )
    
    # Add critical path if provided
    critical_path_trace = None
    if critical_path and len(critical_path) > 1:
        crit_x = []
        crit_y = []
        for i in range(len(critical_path) - 1):
            x0, y0 = pos[critical_path[i]]
            x1, y1 = pos[critical_path[i + 1]]
            crit_x.extend([x0, x1, None])
            crit_y.extend([y0, y1, None])
        
        critical_path_trace = go.Scatter(
            x=crit_x, y=crit_y,
            line=dict(width=4, color='#FF5722'),
            hoverinfo='none',
            mode='lines',
            name='Critical Path'
        )
    
    # Create layout for the graph
    layout = go.Layout(
        title='Workflow Dependency Graph',
        showlegend=True,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        legend=dict(
            x=0,
            y=1,
            traceorder="normal",
            bgcolor='rgba(255,255,255,0.5)',
            bordercolor='rgba(0,0,0,0)'
        ),
        plot_bgcolor='rgba(248,249,250,1)',
        paper_bgcolor='rgba(248,249,250,1)',
    )
    
    # Create figure
    fig = go.Figure(layout=layout)
    
    # Add traces
    fig.add_trace(edge_trace)
    if critical_path_trace:
        fig.add_trace(critical_path_trace)
    fig.add_trace(node_trace)
    
    # Update hover info
    fig.update_traces(
        hovertemplate="<b>%{text}</b><br>",
        selector=dict(type='scatter', mode='markers')
    )
    
    return fig

def extract_workflow_from_code(code, language):
    """Use AI to extract workflow information from code"""
    if not st.session_state.model_interface.check_openai_status() and not st.session_state.model_interface.check_anthropic_status():
        st.error("No AI services available. Please configure API keys.")
        return None
    
    # Create prompt for workflow extraction
    prompt = f"""
    Analyze the following {language} code and identify the workflow or process steps:

    ```{language}
    {code}
    ```

    Extract and structure the workflow as a directed graph, identifying:
    1. Individual steps/functions/methods in the code that form part of a workflow
    2. Dependencies between the steps (what steps depend on which other steps)
    3. Estimated relative duration/complexity of each step (1-10 scale)
    4. Current status of each step (pending, in_progress, completed)
    
    Format your response as a JSON object with the following structure:
    {{
        "workflow_name": "Name of the workflow",
        "workflow_description": "Brief description of what this workflow does",
        "steps": [
            {{
                "id": "unique_id_for_step",
                "name": "Human readable name for this step",
                "description": "Description of what this step does",
                "type": "task or decision",
                "depends_on": ["id_of_dependency1", "id_of_dependency2"],
                "duration": 1-10 value representing relative complexity,
                "status": "pending, in_progress, or completed"
            }}
        ],
        "metrics": {{
            "total_steps": number of steps,
            "estimated_complexity": 1-100 value of overall complexity,
            "bottlenecks": ["id_of_bottleneck1", "id_of_bottleneck2"]
        }}
    }}
    
    If there is not enough information to determine a complete workflow, make reasonable inferences about the likely workflow structure.
    """
    
    try:
        # Use available model
        provider = "openai" if st.session_state.model_interface.check_openai_status() else "anthropic"
        system_message = "You are an expert code analyzer specialized in extracting workflow structures from code."
        
        response = st.session_state.model_interface.generate_text(
            prompt=prompt,
            system_message=system_message,
            provider=provider
        )
        
        # Extract JSON from the response
        json_match = re.search(r"```json\n(.*?)\n```", response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON without the markdown code block
            json_match = re.search(r"({.*})", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response
        
        # Remove any non-JSON text before or after
        cleaned_json = re.sub(r"^[^{]*", "", json_str)
        cleaned_json = re.sub(r"[^}]*$", "", cleaned_json)
        
        # Parse JSON
        workflow_data = json.loads(cleaned_json)
        return workflow_data
    except Exception as e:
        st.error(f"Error extracting workflow: {str(e)}")
        return None

def analyze_workflow_efficiency(workflow_data):
    """Analyze workflow efficiency and provide recommendations"""
    if not st.session_state.model_interface.check_openai_status() and not st.session_state.model_interface.check_anthropic_status():
        st.error("No AI services available. Please configure API keys.")
        return None
    
    # Create prompt for workflow analysis
    prompt = f"""
    Analyze the following workflow structure and provide detailed efficiency insights:
    
    ```json
    {json.dumps(workflow_data, indent=2)}
    ```
    
    Please provide:
    1. A high-level assessment of workflow efficiency
    2. Identification of bottlenecks and their impact
    3. Specific optimization recommendations
    4. Potential parallelization opportunities
    5. Complexity reduction strategies
    
    Format your response as a JSON object with the following structure:
    {{
        "efficiency_score": 1-100 score of overall efficiency,
        "analysis": "Detailed workflow efficiency analysis",
        "bottlenecks": [
            {{
                "step_id": "id of bottleneck step",
                "impact": "Description of bottleneck impact",
                "recommendation": "Specific recommendation to address this bottleneck"
            }}
        ],
        "optimization_opportunities": [
            {{
                "type": "Category of optimization (parallelization, refactoring, etc.)",
                "description": "Description of the opportunity",
                "steps_affected": ["step_id1", "step_id2"],
                "estimated_improvement": "Quantitative or qualitative improvement estimate"
            }}
        ],
        "overall_recommendations": [
            "Recommendation 1",
            "Recommendation 2"
        ]
    }}
    """
    
    try:
        # Use available model
        provider = "openai" if st.session_state.model_interface.check_openai_status() else "anthropic"
        system_message = "You are an expert workflow optimization analyst specialized in improving process efficiency."
        
        response = st.session_state.model_interface.generate_text(
            prompt=prompt,
            system_message=system_message,
            provider=provider
        )
        
        # Extract JSON from the response
        json_match = re.search(r"```json\n(.*?)\n```", response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON without the markdown code block
            json_match = re.search(r"({.*})", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response
        
        # Remove any non-JSON text before or after
        cleaned_json = re.sub(r"^[^{]*", "", json_str)
        cleaned_json = re.sub(r"[^}]*$", "", cleaned_json)
        
        # Parse JSON
        analysis_data = json.loads(cleaned_json)
        return analysis_data
    except Exception as e:
        st.error(f"Error analyzing workflow: {str(e)}")
        return None

# Example workflows for demonstration
EXAMPLE_WORKFLOWS = {
    "User Authentication Flow": """
function authenticateUser(username, password) {
  // Step 1: Validate input
  if (!username || !password) {
    throw new Error('Username and password are required');
  }
  
  // Step 2: Check if user exists
  const user = getUserFromDatabase(username);
  if (!user) {
    throw new Error('User not found');
  }
  
  // Step 3: Verify password
  const passwordValid = checkPassword(user.id, password);
  if (!passwordValid) {
    logFailedLoginAttempt(user.id);
    throw new Error('Invalid password');
  }
  
  // Step 4: Generate session token
  const token = generateSessionToken(user.id);
  
  // Step 5: Record login
  recordSuccessfulLogin(user.id);
  
  // Step 6: Return authentication result
  return {
    user: {
      id: user.id,
      username: user.username,
      roles: user.roles
    },
    token: token,
    expires: getTokenExpiration(token)
  };
}

function getUserFromDatabase(username) {
  // Simulate database lookup
  console.log(`Looking up user: ${username}`);
  return { id: 'user123', username: username, roles: ['user'] };
}

function checkPassword(userId, password) {
  // Simulate password verification with hash comparison
  console.log(`Verifying password for user: ${userId}`);
  return true;
}

function logFailedLoginAttempt(userId) {
  console.log(`Failed login attempt for user: ${userId}`);
  // Update failed attempts counter and check for suspicious activity
  checkForSuspiciousActivity(userId);
}

function checkForSuspiciousActivity(userId) {
  // Check for multiple failed login attempts
  console.log(`Checking for suspicious activity for user: ${userId}`);
}

function generateSessionToken(userId) {
  // Generate JWT token
  console.log(`Generating session token for user: ${userId}`);
  return 'jwt-token-12345';
}

function getTokenExpiration(token) {
  // Calculate token expiration time
  return new Date(Date.now() + 3600000); // 1 hour
}

function recordSuccessfulLogin(userId) {
  // Record successful login in audit log
  console.log(`Recording successful login for user: ${userId}`);
  updateLastLoginTimestamp(userId);
}

function updateLastLoginTimestamp(userId) {
  // Update last login timestamp in database
  console.log(`Updating last login timestamp for user: ${userId}`);
}
    """,
    
    "Data Processing Pipeline": """
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

def process_data_pipeline(input_file):
    """Main function to process data through the complete pipeline"""
    # Step 1: Load the raw data
    raw_data = load_data(input_file)
    
    # Step 2: Clean the data
    cleaned_data = clean_data(raw_data)
    
    # Step 3: Transform the data
    transformed_data = transform_data(cleaned_data)
    
    # Step 4: Split the data into training and testing sets
    train_data, test_data = split_data(transformed_data)
    
    # Step 5: Scale the features
    scaled_train, scaled_test = scale_features(train_data, test_data)
    
    # Step 6: Save the processed datasets
    save_processed_data(scaled_train, scaled_test)
    
    return {
        "train_data": scaled_train,
        "test_data": scaled_test,
        "statistics": calculate_statistics(transformed_data)
    }

def load_data(file_path):
    """Load data from CSV file"""
    print(f"Loading data from {file_path}")
    try:
        data = pd.read_csv(file_path)
        print(f"Loaded {len(data)} records")
        return data
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        raise

def clean_data(data):
    """Clean the data by handling missing values and outliers"""
    print("Cleaning data...")
    
    # Handle missing values
    data = handle_missing_values(data)
    
    # Remove outliers
    data = remove_outliers(data)
    
    print(f"Data cleaning complete. {len(data)} records remaining")
    return data

def handle_missing_values(data):
    """Handle missing values in the dataset"""
    print("Handling missing values")
    # Fill numeric columns with median
    numeric_columns = data.select_dtypes(include=[np.number]).columns
    for col in numeric_columns:
        data[col] = data[col].fillna(data[col].median())
    
    # Fill categorical columns with mode
    categorical_columns = data.select_dtypes(include=['object']).columns
    for col in categorical_columns:
        data[col] = data[col].fillna(data[col].mode()[0])
    
    return data

def remove_outliers(data):
    """Remove outliers from the dataset"""
    print("Removing outliers")
    numeric_columns = data.select_dtypes(include=[np.number]).columns
    
    for col in numeric_columns:
        q1 = data[col].quantile(0.25)
        q3 = data[col].quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)
        
        data = data[(data[col] >= lower_bound) & (data[col] <= upper_bound)]
    
    return data

def transform_data(data):
    """Transform the data by creating new features and encoding categorical variables"""
    print("Transforming data")
    
    # Create new features
    data = create_new_features(data)
    
    # Encode categorical variables
    data = encode_categorical_variables(data)
    
    print("Data transformation complete")
    return data

def create_new_features(data):
    """Create new features from existing ones"""
    print("Creating new features")
    # Example: Create a new feature (placeholder for actual implementation)
    if 'feature1' in data.columns and 'feature2' in data.columns:
        data['feature_ratio'] = data['feature1'] / data['feature2'].replace(0, 1)
    
    return data

def encode_categorical_variables(data):
    """Encode categorical variables using one-hot encoding"""
    print("Encoding categorical variables")
    categorical_columns = data.select_dtypes(include=['object']).columns
    
    # Perform one-hot encoding
    data = pd.get_dummies(data, columns=list(categorical_columns))
    
    return data

def split_data(data):
    """Split the data into training and testing sets"""
    print("Splitting data into train and test sets")
    
    # Define features and target
    if 'target' in data.columns:
        X = data.drop('target', axis=1)
        y = data['target']
        
        # Split the data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Combine features and target for return
        train_data = pd.concat([X_train, y_train], axis=1)
        test_data = pd.concat([X_test, y_test], axis=1)
    else:
        # If no target column, just split the data
        train_data, test_data = train_test_split(
            data, test_size=0.2, random_state=42
        )
    
    print(f"Train set: {len(train_data)} records, Test set: {len(test_data)} records")
    return train_data, test_data

def scale_features(train_data, test_data):
    """Scale the features using StandardScaler"""
    print("Scaling features")
    
    # Separate features and target if target exists
    if 'target' in train_data.columns:
        X_train = train_data.drop('target', axis=1)
        y_train = train_data['target']
        X_test = test_data.drop('target', axis=1)
        y_test = test_data['target']
        
        # Initialize and fit the scaler
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Convert back to DataFrame
        X_train_scaled = pd.DataFrame(X_train_scaled, columns=X_train.columns)
        X_test_scaled = pd.DataFrame(X_test_scaled, columns=X_test.columns)
        
        # Combine with target
        train_scaled = pd.concat([X_train_scaled, y_train], axis=1)
        test_scaled = pd.concat([X_test_scaled, y_test], axis=1)
    else:
        # Scale all features
        scaler = StandardScaler()
        train_scaled = pd.DataFrame(
            scaler.fit_transform(train_data),
            columns=train_data.columns
        )
        test_scaled = pd.DataFrame(
            scaler.transform(test_data),
            columns=test_data.columns
        )
    
    print("Feature scaling complete")
    return train_scaled, test_scaled

def save_processed_data(train_data, test_data):
    """Save the processed datasets to CSV files"""
    print("Saving processed data")
    
    train_data.to_csv("processed_train_data.csv", index=False)
    test_data.to_csv("processed_test_data.csv", index=False)
    
    print("Data saved successfully")

def calculate_statistics(data):
    """Calculate and return statistics about the data"""
    print("Calculating statistics")
    
    stats = {
        "record_count": len(data),
        "feature_count": len(data.columns),
        "numeric_features": len(data.select_dtypes(include=[np.number]).columns),
        "categorical_features": len(data.select_dtypes(include=['object']).columns)
    }
    
    return stats

# Example usage
if __name__ == "__main__":
    result = process_data_pipeline("raw_data.csv")
    print("Pipeline completed successfully!")
    print(f"Training data shape: {result['train_data'].shape}")
    print(f"Testing data shape: {result['test_data'].shape}")
    print(f"Data statistics: {result['statistics']}")
    """),
    
    "E-commerce Order Processing": ("""
class OrderProcessor {
    constructor(orderRepository, paymentService, inventoryService, emailService) {
        this.orderRepository = orderRepository;
        this.paymentService = paymentService;
        this.inventoryService = inventoryService;
        this.emailService = emailService;
    }

    async processOrder(orderRequest) {
        console.log(`Starting order processing for order request ${orderRequest.id}`);
        
        try {
            // Step a: Validate the order request
            this.validateOrderRequest(orderRequest);
            
            // Step b: Create order in database
            const order = await this.createOrder(orderRequest);
            
            // Step c: Check product inventory
            await this.checkInventory(order);
            
            // Step d: Process payment
            const paymentResult = await this.processPayment(order);
            
            // Step e: Reserve inventory
            await this.reserveInventory(order);
            
            // Step f: Confirm order
            await this.confirmOrder(order, paymentResult);
            
            // Step g: Send confirmation email
            await this.sendOrderConfirmation(order);
            
            // Step h: Return order details
            return this.getOrderDetails(order.id);
            
        } catch (error) {
            // Handle order processing failure
            console.error(`Order processing failed: ${error.message}`);
            await this.handleOrderFailure(orderRequest, error);
            throw error;
        }
    }
    
    validateOrderRequest(orderRequest) {
        console.log(`Validating order request ${orderRequest.id}`);
        
        // Check for required fields
        if (!orderRequest.customer) {
            throw new Error('Customer information is required');
        }
        
        if (!orderRequest.items || orderRequest.items.length === 0) {
            throw new Error('Order must contain at least one item');
        }
        
        // Validate customer details
        if (!orderRequest.customer.email || !this.isValidEmail(orderRequest.customer.email)) {
            throw new Error('Valid customer email is required');
        }
        
        // Validate shipping address
        if (!orderRequest.shippingAddress) {
            throw new Error('Shipping address is required');
        }
        
        // Validate payment information
        if (!orderRequest.paymentMethod) {
            throw new Error('Payment method is required');
        }
        
        console.log(`Order request ${orderRequest.id} validated successfully`);
    }
    
    isValidEmail(email) {
        // Simple email validation
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    
    async createOrder(orderRequest) {
        console.log(`Creating order for request ${orderRequest.id}`);
        
        // Calculate order totals
        const subtotal = this.calculateSubtotal(orderRequest.items);
        const tax = this.calculateTax(subtotal, orderRequest.shippingAddress.country);
        const shipping = this.calculateShipping(orderRequest.items, orderRequest.shippingAddress);
        const total = subtotal + tax + shipping;
        
        // Create order object
        const order = {
            id: this.generateOrderId(),
            customer: orderRequest.customer,
            items: orderRequest.items,
            shippingAddress: orderRequest.shippingAddress,
            paymentMethod: orderRequest.paymentMethod,
            subtotal: subtotal,
            tax: tax,
            shipping: shipping,
            total: total,
            status: 'PENDING',
            createdAt: new Date().toISOString()
        };
        
        // Save to database
        await this.orderRepository.save(order);
        
        console.log(`Order ${order.id} created successfully`);
        return order;
    }
    
    calculateSubtotal(items) {
        return items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    }
    
    calculateTax(subtotal, country) {
        // Tax calculation would normally depend on country/region
        return subtotal * 0.1; // Example: 10% tax
    }
    
    calculateShipping(items, address) {
        // Shipping calculation would depend on items and shipping address
        const totalWeight = items.reduce((sum, item) => sum + (item.weight * item.quantity), 0);
        
        // Example shipping calculation
        let baseRate = 5;
        if (address.country !== 'US') {
            baseRate = 20; // Higher shipping for international
        }
        
        return baseRate + (totalWeight * 0.5);
    }
    
    generateOrderId() {
        // Generate a unique order ID
        return 'ORD-' + Math.random().toString(36).substring(2, 15);
    }
    
    async checkInventory(order) {
        console.log(`Checking inventory for order ${order.id}`);
        
        // Check each item's inventory
        for (const item of order.items) {
            const inventoryLevel = await this.inventoryService.checkInventory(item.productId);
            
            if (inventoryLevel < item.quantity) {
                throw new Error(`Insufficient inventory for product ${item.productId}`);
            }
        }
        
        console.log(`Inventory check passed for order ${order.id}`);
    }
    
    async processPayment(order) {
        console.log(`Processing payment for order ${order.id}`);
        
        // Create payment request
        const paymentRequest = {
            orderId: order.id,
            amount: order.total,
            currency: 'USD',
            paymentMethod: order.paymentMethod
        };
        
        // Process payment
        const paymentResult = await this.paymentService.processPayment(paymentRequest);
        
        if (!paymentResult.success) {
            throw new Error(`Payment failed: ${paymentResult.errorMessage}`);
        }
        
        console.log(`Payment processed successfully for order ${order.id}`);
        return paymentResult;
    }
    
    async reserveInventory(order) {
        console.log(`Reserving inventory for order ${order.id}`);
        
        // Reserve each item in inventory
        for (const item of order.items) {
            await this.inventoryService.reserveInventory(item.productId, item.quantity);
        }
        
        console.log(`Inventory reserved for order ${order.id}`);
    }
    
    async confirmOrder(order, paymentResult) {
        console.log(`Confirming order ${order.id}`);
        
        // Update order status
        order.status = 'CONFIRMED';
        order.paymentId = paymentResult.transactionId;
        order.confirmedAt = new Date().toISOString();
        
        // Save updated order
        await this.orderRepository.save(order);
        
        console.log(`Order ${order.id} confirmed successfully`);
    }
    
    async sendOrderConfirmation(order) {
        console.log(`Sending order confirmation email for order ${order.id}`);
        
        // Create email content
        const emailContent = {
            to: order.customer.email,
            subject: `Order Confirmation #${order.id}`,
            body: `Thank you for your order! Your order #${order.id} has been confirmed.`,
            templateData: {
                order: {
                    id: order.id,
                    items: order.items,
                    total: order.total
                },
                customer: order.customer
            }
        };
        
        // Send email
        await this.emailService.sendEmail(emailContent);
        
        console.log(`Order confirmation email sent for order ${order.id}`);
    }
    
    async getOrderDetails(orderId) {
        console.log(`Retrieving order details for order ${orderId}`);
        
        // Get order from repository
        const order = await this.orderRepository.findById(orderId);
        
        // Format order details for response
        const orderDetails = {
            orderId: order.id,
            status: order.status,
            items: order.items,
            customer: order.customer,
            shipping: {
                address: order.shippingAddress,
                cost: order.shipping
            },
            payment: {
                subtotal: order.subtotal,
                tax: order.tax,
                total: order.total,
                method: order.paymentMethod.type
            },
            dates: {
                created: order.createdAt,
                confirmed: order.confirmedAt
            }
        };
        
        console.log(`Order details retrieved for order ${orderId}`);
        return orderDetails;
    }
    
    async handleOrderFailure(orderRequest, error) {
        console.log(`Handling order failure for request ${orderRequest.id}`);
        
        // Log the failure
        console.error(`Order processing failed: ${error.message}`);
        
        // Send notification to customer service
        await this.emailService.sendEmail({
            to: 'customer-service@example.com',
            subject: `Order Processing Failure - Request ID: ${orderRequest.id}`,
            body: `Order processing failed: ${error.message}`,
            templateData: {
                orderRequest: orderRequest,
                error: error.message
            }
        });
        
        // If order was created, update its status
        try {
            const existingOrder = await this.orderRepository.findByRequestId(orderRequest.id);
            if (existingOrder) {
                existingOrder.status = 'FAILED';
                existingOrder.errorMessage = error.message;
                await this.orderRepository.save(existingOrder);
            }
        } catch (e) {
            console.error(`Failed to update order status: ${e.message}`);
        }
        
        console.log(`Order failure handling completed for request ${orderRequest.id}`);
    }
}

// Example service implementations would be here
class OrderRepository {
    async save(order) {
        // Save to database
    }
    
    async findById(orderId) {
        // Find by ID
    }
    
    async findByRequestId(requestId) {
        // Find by request ID
    }
}

class PaymentService {
    async processPayment(paymentRequest) {
        // Process payment
    }
}

class InventoryService {
    async checkInventory(productId) {
        // Check inventory
    }
    
    async reserveInventory(productId, quantity) {
        // Reserve inventory
    }
}

class EmailService {
    async sendEmail(emailContent) {
        // Send email
    }
}
    """)
}

# Sidebar
st.sidebar.title("Workflow Visualization")

# Input method selection
input_method = st.sidebar.radio(
    "Input Method",
    ["Example Workflow", "Custom Code"]
)

if input_method == "Example Workflow":
    # Example workflow selection
    selected_example = st.sidebar.selectbox(
        "Select Example Workflow",
        list(EXAMPLE_WORKFLOWS.keys())
    )
    
    code_language = "JavaScript" if "Authentication" in selected_example or "Order" in selected_example else "Python"
    code_to_analyze = EXAMPLE_WORKFLOWS[selected_example]
else:
    # Custom code input
    code_language = st.sidebar.selectbox(
        "Select Language",
        ["Python", "JavaScript", "TypeScript", "Java", "C#", "Go", "SQL"]
    )
    
    code_to_analyze = st.sidebar.text_area(
        "Enter Code to Analyze",
        height=300,
        placeholder=f"Paste your {code_language} code here..."
    )

# Analyze button
if st.sidebar.button("Analyze Workflow"):
    if not code_to_analyze.strip():
        st.sidebar.error("Please enter code to analyze")
    else:
        with st.spinner("Analyzing workflow..."):
            # Extract workflow from code
            workflow_data = extract_workflow_from_code(code_to_analyze, code_language)
            
            if workflow_data:
                st.session_state.workflow_data = workflow_data
                st.session_state.analyzed_code = code_to_analyze
                
                # Analyze workflow efficiency
                st.session_state.workflow_details = analyze_workflow_efficiency(workflow_data)
                
                st.sidebar.success("Workflow analysis completed!")

# Add navigation back to homepage
if st.sidebar.button("Back to Home"):
    st.switch_page("app.py")

# Main content
st.title("Workflow Visualization & Analysis")

# Display workflow visualization and analysis
if st.session_state.workflow_data and st.session_state.workflow_details:
    workflow_data = st.session_state.workflow_data
    workflow_details = st.session_state.workflow_details
    
    # Workflow overview
    st.header("Workflow Overview")
    
    # Display workflow name and description
    st.markdown(f"### {workflow_data.get('workflow_name', 'Unnamed Workflow')}")
    st.markdown(workflow_data.get('workflow_description', 'No description available'))
    
    # Display metrics
    metrics = workflow_data.get('metrics', {})
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(
            f"<div class='metric-card'>"
            f"<div class='metric-label'>Total Steps</div>"
            f"<div class='metric-value'>{metrics.get('total_steps', len(workflow_data.get('steps', [])))}</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            f"<div class='metric-card'>"
            f"<div class='metric-label'>Complexity Score</div>"
            f"<div class='metric-value'>{metrics.get('estimated_complexity', workflow_details.get('efficiency_score', 0))}/100</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    
    with col3:
        bottlenecks = metrics.get('bottlenecks', [])
        bottleneck_count = len(bottlenecks)
        
        st.markdown(
            f"<div class='metric-card'>"
            f"<div class='metric-label'>Bottlenecks Identified</div>"
            f"<div class='metric-value'>{bottleneck_count}</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    
    # Create and display workflow graph
    st.header("Workflow Visualization")
    
    try:
        # Create graph from workflow data
        G = create_graph_from_workflow(workflow_data)
        
        # Identify critical path
        critical_path = identify_critical_path(G)
        
        # Create visualization
        fig = plot_workflow_graph(G, critical_path)
        
        # Display the graph
        st.plotly_chart(fig, use_container_width=True)
        
        # Show critical path
        if critical_path:
            st.subheader("Critical Path")
            critical_steps = [workflow_data["steps"][i]["name"] for i in range(len(workflow_data["steps"])) 
                             if workflow_data["steps"][i]["id"] in critical_path]
            st.markdown(" → ".join(critical_steps))
    except Exception as e:
        st.error(f"Error creating workflow visualization: {str(e)}")
    
    # Efficiency Analysis
    st.header("Efficiency Analysis")
    
    # Overall efficiency
    st.markdown(f"**Overall Efficiency Score:** {workflow_details.get('efficiency_score', 0)}/100")
    st.markdown(workflow_details.get('analysis', 'No analysis available'))
    
    # Bottlenecks
    st.subheader("Bottlenecks")
    bottlenecks = workflow_details.get('bottlenecks', [])
    
    if bottlenecks:
        for i, bottleneck in enumerate(bottlenecks):
            step_id = bottleneck.get("step_id", "")
            step_name = next((step["name"] for step in workflow_data["steps"] if step["id"] == step_id), step_id)
            
            st.markdown(
                f"<div class='step-card'>"
                f"<div class='step-title'>{step_name}</div>"
                f"<div><strong>Impact:</strong> {bottleneck.get('impact', 'Unknown')}</div>"
                f"<div><strong>Recommendation:</strong> {bottleneck.get('recommendation', 'None provided')}</div>"
                f"</div>",
                unsafe_allow_html=True
            )
    else:
        st.info("No bottlenecks identified in this workflow.")
    
    # Optimization opportunities
    st.subheader("Optimization Opportunities")
    opportunities = workflow_details.get('optimization_opportunities', [])
    
    if opportunities:
        for opportunity in opportunities:
            affected_steps = opportunity.get("steps_affected", [])
            affected_step_names = []
            
            for step_id in affected_steps:
                step_name = next((step["name"] for step in workflow_data["steps"] if step["id"] == step_id), step_id)
                affected_step_names.append(step_name)
            
            st.markdown(
                f"<div class='step-card'>"
                f"<div class='step-title'>{opportunity.get('type', 'Optimization')}</div>"
                f"<div>{opportunity.get('description', 'No description')}</div>"
                f"<div class='step-info'><strong>Affected Steps:</strong> {', '.join(affected_step_names)}</div>"
                f"<div class='step-info'><strong>Estimated Improvement:</strong> {opportunity.get('estimated_improvement', 'Unknown')}</div>"
                f"</div>",
                unsafe_allow_html=True
            )
    else:
        st.info("No specific optimization opportunities identified.")
    
    # Overall recommendations
    st.subheader("Overall Recommendations")
    recommendations = workflow_details.get('overall_recommendations', [])
    
    if recommendations:
        for recommendation in recommendations:
            st.markdown(f"- {recommendation}")
    else:
        st.info("No overall recommendations provided.")
        
    # Show workflow steps
    with st.expander("View Workflow Steps", expanded=False):
        steps = workflow_data.get("steps", [])
        for step in steps:
            deps = step.get("depends_on", [])
            dep_names = []
            
            for dep_id in deps:
                dep_step = next((s for s in steps if s["id"] == dep_id), None)
                if dep_step:
                    dep_names.append(dep_step["name"])
            
            st.markdown(
                f"<div class='step-card'>"
                f"<div class='step-title'>{step.get('name', 'Unnamed Step')} ({step.get('id', 'no-id')})</div>"
                f"<div>{step.get('description', 'No description')}</div>"
                f"<div class='step-info'><strong>Type:</strong> {step.get('type', 'task')}</div>"
                f"<div class='step-info'><strong>Duration/Complexity:</strong> {step.get('duration', 1)}/10</div>"
                f"<div class='step-info'><strong>Status:</strong> {step.get('status', 'pending')}</div>"
                f"<div class='step-info'><strong>Dependencies:</strong> {', '.join(dep_names) if dep_names else 'None'}</div>"
                f"</div>",
                unsafe_allow_html=True
            )
else:
    # Welcome message
    st.info("""
    ### Workflow Visualization & Analysis Tool
    
    This tool analyzes code to extract and visualize the workflow structure, identify bottlenecks, 
    and provide optimization recommendations.
    
    To get started:
    1. Select "Example Workflow" or "Custom Code" in the sidebar
    2. Choose from example workflows or enter your own code
    3. Click "Analyze Workflow" to generate insights
    
    The analysis will provide you with:
    - Visual representation of the workflow structure
    - Identification of the critical path
    - Bottleneck detection and analysis
    - Optimization recommendations
    """)
    
    # Show example visualization
    st.image("https://miro.medium.com/max/1400/1*5tZVj32BW2PR2o7j6WZE9A.png", 
             caption="Example workflow visualization", 
             use_column_width=True)