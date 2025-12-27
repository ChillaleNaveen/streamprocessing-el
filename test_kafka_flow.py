"""Test Kafka message flow to diagnose Streamlit issue"""
import json
from kafka import KafkaConsumer
from config import config
import time

print("=" * 60)
print("Kafka Response Topic Test")
print("=" * 60)
print(f"Topic: {config.kafka.response_topic}")
print(f"Bootstrap: {config.kafka.bootstrap_servers}")
print("=" * 60)
print()

try:
    consumer = KafkaConsumer(
        config.kafka.response_topic,
        bootstrap_servers=config.kafka.bootstrap_servers,
        group_id=f"test-consumer-{int(time.time())}",
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='latest',
        enable_auto_commit=True,
        consumer_timeout_ms=5000
    )
    
    print("✅ Consumer created successfully")
    print("👂 Listening for messages... (5 seconds)")
    print("   Run batch_producer.py in another terminal to test\n")
    
    message_count = 0
    
    for message in consumer:
        message_count += 1
        data = message.value
        
        print(f"\n📨 Message #{message_count} received!")
        print(f"   Request ID: {data.get('request_id', 'N/A')[:16]}")
        print(f"   Status: {data.get('status', 'N/A')}")
        print(f"   Latency: {data.get('latency', 'N/A')}")
        print(f"   Token Count: {data.get('token_count', 'N/A')}")
        
        if data.get('response'):
            response_preview = data['response'][:80]
            print(f"   Response: {response_preview}...")
    
    if message_count == 0:
        print("\n⚠️ No messages received in 5 seconds")
        print("   Possible issues:")
        print("   1. Producer not running (run batch_producer.py)")
        print("   2. Messages already consumed (try sending new messages)")
        print("   3. Wrong topic name")
    else:
        print(f"\n✅ Successfully received {message_count} messages!")
        print("   Kafka is working correctly.")
        print("   If Streamlit dashboard shows no data, the issue is in the dashboard code.")
    
    consumer.close()
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nTroubleshooting:")
    print("1. Is Kafka running? Check port 9092")
    print("2. Does the topic exist?")
    print("3. Are there any firewall issues?")
