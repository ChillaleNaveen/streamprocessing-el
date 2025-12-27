#!/usr/bin/env python3
"""Test the fixed evidently consumer report generation"""

from evidently import Report
from evidently.metrics import DriftedColumnsCount, DatasetMissingValueCount
import pandas as pd
import os

# Create test data
reference_df = pd.DataFrame({
    'latency': [0.5, 0.6, 0.7, 0.8, 0.9],
    'token_count': [100, 110, 120, 130, 140],
    'response_length': [500, 550, 600, 650, 700]
})

current_df = pd.DataFrame({
    'latency': [0.55, 0.65, 0.75, 0.85, 0.95],
    'token_count': [105, 115, 125, 135, 145],
    'response_length': [510, 560, 610, 660, 710]
})

print("🧪 Testing Evidently Report Generation...")
print("=" * 60)

# Create report
report = Report(metrics=[
    DriftedColumnsCount(),
    DatasetMissingValueCount(),
])

print("🔄 Running drift analysis...")
snapshot = report.run(
    reference_data=reference_df,
    current_data=current_df
)

print(f"✅ Analysis complete!")
print(f"   Snapshot type: {type(snapshot)}")
print(f"   Has save_html: {hasattr(snapshot, 'save_html')}")
print(f"   Has save_json: {hasattr(snapshot, 'save_json')}")

# Save report
os.makedirs("./evidently_reports", exist_ok=True)
html_path = "./evidently_reports/test_report.html"
json_path = "./evidently_reports/test_report.json"

snapshot.save_html(html_path)
print(f"✅ HTML report saved: {html_path}")

snapshot.save_json(json_path)
print(f"✅ JSON report saved: {json_path}")

print("=" * 60)
print("🎉 All tests passed! Evidently is working correctly!")
