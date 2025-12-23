import os
from dataclasses import dataclass, field

@dataclass
class KafkaConfig:
    """Kafka configuration - Optimized for 16GB RAM"""
    bootstrap_servers: str = "localhost:9092"
    request_topic: str = "llm-requests"
    response_topic: str = "llm-responses"
    consumer_group: str = "llmops-monitoring"
    
    # Performance tuning
    max_poll_records: int = 10  # Reduced from default 500
    session_timeout_ms: int = 30000  # 30 seconds
    heartbeat_interval_ms: int = 10000  # 10 seconds
    max_poll_interval_ms: int = 300000  # 5 minutes
    
@dataclass
class OllamaConfig:
    """Ollama LLM configuration"""
    base_url: str = "http://localhost:11434"
    model: str = "tinyllama"  # Lightweight model for 16GB RAM
    # Alternative models (install with: ollama pull <model>):
    # - "tinyllama" (1.1B params) - Fastest, least memory
    # - "llama2" (7B params) - Good balance
    # - "mistral" (7B params) - Better quality
    # - "phi" (2.7B params) - Good for coding
    
    temperature: float = 0.7
    max_tokens: int = 256  # Reduced for faster responses
    timeout: int = 60  # Request timeout in seconds
    
@dataclass
class MLflowConfig:
    """MLflow tracking configuration"""
    tracking_uri: str = "http://localhost:5000"
    experiment_name: str = "llm-monitoring"
    artifact_location: str = "./mlruns"
    
    # Performance settings
    log_artifacts: bool = False  # Disable to reduce I/O
    
@dataclass
class EvidentlyConfig:
    """Evidently data quality monitoring"""
    reports_dir: str = "./evidently_reports"
    reference_data_path: str = "./data/reference_data.csv"
    batch_size: int = 30  # Reduced from 50 for faster reports
    
    # Report generation settings
    generate_html: bool = True
    generate_json: bool = True
    
@dataclass
class StreamingConfig:
    """Real-time streaming configuration"""
    buffer_size: int = 50  # Keep last 50 samples in memory
    update_interval: int = 2  # Seconds between UI updates
    max_message_size: int = 10485760  # 10MB max message size
    
@dataclass
class PerformanceConfig:
    """Performance tuning for HP Pavilion i5-1240P"""
    max_concurrent_requests: int = 5  # Limit concurrent LLM calls
    request_delay: float = 3.0  # Seconds between requests
    consumer_timeout_ms: int = 1000  # Kafka consumer timeout
    enable_caching: bool = False  # Disable caching to save memory
    
@dataclass
class AppConfig:
    """Main application configuration"""
    kafka: KafkaConfig = field(default_factory=KafkaConfig)
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    mlflow: MLflowConfig = field(default_factory=MLflowConfig)
    evidently: EvidentlyConfig = field(default_factory=EvidentlyConfig)
    streaming: StreamingConfig = field(default_factory=StreamingConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    
    # Logging
    log_level: str = "INFO"
    enable_debug: bool = False
    
    # Data retention
    max_data_age_days: int = 7  # Auto-cleanup old data
    
# Global config instance
config = AppConfig()

# Environment variable overrides
if os.getenv("KAFKA_BOOTSTRAP_SERVERS"):
    config.kafka.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")

if os.getenv("OLLAMA_MODEL"):
    config.ollama.model = os.getenv("OLLAMA_MODEL")

if os.getenv("MLFLOW_TRACKING_URI"):
    config.mlflow.tracking_uri = os.getenv("MLFLOW_TRACKING_URI")

# Print configuration on import (for debugging)
if config.enable_debug:
    print("=" * 60)
    print("LLMOps Configuration (Optimized)")
    print("=" * 60)
    print(f"Kafka: {config.kafka.bootstrap_servers}")
    print(f"Ollama Model: {config.ollama.model}")
    print(f"MLflow: {config.mlflow.tracking_uri}")
    print(f"Buffer Size: {config.streaming.buffer_size}")
    print(f"Batch Size: {config.evidently.batch_size}")
    print(f"Max Concurrent: {config.performance.max_concurrent_requests}")
    print("=" * 60)