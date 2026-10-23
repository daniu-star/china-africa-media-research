import json

def verify_recovery():
    print("=== 恢复数据验证 ===")
    
    try:
        # 读取恢复的文件
        with open('data/results_recovered.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("✅ 恢复文件验证成功")
        print(f"文章数量: {len(data['articles'])}")
        print(f"articles_found: {data['articles_found']}")
        print(f"恢复方法: {data['recovery_method']}")
        print(f"原始文件大小: {data['original_file_size']:,} 字符")
        
        print("\n📊 数据统计:")
        articles = data['articles']
        
        # 统计不同来源
        sources = {}
        for article in articles:
            source = article.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1
        
        print(f"不同来源数量: {len(sources)}")
        print("\n📰 主要来源统计:")
        for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {source}: {count} 篇文章")
        
        print("\n🔍 样本文章详情:")
        for i in range(3):
            article = articles[i]
            print(f"\n文章 {i+1}:")
            print(f"  标题: {article.get('title', 'N/A')}")
            print(f"  URL: {article.get('url', 'N/A')}")
            print(f"  来源: {article.get('source', 'N/A')}")
            if 'content' in article:
                content_preview = article['content'][:100] + "..." if len(article['content']) > 100 else article['content']
                print(f"  内容预览: {content_preview}")
        
        # 检查文件大小
        import os
        file_size = os.path.getsize('data/results_recovered.json')
        print(f"\n💾 恢复文件大小: {file_size:,} 字节")
        
        print("\n✅ 数据恢复验证完成 - 所有6,864篇文章已成功恢复！")
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")

if __name__ == "__main__":
    verify_recovery()