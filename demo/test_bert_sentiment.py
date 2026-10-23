import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# 初始化BERT模型和分词器
def init_bert_model():
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
def analyze_bert_sentiment(text, tokenizer, model, device):
    if not text:
        return {
            'label': 'neutral',
            'score': 0.0,
            'positive': 0.0,
            'negative': 0.0
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
        'label': sentiment_label,
        'score': round(sentiment_score, 4),
        'positive': round(positive_score, 4),
        'negative': round(negative_score, 4)
    }

# 主测试函数
def main():
    # 测试文本
    test_texts = [
        "China halts ban on export to US of some dual-use metals, which is good for trade relations.",
        "Trump hails Central Asia's 'unbelievable potential' at summit.",
        "China says will 'fight to the end' in US trade war.",
        "Early-morning earthquake injures 11 in northwest China's Gansu province.",
        "The meeting between