import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.table import Table
import numpy as np

plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman']
plt.rcParams['axes.unicode_minus'] = False

table_data = [
    ['Variable Name', 'Type', 'Calculation Formula', 'Range/Category', 'Reliability'],
    ['Time Variable', 'Numerical', 'time_index = year(date)', '0-2025', 'Single indicator'],
    ['Cooperation Willingness', 'Numerical', 'cooperation_willingness_advanced =\nStandardized(Smoothed(Cosine Similarity\n(Text Embedding, Cooperation Topic Embedding)))', '0-1', '4.23/5.0'],
    ['Development Demand\nPerception', 'Numerical', 'development_demand_pca =\nPCA(development_features)', '-', '0.6945'],
    ['Source Region', 'Categorical', 'source_region_5 =\nClassification(source)', 'North Africa, West Africa,\nEast Africa, Southern Africa,\nCentral Africa', 'Single indicator']
]

fig, ax = plt.subplots(figsize=(16, 6), facecolor='white')
ax.axis('off')

n_rows = len(table_data)
n_cols = len(table_data[0])

cell_widths = [0.18, 0.10, 0.35, 0.20, 0.12]

table = ax.table(
    cellText=table_data,
    cellLoc='center',
    loc='center',
    colWidths=cell_widths,
    bbox=[0.02, 0.1, 0.96, 0.85]
)

table.auto_set_font_size(False)
table.set_fontsize(10)

for key in table.get_celld().keys():
    cell = table.get_celld()[key]
    row, col = key
    
    cell.set_edgecolor('#424242')
    cell.set_linewidth(1.0)
    cell.set_text_props(fontfamily='Times New Roman', ha='center', va='center')
    
    if row == 0:
        cell.set_text_props(fontweight='bold', fontfamily='Times New Roman', fontsize=11)
        cell.set_facecolor('#E3F2FD')
        cell.set_height(0.12)
    else:
        cell.set_facecolor('white')
        cell.set_height(0.18)
        if col == 0:
            cell.set_text_props(fontweight='bold', fontfamily='Times New Roman')

ax.text(0.5, 0.98, 'Table 1. Independent Variables Summary', 
        ha='center', va='top', fontsize=14, fontweight='bold',
        fontfamily='Times New Roman', transform=ax.transAxes)

ax.axhline(y=0.95, xmin=0.02, xmax=0.98, color='#1565C0', linewidth=2)
ax.axhline(y=0.08, xmin=0.02, xmax=0.98, color='#1565C0', linewidth=2)

output_path = 'c:/Users/13067/Desktop/论文/非洲/Independent_Variables_Table_English.png'
plt.savefig(output_path, dpi=600, bbox_inches='tight', facecolor='white', edgecolor='none', pad_inches=0.2)
print(f"PNG saved to: {output_path}")

output_pdf = 'c:/Users/13067/Desktop/论文/非洲/Independent_Variables_Table_English.pdf'
plt.savefig(output_pdf, dpi=600, bbox_inches='tight', facecolor='white', edgecolor='none', pad_inches=0.2)
print(f"PDF saved to: {output_pdf}")

plt.close()

print("\nTable generation completed successfully!")

df = pd.DataFrame(table_data[1:], columns=table_data[0])
csv_path = 'c:/Users/13067/Desktop/论文/非洲/Independent_Variables_Table_English.csv'
df.to_csv(csv_path, index=False, encoding='utf-8-sig')
print(f"CSV saved to: {csv_path}")
