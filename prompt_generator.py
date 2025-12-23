import json
import csv
import random
from datetime import datetime
from pathlib import Path

class PromptGenerator:
    """Generate diverse test prompts for LLM monitoring"""
    
    def __init__(self, output_dir="./data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Prompt categories with examples
        self.prompt_categories = {
            "technical": [
                "What is artificial intelligence?",
                "Explain machine learning in simple terms.",
                "What are the benefits of cloud computing?",
                "How does blockchain technology work?",
                "What is the difference between AI and ML?",
                "Explain containerization and Docker.",
                "What are microservices?",
                "How does Kubernetes work?",
                "What is continuous integration?",
                "Explain REST APIs.",
                "What is database normalization?",
                "How does encryption work?",
                "What are design patterns in software?",
                "Explain object-oriented programming.",
                "What is test-driven development?"
            ],
            "coding": [
                "Write a Python function to reverse a string.",
                "How do I sort a list in Python?",
                "Explain list comprehensions in Python.",
                "What is the difference between append and extend?",
                "How do I read a CSV file in Python?",
                "Write a function to find duplicates in a list.",
                "How do I handle exceptions in Python?",
                "Explain decorators in Python.",
                "What are lambda functions?",
                "How do I work with JSON in Python?",
                "Write a function to check if a number is prime.",
                "How do I use regular expressions?",
                "What is the difference between is and ==?",
                "How do I create a virtual environment?",
                "Explain Python generators."
            ],
            "data_science": [
                "What is exploratory data analysis?",
                "Explain the bias-variance tradeoff.",
                "What is cross-validation?",
                "How does gradient descent work?",
                "What is overfitting in machine learning?",
                "Explain the difference between classification and regression.",
                "What are neural networks?",
                "How does a decision tree work?",
                "What is feature engineering?",
                "Explain k-means clustering.",
                "What is the purpose of normalization?",
                "How do you handle missing data?",
                "What is A/B testing?",
                "Explain the confusion matrix.",
                "What is dimensionality reduction?"
            ],
            "business": [
                "What is digital transformation?",
                "Explain agile methodology.",
                "What is a minimum viable product?",
                "How do you measure customer satisfaction?",
                "What is market segmentation?",
                "Explain the concept of ROI.",
                "What is supply chain management?",
                "How does project management work?",
                "What is business intelligence?",
                "Explain key performance indicators.",
                "What is change management?",
                "How do you conduct a SWOT analysis?",
                "What is customer relationship management?",
                "Explain the product lifecycle.",
                "What is lean methodology?"
            ],
            "general": [
                "How does photosynthesis work?",
                "What causes climate change?",
                "Explain the water cycle.",
                "What is renewable energy?",
                "How do vaccines work?",
                "What is the greenhouse effect?",
                "Explain the theory of evolution.",
                "What causes earthquakes?",
                "How does the human immune system work?",
                "What is biodiversity?",
                "Explain the solar system.",
                "What is sustainable development?",
                "How does DNA replication work?",
                "What are fossil fuels?",
                "Explain the concept of gravity."
            ],
            "creative": [
                "Write a haiku about coding.",
                "Create a metaphor for cloud computing.",
                "Suggest a creative team name for developers.",
                "Write a slogan for a tech startup.",
                "Create an analogy for neural networks.",
                "Suggest a name for a new programming language.",
                "Write a short description of future technology.",
                "Create a tagline for an AI product.",
                "Suggest creative ways to explain algorithms.",
                "Write a brief story about a robot.",
                "Create a metaphor for debugging.",
                "Suggest innovative app ideas.",
                "Write a poem about data science.",
                "Create an analogy for APIs.",
                "Suggest a name for a coding bootcamp."
            ]
        }
    
    def generate_prompts(self, num_prompts=100):
        """Generate random prompts from all categories"""
        all_prompts = []
        
        for category, prompts in self.prompt_categories.items():
            for prompt in prompts:
                all_prompts.append({
                    "prompt": prompt,
                    "category": category,
                    "complexity": self._estimate_complexity(prompt)
                })
        
        # If we need more, randomly sample with replacement
        if num_prompts > len(all_prompts):
            additional = random.choices(all_prompts, k=num_prompts - len(all_prompts))
            all_prompts.extend(additional)
        
        # Shuffle and limit to requested number
        random.shuffle(all_prompts)
        return all_prompts[:num_prompts]
    
    def _estimate_complexity(self, prompt):
        """Estimate prompt complexity based on length and keywords"""
        length = len(prompt.split())
        
        complex_keywords = ["explain", "difference", "compare", "analyze", "evaluate"]
        simple_keywords = ["what", "how", "list", "name", "define"]
        
        complexity_score = 0
        
        # Length factor
        if length > 15:
            complexity_score += 2
        elif length > 10:
            complexity_score += 1
        
        # Keyword factor
        prompt_lower = prompt.lower()
        if any(kw in prompt_lower for kw in complex_keywords):
            complexity_score += 2
        elif any(kw in prompt_lower for kw in simple_keywords):
            complexity_score += 1
        
        # Classify
        if complexity_score >= 3:
            return "high"
        elif complexity_score >= 2:
            return "medium"
        else:
            return "low"
    
    def save_to_json(self, prompts, filename="test_prompts.json"):
        """Save prompts to JSON file"""
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(prompts, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved {len(prompts)} prompts to {filepath}")
        return filepath
    
    def save_to_csv(self, prompts, filename="test_prompts.csv"):
        """Save prompts to CSV file"""
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["prompt", "category", "complexity"])
            writer.writeheader()
            writer.writerows(prompts)
        
        print(f"✅ Saved {len(prompts)} prompts to {filepath}")
        return filepath
    
    def generate_weighted_prompts(self, num_prompts=100, category_weights=None):
        """Generate prompts with weighted distribution across categories"""
        if category_weights is None:
            category_weights = {
                "technical": 0.25,
                "coding": 0.20,
                "data_science": 0.20,
                "business": 0.15,
                "general": 0.10,
                "creative": 0.10
            }
        
        prompts = []
        
        for category, weight in category_weights.items():
            num_category = int(num_prompts * weight)
            category_prompts = self.prompt_categories.get(category, [])
            
            # Sample with replacement if needed
            if num_category > len(category_prompts):
                selected = random.choices(category_prompts, k=num_category)
            else:
                selected = random.sample(category_prompts, min(num_category, len(category_prompts)))
            
            for prompt in selected:
                prompts.append({
                    "prompt": prompt,
                    "category": category,
                    "complexity": self._estimate_complexity(prompt),
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        random.shuffle(prompts)
        return prompts
    
    def create_test_scenarios(self):
        """Create specific test scenarios for monitoring"""
        scenarios = {
            "quick_test": self.generate_prompts(10),
            "medium_test": self.generate_prompts(50),
            "load_test": self.generate_prompts(200),
            "category_balanced": self.generate_weighted_prompts(100)
        }
        
        # Save each scenario
        for name, prompts in scenarios.items():
            self.save_to_json(prompts, f"{name}.json")
            self.save_to_csv(prompts, f"{name}.csv")
        
        print(f"\n✅ Created {len(scenarios)} test scenarios")
        return scenarios
    
    def print_summary(self, prompts):
        """Print summary statistics of generated prompts"""
        print("\n" + "="*50)
        print("📊 Prompt Generation Summary")
        print("="*50)
        
        # Category distribution
        categories = {}
        complexities = {}
        
        for p in prompts:
            cat = p['category']
            comp = p['complexity']
            categories[cat] = categories.get(cat, 0) + 1
            complexities[comp] = complexities.get(comp, 0) + 1
        
        print(f"\nTotal Prompts: {len(prompts)}")
        
        print("\nCategory Distribution:")
        for cat, count in sorted(categories.items()):
            percentage = (count / len(prompts)) * 100
            print(f"  • {cat}: {count} ({percentage:.1f}%)")
        
        print("\nComplexity Distribution:")
        for comp, count in sorted(complexities.items()):
            percentage = (count / len(prompts)) * 100
            print(f"  • {comp}: {count} ({percentage:.1f}%)")
        
        print("\n" + "="*50)


def main():
    print("🚀 Prompt Generator for LLMOps Monitoring")
    print("="*50)
    
    generator = PromptGenerator()
    
    # Generate different test sets
    print("\n1️⃣ Generating quick test set (10 prompts)...")
    quick_prompts = generator.generate_prompts(10)
    generator.save_to_json(quick_prompts, "quick_test.json")
    generator.save_to_csv(quick_prompts, "quick_test.csv")
    
    print("\n2️⃣ Generating medium test set (50 prompts)...")
    medium_prompts = generator.generate_prompts(50)
    generator.save_to_json(medium_prompts, "medium_test.json")
    generator.save_to_csv(medium_prompts, "medium_test.csv")
    
    print("\n3️⃣ Generating load test set (200 prompts)...")
    load_prompts = generator.generate_prompts(200)
    generator.save_to_json(load_prompts, "load_test.json")
    generator.save_to_csv(load_prompts, "load_test.csv")
    
    print("\n4️⃣ Generating balanced test set (100 prompts)...")
    balanced_prompts = generator.generate_weighted_prompts(100)
    generator.save_to_json(balanced_prompts, "balanced_test.json")
    generator.save_to_csv(balanced_prompts, "balanced_test.csv")
    
    # Print summary
    generator.print_summary(balanced_prompts)
    
    print("\n✅ All prompt sets generated successfully!")
    print(f"📁 Location: ./data/")
    print("\n💡 Next steps:")
    print("  1. Review generated prompts in the data folder")
    print("  2. Run: python batch_producer.py --file data/quick_test.json")
    print("  3. Monitor results in the Streamlit dashboard")


if __name__ == "__main__":
    main()