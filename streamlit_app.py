import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import mlflow
from kafka import KafkaConsumer
import threading
import time
from config import config
import os
from pathlib import Path
from collections import deque

# Page config
st.set_page_config(
    page_title="LLMOps Monitoring Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state with optimized buffer size
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'metrics_data' not in st.session_state:
    st.session_state.metrics_data = deque(maxlen=50)  # Keep last 50 for performance
if 'consumer_running' not in st.session_state:
    st.session_state.consumer_running = False
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()
if 'response_stream' not in st.session_state:
    st.session_state.response_stream = deque(maxlen=20)  # Last 20 responses

class DashboardConsumer:
    """Background consumer for real-time updates - Optimized"""
    def __init__(self):
        try:
            self.consumer = KafkaConsumer(
                config.kafka.response_topic,
                bootstrap_servers=config.kafka.bootstrap_servers,
                group_id=f"{config.kafka.consumer_group}-dashboard-{int(time.time())}",
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True,
                consumer_timeout_ms=1000,
                max_poll_records=10  # Limit to reduce load
            )
            self.running = False
            print("✅ Dashboard consumer initialized")
        except Exception as e:
            print(f"❌ Consumer init error: {e}")
            self.consumer = None
        
    def consume(self):
        """Consume messages in background"""
        if not self.consumer:
            print("❌ No consumer available")
            return
            
        self.running = True
        print("👂 Dashboard consumer started")
        
        while self.running:
            try:
                messages = self.consumer.poll(timeout_ms=1000)
                
                for topic_partition, records in messages.items():
                    for record in records:
                        data = record.value
                        
                        # Add to metrics
                        st.session_state.metrics_data.append(data)
                        
                        # Add to response stream for display
                        if data.get('status') == 'success':
                            st.session_state.response_stream.append({
                                'timestamp': data['timestamp'],
                                'request_id': data['request_id'][:8],
                                'response': data.get('response', ''),
                                'latency': data.get('latency', 0),
                                'tokens': data.get('token_count', 0)
                            })
                        
                time.sleep(0.5)  # Small delay to reduce CPU usage
                        
            except Exception as e:
                print(f"Consumer error: {e}")
                time.sleep(2)
    
    def stop(self):
        self.running = False
        if self.consumer:
            self.consumer.close()
        print("🛑 Consumer stopped")

def start_background_consumer():
    """Start consumer in background thread"""
    if not st.session_state.consumer_running:
        consumer = DashboardConsumer()
        thread = threading.Thread(target=consumer.consume, daemon=True)
        thread.start()
        st.session_state.consumer_running = True
        st.session_state.consumer_thread = thread
        st.session_state.consumer_instance = consumer
        return True
    return False

def get_mlflow_metrics():
    """Fetch metrics from MLflow - with error handling"""
    try:
        mlflow.set_tracking_uri(config.mlflow.tracking_uri)
        client = mlflow.tracking.MlflowClient()
        
        experiment = client.get_experiment_by_name(config.mlflow.experiment_name)
        if experiment:
            runs = client.search_runs(
                experiment.experiment_id, 
                max_results=50,
                order_by=["start_time DESC"]
            )
            
            metrics_list = []
            for run in runs:
                try:
                    metrics_list.append({
                        'run_id': run.info.run_id[:8],
                        'latency': run.data.metrics.get('latency_seconds', 0),
                        'tokens': run.data.metrics.get('token_count', 0),
                        'response_length': run.data.metrics.get('response_length', 0),
                        'status': run.data.tags.get('status', 'unknown'),
                        'timestamp': datetime.fromtimestamp(run.info.start_time / 1000)
                    })
                except Exception as e:
                    continue
            
            return pd.DataFrame(metrics_list)
    except Exception as e:
        st.warning(f"MLflow connection issue: {str(e)}")
        return pd.DataFrame()
    
    return pd.DataFrame()

def get_evidently_reports():
    """Get latest Evidently reports"""
    reports_dir = Path(config.evidently.reports_dir)
    if not reports_dir.exists():
        return []
    
    try:
        reports = list(reports_dir.glob("drift_report_*.html"))
        reports.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return reports[:5]
    except Exception as e:
        return []

def format_timestamp(ts_str):
    """Format ISO timestamp to readable string"""
    try:
        dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        return dt.strftime('%H:%M:%S')
    except:
        return ts_str

def main():
    # Custom CSS for better appearance
    st.markdown("""
        <style>
        .main-header {font-size: 2.5rem; font-weight: bold; color: #1E88E5;}
        .metric-card {
            background-color: #f0f2f6;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .status-success {color: #4CAF50; font-weight: bold;}
        .status-error {color: #f44336; font-weight: bold;}
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<p class="main-header">🤖 LLMOps Monitoring Dashboard</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Start background consumer
    if not st.session_state.consumer_running:
        with st.spinner("Starting real-time data consumer..."):
            if start_background_consumer():
                st.success("✅ Real-time consumer started!")
                time.sleep(2)
                st.rerun()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ System Status")
        
        # Connection status
        try:
            from kafka import KafkaConsumer
            test_consumer = KafkaConsumer(
                bootstrap_servers=config.kafka.bootstrap_servers,
                consumer_timeout_ms=1000
            )
            test_consumer.close()
            st.success("🟢 Kafka Connected")
        except:
            st.error("🔴 Kafka Offline")
        
        try:
            mlflow.set_tracking_uri(config.mlflow.tracking_uri)
            mlflow.tracking.MlflowClient().search_experiments()
            st.success("🟢 MLflow Connected")
        except:
            st.error("🔴 MLflow Offline")
        
        st.markdown("---")
        st.header("🔧 Configuration")
        st.write(f"**Model:** {config.ollama.model}")
        st.write(f"**Kafka:** localhost:9092")
        st.write(f"**Buffer Size:** 50 samples")
        
        st.markdown("---")
        
        # Auto-refresh toggle
        auto_refresh = st.checkbox("🔄 Auto Refresh (10s)", value=False)
        
        if st.button("🔄 Manual Refresh"):
            st.rerun()
        
        # Clear data button
        if st.button("🗑️ Clear Data"):
            st.session_state.metrics_data.clear()
            st.session_state.response_stream.clear()
            st.success("Data cleared!")
            time.sleep(1)
            st.rerun()
    
    # Auto-refresh logic
    if auto_refresh:
        time_diff = (datetime.now() - st.session_state.last_refresh).seconds
        if time_diff >= 10:
            st.session_state.last_refresh = datetime.now()
            st.rerun()
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Real-time Metrics",
        "💬 Response Stream",
        "📈 MLflow Tracking",
        "📉 Drift Analysis",
        "🧪 Test LLM"
    ])
    
    # Tab 1: Real-time Metrics
    with tab1:
        st.header("Real-time Performance Metrics")
        
        if len(st.session_state.metrics_data) > 0:
            df = pd.DataFrame(list(st.session_state.metrics_data))
            
            # Metrics summary
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                avg_latency = df['latency'].mean()
                st.metric("⏱️ Avg Latency", f"{avg_latency:.2f}s")
            
            with col2:
                avg_tokens = df['token_count'].mean()
                st.metric("🔤 Avg Tokens", f"{int(avg_tokens)}")
            
            with col3:
                success_rate = (df['status'] == 'success').mean() * 100
                st.metric("✅ Success Rate", f"{success_rate:.1f}%")
            
            with col4:
                total_requests = len(df)
                st.metric("📨 Total Requests", total_requests)
            
            st.markdown("---")
            
            # Charts in columns
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("⏱️ Latency Trend")
                fig_latency = px.line(
                    df.reset_index(), 
                    x='index', 
                    y='latency',
                    title="Request Latency Over Time",
                    labels={'index': 'Request #', 'latency': 'Latency (s)'}
                )
                fig_latency.update_layout(height=300)
                st.plotly_chart(fig_latency, use_container_width=True)
            
            with col2:
                st.subheader("📊 Status Distribution")
                status_counts = df['status'].value_counts()
                fig_status = px.pie(
                    values=status_counts.values,
                    names=status_counts.index,
                    title="Request Status",
                    color_discrete_sequence=['#4CAF50', '#f44336']
                )
                fig_status.update_layout(height=300)
                st.plotly_chart(fig_status, use_container_width=True)
            
            # Token and response length distribution
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🔤 Token Distribution")
                fig_tokens = px.histogram(
                    df, 
                    x='token_count',
                    nbins=15,
                    title="Token Count Distribution"
                )
                fig_tokens.update_layout(height=300)
                st.plotly_chart(fig_tokens, use_container_width=True)
            
            with col2:
                st.subheader("📏 Response Length")
                fig_length = px.histogram(
                    df, 
                    x='response_length',
                    nbins=15,
                    title="Response Length Distribution"
                )
                fig_length.update_layout(height=300)
                st.plotly_chart(fig_length, use_container_width=True)
            
            # Recent requests table
            st.subheader("📋 Recent Requests")
            display_df = df[['timestamp', 'request_id', 'latency', 'token_count', 'status']].tail(10)
            display_df['timestamp'] = display_df['timestamp'].apply(format_timestamp)
            display_df['request_id'] = display_df['request_id'].str[:8]
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
        else:
            st.info("📡 Waiting for real-time data... Run a test to see metrics!")
            st.code("python batch_producer.py --file data/quick_test.json --delay 3.0")
    
    # Tab 2: Response Stream
    with tab2:
        st.header("💬 Live Response Stream")
        
        if len(st.session_state.response_stream) > 0:
            st.success(f"📊 Showing {len(st.session_state.response_stream)} most recent responses")
            
            # Display responses in reverse chronological order
            for idx, resp in enumerate(reversed(list(st.session_state.response_stream))):
                with st.expander(
                    f"🔹 Response {resp['request_id']} | "
                    f"⏱️ {resp['latency']:.2f}s | "
                    f"🔤 {resp['tokens']} tokens | "
                    f"🕐 {format_timestamp(resp['timestamp'])}", 
                    expanded=(idx < 3)  # Expand first 3
                ):
                    st.markdown("**Response:**")
                    st.write(resp['response'])
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Latency", f"{resp['latency']:.2f}s")
                    with col2:
                        st.metric("Tokens", resp['tokens'])
                    with col3:
                        st.metric("Time", format_timestamp(resp['timestamp']))
        else:
            st.info("📭 No responses yet. Run a test to see LLM responses stream in!")
            st.markdown("""
                **To start seeing responses:**
                1. Open a new terminal
                2. Run: `python batch_producer.py --file data/quick_test.json --delay 3.0`
                3. Watch responses appear here in real-time!
            """)
    
    # Tab 3: MLflow Tracking
    with tab3:
        st.header("📈 MLflow Experiment Tracking")
        
        with st.spinner("Loading MLflow data..."):
            mlflow_df = get_mlflow_metrics()
        
        if not mlflow_df.empty:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📊 Total Runs", len(mlflow_df))
            
            with col2:
                avg_lat = mlflow_df['latency'].mean()
                st.metric("⏱️ Avg Latency", f"{avg_lat:.2f}s")
            
            with col3:
                avg_tok = mlflow_df['tokens'].mean()
                st.metric("🔤 Avg Tokens", f"{int(avg_tok)}")
            
            with col4:
                success = (mlflow_df['status'] == 'success').sum()
                st.metric("✅ Successful", success)
            
            st.markdown("---")
            
            # Latency over time
            st.subheader("⏱️ Latency Trend")
            fig = px.line(
                mlflow_df,
                x='timestamp',
                y='latency',
                title="Latency Over Time",
                markers=True
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # Token vs Latency scatter
            st.subheader("🔤 Tokens vs Latency")
            fig_scatter = px.scatter(
                mlflow_df,
                x='tokens',
                y='latency',
                color='status',
                size='response_length',
                title="Token Count vs Latency",
                hover_data=['run_id']
            )
            fig_scatter.update_layout(height=400)
            st.plotly_chart(fig_scatter, use_container_width=True)
            
            # Detailed runs table
            st.subheader("📋 Experiment Runs")
            st.dataframe(mlflow_df, use_container_width=True, hide_index=True)
            
            # MLflow UI link
            st.markdown(f"🔗 [Open MLflow UI]({config.mlflow.tracking_uri})")
        else:
            st.warning("⚠️ No MLflow data available. Ensure MLflow consumer is running.")
            st.code("Check MLflow Consumer window for errors")
    
    # Tab 4: Drift Analysis
    with tab4:
        st.header("📉 Data Drift Reports")
        
        reports = get_evidently_reports()
        
        if reports:
            st.success(f"✅ Found {len(reports)} drift reports")
            
            # Report selector
            selected_report = st.selectbox(
                "📊 Select a report to view:",
                reports,
                format_func=lambda x: f"{x.name} ({datetime.fromtimestamp(x.stat().st_mtime).strftime('%Y-%m-%d %H:%M')})"
            )
            
            if selected_report:
                # Display report
                with open(selected_report, 'r', encoding='utf-8') as f:
                    report_html = f.read()
                st.components.v1.html(report_html, height=800, scrolling=True)
                
                # Download button
                st.download_button(
                    "📥 Download Report",
                    report_html,
                    file_name=selected_report.name,
                    mime="text/html"
                )
        else:
            st.info("📊 No drift reports yet. Reports are generated after collecting enough samples.")
            st.markdown(f"""
                **How it works:**
                - Evidently collects responses in batches
                - After **{config.evidently.batch_size} samples**, a drift report is generated
                - Reports show data quality and drift metrics
                
                **Current status:** Waiting for {config.evidently.batch_size} samples
            """)
    
    # Tab 5: Test LLM
    with tab5:
        st.header("🧪 Test LLM Interface")
        
        st.info("💡 This sends requests through the full monitoring pipeline (Kafka → LLM → Monitoring)")
        
        try:
            from producer import LLMProducer
            
            # Initialize producer
            if 'producer' not in st.session_state:
                with st.spinner("Initializing LLM producer..."):
                    st.session_state.producer = LLMProducer()
                    st.success("✅ Producer ready!")
            
            # Display chat messages
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
            
            # Chat input
            prompt = st.chat_input("Ask a question...")
            
            if prompt:
                # Display user message
                with st.chat_message("user"):
                    st.write(prompt)
                st.session_state.messages.append({"role": "user", "content": prompt})
                
                # Get LLM response
                with st.chat_message("assistant"):
                    with st.spinner("🤔 Thinking..."):
                        try:
                            response, request_id = st.session_state.producer.generate_response(prompt)
                            
                            st.write(response)
                            st.caption(f"Request ID: {request_id[:8]} | Check metrics tab for details!")
                            
                            # Add to messages
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": response
                            })
                            
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                            st.write("**Troubleshooting:**")
                            st.write("1. Check if Ollama is running: `ollama serve`")
                            st.write("2. Check if Kafka is running")
                            st.write("3. Check consumer windows for errors")
            
            # Quick test prompts
            with st.expander("💡 Quick Test Prompts"):
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("What is AI?"):
                        st.session_state.test_prompt = "What is artificial intelligence?"
                        st.rerun()
                    if st.button("Explain ML"):
                        st.session_state.test_prompt = "Explain machine learning in simple terms"
                        st.rerun()
                
                with col2:
                    if st.button("Python tips"):
                        st.session_state.test_prompt = "Give me 3 Python programming tips"
                        st.rerun()
                    if st.button("Cloud computing"):
                        st.session_state.test_prompt = "What are benefits of cloud computing?"
                        st.rerun()
            
            # Clear chat
            if st.button("🗑️ Clear Chat"):
                st.session_state.messages = []
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ Failed to initialize: {str(e)}")
            st.markdown("""
                **Troubleshooting:**
                1. Ensure Kafka is running on port 9092
                2. Ensure Ollama is running on port 11434
                3. Check that `producer.py` exists
                4. Run: `pip install -r requirements.txt`
            """)
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("🔗 [MLflow UI](http://localhost:5000)")
    with col2:
        st.markdown("📊 [Kafka Topics](http://localhost:9092)")
    with col3:
        st.markdown(f"🕐 Last update: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()