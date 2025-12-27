import json
import os
import pandas as pd
from kafka import KafkaConsumer
from evidently import Report
from evidently.metrics import (
    # Drift metrics available in Evidently 0.7.17
    DriftedColumnsCount,
    ValueDrift,
    
    # Data quality metrics
    DatasetMissingValueCount,
    
    # Correlation metrics for richer analysis
    DatasetCorrelations,
    ColumnCorrelations,
    ColumnCorrelationMatrix,
)
from config import config
from datetime import datetime
import traceback

class EvidentlyConsumer:
    """Evidently consumer for data drift monitoring - Enhanced with comprehensive metrics"""
    
    def __init__(self):
        # Create reports directory
        os.makedirs(config.evidently.reports_dir, exist_ok=True)
        
        print("🔧 Initializing Evidently Consumer...")
        
        try:
            # Initialize Kafka Consumer
            self.consumer = KafkaConsumer(
                config.kafka.response_topic,
                bootstrap_servers=config.kafka.bootstrap_servers,
                group_id=f"{config.kafka.consumer_group}-evidently",
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True,
                consumer_timeout_ms=config.performance.consumer_timeout_ms
            )
            
            print(f"✅ Connected to topic: {config.kafka.response_topic}")
            
        except Exception as e:
            print(f"❌ Failed to connect to Kafka: {e}")
            raise
        
        # Data buffer
        self.current_data = []
        self.reference_data = None
        self.batch_count = 0
        
        # Drift tracking
        self.drift_history = []
        
        print(f"📊 Batch size: {config.evidently.batch_size} samples")
        print(f"📁 Reports directory: {config.evidently.reports_dir}")
        
    def load_reference_data(self):
        """Load reference dataset"""
        try:
            if os.path.exists(config.evidently.reference_data_path):
                self.reference_data = pd.read_csv(config.evidently.reference_data_path)
                print(f"✅ Loaded reference data: {len(self.reference_data)} samples")
                
                # Show reference data statistics
                print("\n📊 Reference Data Statistics:")
                numeric_cols = ['latency', 'token_count', 'response_length']
                for col in numeric_cols:
                    if col in self.reference_data.columns:
                        mean = self.reference_data[col].mean()
                        std = self.reference_data[col].std()
                        print(f"  {col}: μ={mean:.2f}, σ={std:.2f}")
                
                return True
            else:
                print("⚠️ No reference data found. Will create after first batch.")
                return False
        except Exception as e:
            print(f"⚠️ Error loading reference data: {e}")
            return False
    
    def create_dataframe(self, data_list):
        """Convert message list to DataFrame with proper data types"""
        try:
            df = pd.DataFrame([{
                'request_id': str(d.get('request_id', 'unknown'))[:16],
                'timestamp': pd.to_datetime(d.get('timestamp')),
                'latency': float(d.get('latency', 0.0)),
                'token_count': int(d.get('token_count', 0)),
                'response_length': int(d.get('response_length', 0)),
                'model': str(d.get('model', 'unknown')),
                'status': str(d.get('status', 'unknown'))
            } for d in data_list])
            
            return df
        except Exception as e:
            print(f"❌ Error creating dataframe: {e}")
            traceback.print_exc()
            return pd.DataFrame()
    
    def generate_report(self, current_df, reference_df):
        """Generate comprehensive drift report with rich metrics"""
        try:
            print("\n📊 Generating Comprehensive Drift Report...")
            
            # Ensure both dataframes have same columns
            common_cols = list(set(current_df.columns) & set(reference_df.columns))
            current_clean = current_df[common_cols].copy()
            reference_clean = reference_df[common_cols].copy()
            
            # Focus on numeric columns for drift analysis
            numeric_cols = ['latency', 'token_count', 'response_length']
            current_numeric = current_clean[numeric_cols]
            reference_numeric = reference_clean[numeric_cols]
            
            # Build comprehensive metrics list (compatible with Evidently 0.7.17)
            metrics = [
                # Overall drift count - shows how many columns are drifting
                DriftedColumnsCount(),
                
                # Per-column drift detection (available in 0.7.17)
                ValueDrift(column="latency"),
                ValueDrift(column="token_count"),
                ValueDrift(column="response_length"),
                
                # Data quality
                DatasetMissingValueCount(),
                
                # Correlation analysis (shows relationships between metrics)
                DatasetCorrelations(),
            ]
            
            # Create report
            report = Report(metrics=metrics)
            
            print("🔄 Running comprehensive drift analysis...")
            print(f"   Reference: {len(reference_numeric)} samples")
            print(f"   Current:   {len(current_numeric)} samples")
            
            snapshot = report.run(
                reference_data=reference_numeric,
                current_data=current_numeric
            )
            
            # Extract drift scores for logging
            try:
                result_dict = snapshot.as_dict()
                dataset_drift = result_dict['metrics'][0]['result']
                
                drift_info = {
                    'timestamp': datetime.now().isoformat(),
                    'batch_number': self.batch_count,
                    'dataset_drift_detected': dataset_drift.get('drift_share', 0),
                    'number_of_drifted_columns': dataset_drift.get('number_of_drifted_columns', 0)
                }
                
                self.drift_history.append(drift_info)
                
                print(f"\n📈 Drift Analysis Results:")
                print(f"   Drift Share: {drift_info['dataset_drift_detected']:.2%}")
                print(f"   Drifted Columns: {drift_info['number_of_drifted_columns']}")
                
            except Exception as e:
                print(f"   ⚠️ Could not extract drift scores: {e}")
            
            # Save HTML report with better naming
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            drift_score = drift_info.get('dataset_drift_detected', 0) if 'drift_info' in locals() else 0
            
            report_filename = f"drift_report_{timestamp}_batch-{self.batch_count:03d}_drift-{drift_score:.3f}.html"
            report_path = os.path.join(config.evidently.reports_dir, report_filename)
            
            snapshot.save_html(report_path)
            print(f"✅ HTML Report saved: {report_filename}")
            
            # Save JSON summary
            if config.evidently.generate_json:
                json_path = report_path.replace('.html', '.json')
                snapshot.save_json(json_path)
                print(f"✅ JSON Summary saved")
            
            # Save drift history
            self._save_drift_history()
            
            return report_path
            
        except Exception as e:
            print(f"❌ Error generating report: {e}")
            traceback.print_exc()
            return None
    
    def _save_drift_history(self):
        """Save drift history to JSON for trend analysis"""
        try:
            history_path = os.path.join(config.evidently.reports_dir, "drift_history.json")
            with open(history_path, 'w') as f:
                json.dump(self.drift_history, f, indent=2)
            print(f"📊 Drift history saved ({len(self.drift_history)} batches)")
        except Exception as e:
            print(f"⚠️ Could not save drift history: {e}")
    
    def start_consuming(self):
        """Start consuming and analyzing messages"""
        print("👂 Starting to consume messages...")
        print("=" * 60)
        
        self.load_reference_data()
        
        try:
            for message in self.consumer:
                data = message.value
                
                # Skip failed requests
                if data.get('status') != 'success':
                    print(f"⏭️ Skipping failed request: {data.get('request_id', 'unknown')[:8]}")
                    continue
                
                self.current_data.append(data)
                print(f"📥 Collected: {len(self.current_data)}/{config.evidently.batch_size} samples", end='\r')
                
                # Generate report when batch is full
                if len(self.current_data) >= config.evidently.batch_size:
                    self.batch_count += 1
                    print(f"\n\n🔬 Batch #{self.batch_count} complete! Generating drift analysis...")
                    print("=" * 60)
                    
                    current_df = self.create_dataframe(self.current_data)
                    
                    if current_df.empty:
                        print("❌ Failed to create dataframe")
                        self.current_data = []
                        continue
                    
                    # Show current batch statistics
                    print("\n📊 Current Batch Statistics:")
                    for col in ['latency', 'token_count', 'response_length']:
                        mean = current_df[col].mean()
                        std = current_df[col].std()
                        print(f"  {col}: μ={mean:.2f}, σ={std:.2f}")
                    
                    # Create reference data if not exists
                    if self.reference_data is None:
                        self.reference_data = current_df.copy()
                        
                        # Ensure data directory exists
                        os.makedirs(os.path.dirname(config.evidently.reference_data_path), exist_ok=True)
                        
                        self.reference_data.to_csv(config.evidently.reference_data_path, index=False)
                        print(f"\n✅ Created reference dataset with {len(self.reference_data)} samples")
                        print(f"📁 Saved to: {config.evidently.reference_data_path}")
                    else:
                        # Generate drift report
                        report_path = self.generate_report(current_df, self.reference_data)
                        
                        if report_path:
                            print(f"✅ Comprehensive drift analysis complete!")
                            print(f"📊 View report: {report_path}")
                        else:
                            print("⚠️ Report generation had issues, but continuing...")
                    
                    # Clear buffer
                    self.current_data = []
                    print("=" * 60)
                    print("👂 Continuing to collect samples...\n")
                    
        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down Evidently consumer...")
            
            # Save remaining data as reference if needed
            if len(self.current_data) > 0:
                print(f"\n💾 Saving {len(self.current_data)} samples...")
                
                if self.reference_data is None:
                    df = self.create_dataframe(self.current_data)
                    if not df.empty:
                        os.makedirs(os.path.dirname(config.evidently.reference_data_path), exist_ok=True)
                        df.to_csv(config.evidently.reference_data_path, index=False)
                        print(f"✅ Saved {len(self.current_data)} samples as reference data")
                else:
                    print("ℹ️ Reference data already exists, discarding partial batch")
                    
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            traceback.print_exc()
            
        finally:
            self.consumer.close()
            print("✅ Consumer closed cleanly")

if __name__ == "__main__":
    print("=" * 60)
    print("Enhanced Evidently Data Drift Monitor")
    print("WITH COMPREHENSIVE METRICS")
    print("=" * 60)
    print()
    
    try:
        consumer = EvidentlyConsumer()
        consumer.start_consuming()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        traceback.print_exc()