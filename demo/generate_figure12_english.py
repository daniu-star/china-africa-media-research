import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import os

plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 11
plt.rcParams['figure.dpi'] = 600

emotion_dimensions = ['Confusion', 'Surprise', 'Fear', 'Sadness', 'Anger', 'Worry', 'Pride', 'Joy', 'Trust', 'Anticipation']

left_panel_data = {
    'iv_name': 'Development Demand\nPerception',
    'dv_name': 'Identification',
    'direct_path': 0.083,
    'x_to_m': [0.001, -0.005, -0.005, 0.000, -0.023, -0.002, -0.001, -0.003, -0.000, -0.006],
    'm_to_y': [0.001, -0.001, -0.001, -0.000, 0.008, -0.001, -0.001, -0.000, -0.000, 0.001]
}

right_panel_data = {
    'iv_name': 'Willingness to\nCooperate',
    'dv_name': 'Identification',
    'direct_path': 0.115,
    'x_to_m': [0.008, -0.004, -0.005, 0.000, -0.02, 0.006, -0.005, -0.002, 0.008, 0.005],
    'm_to_y': [-0.001, -0.000, -0.001, 0.000, 0.009, 0.000, 0.000, 0.000, -0.001, 0.000]
}

def draw_sem_path_diagram(ax, panel_data, title):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    iv_x, iv_y = 0.12, 0.5
    dv_x, dv_y = 0.88, 0.5
    
    n_mediators = len(emotion_dimensions)
    mediator_y_positions = np.linspace(0.05, 0.95, n_mediators)
    mediator_x = 0.5
    
    node_color = '#4CAF50'
    node_border_color = '#2E7D32'
    mediator_color = '#81C784'
    mediator_border_color = '#388E3C'
    arrow_color = '#616161'
    
    iv_box = FancyBboxPatch((iv_x - 0.08, iv_y - 0.06), 0.16, 0.12,
                             boxstyle='round,pad=0.02,rounding_size=0.02',
                             facecolor=node_color, edgecolor=node_border_color,
                             linewidth=2.5, alpha=0.95, zorder=5)
    ax.add_patch(iv_box)
    ax.text(iv_x, iv_y, panel_data['iv_name'], ha='center', va='center',
            fontsize=11, fontweight='bold', fontfamily='Times New Roman', color='white', zorder=6)
    
    dv_box = FancyBboxPatch((dv_x - 0.07, dv_y - 0.06), 0.14, 0.12,
                             boxstyle='round,pad=0.02,rounding_size=0.02',
                             facecolor=node_color, edgecolor=node_border_color,
                             linewidth=2.5, alpha=0.95, zorder=5)
    ax.add_patch(dv_box)
    ax.text(dv_x, dv_y, panel_data['dv_name'], ha='center', va='center',
            fontsize=11, fontweight='bold', fontfamily='Times New Roman', color='white', zorder=6)
    
    mediator_width = 0.09
    mediator_height = 0.04
    for i, (emotion, med_y) in enumerate(zip(emotion_dimensions, mediator_y_positions)):
        med_box = FancyBboxPatch((mediator_x - mediator_width/2, med_y - mediator_height/2),
                                  mediator_width, mediator_height,
                                  boxstyle='round,pad=0.01,rounding_size=0.01',
                                  facecolor=mediator_color, edgecolor=mediator_border_color,
                                  linewidth=1.8, alpha=0.95, zorder=5)
        ax.add_patch(med_box)
        ax.text(mediator_x, med_y, emotion, ha='center', va='center',
                fontsize=8, fontweight='bold', fontfamily='Times New Roman', color='#1B5E20', zorder=6)
    
    for i, med_y in enumerate(mediator_y_positions):
        ax.annotate('', xy=(mediator_x - mediator_width/2 - 0.01, med_y),
                   xytext=(iv_x + 0.08 + 0.01, iv_y),
                   arrowprops=dict(arrowstyle='->', color=arrow_color, lw=1.2,
                                  connectionstyle='arc3,rad=0'),
                   zorder=3)
        
        mid_x = (iv_x + 0.08 + mediator_x - mediator_width/2) / 2
        mid_y = (iv_y + med_y) / 2
        coeff = panel_data['x_to_m'][i]
        ax.text(mid_x, mid_y + 0.015, f'{coeff:.3f}', ha='center', va='bottom',
                fontsize=7, fontfamily='Times New Roman', color='#424242',
                bbox=dict(boxstyle='round,pad=0.1', facecolor='white', edgecolor='none', alpha=0.9), zorder=7)
    
    for i, med_y in enumerate(mediator_y_positions):
        ax.annotate('', xy=(dv_x - 0.07 - 0.01, dv_y),
                   xytext=(mediator_x + mediator_width/2 + 0.01, med_y),
                   arrowprops=dict(arrowstyle='->', color=arrow_color, lw=1.2,
                                  connectionstyle='arc3,rad=0'),
                   zorder=3)
        
        mid_x = (mediator_x + mediator_width/2 + dv_x - 0.07) / 2
        mid_y = (med_y + dv_y) / 2
        coeff = panel_data['m_to_y'][i]
        ax.text(mid_x, mid_y + 0.015, f'{coeff:.3f}', ha='center', va='bottom',
                fontsize=7, fontfamily='Times New Roman', color='#424242',
                bbox=dict(boxstyle='round,pad=0.1', facecolor='white', edgecolor='none', alpha=0.9), zorder=7)
    
    ax.annotate('', xy=(dv_x - 0.07 - 0.01, dv_y + 0.03),
               xytext=(iv_x + 0.08 + 0.01, iv_y + 0.03),
               arrowprops=dict(arrowstyle='->', color='#D32F2F', lw=2.5,
                              connectionstyle='arc3,rad=0.15'),
               zorder=4)
    
    direct_mid_x = (iv_x + 0.08 + dv_x - 0.07) / 2
    direct_mid_y = iv_y + 0.001
    ax.text(direct_mid_x, direct_mid_y, f'{panel_data["direct_path"]:.3f}', ha='center', va='bottom',
            fontsize=10, fontweight='bold', fontfamily='Times New Roman', color='#D32F2F',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='#D32F2F', linewidth=1.5, alpha=0.95), zorder=7)
    
    ax.set_title(title, fontsize=13, fontweight='bold', fontfamily='Times New Roman',
                pad=15, color='#212121')

