import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def generate_24hr_wire_count_graph(df, title="24-Hour Summary", output_folder=r"C:\Users\6078\Desktop\3348_wire_count\Email_summary\output_graphs"):
    print("🖼️ Preparing 24-hour graph...")

    required_cols = {'Time', 'LCG Count', 'PWLC Count', 'TOTAL Count'}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"Missing columns: {required_cols - set(df.columns)}")
    if df.empty:
        raise ValueError("DataFrame is empty.")

    # Convert Time to string (for safe merge)
    df['Time'] = df['Time'].astype(str)

    # Generate complete 24-hour time range from 07:00 AM to next day 07:00 AM
    base_time = datetime.strptime("07:00 AM", "%I:%M %p")
    time_labels = [(base_time + timedelta(hours=i)).strftime('%I:%M %p') for i in range(24)]

    # Create a base DataFrame with all 24 time labels
    base_df = pd.DataFrame({'Time': time_labels})
    merged_df = base_df.merge(df, on='Time', how='left')
    merged_df.fillna(0, inplace=True)

    # Ensure counts are integers
    for col in ['LCG Count', 'PWLC Count', 'TOTAL Count']:
        merged_df[col] = merged_df[col].astype(int)

    # Plotting
    os.makedirs(output_folder, exist_ok=True)
    fig, ax = plt.subplots(figsize=(16, 8))

    x = list(range(24))
    ax.plot(x, merged_df['LCG Count'], marker='o', linestyle='-', color='navy', linewidth=2.5, label='LCG Count')
    ax.plot(x, merged_df['PWLC Count'], marker='s', linestyle='--', color='red', linewidth=2.5, label='PWLC Count')
    ax.plot(x, merged_df['TOTAL Count'], marker='D', linestyle='-.', color='green', linewidth=2.5, label='TOTAL Count')

    # Value labels
        # Value labels + wire name at first point
    for i, y in enumerate(merged_df['LCG Count']):
        ax.text(i, y + 0.8, str(y), ha='center', fontsize=16, color='navy')
        if i == 0:
            ax.text(i, y + 4, "LCG Count", ha='left', fontsize=11, fontweight='bold', color='navy')

    for i, y in enumerate(merged_df['PWLC Count']):
        ax.text(i, y + 0.8, str(y), ha='center', fontsize=16, color='red')
        if i == 0:
            ax.text(i, y + 4, "PWLC Count", ha='left', fontsize=11, fontweight='bold', color='red')

    for i, y in enumerate(merged_df['TOTAL Count']):
        ax.text(i, y + 0.8, str(y), ha='center', fontsize=16, color='green')
        if i == 0:
            ax.text(i, y + 4, "TOTAL Count", ha='left', fontsize=11, fontweight='bold', color='green')


    # X-axis ticks
    ax.set_xticks(x)
    ax.set_xticklabels(time_labels, rotation=45, ha='right', fontsize=10)

    ax.set_title(title, fontsize=18, fontweight='bold', color='#2c3e50', pad=20)
    ax.set_xlabel("Time (7 AM to 6.59 AM)", fontsize=14)
    ax.set_ylabel("Wire Count", fontsize=14)

    ax.set_ylim(0, 60)
    ax.set_yticks(range(0, 51, 5))
    ax.tick_params(axis='y', labelsize=11)

    ax.grid(True, linestyle='--', alpha=0.3)
    for spine in ax.spines.values():
        spine.set_edgecolor('#888')
        spine.set_linewidth(1)

    # ax.legend(loc='upper left', fontsize=12)

    filename = f"wire_count_24hr_graph.png"
    graph_path = os.path.join(output_folder, filename)
    fig.tight_layout()
    fig.savefig(graph_path, dpi=100, bbox_inches='tight')
    plt.close(fig)

    print(f"✅ Final 24-Hour Graph saved at: {graph_path}")
    return graph_path
