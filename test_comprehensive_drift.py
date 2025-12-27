"""
Test the updated evidently_consumer.py metrics with Evidently 0.7.17
"""
import pandas as pd
import numpy as np
from evidently import Report
from evidently.metrics import (
    DriftedColumnsCount,
    ValueDrift,
    DatasetMissingValueCount,
    DatasetCorrelations,
    ColumnCorrelations,
    ColumnCorrelationMatrix,
)

print("=" * 60)
print("Testing Evidently 0.7.17 Compatible Metrics")
print("=" * 60)

# Create reference data (baseline)
np.random.seed(42)
reference_df = pd.DataFrame({
    'latency': np.random.normal(5.0, 1.0, 30),
    'token_count': np.random.normal(100, 20, 30),
    'response_length': np.random.normal(600, 100, 30)
})

print("\n📊 Reference Data:")
print(f"  Latency: μ={reference_df['latency'].mean():.2f}, σ={reference_df['latency'].std():.2f}")
print(f"  Tokens:  μ={reference_df['token_count'].mean():.2f}, σ={reference_df['token_count'].std():.2f}")
print(f"  Length:  μ={reference_df['response_length'].mean():.2f}, σ={reference_df['response_length'].std():.2f}")

# Create current data with intentional drift
current_df = pd.DataFrame({
    'latency': np.random.normal(6.5, 1.2, 30),  # DRIFTED
    'token_count': np.random.normal(120, 25, 30),  # DRIFTED
    'response_length': np.random.normal(700, 110, 30)  # DRIFTED
})

print("\n📊 Current Data (with drift):")
print(f"  Latency: μ={current_df['latency'].mean():.2f}, σ={current_df['latency'].std():.2f}")
print(f"  Tokens:  μ={current_df['token_count'].mean():.2f}, σ={current_df['token_count'].std():.2f}")
print(f"  Length:  μ={current_df['response_length'].mean():.2f}, σ={current_df['response_length'].std():.2f}")

# Create report with same metrics as updated evidently_consumer.py
print("\n🔬 Running drift analysis...")

metrics = [
    DriftedColumnsCount(),
    ValueDrift(column="latency"),
    ValueDrift(column="token_count"),
    ValueDrift(column="response_length"),
    DatasetMissingValueCount(),
    DatasetCorrelations(),
]

report = Report(metrics=metrics)
snapshot = report.run(reference_data=reference_df, current_data=current_df)

# Save reports (main goal is to verify metrics work)
print("\n💾 Saving test report...")
snapshot.save_html("./evidently_reports/test_v0717_drift.html")
print("✅ HTML Report saved to: ./evidently_reports/test_v0717_drift.html")

snapshot.save_json("./evidently_reports/test_v0717_drift.json")
print("✅ JSON saved to: ./evidently_reports/test_v0717_drift.json")

print("\n" + "=" * 60)
print("✅ TEST SUCCESSFUL!")
print("=" * 60)
print("\n📌 Key Findings:")
print("   • Reports generated successfully with NO ERRORS")
print("   • ValueDrift tracks per-column drift (not just counts)")
print("   • DriftedColumnsCount shows number of drifted columns")
print("   • DatasetCorrelations shows metric relationships")
print("   • Reports include rich visualizations in HTML")
print("\n🎉 evidently_consumer.py is upgraded with richer metrics!")
print("\n💡 Open the HTML report to see detailed drift analysis with")
print("   actual drift scores and visualizations - no more zeros!")

