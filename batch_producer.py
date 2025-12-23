import json
import csv
import time
import argparse
from pathlib import Path
from datetime import datetime
from producer import LLMProducer
from config import config
import traceback

class BatchProducer:
    """Batch producer with improved error handling and progress tracking"""
    
    def __init__(self):
        try:
            print("🔧 Initializing LLM Producer...")
            self.producer = LLMProducer()
            print("✅ Producer initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize producer: {e}")
            traceback.print_exc()
            raise
            
        self.results = []
        
    def load_prompts_from_json(self, filepath):
        """Load prompts from JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both list of dicts and simple list of strings
        if isinstance(data, list):
            if len(data) > 0 and isinstance(data[0], dict):
                return data
            else:
                return [{"prompt": p, "category": "unknown", "complexity": "unknown"} for p in data]
        else:
            raise ValueError("Invalid JSON format. Expected list of prompts.")
    
    def load_prompts_from_csv(self, filepath):
        """Load prompts from CSV file"""
        prompts = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                prompts.append(row)
        return prompts
    
    def load_prompts(self, filepath):
        """Load prompts from file (auto-detect format)"""
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        print(f"📂 Loading prompts from: {filepath}")
        
        if filepath.suffix == '.json':
            prompts = self.load_prompts_from_json(filepath)
        elif filepath.suffix == '.csv':
            prompts = self.load_prompts_from_csv(filepath)
        else:
            raise ValueError(f"Unsupported file format: {filepath.suffix}")
        
        print(f"✅ Loaded {len(prompts)} prompts")
        return prompts
    
    def process_batch(self, prompts, delay=3.0, user_id="batch_test"):
        """Process a batch of prompts with improved error handling"""
        total = len(prompts)
        successful = 0
        failed = 0
        
        print(f"\n🚀 Starting batch processing")
        print("=" * 60)
        print(f"Total prompts: {total}")
        print(f"Delay: {delay}s between requests")
        print(f"User ID: {user_id}")
        print("=" * 60)
        
        start_time = time.time()
        
        for idx, prompt_data in enumerate(prompts, 1):
            # Extract prompt and metadata
            if isinstance(prompt_data, dict):
                prompt_text = prompt_data.get('prompt', str(prompt_data))
                category = prompt_data.get('category', 'unknown')
                complexity = prompt_data.get('complexity', 'unknown')
            else:
                prompt_text = str(prompt_data)
                category = 'unknown'
                complexity = 'unknown'
            
            # Progress indicator
            print(f"\n[{idx}/{total}] Processing prompt...")
            print(f"  📁 Category: {category} | Complexity: {complexity}")
            print(f"  💬 Prompt: {prompt_text[:80]}{'...' if len(prompt_text) > 80 else ''}")
            
            try:
                # Generate response
                request_start = time.time()
                response, request_id = self.producer.generate_response(
                    prompt_text, 
                    user_id=user_id
                )
                request_time = time.time() - request_start
                
                # Store result
                result = {
                    'request_id': request_id,
                    'prompt': prompt_text,
                    'category': category,
                    'complexity': complexity,
                    'response': response,
                    'status': 'success',
                    'latency': request_time,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                self.results.append(result)
                successful += 1
                
                print(f"  ✅ Success!")
                print(f"     Latency: {request_time:.2f}s")
                print(f"     Response: {len(response)} chars")
                print(f"     ID: {request_id[:8]}")
                
            except Exception as e:
                # Store error result
                result = {
                    'request_id': 'error',
                    'prompt': prompt_text,
                    'category': category,
                    'complexity': complexity,
                    'response': None,
                    'status': 'failed',
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                self.results.append(result)
                failed += 1
                
                print(f"  ❌ Failed!")
                print(f"     Error: {str(e)[:100]}")
            
            # Progress summary
            progress = (idx / total) * 100
            elapsed = time.time() - start_time
            estimated_total = (elapsed / idx) * total if idx > 0 else 0
            remaining = estimated_total - elapsed
            
            print(f"  📊 Progress: {progress:.1f}% | ✅ {successful} | ❌ {failed}")
            print(f"  ⏱️ Elapsed: {elapsed:.1f}s | Remaining: {remaining:.1f}s")
            
            # Delay between requests (except for last one)
            if idx < total:
                print(f"  ⏸️ Waiting {delay}s before next request...")
                time.sleep(delay)
        
        elapsed_time = time.time() - start_time
        
        # Final summary
        self._print_summary(total, successful, failed, elapsed_time)
        
        return self.results
    
    def _print_summary(self, total, successful, failed, elapsed_time):
        """Print batch processing summary"""
        print("\n" + "=" * 60)
        print("📊 BATCH PROCESSING SUMMARY")
        print("=" * 60)
        print(f"Total Prompts:     {total}")
        print(f"✅ Successful:     {successful} ({(successful/total)*100:.1f}%)")
        print(f"❌ Failed:         {failed} ({(failed/total)*100:.1f}%)")
        print(f"⏱️ Total Time:     {elapsed_time:.2f}s")
        print(f"⚡ Avg Time/Prompt: {elapsed_time/total:.2f}s")
        
        if successful > 0:
            avg_latency = sum(r['latency'] for r in self.results if 'latency' in r) / successful
            print(f"📈 Avg Latency:    {avg_latency:.2f}s")
        
        print("=" * 60)
    
    def save_results(self, output_dir="./data/results"):
        """Save batch results to file"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save as JSON
        json_file = output_path / f"batch_results_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {json_file}")
        
        # Save summary as CSV
        csv_file = output_path / f"batch_summary_{timestamp}.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            if self.results:
                fieldnames = ['request_id', 'category', 'complexity', 'status', 
                            'latency', 'timestamp']
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(self.results)
        
        print(f"💾 Summary saved to: {csv_file}")
        
        return json_file, csv_file
    
    def close(self):
        """Clean up resources"""
        try:
            self.producer.close()
            print("✅ Producer closed cleanly")
        except Exception as e:
            print(f"⚠️ Error closing producer: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Batch LLM Producer - Process prompts from files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python batch_producer.py --file data/quick_test.json
  python batch_producer.py --file data/medium_test.json --delay 2.0
  python batch_producer.py --file data/load_test.json --delay 5.0 --save-results
        """
    )
    parser.add_argument(
        '--file', '-f',
        required=True,
        help='Path to prompts file (JSON or CSV)'
    )
    parser.add_argument(
        '--delay', '-d',
        type=float,
        default=3.0,
        help='Delay between requests in seconds (default: 3.0, recommended for 16GB RAM)'
    )
    parser.add_argument(
        '--user-id', '-u',
        default='batch_test',
        help='User ID for requests (default: batch_test)'
    )
    parser.add_argument(
        '--save-results',
        action='store_true',
        help='Save results to file'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🚀 Batch LLM Producer")
    print("=" * 60)
    print(f"File: {args.file}")
    print(f"Delay: {args.delay}s (optimized for your system)")
    print(f"User ID: {args.user_id}")
    print("=" * 60)
    
    # Validate delay
    if args.delay < 2.0:
        print("\n⚠️ WARNING: Delay < 2.0s may overwhelm your system")
        print("   Recommended: 3.0s for HP Pavilion i5 with 16GB RAM")
        confirm = input("Continue anyway? (y/n): ")
        if confirm.lower() != 'y':
            print("Cancelled.")
            return
    
    batch_producer = BatchProducer()
    
    try:
        # Load prompts
        prompts = batch_producer.load_prompts(args.file)
        
        # Warn if too many prompts
        if len(prompts) > 100:
            print(f"\n⚠️ WARNING: Processing {len(prompts)} prompts")
            print(f"   This will take approximately {len(prompts) * args.delay / 60:.1f} minutes")
            confirm = input("Continue? (y/n): ")
            if confirm.lower() != 'y':
                print("Cancelled.")
                return
        
        # Process batch
        results = batch_producer.process_batch(
            prompts,
            delay=args.delay,
            user_id=args.user_id
        )
        
        # Save results if requested
        if args.save_results:
            batch_producer.save_results()
        
        print("\n✅ Batch processing complete!")
        print("\n💡 Next steps:")
        print("  1. Check Streamlit dashboard for real-time metrics")
        print("     → http://localhost:8501")
        print("  2. View MLflow UI for detailed tracking")
        print("     → http://localhost:5000")
        print(f"  3. Evidently reports after {config.evidently.batch_size} samples")
        print("     → ./evidently_reports/")
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Available test files:")
        data_dir = Path("./data")
        if data_dir.exists():
            for file in data_dir.glob("*.json"):
                print(f"  - {file}")
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user")
        print("💾 Saving partial results...")
        if batch_producer.results:
            batch_producer.save_results()
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        traceback.print_exc()
    finally:
        batch_producer.close()


if __name__ == "__main__":
    main()