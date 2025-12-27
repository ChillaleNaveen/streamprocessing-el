"""Test evidently imports"""
print("Testing evidently imports...")

try:
    from evidently import ColumnMapping
    print("✅ ColumnMapping imported")
except Exception as e:
    print(f"❌ ColumnMapping failed: {e}")

try:
    from evidently.report import Report
    print("✅ Report imported")
except Exception as e:
    print(f"❌ Report failed: {e}")

try:
    from evidently.metrics import DataDriftTable, DatasetDriftMetric, DatasetMissingValuesMetric
    print("✅ Metrics imported")
except Exception as e:
    print(f"❌ Metrics failed: {e}")

print("\n✅ All imports successful!")
