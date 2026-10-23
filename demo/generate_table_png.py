import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from matplotlib.table import Table

plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman']
plt.rcParams['axes.unicode_minus'] = False

REGION_MAPPING = {
    '东非': 'East Africa',
    '中非': 'Central Africa',
    '西非': 'West Africa',
    '南非': 'Southern Africa',
    '北非': 'North Africa'
}

SENTIMENT_MAPPING = {
    'positive': 'Positive',
    'neutral': 'Neutral',
    'negative': 'Negative'
}

def main():
    input_file = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_complete_features.csv'
    
    print("Loading data...")
    df = pd.read_csv(input_file, low_memory=False)
    
    total_n = len(df)
    print(f"Total sample: {total_n:,}")
    
    if 'source_region_5' in df.columns:
        df['source_region_en'] = df['source_region_5'].map(REGION_MAPPING).fillna(df['source_region_5'])
        region_stats = df['source_region_en'].value_counts()
        region_stats_list = [(cat, n, n/total_n*100) for cat, n in region_stats.items()]
    else:
        region_stats_list = []
    
    if 'sentiment_label' in df.columns:
        df['sentiment_en'] = df['sentiment_label'].str.lower().map(SENTIMENT_MAPPING).fillna(df['sentiment_label'])
        sentiment_stats = df['sentiment_en'].value_counts()
        sentiment_stats_list = [(cat, n, n/total_n*100) for cat, n in sentiment_stats.items()]
    else:
        sentiment_stats_list = []
    
    continuous_vars = []
    var_configs = [
        ('normalized_sentiment', 'Normalized Sentiment'),
        ('china_africa_community_recognition', 'China-Africa Community Recognition'),
        ('development_demand_pca', 'Development Demand (PCA)'),
        ('cooperation_depth_index', 'Cooperation Depth Index'),
        ('long_term_word_count', 'Long-term Word Count')
    ]
    
    for col, name in var_configs:
        if col in df.columns:
            mean_val = df[col].mean()
            std_val = df[col].std()
            continuous_vars.append((name, mean_val, std_val))
    
    if 'year' in df.columns:
        year_stats = df['year'].value_counts().sort_index(ascending=False)
        year_stats_list = [(int(y), n, n/total_n*100) for y, n in year_stats.head(10).items()]
    else:
        year_stats_list = []
    
    fig, ax = plt.subplots(figsize=(9, 14))
    ax.axis('off')
    
    table_data = []
    
    table_data.append(['Variable', 'Category', 'n (%)'])
    table_data.append(['Total Sample Size', '', f'{total_n:,}'])
    table_data.append(['', '', ''])
    
    table_data.append(['Publication Year', '', ''])
    for year, n, pct in year_stats_list:
        table_data.append(['', str(year), f'{n:,} ({pct:.1f}%)'])
    table_data.append(['', '', ''])
    
    table_data.append(['Source Region', '', ''])
    for region, n, pct in region_stats_list:
        table_data.append(['', region, f'{n:,} ({pct:.1f}%)'])
    table_data.append(['', '', ''])
    
    table_data.append(['Sentiment Distribution', '', ''])
    for sentiment, n, pct in sentiment_stats_list:
        table_data.append(['', sentiment, f'{n:,} ({pct:.1f}%)'])
    table_data.append(['', '', ''])
    
    table_data.append(['Continuous Variables', '', 'Mean ± SD'])
    for var_name, mean_val, std_val in continuous_vars:
        table_data.append(['', var_name, f'{mean_val:.2f} ± {std_val:.2f}'])
    
    n_rows = len(table_data)
    n_cols = 3
    
    cell_widths = [0.35, 0.35, 0.25]
    
    table = ax.table(
        cellText=table_data,
        cellLoc='left',
        loc='center',
        colWidths=cell_widths,
        bbox=[0.08, 0.08, 0.84, 0.80]
    )
    
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    
    for i, key in enumerate(table.get_celld().keys()):
        cell = table.get_celld()[key]
        cell.set_edgecolor('white')
        cell.set_text_props(fontfamily='Times New Roman')
        cell.set_height(0.022)
        
        row, col = key
        
        if row == 0:
            cell.set_text_props(fontweight='bold', fontfamily='Times New Roman', fontsize=11)
            cell.set_facecolor('#E8E8E8')
        elif table_data[row][0] != '' and table_data[row][1] == '' and table_data[row][2] == '':
            cell.set_text_props(fontweight='bold', fontfamily='Times New Roman', style='italic', fontsize=11)
        elif table_data[row][0] != '' and table_data[row][1] == '':
            cell.set_text_props(fontweight='bold', fontfamily='Times New Roman', fontsize=11)
        
        if col == 2 and row > 0:
            cell.set_text_props(ha='right', fontfamily='Times New Roman', fontsize=11)
    
    ax.text(0.5, 0.95, 'Table 1. Sample Profile', 
            ha='center', va='bottom', fontsize=13, fontweight='bold',
            fontfamily='Times New Roman', transform=ax.transAxes)
    
    line_y_top = 0.90
    line_y_header = 0.88
    line_y_bottom = 0.05
    
    ax.axhline(y=line_y_top, xmin=0.08, xmax=0.92, color='black', linewidth=1.5)
    ax.axhline(y=line_y_header, xmin=0.08, xmax=0.92, color='black', linewidth=1.0)
    ax.axhline(y=line_y_bottom, xmin=0.08, xmax=0.92, color='black', linewidth=1.5)
    
    output_path = 'c:/Users/13067/Desktop/论文/非洲/sample_profile_table.png'
    plt.savefig(output_path, dpi=600, bbox_inches='tight', facecolor='white', edgecolor='none', pad_inches=0.3)
    print(f"PNG saved to: {output_path}")
    
    plt.close()
    
    print("Done!")

if __name__ == "__main__":
    main()
