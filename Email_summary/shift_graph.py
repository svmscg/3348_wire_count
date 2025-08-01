import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import timedelta # Import timedelta for the offset

def generate_shift_wire_count_graph(df, shift_name, output_folder=r"C:\Users\6078\Desktop\3348_wire_count\Email_summary\output_graphs"):
    print("🖼️ Preparing graph...")

    required_cols = {'Time', 'LCG Count', 'PWLC Count', 'TOTAL Count'}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"Missing required columns in DataFrame: {required_cols - set(df.columns)}")
    if df.empty:
        raise ValueError("Shift summary DataFrame is empty. Cannot generate graph.")

    try:
        df['Time'] = pd.to_datetime(df['Time'], format="%I:%M %p")
    except Exception as e:
        raise ValueError(f"Error parsing 'Time' column: {e}")

    os.makedirs(output_folder, exist_ok=True)

    fig, ax = plt.subplots(figsize=(14, 8))

    # Plot each line with its own color
    ax.plot(df['Time'], df['LCG Count'], marker='o', linestyle='-', color='blue', linewidth=2.5)
    ax.plot(df['Time'], df['PWLC Count'], marker='s', linestyle='--', color='red', linewidth=2.5)
    ax.plot(df['Time'], df['TOTAL Count'], marker='D', linestyle='-.', color='green', linewidth=2.5)

    # --- Add continuous numerical labels for each line ---
    # LCG Count labels (above the line)
    for x, y in zip(df['Time'], df['LCG Count']):
        ax.text(x, y + 2, str(y), ha='center', va='bottom', fontsize=15, color='blue')
    
    # PWLC Count labels (below the line)
    for x, y in zip(df['Time'], df['PWLC Count']):
        ax.text(x, y - 2, str(y), ha='center', va='top', fontsize=15, color='red')
    
    # TOTAL Count labels (above the line)
    for x, y in zip(df['Time'], df['TOTAL Count']):
        ax.text(x, y + 2, str(y), ha='center', va='bottom', fontsize=15, color='green')

    # --- Add single name labels at the starting point ---
    first_x = df['Time'].iloc[0]
    first_y_lcg = df['LCG Count'].iloc[0]
    first_y_pwlc = df['PWLC Count'].iloc[0]
    first_y_total = df['TOTAL Count'].iloc[0]
    
    # Define a small horizontal offset to move the text to the right
    horizontal_offset = timedelta(minutes=30)
    
    # LCG Count name label (above the line)
    ax.text(first_x , first_y_lcg + 5, "LCG Count", ha='left', va='bottom', fontsize=16, color='blue', fontweight='bold')
    
    # PWLC Count name label (below the line)
    ax.text(first_x , first_y_pwlc - 6, "PWLC Count", ha='left', va='top', fontsize=16, color='red', fontweight='bold')
    
    # TOTAL Count name label (below the line) - unchanged position
    ax.text(first_x, first_y_total - 2, "TOTAL Count", ha='left', va='top', fontsize=16, color='green', fontweight='bold')
    
    # Titles and labels
    ax.set_title(f"{shift_name} – Hourly Wire Count Summary", fontsize=18, fontweight='bold', color='#2c3e50', pad=20)
    ax.set_xlabel("Time", fontsize=14, labelpad=10)
    ax.set_ylabel("Wire Count", fontsize=14, labelpad=10)

    # X-axis formatting
    ax.set_xticks(df['Time'])
    ax.set_xticklabels(df['Time'].dt.strftime('%I:%M %p'), rotation=45, ha='right', fontsize=11)

    # Y-axis formatting
    max_y = 54
    ax.set_ylim(0, max_y)
    ax.set_yticks(range(0, max_y + 1, 4))
    ax.tick_params(axis='y', labelsize=11)

    # Grid & border
    ax.grid(True, linestyle='--', alpha=0.4)
    for spine in ax.spines.values():
        spine.set_edgecolor('#aaa')
        spine.set_linewidth(1)

    filename = f"{shift_name.replace(' ', '_')}_wire_graph.png"
    graph_path = os.path.join(output_folder, filename)
    fig.tight_layout()
    fig.savefig(graph_path, dpi=100, bbox_inches='tight')
    plt.close(fig)

    print(f"✅ Graph saved at: {graph_path}")
    return graph_path