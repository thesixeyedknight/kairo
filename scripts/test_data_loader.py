import sys
import os
import pandas as pd

# Ensure we can import kairo.src
# Script is in scripts/, so we need to add parent directory (kairo_project) to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from kairo.src.data_loader import fetch_data

def test_data_loader():
    reports_dir = os.path.join(current_dir, 'reports')
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
        
    report_file = os.path.join(reports_dir, 'test_data_loader_report.md')
    
    with open(report_file, 'w') as f:
        f.write("# Test Data Loader Report\n\n")
        
        try:
            print("Fetching SPY data...") # Console output for progress
            df = fetch_data('SPY')
            
            f.write("## Execution Status\n")
            f.write("Success\n\n")
            
            f.write("## Data Shape\n")
            f.write(f"{df.shape}\n\n")
            
            f.write("## Head\n")
            f.write("```\n")
            f.write(df.head().to_string())
            f.write("\n```\n")
            
            print(f"Test completed. Report saved to {report_file}")
            
        except Exception as e:
            f.write("## Execution Status\n")
            f.write(f"Failed: {str(e)}\n")
            print(f"Test failed: {e}")

if __name__ == "__main__":
    test_data_loader()
