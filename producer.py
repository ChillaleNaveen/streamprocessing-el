import json
import time
import uuid
from datetime import datetime
from kafka import KafkaProducer
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.callbacks.base import BaseCallbackHandler
from config import config

class MonitoringCallback(BaseCallbackHandler):
    """Captures LLM execution metrics"""
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.token_count = 0
        
    def on_llm_start(self, serialized, prompts, **kwargs):
        self.start_time = time.time()
        
    def on_llm_end(self, response, **kwargs):
        self.end_time = time.time()
        # Estimate token count (rough approximation)
        if response.generations:
            text = response.generations[0][0].text
            self.token_count = len(text.split())

class LLMProducer:
    def __init__(self):
        # Initialize Kafka Producer
        self.producer = KafkaProducer(
            bootstrap_servers=config.kafka.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        # Initialize Ollama LLM with timeout
        self.llm = Ollama(
            base_url=config.ollama.base_url,
            model=config.ollama.model,
            temperature=config.ollama.temperature,
            timeout=60  # Explicit timeout to prevent hanging
        )
        
        # Prompt template
        self.prompt_template = PromptTemplate(
            input_variables=["question"],
            template="Answer the following question concisely:\n\nQuestion: {question}\n\nAnswer:"
        )
        
    def generate_response(self, user_prompt: str, user_id: str = "default"):
        """Process prompt and publish to Kafka"""
        
        # Generate unique IDs
        request_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Format prompt
        formatted_prompt = self.prompt_template.format(question=user_prompt)
        
        # Publish request message
        request_message = {
            "request_id": request_id,
            "session_id": session_id,
            "user_id": user_id,
            "timestamp": timestamp,
            "prompt": user_prompt,
            "formatted_prompt": formatted_prompt,
            "model": config.ollama.model,
            "temperature": config.ollama.temperature,
            "max_tokens": config.ollama.max_tokens
        }
        
        self.producer.send(config.kafka.request_topic, request_message)
        print(f"📨 Published request: {request_id}")
        
        # Execute LLM call with monitoring
        start_time = time.time()
        
        try:
            # Note: callbacks parameter removed due to LangChain version compatibility
            response_text = self.llm.invoke(formatted_prompt)
            latency = time.time() - start_time
            status = "success"
            error = None
            
            # Estimate token count from response
            token_count = len(response_text.split())
            
        except Exception as e:
            response_text = ""
            latency = time.time() - start_time
            status = "error"
            error = str(e)
            token_count = 0
            print(f"❌ ERROR: {error}")
        
        # Publish response message (includes prompt for dashboard display)
        response_message = {
            "request_id": request_id,
            "session_id": session_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "prompt": user_prompt,  # Original user prompt
            "formatted_prompt": formatted_prompt,  # Formatted prompt sent to LLM
            "response": response_text,
            "latency": latency,
            "token_count": token_count,
            "response_length": len(response_text),
            "model": config.ollama.model,
            "temperature": config.ollama.temperature,
            "status": status,
            "error": error
        }
        
        self.producer.send(config.kafka.response_topic, response_message)
        print(f"✅ Published response: {request_id} (latency: {latency:.2f}s)")
        
        return response_text, request_id
    
    def close(self):
        self.producer.flush()
        self.producer.close()

if __name__ == "__main__":
    producer = LLMProducer()
    
    # Test prompts
    test_prompts = [
        "What is artificial intelligence?",
        "Explain machine learning in simple terms.",
        "What are the benefits of cloud computing?",
        "How does blockchain technology work?",
        "What is the difference between AI and ML?"
    ]
    
    print("🚀 Starting LLM Producer Test...")
    
    for prompt in test_prompts:
        print(f"\n📝 Prompt: {prompt}")
        response, req_id = producer.generate_response(prompt)
        print(f"💬 Response: {response[:100]}...")
        time.sleep(2)  # Pause between requests
    
    producer.close()
    print("\n✅ Test completed!")