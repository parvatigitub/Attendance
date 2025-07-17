import pandas as pd
import os
from datetime import datetime
from flask import current_app

def generate_attendance_excel(data):
    # Create exports directory if it doesn't exist
    export_dir = os.path.join(current_app.root_path, 'static', 'exports')
    os.makedirs(export_dir, exist_ok=True)
    
    # Generate filename with timestamp
    filename = f"attendance_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    
    # Create full file path
    filepath = os.path.join(export_dir, filename)
    
    # Save the Excel file
    df = pd.DataFrame(data)
    df.to_excel(filepath, index=False)
    
    # Return the relative path for send_file
    return filepath
