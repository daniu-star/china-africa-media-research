import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import numpy as np
from matplotlib.gridspec import GridSpec

plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9
plt.rcParams['legend.fontsize'] = 9
plt.rcParams['figure.dpi'] = 300

NATURE_COLORS = {
    'primary': '#2E86AB',
    'secondary': '#A23B72', 
    'tertiary': '#F18F01',
    'quaternary': '#C73E1D',
    'neutral': '#3B1F2B',
    'light_blue': '#4A90D9',
    'light_green': '#5CB85C',
    'light_orange': '#F5A623',
    'gray': '#7F8C8D'
}

def main():
    input_file = 'c:/Users/13067/Desktop/论文/非洲/demo/清洗数据/enhanced_data_with_complete_features.csv'
    
    print("Loading analysis data...")
    df = pd.read_csv(input_file, low_memory=False)
    print(f"Total data: {len(df)} records")
    
    print("\nPreprocessing data...")
    
    if 'year' in df.columns:
        df['parsed_date'] = pd.to_datetime(df['year'].astype(str) + '-01-01', errors='coerce')
    else:
        df['parsed_date'] = pd.to_datetime(df.get('date', '2020-01-01'), errors='coerce')
    
    if 'title' in df.columns:
        df['title_length'] = df['title'].str.len()
    else:
        df['title_length'] = 50
    
    if 'summary' in df.columns:
        df['summary_length'] = df['summary'].str.len()
    else:
        df['summary_length'] = 200
    
    df['total_length'] = df['title_length'] + df['summary_length']
    
    if '主题' in df.columns:
        df['clean_category'] = df['主题']
    elif 'category' in df.columns:
        df['clean_category'] = df['category'].astype(str).str.split('\n').str[0].str.strip()
    else:
        df['clean_category'] = 'General'
    
    if 'source' in df.columns:
        source_counts = df['source'].value_counts()
        top_sources = source_counts[source_counts >= 10].index.tolist()
        df['clean_source'] = df['source'].apply(lambda x: x if x in top_sources else 'Others')
    elif 'source_region_5' in df.columns:
        df['clean_source'] = df['source_region_5']
    else:
        df['clean_source'] = 'Unknown'
    
    if 'normalized_sentiment' in df.columns:
        df['final_sentiment_score'] = df['normalized_sentiment']
        df['final_sentiment_label'] = df['normalized_sentiment'].apply(
            lambda x: 'positive' if x > 0.1 else ('negative' if x < -0.1 else 'neutral')
        )
    else:
        sentiment_cols = [col for col in df.columns if 'sentiment' in col.lower() and 'score' in col.lower()]
        if sentiment_cols:
            df['final_sentiment_score'] = df[sentiment_cols[0]]
            df['final_sentiment_label'] = df[sentiment_cols[0]].apply(
                lambda x: 'positive' if x > 0.1 else ('negative' if x < -0.1 else 'neutral')
            )
        else:
            df['final_sentiment_score'] = 0
            df['final_sentiment_label'] = 'neutral'
    
    print("Data preprocessing completed!")
    
    fig = plt.figure(figsize=(11, 14))
    gs = GridSpec(4, 2, figure=fig, hspace=0.35, wspace=0.25, 
                  left=0.08, right=0.95, top=0.95, bottom=0.05)
    
    total_articles = len(df)
    avg_title_length = df['title_length'].mean()
    avg_summary_length = df['summary_length'].mean()
    unique_sources = df['clean_source'].nunique()
    unique_categories = df['clean_category'].nunique()
    sentiment_counts = df['final_sentiment_label'].value_counts()
    
    ax_info = fig.add_subplot(gs[0, :])
    ax_info.axis('off')
    
    info_text = (
        f"Sample Overview\n\n"
        f"Total articles: {total_articles:,}\n"
        f"Average title length: {avg_title_length:.1f} characters\n"
        f"Average summary length: {avg_summary_length:.1f} characters\n"
        f"Number of sources: {unique_sources}\n"
        f"Number of categories: {unique_categories}\n"
        f"Sentiment distribution: Positive {sentiment_counts.get('positive', 0):,}, "
        f"Neutral {sentiment_counts.get('neutral', 0):,}, Negative {sentiment_counts.get('negative', 0):,}"
    )
    
    ax_info.text(0.5, 0.5, info_text, ha='center', va='center', fontsize=11,
                 fontfamily='Times New Roman', 
                 bbox=dict(boxstyle='round,pad=0.5', facecolor='#F8F9FA', edgecolor='#DEE2E6', linewidth=1))
    
    ax1 = fig.add_subplot(gs[1, 0])
    source_dist = df['clean_source'].value_counts().sort_values(ascending=False).head(10)
    bars1 = ax1.barh(range(len(source_dist)), source_dist.values, color=NATURE_COLORS['primary'], edgecolor='white', linewidth=0.5)
    ax1.set_yticks(range(len(source_dist)))
    ax1.set_yticklabels(source_dist.index, fontfamily='Times New Roman')
    ax1.set_xlabel('Number of Articles', fontfamily='Times New Roman')
    ax1.set_title('(a) Distribution of News Sources', fontfamily='Times New Roman', fontweight='bold', loc='left')
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.grid(axis='x', linestyle='--', alpha=0.3)
    ax1.invert_yaxis()
    
    ax2 = fig.add_subplot(gs[1, 1])
    category_dist = df['clean_category'].value_counts().sort_values(ascending=False).head(8)
    bars2 = ax2.barh(range(len(category_dist)), category_dist.values, color=NATURE_COLORS['secondary'], edgecolor='white', linewidth=0.5)
    ax2.set_yticks(range(len(category_dist)))
    ax2.set_yticklabels(category_dist.index, fontfamily='Times New Roman')
    ax2.set_xlabel('Number of Articles', fontfamily='Times New Roman')
    ax2.set_title('(b) Distribution of News Categories', fontfamily='Times New Roman', fontweight='bold', loc='left')
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.grid(axis='x', linestyle='--', alpha=0.3)
    ax2.invert_yaxis()
    
    ax3 = fig.add_subplot(gs[2, 0])
    if 'parsed_date' in df.columns:
        df['publish_year'] = df['parsed_date'].dt.year
        year_counts = df['publish_year'].value_counts().sort_index()
        ax3.bar(range(len(year_counts)), year_counts.values, color=NATURE_COLORS['tertiary'], edgecolor='white', linewidth=0.5)
        ax3.set_xticks(range(len(year_counts)))
        ax3.set_xticklabels([str(int(y)) for y in year_counts.index], rotation=45, ha='right', fontfamily='Times New Roman')
    ax3.set_xlabel('Publication Year', fontfamily='Times New Roman')
    ax3.set_ylabel('Number of Articles', fontfamily='Times New Roman')
    ax3.set_title('(c) Temporal Distribution', fontfamily='Times New Roman', fontweight='bold', loc='left')
    ax3.spines['top'].set_visible(False)
    ax3.spines['right'].set_visible(False)
    ax3.grid(axis='y', linestyle='--', alpha=0.3)
    
    ax4 = fig.add_subplot(gs[2, 1])
    sentiment_dist = df['final_sentiment_label'].value_counts()
    colors_pie = [NATURE_COLORS['light_green'], NATURE_COLORS['gray'], NATURE_COLORS['quaternary']]
    labels_pie = ['Positive', 'Neutral', 'Negative']
    sizes = [sentiment_dist.get('positive', 0), sentiment_dist.get('neutral', 0), sentiment_dist.get('negative', 0)]
    wedges, texts, autotexts = ax4.pie(sizes, labels=labels_pie, autopct='%1.1f%%', 
                                        startangle=90, colors=colors_pie,
                                        wedgeprops=dict(edgecolor='white', linewidth=1))
    for text in texts + autotexts:
        text.set_fontfamily('Times New Roman')
    ax4.set_title('(d) Sentiment Distribution', fontfamily='Times New Roman', fontweight='bold', loc='left')
    
    ax5 = fig.add_subplot(gs[3, 0])
    sns.histplot(df['final_sentiment_score'].dropna(), bins=30, kde=True, ax=ax5, 
                 color=NATURE_COLORS['primary'], edgecolor='white', linewidth=0.5, alpha=0.7)
    ax5.axvline(x=0, color=NATURE_COLORS['quaternary'], linestyle='--', linewidth=1.5, label='Neutral')
    ax5.set_xlabel('Sentiment Score', fontfamily='Times New Roman')
    ax5.set_ylabel('Frequency', fontfamily='Times New Roman')
    ax5.set_title('(e) Sentiment Score Distribution', fontfamily='Times New Roman', fontweight='bold', loc='left')
    ax5.spines['top'].set_visible(False)
    ax5.spines['right'].set_visible(False)
    ax5.grid(axis='y', linestyle='--', alpha=0.3)
    ax5.legend(prop={'family': 'Times New Roman'})
    
    ax6 = fig.add_subplot(gs[3, 1])
    box_data = df[['title_length', 'summary_length']].dropna()
    box_data.columns = ['Title', 'Summary']
    bp = ax6.boxplot([box_data['Title'].dropna(), box_data['Summary'].dropna()], 
                     patch_artist=True, widths=0.6)
    colors_box = [NATURE_COLORS['primary'], NATURE_COLORS['secondary']]
    for patch, color in zip(bp['boxes'], colors_box):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    for element in ['whiskers', 'caps']:
        for item in bp[element]:
            item.set_color(NATURE_COLORS['neutral'])
    ax6.set_xticklabels(['Title', 'Summary'], fontfamily='Times New Roman')
    ax6.set_ylabel('Character Count', fontfamily='Times New Roman')
    ax6.set_title('(f) Text Length Distribution', fontfamily='Times New Roman', fontweight='bold', loc='left')
    ax6.spines['top'].set_visible(False)
    ax6.spines['right'].set_visible(False)
    ax6.grid(axis='y', linestyle='--', alpha=0.3)
    
    output_path = 'c:/Users/13067/Desktop/论文/非洲/Sample_Profile_English.png'
    plt.savefig(output_path, dpi=600, bbox_inches='tight', facecolor='white', edgecolor='none')
    print(f"\nFigure saved to: {output_path}")
    
    output_pdf = 'c:/Users/13067/Desktop/论文/非洲/Sample_Profile_English.pdf'
    plt.savefig(output_pdf, dpi=600, bbox_inches='tight', facecolor='white', edgecolor='none')
    print(f"PDF saved to: {output_pdf}")
    
    plt.close()
    
    print("\nVisualization completed!")
    print("The figure follows Nature/Science journal style with:")
    print("- Times New Roman font family")
    print("- Clean, minimal design")
    print("- High resolution (600 DPI)")
    print("- Professional color palette")

if __name__ == "__main__":
    main()
