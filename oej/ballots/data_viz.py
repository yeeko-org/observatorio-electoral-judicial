import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import numpy as np
from oej.ballots.data_sb import data

# Your data

# Convert to DataFrame
df = pd.DataFrame(data['traffic'])
df['date'] = pd.to_datetime(df['date'])
df = df.dropna()  # Remove rows with null values
df['total_gb'] = df['total_bytes'] / (1024**3)  # Convert bytes to GB
df['bytes_per_request'] = df['total_bytes'] / df['api_requests']

# Set up the plotting style
plt.style.use('seaborn-v0_8')
fig = plt.figure(figsize=(20, 15))

# 1. Daily API Requests Over Time
plt.subplot(3, 3, 1)
plt.plot(df['date'], df['api_requests'], marker='o', linewidth=2, markersize=4)
plt.title('Daily API Requests Over Time', fontsize=14, fontweight='bold')
plt.xlabel('Date')
plt.ylabel('API Requests')
plt.xticks(rotation=45)
plt.grid(True, alpha=0.3)

# 2. Daily Traffic (GB) Over Time
plt.subplot(3, 3, 2)
plt.plot(df['date'], df['total_gb'], marker='o', color='red', linewidth=2, markersize=4)
plt.title('Daily Traffic (GB) Over Time', fontsize=14, fontweight='bold')
plt.xlabel('Date')
plt.ylabel('Traffic (GB)')
plt.xticks(rotation=45)
plt.grid(True, alpha=0.3)

# 3. Bytes per Request Over Time
plt.subplot(3, 3, 3)
plt.plot(df['date'], df['bytes_per_request'], marker='o', color='green', linewidth=2, markersize=4)
plt.title('Average Bytes per Request', fontsize=14, fontweight='bold')
plt.xlabel('Date')
plt.ylabel('Bytes per Request')
plt.xticks(rotation=45)
plt.grid(True, alpha=0.3)

# 4. Correlation Scatter Plot
plt.subplot(3, 3, 4)
plt.scatter(df['api_requests'], df['total_gb'], alpha=0.6, s=50)
plt.title('API Requests vs Traffic (GB)', fontsize=14, fontweight='bold')
plt.xlabel('API Requests')
plt.ylabel('Traffic (GB)')
plt.grid(True, alpha=0.3)

# 5. Monthly Usage vs Limit (Gauge-like chart)
plt.subplot(3, 3, 5)
monthly_limit_gb = data['montly_traffic_limit'] / (1024**3)
monthly_used_gb = data['traffic_used_this_month'] / (1024**3)
usage_percentage = (monthly_used_gb / monthly_limit_gb) * 100

categories = ['Used', 'Remaining']
values = [monthly_used_gb, monthly_limit_gb - monthly_used_gb]
colors = ['#ff6b6b', '#51cf66']

plt.pie(values, labels=categories, colors=colors, autopct='%1.1f%%', startangle=90)
plt.title(f'Monthly Traffic Usage\n{usage_percentage:.2f}% Used', fontsize=14, fontweight='bold')

# 6. Daily Traffic Heatmap (by week)
plt.subplot(3, 3, 6)
df['week'] = df['date'].dt.isocalendar().week
df['day_of_week'] = df['date'].dt.day_name()

# Create pivot table for heatmap
heatmap_data = df.pivot_table(values='total_gb', index='week', columns='day_of_week', aggfunc='sum', fill_value=0)
# Reorder columns to start with Monday
day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
heatmap_data = heatmap_data.reindex(columns=[day for day in day_order if day in heatmap_data.columns])

sns.heatmap(heatmap_data, annot=True, fmt='.1f', cmap='YlOrRd', cbar_kws={'label': 'Traffic (GB)'})
plt.title('Weekly Traffic Heatmap (GB)', fontsize=14, fontweight='bold')
plt.ylabel('Week Number')

# 7. Top 10 Highest Traffic Days
plt.subplot(3, 3, 7)
top_10 = df.nlargest(10, 'total_gb')
bars = plt.bar(range(len(top_10)), top_10['total_gb'], color='orange', alpha=0.7)
plt.title('Top 10 Highest Traffic Days', fontsize=14, fontweight='bold')
plt.xlabel('Rank')
plt.ylabel('Traffic (GB)')
plt.xticks(range(len(top_10)), [f"{date.strftime('%m-%d')}" for date in top_10['date']], rotation=45)

# Add value labels on bars
for i, bar in enumerate(bars):
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
             f'{height:.1f}GB', ha='center', va='bottom', fontsize=9)

# 8. Rolling Average (7-day)
plt.subplot(3, 3, 8)
df_sorted = df.sort_values('date')
df_sorted['requests_7day_avg'] = df_sorted['api_requests'].rolling(window=7).mean()
df_sorted['traffic_7day_avg'] = df_sorted['total_gb'].rolling(window=7).mean()

plt.plot(df_sorted['date'], df_sorted['api_requests'], alpha=0.3, label='Daily Requests')
plt.plot(df_sorted['date'], df_sorted['requests_7day_avg'], linewidth=2, label='7-day Average')
plt.title('API Requests - 7 Day Moving Average', fontsize=14, fontweight='bold')
plt.xlabel('Date')
plt.ylabel('API Requests')
plt.legend()
plt.xticks(rotation=45)
plt.grid(True, alpha=0.3)

# 9. Summary Statistics
plt.subplot(3, 3, 9)
plt.axis('off')
stats_text = f"""
SUMMARY STATISTICS

Total Period Traffic: {data['total_traffic_per_time_period'] / (1024**3):.2f} GB
Total Requests: {data['total_requests_per_time_period']:,}
Monthly Limit: {monthly_limit_gb:.2f} GB
Monthly Used: {monthly_used_gb:.2f} GB
Usage %: {usage_percentage:.2f}%

Daily Averages:
- Requests: {df['api_requests'].mean():.0f}
- Traffic: {df['total_gb'].mean():.2f} GB
- Bytes/Request: {df['bytes_per_request'].mean():.0f}

Peak Day:
- Requests: {df['api_requests'].max():,}
- Traffic: {df['total_gb'].max():.2f} GB
"""

plt.text(0.1, 0.9, stats_text, transform=plt.gca().transAxes, fontsize=11,
         verticalalignment='top', fontfamily='monospace',
         bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))

plt.tight_layout()
plt.show()

# Additional: Create a summary table
print("\n" + "="*60)
print("DATA SUMMARY TABLE")
print("="*60)
summary_df = df.describe().round(2)
print(summary_df[['api_requests', 'total_gb', 'bytes_per_request']])

print(f"\nMonthly Traffic Limit: {monthly_limit_gb:.2f} GB")
print(f"Monthly Traffic Used: {monthly_used_gb:.2f} GB")
print(f"Remaining: {monthly_limit_gb - monthly_used_gb:.2f} GB")
print(f"Usage Percentage: {usage_percentage:.2f}%")