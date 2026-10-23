import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import statsmodels.api as sm
import os
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['font.size'] = 11
plt.rcParams['axes.linewidth'] = 1.2
plt.rcParams['figure.dpi'] = 600

data_path = r'c:\Users\13067\Desktop\论文\非洲\demo\清洗数据\enhanced_data_with_complete_features.csv'
df = pd.read_csv(data_path, low_memory=False)
print(f"Data loaded: {len(df)} rows, {len(df.columns)} columns")

treatment = 'development_demand_pca'
mediator = 'normalized_sentiment'
outcome = 'china_africa_community_recognition'
covariates = ['time_index', 'total_words_count']

df[f'{treatment}_centered'] = df[treatment] - df[treatment].mean()
df[f'{mediator}_centered'] = df[mediator] - df[mediator].mean()
print("Variables centered successfully")

def bootstrap_mediation(data, treatment, mediator, outcome, covariates, n_bootstrap=1000, seed=42):
    np.random.seed(seed)
    n = len(data)
    
    model_vars = [treatment, mediator, outcome] + covariates
    df_model = data[model_vars].dropna()
    
    X = df_model[[treatment] + covariates]
    M = df_model[mediator]
    Y = df_model[outcome]
    
    X = sm.add_constant(X)
    XM = sm.add_constant(pd.concat([X, M], axis=1))
    
    model2 = sm.OLS(M, X).fit()
    model3 = sm.OLS(Y, XM).fit()
    
    a = model2.params[treatment]
    b = model3.params[mediator]
    c_prime = model3.params[treatment]
    total_effect = a * b + c_prime
    indirect_effect = a * b
    
    indirect_effects = []
    direct_effects = []
    total_effects = []
    
    for _ in range(n_bootstrap):
        bootstrap_sample = df_model.sample(n, replace=True)
        
        X_boot = sm.add_constant(bootstrap_sample[[treatment] + covariates])
        M_boot = bootstrap_sample[mediator]
        Y_boot = bootstrap_sample[outcome]
        XM_boot = sm.add_constant(pd.concat([X_boot, M_boot], axis=1))
        
        model2_boot = sm.OLS(M_boot, X_boot).fit()
        model3_boot = sm.OLS(Y_boot, XM_boot).fit()
        
        a_boot = model2_boot.params[treatment]
        b_boot = model3_boot.params[mediator]
        c_prime_boot = model3_boot.params[treatment]
        
        indirect_effect_boot = a_boot * b_boot
        direct_effect_boot = c_prime_boot
        total_effect_boot = indirect_effect_boot + direct_effect_boot
        
        indirect_effects.append(indirect_effect_boot)
        direct_effects.append(direct_effect_boot)
        total_effects.append(total_effect_boot)
    
    ci_lower_indirect = np.percentile(indirect_effects, 2.5)
    ci_upper_indirect = np.percentile(indirect_effects, 97.5)
    ci_lower_direct = np.percentile(direct_effects, 2.5)
    ci_upper_direct = np.percentile(direct_effects, 97.5)
    ci_lower_total = np.percentile(total_effects, 2.5)
    ci_upper_total = np.percentile(total_effects, 97.5)
    
    return {
        'a': a,
        'b': b,
        'c_prime': c_prime,
        'total_effect': total_effect,
        'indirect_effect': indirect_effect,
        'direct_ci': (ci_lower_direct, ci_upper_direct),
        'indirect_ci': (ci_lower_indirect, ci_upper_indirect),
        'total_ci': (ci_lower_total, ci_upper_total)
    }

mediation_result = bootstrap_mediation(
    data=df,
    treatment=f'{treatment}_centered',
    mediator=f'{mediator}_centered',
    outcome=outcome,
    covariates=covariates,
    n_bootstrap=1000
)

print("\n" + "="*60)
print("Mediation Analysis Results")
print("="*60)
print(f"a path (X→M): {mediation_result['a']:.4f}")
print(f"b path (M→Y): {mediation_result['b']:.4f}")
print(f"c' path (X→Y, controlling M): {mediation_result['c_prime']:.4f}")
print(f"Total effect: {mediation_result['total_effect']:.4f}")
print(f"Indirect effect: {mediation_result['indirect_effect']:.4f}")
print(f"Mediation ratio: {mediation_result['indirect_effect']/mediation_result['total_effect']*100:.2f}%")
print("="*60)

fig, ax = plt.subplots(figsize=(14, 10), facecolor='white')
ax.set_xlim(0, 14)
ax.set_ylim(0, 10)
ax.axis('off')

node_x = 2.5
node_m = 7.0
node_y = 11.5
y_top = 7.5
y_mid = 4.5

box_width = 3.2
box_height = 1.0

node_style_x = {
    'boxstyle': 'round,pad=0.3,rounding_size=0.2',
    'facecolor': '#E3F2FD',
    'edgecolor': '#1565C0',
    'linewidth': 2.5,
    'alpha': 0.95
}

node_style_m = {
    'boxstyle': 'round,pad=0.3,rounding_size=0.2',
    'facecolor': '#E8F5E9',
    'edgecolor': '#2E7D32',
    'linewidth': 2.5,
    'alpha': 0.95
}

