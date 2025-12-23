import json
import os
import pandas as pd
from kafka import KafkaConsumer
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, DataQualityPreset
from config import config
from datetime import datetime
import traceback

class EvidentlyConsumer:
    """Evidently consumer for data drift monitoring - Fixed version"""
    
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
        
        print(f"📊 Batch size: {config.evidently.batch_size} samples")
        print(f"📁 Reports directory: {config.evidently.reports_dir}")
        
    def load_reference_data(self):
        """Load reference dataset"""
        try:
            if os.path.exists(config.evidently.reference_data_path):
                self.reference_data = pd.read_csv(config.evidently.reference_data_path)
                print(f"✅ Loaded reference data: {len(self.reference_data)} samples")
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
        """Generate Evidently drift report with proper error handling"""
        try:
            print("\n📊 Generating Evidently report...")
            
            # Ensure both dataframes have same columns
            common_cols = list(set(current_df.columns) & set(reference_df.columns))
            current_clean = current_df[common_cols].copy()
            reference_clean = reference_df[common_cols].copy()
            
            # Drop timestamp and non-numeric for drift analysis
            numeric_cols = ['latency', 'token_count', 'response_length']
            
            current_numeric = current_clean[numeric_cols]
            reference_numeric = reference_clean[numeric_cols]
            
            # Create report with proper metric presets
            report = Report(metrics=[
                DataDriftPreset(),
                DataQualityPreset()
            ])
            
            print("🔄 Running drift analysis...")
            report.run(
                reference_data=reference_numeric,
                current_data=current_numeric
            )
            
            # Save HTML report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = os.path.join(
                config.evidently.reports_dir,
                f"drift_report_{timestamp}.html"
            )
            
            report.save_html(report_path)
            print(f"✅ Report saved: {report_path}")
            
            # Save JSON summary if enabled
            if config.evidently.generate_json:
                json_path = report_path.replace('.html', '.json')
                report.save_json(json_path)
                print(f"✅ JSON saved: {json_path}")
            
            return report_path
            
        except Exception as e:
            print(f"❌ Error generating report: {e}")
            traceback.print_exc()
            return None
    
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
                    print(f"\n\n🔬 Batch complete! Generating drift analysis...")
                    print("=" * 60)
                    
                    current_df = self.create_dataframe(self.current_data)
                    
                    if current_df.empty:
                        print("❌ Failed to create dataframe")
                        self.current_data = []
                        continue
                    
                    # Create reference data if not exists
                    if self.reference_data is None:
                        self.reference_data = current_df.copy()
                        
                        # Ensure data directory exists
                        os.makedirs(os.path.dirname(config.evidently.reference_data_path), exist_ok=True)
                        
                        self.reference_data.to_csv(config.evidently.reference_data_path, index=False)
                        print(f"✅ Created reference dataset with {len(self.reference_data)} samples")
                        print(f"📁 Saved to: {config.evidently.reference_data_path}")
                    else:
                        # Generate drift report
                        report_path = self.generate_report(current_df, self.reference_data)
                        
                        if report_path:
                            print(f"✅ Drift analysis complete!")
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
    print("Evidently Data Drift Monitor")
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