"""
Sector Rotation Scan — Chart Generator Template
Usage: Write this to /tmp/gen_charts.py, then run via terminal()
Requires: pip install matplotlib --break-system-packages
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Dark theme config
plt.style.use('dark_background')
plt.rcParams.update({
    'figure.facecolor': '#0f0f23',
    'axes.facecolor': '#1a1a3e',
    'text.color': '#e0e0e0',
    'axes.labelcolor': '#e0e0e0',
    'xtick.color': '#b0b0b0',
    'ytick.color': '#b0b0b0',
})

def temp_color(pct_from_52h):
    if pct_from_52h > -5: return '#ff4444'   # HOT
    elif pct_from_52h > -15: return '#ff8c00' # WARM
    elif pct_from_52h > -25: return '#ffd700' # COOL
    else: return '#4488ff'                     # COLD

def temp_label(pct_from_52h):
    if pct_from_52h > -5: return 'HOT'
    elif pct_from_52h > -15: return 'WARM'
    elif pct_from_52h > -25: return 'COOL'
    else: return 'COLD'

def make_sector_temp_chart(data, output_path='/tmp/chart_sector_temp.png'):
    """
    data: list of tuples (name, pct_3m, pct_from_52h)
    """
    data.sort(key=lambda x: x[2], reverse=True)
    names = [d[0] for d in data]
    pct_3m = [d[1] for d in data]
    pct_fh = [d[2] for d in data]
    colors = [temp_color(p) for p in pct_fh]

    fig, ax = plt.subplots(figsize=(14, max(8, len(data) * 0.5)))
    ax.barh(range(len(names)), pct_fh, color=colors, alpha=0.85, height=0.7,
            edgecolor='white', linewidth=0.3)

    for i, (pfh, p3m) in enumerate(zip(pct_fh, pct_3m)):
        ax.text(pfh - 0.5, i, f'{pfh:.0f}%', va='center', ha='right',
                fontsize=9, fontweight='bold', color='white')
        ax.text(5, i, f'3M: {p3m:+.0f}%', va='center', ha='left',
                fontsize=8, color='#999')

    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=10)
    ax.set_xlabel('% From 52-Week High', fontsize=12, fontweight='bold')
    ax.set_title('SECTOR TEMPERATURE MAP', fontsize=15, fontweight='bold',
                 pad=15, color='#00d4ff')

    legend = [
        mpatches.Patch(facecolor='#ff4444', label='HOT (<5%)'),
        mpatches.Patch(facecolor='#ff8c00', label='WARM (5-15%)'),
        mpatches.Patch(facecolor='#ffd700', label='COOL (15-25%)'),
        mpatches.Patch(facecolor='#4488ff', label='COLD (>25%)'),
    ]
    ax.legend(handles=legend, loc='lower right', fontsize=9,
              facecolor='#0f0f23', edgecolor='#555')
    for thresh in [-5, -15, -25]:
        ax.axvline(x=thresh, color=temp_color(thresh), linestyle='--', alpha=0.3)
    ax.set_xlim(min(pct_fh) - 10, 5)
    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    return output_path
