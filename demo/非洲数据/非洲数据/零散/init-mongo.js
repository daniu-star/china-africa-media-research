// MongoDB初始化脚本
db = db.getSiblingDB('crawler_db');

// 创建用户
if (db.getUser('crawler_user') == null) {
    db.createUser({
        user: 'crawler_user',
        pwd: 'crawler_password',
        roles: [
            {
                role: 'readWrite',
                db: 'crawler_db'
            }
        ]
    });
}

// 创建集合和索引
db.createCollection('tasks');
db.createCollection('results');
db.createCollection('articles');
db.createCollection('worker_status');

// 创建索引
db.tasks.createIndex({ "task_id": 1 }, { unique: true });
db.tasks.createIndex({ "status": 1 });
db.tasks.createIndex({ "keyword": 1, "year": 1 });

db.results.createIndex({ "task_id": 1 }, { unique: true });
db.results.createIndex({ "keyword": 1, "year": 1 });
db.results.createIndex({ "worker_id": 1 });

db.articles.createIndex({ "article_id": 1 }, { unique: true });
db.articles.createIndex({ "keyword": 1, "year": 1 });
db.articles.createIndex({ "source": 1 });
db.articles.createIndex({ "crawled_at": 1 });

db.worker_status.createIndex({ "worker_id": 1 }, { unique: true });
db.worker_status.createIndex({ "last_heartbeat": 1 });

print('MongoDB初始化完成');