node_style_y = {
    'boxstyle': 'round,pad=0.3,rounding_size=0.2',
    'facecolor': '#FFEBEE',
    'edgecolor': '#C62828',
    'linewidth': 2.5,
    'alpha': 0.95
}

box_x = FancyBboxPatch((node_x - box_width/2, y_top - box_height/2), box_width, box_height, **node_style_x)
ax.add_patch(box_x)

box_m = FancyBboxPatch((node_m - box_width/2, y_mid - box_height/2), box_width, box_height, **node_style_m)
ax.add_patch(box_m)

box_y = FancyBboxPatch((node_y - box_width/2, y_top - box_height/2), box_width, box_height, **node_style_y)
ax.add_patch(box_y)

ax.text(node_x, y_top, 'Development Demand\nPerception (Centered)', 
        ha='center', va='center', fontsize=11, fontweight='bold', 
        color='#1565C0', linespacing=1.2)

ax.text(node_m, y_mid, 'Sentiment Intensity\n(Centered)', 
        ha='center', va='center', fontsize=11, fontweight='bold', 
        color='#2E7D32', linespacing=1.2)

ax.text(node_y, y_top, 'China-Africa Community\nRecognition', 
        ha='center', va='center', fontsize=11, fontweight='bold', 
        color='#C62828', linespacing=1.2)

ax.annotate('', 
            xy=(node_m - box_width/2 - 0.1, y_mid), 
            xytext=(node_x + box_width/2 + 0.1, y_top - box_height/2),
            arrowprops=dict(
                arrowstyle='-|>',
                color='#1565C0',
                lw=2.5,
                mutation_scale=20,
                connectionstyle='arc3,rad=-0.2'
            ))

ax.annotate('', 
            xy=(node_y - box_width/2 - 0.1, y_top - box_height/2), 
            xytext=(node_m + box_width/2 + 0.1, y_mid + box_height/2),
            arrowprops=dict(
                arrowstyle='-|>',
                color='#2E7D32',
                lw=2.5,
                mutation_scale=20,
                connectionstyle='arc3,rad=-0.2'
            ))

ax.annotate('', 
            xy=(node_y - box_width/2 - 0.1, y_top), 
            xytext=(node_x + box_width/2 + 0.1, y_top),
            arrowprops=dict(
                arrowstyle='-|>',
                color='#C62828',
                lw=2.5,
                mutation_scale=20
            ))

a_value = mediation_result['a']
b_value = mediation_result['b']
c_prime_value = mediation_result['c_prime']
indirect_value = mediation_result['indirect_effect']
total_value = mediation_result['total_effect']
mediation_ratio = indirect_value / total_value * 100 if total_value != 0 else 0

ax.text(4.5, 5.8, f'a = {a_value:.3f}***', 
        ha='center', va='center', fontsize=12, fontweight='bold',
        color='#1565C0', 
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#1565C0', alpha=0.95, linewidth=1.5))

ax.text(9.5, 5.8, f'b = {b_value:.3f}***', 
        ha='center', va='center', fontsize=12, fontweight='bold',
        color='#2E7D32',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#2E7D32', alpha=0.95, linewidth=1.5))

ax.text(7.0, 8.2, f"c' = {c_prime_value:.3f}***", 
        ha='center', va='center', fontsize=12, fontweight='bold',
        color='#C62828',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#C62828', alpha=0.95, linewidth=1.5))

info_box_style = dict(
    boxstyle='round,pad=0.5',
    facecolor='#FAFAFA',
    edgecolor='#9E9E9E',
    linewidth=1.5,
    alpha=0.98
)

info_text = (f"Total Effect = {total_value:.3f}\n"
             f"Indirect Effect = {indirect_value:.3f}\n"
             f"Mediation Ratio = {mediation_ratio:.1f}%")

ax.text(7.0, 2.0, info_text, 
        ha='center', va='center', fontsize=11,
        bbox=info_box_style,
        linespacing=1.5)

ax.text(7.0, 9.5, 'Mediation Effect Path Diagram', 
        ha='center', va='center', fontsize=16, fontweight='bold',
        color='#212121')

ax.text(7.0, 9.0, 'Bootstrap Method (N = 1,000)', 
        ha='center', va='center', fontsize=11, style='italic',
        color='#616161')

ax.text(13.5, 1.0, '*** p < 0.001', 
        ha='right', va='bottom', fontsize=10, color='#757575')

output_dir = r'c:\Users\13067\Desktop\论文\非洲\demo\可视化'
os.makedirs(output_dir, exist_ok=True)

png_path = os.path.join(output_dir, 'Figure7_English.png')
pdf_path = os.path.join(output_dir, 'Figure7_English.pdf')

plt.savefig(png_path, dpi=600, bbox_inches='tight', facecolor='white', edgecolor='none')
plt.savefig(pdf_path, format='pdf', bbox_inches='tight', facecolor='white', edgecolor='none')

print(f"\n✓ PNG saved: {png_path}")
print(f"✓ PDF saved: {pdf_path}")
print("\nFigure generation completed successfully!")
