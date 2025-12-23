import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
import argparse

class ResultsAnalyzer:
    """Analyze batch test results"""
    
    def __init__(self, results_dir="./data/results"):
        self.results_dir = Path(results_dir)
        
    def load_latest_results(self):
        """Load the most recent results file"""
        if not self.results_dir.exists():
            print("❌ Results directory not found")
            return None
        
        json_files = list(self.results_dir.glob("batch_results_*.json"))
        
        if not json_files:
            print("❌ No result files found")
            return None
        
        # Get most recent
        latest = max(json_files, key=lambda p: p.stat().st_mtime)
        
        print(f"📂 Loading: {latest.name}")
        
        with open(latest, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_specific_results(self, filename):
        """Load specific results file"""
        filepath = self.results_dir / filename
        
        if not filepath.exists():
            print(f"❌ File not found: {filepath}")
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def create_dataframe(self, results):
        """Convert results to pandas DataFrame"""
        # Extract key metrics
        data = []
        for r in results:
            data.append({
                'request_id': r['request_id'],
                'category': r.get('category', 'unknown'),
                'complexity': r.get('complexity', 'unknown'),
                'status': r['status'],
                'response_length': len(r.get('response', '')),
                'timestamp': r['timestamp']
            })
        
        return pd.DataFrame(data)
    
    def print_summary(self, results):
        """Print comprehensive summary statistics"""
        df = self.create_dataframe(results)
        
        print("\n" + "="*60)
        print("📊 RESULTS ANALYSIS SUMMARY")
        print("="*60)
        
        # Overall stats
        total = len(df)
        successful = (df['status'] == 'success').sum()
        failed = (df['status'] == 'failed').sum()
        success_rate = (successful / total) * 100
        
        print(f"\n📈 Overall Statistics:")
        print(f"  • Total Requests:    {total}")
        print(f"  • Successful:        {successful} ({success_rate:.1f}%)")
        print(f"  • Failed:            {failed} ({(failed/total)*100:.1f}%)")
        
        # Response length stats
        successful_df = df[df['status'] == 'success']
        if not successful_df.empty:
            print(f"\n📝 Response Length (successful only):")
            print(f"  • Average:           {successful_df['response_length'].mean():.0f} chars")
            print(f"  • Median:            {successful_df['response_length'].median():.0f} chars")
            print(f"  • Min:               {successful_df['response_length'].min():.0f} chars")
            print(f"  • Max:               {successful_df['response_length'].max():.0f} chars")
        
        # Category breakdown
        print(f"\n🏷️  Category Distribution:")
        category_counts = df['category'].value_counts()
        for cat, count in category_counts.items():
            percentage = (count / total) * 100
            cat_success = df[(df['category'] == cat) & (df['status'] == 'success')].shape[0]
            cat_success_rate = (cat_success / count) * 100 if count > 0 else 0
            print(f"  • {cat:15s}: {count:3d} ({percentage:5.1f}%) - {cat_success_rate:.0f}% success")
        
        # Complexity breakdown
        print(f"\n🎯 Complexity Distribution:")
        complexity_counts = df['complexity'].value_counts()
        for comp, count in complexity_counts.items():
            percentage = (count / total) * 100
            comp_success = df[(df['complexity'] == comp) & (df['status'] == 'success')].shape[0]
            comp_success_rate = (comp_success / count) * 100 if count > 0 else 0
            print(f"  • {comp:10s}: {count:3d} ({percentage:5.1f}%) - {comp_success_rate:.0f}% success")
        
        # Failure analysis
        if failed > 0:
            print(f"\n❌ Failure Analysis:")
            failed_df = df[df['status'] == 'failed']
            print(f"  • Failed categories: {failed_df['category'].value_counts().to_dict()}")
            print(f"  • Failed complexity: {failed_df['complexity'].value_counts().to_dict()}")
        
        print("\n" + "="*60)
    
    def generate_visualizations(self, results, output_dir="./data/analysis"):
        """Generate visualization charts"""
        df = self.create_dataframe(results)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        sns.set_style("whitegrid")
        
        # 1. Status distribution
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Status pie chart
        status_counts = df['status'].value_counts()
        axes[0, 0].pie(status_counts, labels=status_counts.index, autopct='%1.1f%%', startangle=90)
        axes[0, 0].set_title('Request Status Distribution')
        
        # Category bar chart
        category_counts = df['category'].value_counts()
        category_counts.plot(kind='bar', ax=axes[0, 1], color='skyblue')
        axes[0, 1].set_title('Prompts by Category')
        axes[0, 1].set_xlabel('Category')
        axes[0, 1].set_ylabel('Count')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # Complexity distribution
        complexity_counts = df['complexity'].value_counts()
        complexity_counts.plot(kind='bar', ax=axes[1, 0], color='lightcoral')
        axes[1, 0].set_title('Prompts by Complexity')
        axes[1, 0].set_xlabel('Complexity')
        axes[1, 0].set_ylabel('Count')
        axes[1, 0].tick_params(axis='x', rotation=0)
        
        # Response length distribution
        successful_df = df[df['status'] == 'success']
        if not successful_df.empty:
            axes[1, 1].hist(successful_df['response_length'], bins=20, color='lightgreen', edgecolor='black')
            axes[1, 1].set_title('Response Length Distribution')
            axes[1, 1].set_xlabel('Response Length (chars)')
            axes[1, 1].set_ylabel('Frequency')
        
        plt.tight_layout()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_path / f"analysis_{timestamp}.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"\n📊 Visualization saved: {output_file}")
        
        plt.close()
        
        # 2. Success rate by category heatmap
        if not df.empty:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Create pivot table
            pivot_data = df.groupby(['category', 'status']).size().unstack(fill_value=0)
            
            if 'success' in pivot_data.columns:
                success_rates = (pivot_data['success'] / pivot_data.sum(axis=1) * 100).sort_values(ascending=False)
                
                success_rates.plot(kind='barh', ax=ax, color='#2ecc71')
                ax.set_title('Success Rate by Category', fontsize=14, fontweight='bold')
                ax.set_xlabel('Success Rate (%)')
                ax.set_ylabel('Category')
                ax.set_xlim(0, 100)
                
                # Add value labels
                for i, v in enumerate(success_rates):
                    ax.text(v + 1, i, f'{v:.1f}%', va='center')
                
                plt.tight_layout()
                
                output_file2 = output_path / f"success_rates_{timestamp}.png"
                plt.savefig(output_file2, dpi=300, bbox_inches='tight')
                print(f"📊 Success rates saved: {output_file2}")
                
                plt.close()
    
    def export_summary_report(self, results, output_dir="./data/analysis"):
        """Export detailed summary report"""
        df = self.create_dataframe(results)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create summary statistics
        summary = {
            'total_requests': len(df),
            'successful': (df['status'] == 'success').sum(),
            'failed': (df['status'] == 'failed').sum(),
            'success_rate': f"{(df['status'] == 'success').mean() * 100:.2f}%",
            'avg_response_length': df[df['status'] == 'success']['response_length'].mean(),
            'category_distribution': df['category'].value_counts().to_dict(),
            'complexity_distribution': df['complexity'].value_counts().to_dict(),
            'timestamp': timestamp
        }
        
        # Save as JSON
        json_file = output_path / f"summary_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        print(f"📄 Summary report saved: {json_file}")
        
        return summary
    
    def compare_results(self, file1, file2):
        """Compare two result files"""
        results1 = self.load_specific_results(file1)
        results2 = self.load_specific_results(file2)
        
        if not results1 or not results2:
            return
        
        df1 = self.create_dataframe(results1)
        df2 = self.create_dataframe(results2)
        
        print("\n" + "="*60)
        print("🔄 COMPARISON ANALYSIS")
        print("="*60)
        
        print(f"\n📁 File 1: {file1}")
        print(f"   • Total:     {len(df1)}")
        print(f"   • Success:   {(df1['status'] == 'success').sum()} ({(df1['status'] == 'success').mean()*100:.1f}%)")
        print(f"   • Avg Length: {df1[df1['status'] == 'success']['response_length'].mean():.0f} chars")
        
        print(f"\n📁 File 2: {file2}")
        print(f"   • Total:     {len(df2)}")
        print(f"   • Success:   {(df2['status'] == 'success').sum()} ({(df2['status'] == 'success').mean()*100:.1f}%)")
        print(f"   • Avg Length: {df2[df2['status'] == 'success']['response_length'].mean():.0f} chars")
        
        print("\n" + "="*60)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze batch test results"
    )
    parser.add_argument(
        '--file', '-f',
        help='Specific results file to analyze (default: latest)'
    )
    parser.add_argument(
        '--visualize', '-v',
        action='store_true',
        help='Generate visualization charts'
    )
    parser.add_argument(
        '--export', '-e',
        action='store_true',
        help='Export summary report'
    )
    parser.add_argument(
        '--compare', '-c',
        nargs=2,
        help='Compare two result files'
    )
    
    args = parser.parse_args()
    
    print("📊 Results Analyzer")
    print("="*60)
    
    analyzer = ResultsAnalyzer()
    
    # Comparison mode
    if args.compare:
        analyzer.compare_results(args.compare[0], args.compare[1])
        return
    
    # Load results
    if args.file:
        results = analyzer.load_specific_results(args.file)
    else:
        results = analyzer.load_latest_results()
    
    if not results:
        return
    
    # Print summary
    analyzer.print_summary(results)
    
    # Generate visualizations
    if args.visualize:
        print("\n📊 Generating visualizations...")
        try:
            analyzer.generate_visualizations(results)
        except Exception as e:
            print(f"❌ Error generating visualizations: {e}")
            print("💡 Tip: Install matplotlib and seaborn: pip install matplotlib seaborn")
    
    # Export report
    if args.export:
        print("\n📄 Exporting summary report...")
        analyzer.export_summary_report(results)
    
    print("\n✅ Analysis complete!")


if __name__ == "__main__":
    main()