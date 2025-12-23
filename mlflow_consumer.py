import json
import mlflow
from kafka import KafkaConsumer
from config import config
from datetime import datetime

class MLflowConsumer:
    def __init__(self):
        # Set MLflow tracking URI
        mlflow.set_tracking_uri(config.mlflow.tracking_uri)
        mlflow.set_experiment(config.mlflow.experiment_name)
        
        # Initialize Kafka Consumer
        self.consumer = KafkaConsumer(
            config.kafka.response_topic,
            bootstrap_servers=config.kafka.bootstrap_servers,
            group_id=f"{config.kafka.consumer_group}-mlflow",
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            enable_auto_commit=True
        )
        
        print(f"🔗 MLflow Consumer connected to topic: {config.kafka.response_topic}")
    
    def log_to_mlflow(self, message):
        """Log LLM response to MLflow"""
        with mlflow.start_run(run_name=f"llm-{message['request_id'][:8]}"):
            # Log parameters
            mlflow.log_param("model", message.get("model", "unknown"))
            mlflow.log_param("request_id", message["request_id"])
            mlflow.log_param("user_id", message.get("user_id", "unknown"))
            
            # Log metrics
            mlflow.log_metric("latency_seconds", message["latency"])
            mlflow.log_metric("token_count", message["token_count"])
            mlflow.log_metric("response_length", message["response_length"])
            mlflow.log_metric("success", 1 if message["status"] == "success" else 0)
            
            # Log tags
            mlflow.set_tag("status", message["status"])
            mlflow.set_tag("timestamp", message["timestamp"])
            
            # Log artifacts (optional - save response text)
            if message["status"] == "success":
                with open("temp_response.txt", "w") as f:
                    f.write(message["response"])
                mlflow.log_artifact("temp_response.txt")
            
            if message.get("error"):
                mlflow.log_param("error", message["error"])
    
    def start_consuming(self):
        """Start consuming messages from Kafka"""
        print("👂 Starting to consume messages...")
        
        try:
            for message in self.consumer:
                data = message.value
                print(f"\n📊 Received response: {data['request_id'][:8]}... "
                      f"(latency: {data['latency']:.2f}s, tokens: {data['token_count']})")
                
                try:
                    self.log_to_mlflow(data)
                    print(f"✅ Logged to MLflow")
                except Exception as e:
                    print(f"❌ Error logging to MLflow: {e}")
                    
        except KeyboardInterrupt:
            print("\n🛑 Shutting down MLflow consumer...")
        finally:
            self.consumer.close()

if __name__ == "__main__":
    consumer = MLflowConsumer()
    consumer.start_consuming()