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
import queue

# Page config
st.set_page_config(
    page_title="LLMOps Monitoring Dashboard",
    page_icon="",
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
if 'message_queue' not in st.session_state:
    st.session_state.message_queue = queue.Queue()  # Thread-safe queue for background consumer

class DashboardConsumer:
    """Background consumer for real-time updates - Thread-safe version"""
    def __init__(self, message_queue):
        self.message_queue = message_queue
        try:
            # Use unique consumer group to start fresh each time
            import uuid
            unique_group = f"{config.kafka.consumer_group}-dashboard-{uuid.uuid4().hex[:8]}"
            
            self.consumer = KafkaConsumer(
                config.kafka.response_topic,
                bootstrap_servers=config.kafka.bootstrap_servers,
                group_id=unique_group,  # Unique group ensures fresh start
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',  # Read ALL messages from beginning
                enable_auto_commit=False,  # Don't commit offsets - always start fresh
                consumer_timeout_ms=1000,
                max_poll_records=10  # Limit to reduce load
            )
            self.running = False
            self.message_count = 0
            print(f"✅ Dashboard consumer initialized with group: {unique_group}")
            print(f"   Listening to topic: {config.kafka.response_topic}")
        except Exception as e:
            print(f"❌ Consumer init error: {e}")
            self.consumer = None
        
    def consume(self):
        """Consume messages in background - Thread-safe"""
        if not self.consumer:
            print("⚠️  No consumer available")
            return
            
        self.running = True
        print(f"🎯 Dashboard consumer started, listening to {config.kafka.response_topic}")
        
        while self.running:
            try:
                messages = self.consumer.poll(timeout_ms=1000)
                
                for topic_partition, records in messages.items():
                    for record in records:
                        try:
                            data = record.value
                            self.message_count += 1
                            
                            print(f"📨 Dashboard received message #{self.message_count}: {data.get('request_id', 'N/A')[:8]}")
                            
                            # Use thread-safe queue instead of directly accessing st.session_state
                            self.message_queue.put(data)
                            print(f"    ✅ Added to queue (queue size: ~{self.message_queue.qsize()})")
                            
                        except Exception as e:
                            print(f"    ❌ Error processing message: {e}")
                        
                time.sleep(0.5)  # Small delay to reduce CPU usage
                        
            except Exception as e:
                print(f"❌ Consumer error: {e}")
                time.sleep(2)
    
    def stop(self):
        self.running = False
        if self.consumer:
            self.consumer.close()
        print(f"🛑 Consumer stopped (processed {self.message_count} messages)")

def start_background_consumer():
    """Start consumer in background thread"""
    if not st.session_state.consumer_running:
        consumer = DashboardConsumer(st.session_state.message_queue)
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
                max_results=1000,  # Increased from 50 to show more runs
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
    """Format ISO timestamp to readable string in IST"""
    try:
        dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        # Convert to IST (UTC+5:30)
        ist_dt = dt + timedelta(hours=5, minutes=30)
        return ist_dt.strftime('%H:%M:%S IST')
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
    
    st.markdown('<p class="main-header"> LLMOps Monitoring Dashboard</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Start background consumer
    if not st.session_state.consumer_running:
        with st.spinner("Starting real-time data consumer..."):
            if start_background_consumer():
                st.success(" Real-time consumer started!")
                time.sleep(2)
                st.rerun()
    
    # Sidebar
    with st.sidebar:
        st.header("️ System Status")
        
        # Connection status
        try:
            from kafka import KafkaConsumer
            test_consumer = KafkaConsumer(
                bootstrap_servers=config.kafka.bootstrap_servers,
                consumer_timeout_ms=1000
            )
            test_consumer.close()
            st.success(" Kafka Connected")
        except:
            st.error(" Kafka Offline")
        
        try:
            mlflow.set_tracking_uri(config.mlflow.tracking_uri)
            mlflow.tracking.MlflowClient().search_experiments()
            st.success(" MLflow Connected")
        except:
            st.error(" MLflow Offline")
        
        st.markdown("---")
        st.header(" Configuration")
        st.write(f"**Model:** {config.ollama.model}")
        st.write(f"**Buffer Size:** 50 samples")
        
        
        st.markdown("---")
        st.header("Data Consumer")
        
        # Show consumer status
        if st.session_state.consumer_running:
            st.success("Consumer: RUNNING")
            if hasattr(st.session_state, 'consumer_instance'):
                msg_count = st.session_state.consumer_instance.message_count
                st.metric("Messages Received", msg_count)
                st.metric("Queue Size", st.session_state.message_queue.qsize())
                st.metric("Data Points", len(st.session_state.metrics_data))
                st.metric("Responses", len(st.session_state.response_stream))
        else:
            st.warning("Consumer: NOT RUNNING")
        
        # Restart consumer button
        if st.button("Restart Consumer", help="Restart to read ALL messages from Kafka"):
            if hasattr(st.session_state, 'consumer_instance') and st.session_state.consumer_instance:
                st.session_state.consumer_instance.stop()
            st.session_state.consumer_running = False
            st.session_state.response_stream.clear()
            st.session_state.metrics_data.clear()
            st.info("Restarting consumer...")
            time.sleep(1)
            st.rerun()
        
        st.markdown("---")
        
        # Auto-refresh toggle - ENABLED BY DEFAULT for real-time updates
        auto_refresh = st.checkbox(" Auto Refresh (5s)", value=True)
        st.caption(" Keep this ON to see real-time updates!")
        
        if st.button(" Manual Refresh"):
            st.rerun()
        
        # Clear data button
        if st.button("️ Clear Data"):
            st.session_state.metrics_data.clear()
            st.session_state.response_stream.clear()
            # Also clear the queue
            while not st.session_state.message_queue.empty():
                try:
                    st.session_state.message_queue.get_nowait()
                except:
                    break
            st.success("Data cleared!")
            time.sleep(1)
            st.rerun()
    
    # Process messages from queue (thread-safe way to get data from background consumer)
    messages_processed = 0
    while not st.session_state.message_queue.empty() and messages_processed < 100:
        try:
            data = st.session_state.message_queue.get_nowait()
            
            # Add to metrics data
            st.session_state.metrics_data.append(data)
            
            # Add to response stream for display
            if data.get('status') == 'success':
                response_item = {
                    'timestamp': data['timestamp'],
                    'request_id': data['request_id'][:8],
                    'prompt': data.get('prompt', 'N/A'),  # Original user prompt
                    'response': data.get('response', ''),
                    'latency': data.get('latency', 0),
                    'tokens': data.get('token_count', 0),
                    'response_length': data.get('response_length', 0),
                    'model': data.get('model', 'N/A'),
                    'user_id': data.get('user_id', 'N/A')
                }
                st.session_state.response_stream.append(response_item)
            
            messages_processed += 1
        except queue.Empty:
            break
    
    # Debug: Print to console
    if messages_processed > 0:
        print(f"🔄 Processed {messages_processed} messages from queue on this refresh")

    # Auto-refresh logic - REDUCED TO 5 SECONDS
    if auto_refresh:
        time_diff = (datetime.now() - st.session_state.last_refresh).seconds
        if time_diff >= 5:  # Faster refresh for real-time feel
            st.session_state.last_refresh = datetime.now()
            st.rerun()
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        " Real-time Metrics",
        " Response Stream",
        " MLflow Tracking",
        " Drift Analysis",
        " Auto Streaming"
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
                st.metric(" Avg Tokens", f"{int(avg_tokens)}")
            
            with col3:
                success_rate = (df['status'] == 'success').mean() * 100
                st.metric(" Success Rate", f"{success_rate:.1f}%")
            
            with col4:
                total_requests = len(df)
                st.metric(" Total Requests", total_requests)
            
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
                st.subheader(" Status Distribution")
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
                st.subheader(" Token Distribution")
                fig_tokens = px.histogram(
                    df, 
                    x='token_count',
                    nbins=15,
                    title="Token Count Distribution"
                )
                fig_tokens.update_layout(height=300)
                st.plotly_chart(fig_tokens, use_container_width=True)
            
            with col2:
                st.subheader(" Response Length")
                fig_length = px.histogram(
                    df, 
                    x='response_length',
                    nbins=15,
                    title="Response Length Distribution"
                )
                fig_length.update_layout(height=300)
                st.plotly_chart(fig_length, use_container_width=True)
            
            # Recent requests table
            st.subheader(" Recent Requests")
            display_df = df[['timestamp', 'request_id', 'latency', 'token_count', 'status']].tail(10)
            display_df['timestamp'] = display_df['timestamp'].apply(format_timestamp)
            display_df['request_id'] = display_df['request_id'].str[:8]
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
        else:
            st.info(" Waiting for real-time data... Run a test to see metrics!")
            
    
    # Tab 2: Response Stream
    with tab2:
        st.header("Live Response Stream")
        st.caption("View both requests (prompts) and responses with comprehensive metadata")
        
        if len(st.session_state.response_stream) > 0:
            st.success(f"Showing {len(st.session_state.response_stream)} most recent request-response pairs")
            
            # Display responses in reverse chronological order
            for idx, resp in enumerate(reversed(list(st.session_state.response_stream))):
                with st.expander(
                    f"Request {resp['request_id']} | "
                    f"Latency: {resp['latency']:.2f}s | "
                    f"Tokens: {resp['tokens']} | "
                    f"Time: {format_timestamp(resp['timestamp'])}", 
                    expanded=(idx < 3)  # Expand first 3
                ):
                    # Request Section
                    st.markdown("### Request")
                    st.markdown(f"**Prompt:**")
                    st.info(resp['prompt'])
                    
                    # Response Section
                    st.markdown("### Response")
                    st.markdown(f"**Generated Answer:**")
                    st.success(resp['response'])
                    
                    # Metadata Section
                    st.markdown("---")
                    st.markdown("### Metadata")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Latency", f"{resp['latency']:.2f}s")
                    with col2:
                        st.metric("Tokens", resp['tokens'])
                    with col3:
                        st.metric("Response Length", f"{resp['response_length']} chars")
                    with col4:
                        st.metric("Time", format_timestamp(resp['timestamp']))
                    
                    # Additional details
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Model:** {resp['model']}")
                    with col2:
                        st.write(f"**User ID:** {resp['user_id']}")
                    with col3:
                        st.write(f"**Request ID:** {resp['request_id']}")
                    
        else:
            st.info("No responses yet. Run a test to see LLM request-response pairs stream in!")
            st.markdown("""
                **To start seeing responses:**
                1. Use the **Test LLM** tab to send individual requests
                2. Watch request-response pairs appear here in real-time!
                
                **What you'll see:**
                - The original prompt/question
                - The LLM's generated response
                - Comprehensive metadata (latency, tokens, model, etc.)
            """)
    
    # Tab 3: MLflow Tracking
    with tab3:
        st.header(" MLflow Experiment Tracking")
        
        with st.spinner("Loading MLflow data..."):
            mlflow_df = get_mlflow_metrics()
        
        if not mlflow_df.empty:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(" Total Runs", len(mlflow_df))
            
            with col2:
                avg_lat = mlflow_df['latency'].mean()
                st.metric("⏱️ Avg Latency", f"{avg_lat:.2f}s")
            
            with col3:
                avg_tok = mlflow_df['tokens'].mean()
                st.metric(" Avg Tokens", f"{int(avg_tok)}")
            
            with col4:
                success = (mlflow_df['status'] == 'success').sum()
                st.metric(" Successful", success)
            
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
            st.subheader(" Tokens vs Latency")
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
            st.subheader(" Experiment Runs")
            st.dataframe(mlflow_df, use_container_width=True, hide_index=True)
            
            # MLflow UI link
            st.markdown(f" [Open MLflow UI]({config.mlflow.tracking_uri})")
        else:
            st.warning("️ No MLflow data available. Ensure MLflow consumer is running.")
            st.code("Check MLflow Consumer window for errors")
    
    # Tab 4: Drift Analysis
    with tab4:
        st.header(" Data Drift Reports")
        
        reports = get_evidently_reports()
        
        if reports:
            st.success(f" Found {len(reports)} drift reports")
            
            # Report selector
            selected_report = st.selectbox(
                " Select a report to view:",
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
                    " Download Report",
                    report_html,
                    file_name=selected_report.name,
                    mime="text/html"
                )
        else:
            st.info(" No drift reports yet. Reports are generated after collecting enough samples.")
            st.markdown(f"""
                **How it works:**
                - Evidently collects responses in batches
                - After **{config.evidently.batch_size} samples**, a drift report is generated
                - Reports show data quality and drift metrics
                
                **Current status:** Waiting for {config.evidently.batch_size} samples
            """)
    
    
    # # Tab 5: Test LLM (HIDDEN FOR NOW)
    # with tab5:
    #     st.header("🧪 Test LLM Interface")
    #     ... (commented out)
    
    # Tab 5: Auto Streaming
    with tab5:
        st.header(" Automated Test Data Streaming")
        
        st.info(" Start streaming test data automatically without opening a terminal. Perfect for continuous testing!")
        
        # Initialize streaming state
        if 'streaming_active' not in st.session_state:
            st.session_state.streaming_active = False
        if 'streaming_thread' not in st.session_state:
            st.session_state.streaming_thread = None
        if 'streaming_stats' not in st.session_state:
            st.session_state.streaming_stats = {
                'total': 0,
                'successful': 0,
                'failed': 0,
                'current': 0
            }
        
        # Configuration section
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("️ Configuration")
            
            # Find available test files
            from pathlib import Path
            data_dir = Path("./data")
            test_files = []
            if data_dir.exists():
                test_files = [f.name for f in data_dir.glob("*.json")]
            
            if not test_files:
                st.error(" No test files found in ./data/ directory")
                test_file = None
            else:
                test_file = st.selectbox(
                    " Select Test File",
                    test_files,
                    index=test_files.index("quick_test.json") if "quick_test.json" in test_files else 0
                )
            
            delay = st.slider(
                "⏱️ Delay Between Requests (seconds)",
                min_value=1.0,
                max_value=10.0,
                value=3.0,
                step=0.5,
                help="Time to wait between sending each request"
            )
            
            loop_mode = st.checkbox(
                " Loop Continuously",
                value=False,
                help="Keep streaming data in a loop (restart from beginning when done)"
            )
            
        with col2:
            st.subheader(" Streaming Status")
            
            if st.session_state.streaming_active:
                st.success(" Streaming ACTIVE")
            else:
                st.info(" Streaming STOPPED")
            
            # Stats display
            stats = st.session_state.streaming_stats
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric(" Total Sent", stats['total'])
            with col_b:
                st.metric(" Success", stats['successful'])
            with col_c:
                st.metric(" Failed", stats['failed'])
            
            if stats['total'] > 0:
                st.progress(stats['current'] / max(stats['total'], 1))
        
        st.markdown("---")
        
        # Control buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("▶️ Start Streaming", disabled=st.session_state.streaming_active or not test_file, use_container_width=True):
                if test_file:
                    st.session_state.streaming_active = True
                    st.session_state.streaming_config = {
                        'file': test_file,
                        'delay': delay,
                        'loop': loop_mode
                    }
                    # Reset stats
                    st.session_state.streaming_stats = {
                        'total': 0,
                        'successful': 0,
                        'failed': 0,
                        'current': 0
                    }
                    st.rerun()
        
        with col2:
            if st.button("⏸️ Stop Streaming", disabled=not st.session_state.streaming_active, use_container_width=True):
                st.session_state.streaming_active = False
                st.rerun()
        
        with col3:
            if st.button(" Reset Stats", use_container_width=True):
                st.session_state.streaming_stats = {
                    'total': 0,
                    'successful': 0,
                    'failed': 0,
                    'current': 0
                }
                st.rerun()
        
        with col4:
            if st.button(" Refresh Files", use_container_width=True):
                st.rerun()
        
        # Start streaming in background if active
        if st.session_state.streaming_active:
            try:
                from batch_producer import BatchProducer
                import json
                
                # Load prompts
                config_data = st.session_state.streaming_config
                file_path = Path("./data") / config_data['file']
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    prompts = json.load(f)
                
                if isinstance(prompts, list) and len(prompts) > 0:
                    if not isinstance(prompts[0], dict):
                        prompts = [{"prompt": p, "category": "unknown", "complexity": "unknown"} for p in prompts]
                    
                    st.session_state.streaming_stats['total'] = len(prompts)
                    
                    # Show current streaming info
                    st.markdown("---")
                    st.subheader(" Current Streaming Session")
                    
                    info_col1, info_col2, info_col3 = st.columns(3)
                    with info_col1:
                        st.write(f"**File:** {config_data['file']}")
                    with info_col2:
                        st.write(f"**Prompts:** {len(prompts)}")
                    with info_col3:
                        st.write(f"**Delay:** {config_data['delay']}s")
                    
                    # Process one request per rerun (non-blocking)
                    current = st.session_state.streaming_stats['current']
                    
                    if current < len(prompts):
                        prompt_data = prompts[current]
                        prompt_text = prompt_data.get('prompt', str(prompt_data))
                        
                        st.write(f"**Sending request {current + 1}/{len(prompts)}...**")
                        st.write(f" Prompt: {prompt_text[:100]}{'...' if len(prompt_text) > 100 else ''}")
                        
                        try:
                            # Initialize producer if needed
                            if 'streaming_producer' not in st.session_state:
                                st.session_state.streaming_producer = BatchProducer()
                            
                            # Don't use spinner - it blocks the rerun mechanism
                            response, request_id = st.session_state.streaming_producer.producer.generate_response(
                                prompt_text,
                                user_id="streamlit_auto"
                            )
                            
                            st.session_state.streaming_stats['successful'] += 1
                            st.success(f"Request {current + 1} sent successfully! ID: {request_id[:8]}")
                            
                        except Exception as e:
                            st.session_state.streaming_stats['failed'] += 1
                            st.error(f"Request {current + 1} failed: {str(e)[:100]}")
                        
                        # Update current position
                        st.session_state.streaming_stats['current'] = current + 1
                        
                        # Wait and rerun
                        time.sleep(config_data['delay'])
                        st.rerun()
                    
                    else:
                        # Finished streaming
                        if config_data['loop']:
                            st.info(" Restarting from beginning (Loop Mode)")
                            st.session_state.streaming_stats['current'] = 0
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.success(" Streaming completed!")
                            st.balloons()
                            st.session_state.streaming_active = False
                            if st.button(" Start Again"):
                                st.session_state.streaming_stats['current'] = 0
                                st.session_state.streaming_active = True
                                st.rerun()
                
            except Exception as e:
                st.error(f" Streaming error: {str(e)}")
                st.session_state.streaming_active = False
                import traceback
                with st.expander(" Error Details"):
                    st.code(traceback.format_exc())
        
        else:
            # Show instructions when not streaming
            st.markdown("---")
            
    
    
    # Footer
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(" [MLflow UI](http://localhost:5000)")
    
    with col2:
        st.markdown(f" Last update: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()