fig = plt.figure(figsize=(22, 14), facecolor='white')

ax1 = fig.add_axes([0.02, 0.08, 0.46, 0.84])
draw_sem_path_diagram(ax1, left_panel_data, '(a) Development Demand Perception Model')

ax2 = fig.add_axes([0.52, 0.08, 0.46, 0.84])
draw_sem_path_diagram(ax2, right_panel_data, '(b) Willingness to Cooperate Model')

fig.suptitle('Multiple Mediation Model of Emotional Dimensions\n(Standardized Path Coefficients)',
            fontsize=16, fontweight='bold', fontfamily='Times New Roman', y=0.97, color='#212121')

legend_ax = fig.add_axes([0.25, 0.01, 0.5, 0.05])
legend_ax.axis('off')

legend_text = ('Note: IV = Independent Variable; M = Mediator (Emotion Dimensions); DV = Dependent Variable\n'
              'Path coefficients are standardized. Direct path shown in red (curved arrow).')
legend_ax.text(0.5, 0.5, legend_text, ha='center', va='center',
              fontsize=10, fontfamily='Times New Roman',
              bbox=dict(boxstyle='round,pad=0.5', alpha=0.95, facecolor='#FAFAFA',
                       edgecolor='#BDBDBD', linewidth=1.5))

output_dir = r'c:\Users\13067\Desktop\论文\非洲\demo\可视化'
os.makedirs(output_dir, exist_ok=True)

png_path = os.path.join(output_dir, 'Figure12_English.png')
plt.savefig(png_path, dpi=600, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f"\n✓ PNG saved: {png_path}")

pdf_path = os.path.join(output_dir, 'Figure12_English.pdf')
plt.savefig(pdf_path, format='pdf', bbox_inches='tight', facecolor='white', edgecolor='none')
print(f"✓ PDF saved: {pdf_path}")

plt.close()

print("\nFigure 12 English version generated successfully!")
print("\nData Summary:")
print("Left Panel (Development Demand Perception):")
print(f"  - Direct path coefficient: {left_panel_data['direct_path']}")
print(f"  - X→M coefficients: {left_panel_data['x_to_m']}")
print(f"  - M→Y coefficients: {left_panel_data['m_to_y']}")
print("\nRight Panel (Willingness to Cooperate):")
print(f"  - Direct path coefficient: {right_panel_data['direct_path']}")
print(f"  - X→M coefficients: {right_panel_data['x_to_m']}")
print(f"  - M→Y coefficients: {right_panel_data['m_to_y']}")
print(f"\nMediator variables: {', '.join(emotion_dimensions)}")
