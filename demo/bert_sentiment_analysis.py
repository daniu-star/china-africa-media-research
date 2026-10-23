import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from tqdm import tqdm
from typing import Dict, Any

# 初始化BERT模型和分词器
def init_bert_model():
    # 使用轻量级的DistilBERT模型，专门用于情感分析
    model_name = "distilbert-base-uncased-finetuned-sst-2-english"
    
    print(f"正在加载BERT模型: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    
    # 检查是否有GPU可用
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()  # 设置为评估模式
    
    print(f"模型加载完成，使用设备: {device}")
    return tokenizer, model, device

# BERT情感分析函数
def analyze_bert_sentiment(text: str, tokenizer, model, device) -> Dict[str, Any]:
    if not text or pd.isna(text):
        return {
            'bert_sentiment_label': 'neutral',
            'bert_sentiment_score': 0.0,
            'bert_positive_score': 0.0,
            'bert_negative_score': 0.0
        }
    
    # 文本截断，处理BERT最大序列长度限制
    inputs = tokenizer(
        text,
        truncation=True,
        max_length=512,
        return_tensors="pt",
        padding=True
    )
    
    # 将输入移动到设备上
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    # 推理
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        
    # 计算概率
    probabilities = torch.softmax(logits, dim=1).cpu().numpy()[0]
    
    # 获取结果
    negative_score, positive_score = probabilities
    sentiment_score = positive_score - negative_score  # 范围: [-1, 1]
    
    # 确定情感标签
    if sentiment_score > 0.1:
        sentiment_label = "positive"
    elif sentiment_score < -0.1:
        sentiment_label = "negative"
    else:
        sentiment_label = "neutral"
    
    return {
        'bert_sentiment_label': sentiment_label,
        'bert_sentiment_score': round(sentiment_score, 4),
        'bert_positive_score': round(positive_score, 4),
        'bert_negative_score': round(negative_score, 4)
    }

# 批量处理BERT情感分析，提高效率
def batch_analyze_bert_sentiment(texts, tokenizer, model, device, batch_size=8):
    results = []
    
    # 分批处理
    for i in tqdm(range(0, len(texts), batch_size), desc="BERT情感分析进度"):
        batch_texts = texts[i:i+batch_size]
        
        # 预处理文本
        inputs = tokenizer(
            batch_texts,
            truncation=True,
            max_length=512,
            return_tensors="pt",
            padding=True
        )
        
        # 将输入移动到设备上
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        # 推理
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            probabilities = torch.softmax(logits, dim=1).cpu().numpy()
        
        # 处理结果
        for j, prob in enumerate(probabilities):
            negative_score, positive_score = prob
            sentiment_score = positive_score - negative_score
            
            if sentiment_score > 0.1:
                sentiment_label = "positive"
            elif sentiment_score < -0.1:
                sentiment_label = "negative"
            else:
                sentiment_label = "neutral"
            
            results.append({
                'bert_sentiment_label': sentiment_label,
                'bert_sentiment_score': round(sentiment_score, 4),
                'bert_positive_score': round(positive_score, 4),
                'bert_negative_score': round(negative_score, 4)
            })
    
    return results

# 主函数
def main():
    # 文件路径
    input_file = '清洗数据/enhanced_cleaned_data.csv'
    output_file = '清洗数据/bert_sentiment_analyzed_data.csv'
    
    print("正在读取增强后的数据...")
    # 读取增强后的数据
    df = pd.read_csv(input_file, usecols=['original_index', 'data_type', 'title', 'summary', 'cleaned_title', 'cleaned_summary', 'combined_text', 'date', 'category', 'source', 'scraped_time'])
    
    print(f"数据总量: {len(df)} 条")
    
    # 初始化BERT模型
    tokenizer, model, device = init_bert_model()
    
    # 获取要分析的文本列表
    texts = df['combined_text'].tolist()
    
    # 对每条新闻进行BERT情感分析
    print("\n正在进行BERT情感分析...")
    bert_results = batch_analyze_bert_sentiment(texts, tokenizer, model, device, batch_size=16)
    
    # 将BERT情感分析结果转换为DataFrame
    bert_results_df = pd.DataFrame(bert_results)
    
    # 将BERT情感分析结果合并到原数据中
    df_with_bert_sentiment = pd.concat([df, bert_results_df], axis=1)
    
    # 保存结果
    print("\n正在保存BERT情感分析结果...")
    df_with_bert_sentiment.to_csv(output_file, index=False, encoding='utf-8')
    
    print("✓ BERT情感分析完成！")
    print(f"✓ 结果已保存到 {output_file}")
    print(f"✓ 数据形状: {df_with_bert_sentiment.shape}")
    
    # 显示前5行结果
    print("\nBERT情感分析结果示例（前5行）:")
    print(df_with_bert_sentiment[['title', 'bert_sentiment_label', 'bert_sentiment_score', 'bert_positive_score', 'bert_negative_score']].head())
    
    # 显示情感分布
    print("\nBERT情感分布:")
    sentiment_distribution = df_with_bert_sentiment['bert_sentiment_label'].value_counts()
    print(sentiment_distribution)
    print("\nBERT情感分布占比:")
    print(df_with_bert_sentiment['bert_sentiment_label'].value_counts(normalize=True))

if __name__ == "__main__":
    main()