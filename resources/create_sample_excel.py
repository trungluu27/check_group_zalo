# Sample Excel file placeholder
# Run this Python script to create a sample Excel file:

import pandas as pd
from pathlib import Path

# Create sample data
data = {
    'username': [
        'Nguyễn Văn A',
        'Trần Thị B', 
        'Lê Văn C',
        'Phạm Thị D',
        'Hoàng Văn E',
        'Võ Thị F',
        'Đặng Văn G',
        'Bùi Thị H',
        'Đỗ Văn I',
        'Ngô Thị J'
    ],
    'email': [
        'nguyenvana@example.com',
        'tranthib@example.com',
        'levanc@example.com',
        'phamthid@example.com',
        'hoangvane@example.com',
        'vothif@example.com',
        'dangvang@example.com',
        'buithih@example.com',
        'dovani@example.com',
        'ngothij@example.com'
    ],
    'department': [
        'Sales', 'Marketing', 'IT', 'HR', 'Finance',
        'Operations', 'Support', 'Sales', 'IT', 'Marketing'
    ]
}

# Create DataFrame
df = pd.DataFrame(data)

# Save to Excel
output_path = Path('resources/sample_usernames.xlsx')
output_path.parent.mkdir(exist_ok=True)
df.to_excel(output_path, index=False, engine='openpyxl')

print(f"Sample Excel file created: {output_path}")
