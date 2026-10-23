#!/usr/bin/env python3
"""
自适应学习引擎 - 基于历史数据优化爬虫策略
整合机器学习算法实现智能策略优化和性能预测
"""

import json
import logging
import time
import statistics
import random
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os

logger = logging.getLogger(__name__)

class AdaptiveLearningEngine:
    """自适应学习引擎 - 基于历史数据优化爬虫策略"""
    
    def __init__(self, config_file: str = None):
        # 学习配置
        self.learning_config = {
            'learning_window_size': 1000,           # 学习窗口大小
            'prediction_horizon': 10,               # 预测时间范围
            'model_retrain_interval': 100,          # 模型重训练间隔
            'feature_decay_factor': 0.95,          # 特征衰减因子
            'exploration_rate': 0.15,              # 探索率
            'confidence_threshold': 0.7,           # 置信度阈值
            'performance_thresholds': {
                'success_rate_low': 0.6,           # 低成功率阈值
                'success_rate_high': 0.9,          # 高成功率阈值
                'latency_critical': 500,           # 关键延迟阈值
                'latency_optimal': 200            # 最优延迟阈值
            }
        }
        
        # 特征工程配置
        self.feature_config = {
            'temporal_features': ['hour', 'day_of_week', 'is_weekend'],
            'performance_features': ['success_rate_5m', 'latency_5m', 'error_rate_5m'],
            'website_features': ['anti_crawler_level', 'response_time', 'stability_score'],
            'proxy_features': ['proxy_quality', 'geographic_fit', 'freshness_score']
        }
        
        # 数据存储
        self.historical_data = {
            'performance_records': deque(maxlen=self.learning_config['learning_window_size']),
            'strategy_decisions': deque(maxlen=self.learning_config['learning_window_size']),
            'website_profiles': {},
            'proxy_performance': {},
            'temporal_patterns': defaultdict(list)
        }
        
        # 机器学习模型
        self.models = {
            'success_rate_predictor': None,
            'latency_predictor': None,
            'strategy_optimizer': None
        }
        
        # 模型训练状态
        self.model_status = {
            'last_trained': None,
            'training_count': 0,
            'model_accuracy': {},
            'feature_importance': {}
        }
        
        # 配置持久化
        self.config_file = config_file
        self.model_dir = 'models'
        self._initialize_model_directory()
        self._load_config()
        
        logger.info("自适应学习引擎初始化完成")
    
    def _initialize_model_directory(self):
        """初始化模型目录"""
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)
    
    def _load_config(self):
        """加载配置文件"""
        if self.config_file and os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.learning_config.update(config.get('learning_config', {}))
                    self.feature_config.update(config.get('feature_config', {}))
                logger.info("学习配置加载成功")
            except Exception as e:
                logger.error(f"配置加载失败: {e}")
    
    def save_config(self):
        """保存配置到文件"""
        if self.config_file:
            try:
                config = {
                    'learning_config': self.learning_config,
                    'feature_config': self.feature_config,
                    'model_status': self.model_status
                }
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                logger.info("学习配置保存成功")
            except Exception as e:
                logger.error(f"配置保存失败: {e}")
    
    def record_performance(self, url: str, strategy: str, success: bool, 
                          latency: float, proxy_info: Dict = None):
        """记录性能数据"""
        timestamp = datetime.now()
        
        # 提取特征
        features = self._extract_features(url, strategy, timestamp, proxy_info)
        
        # 创建性能记录
        performance_record = {
            'timestamp': timestamp,
            'url': url,
            'strategy': strategy,
            'success': success,
            'latency': latency,
            'features': features,
            'proxy_info': proxy_info
        }
        
        # 添加到历史数据
        self.historical_data['performance_records'].append(performance_record)
        
        # 更新网站档案
        self._update_website_profile(url, success, latency, strategy)
        
        # 更新代理性能
        if proxy_info:
            self._update_proxy_performance(proxy_info, success, latency)
        
        # 更新时间模式
        self._update_temporal_patterns(timestamp, success, latency)
        
        # 检查是否需要重新训练模型
        if len(self.historical_data['performance_records']) % self.learning_config['model_retrain_interval'] == 0:
            self._train_models()
    
    def _extract_features(self, url: str, strategy: str, timestamp: datetime, 
                         proxy_info: Dict = None) -> Dict[str, Any]:
        """提取特征向量"""
        features = {}
        
        # 时间特征
        features['hour'] = timestamp.hour
        features['day_of_week'] = timestamp.weekday()
        features['is_weekend'] = 1 if timestamp.weekday() >= 5 else 0
        
        # 性能特征（最近5分钟）
        recent_performance = self._get_recent_performance(5)  # 5分钟
        features.update(recent_performance)
        
        # 网站特征
        website_features = self._get_website_features(url)
        features.update(website_features)
        
        # 代理特征
        if proxy_info:
            proxy_features = self._get_proxy_features(proxy_info)
            features.update(proxy_features)
        
        # 策略特征
        strategy_features = self._get_strategy_features(strategy)
        features.update(strategy_features)
        
        return features
    
    def _get_recent_performance(self, minutes: int) -> Dict[str, float]:
        """获取最近性能数据"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        recent_records = [
            record for record in self.historical_data['performance_records']
            if record['timestamp'] >= cutoff_time
        ]
        
        if not recent_records:
            return {
                'success_rate_5m': 0.8,  # 默认值
                'latency_5m': 300.0,
                'error_rate_5m': 0.2
            }
        
        success_count = sum(1 for record in recent_records if record['success'])
        total_count = len(recent_records)
        
        success_rate = success_count / total_count if total_count > 0 else 0.8
        avg_latency = statistics.mean([r['latency'] for r in recent_records]) if recent_records else 300.0
        
        return {
            'success_rate_5m': success_rate,
            'latency_5m': avg_latency,
            'error_rate_5m': 1 - success_rate
        }
    
    def _get_website_features(self, url: str) -> Dict[str, float]:
        """获取网站特征"""
        if url not in self.historical_data['website_profiles']:
            return {
                'anti_crawler_level': 0.3,  # 默认反爬虫级别
                'response_time': 300.0,     # 默认响应时间
                'stability_score': 0.8      # 默认稳定性分数
            }
        
        profile = self.historical_data['website_profiles'][url]
        
        return {
            'anti_crawler_level': profile.get('anti_crawler_level', 0.3),
            'response_time': profile.get('avg_response_time', 300.0),
            'stability_score': profile.get('stability_score', 0.8)
        }
    
    def _get_proxy_features(self, proxy_info: Dict) -> Dict[str, float]:
        """获取代理特征"""
        proxy_key = f"{proxy_info.get('group', 'unknown')}_{proxy_info.get('proxy', 'unknown')}"
        
        if proxy_key not in self.historical_data['proxy_performance']:
            return {
                'proxy_quality': 0.7,
                'geographic_fit': 0.8,
                'freshness_score': 1.0
            }
        
        performance = self.historical_data['proxy_performance'][proxy_key]
        
        return {
            'proxy_quality': performance.get('quality_score', 0.7),
            'geographic_fit': performance.get('geographic_fit', 0.8),
            'freshness_score': performance.get('freshness_score', 1.0)
        }
    
    def _get_strategy_features(self, strategy: str) -> Dict[str, float]:
        """获取策略特征"""
        # 策略类型编码
        strategy_encoding = {
            'aggressive': [1, 0, 0, 0],
            'balanced': [0, 1, 0, 0],
            'conservative': [0, 0, 1, 0],
            'ultra_conservative': [0, 0, 0, 1]
        }
        
        encoding = strategy_encoding.get(strategy, [0, 0, 0, 0])
        
        return {
            'strategy_aggressive': encoding[0],
            'strategy_balanced': encoding[1],
            'strategy_conservative': encoding[2],
            'strategy_ultra_conservative': encoding[3]
        }
    
    def _update_website_profile(self, url: str, success: bool, latency: float, strategy: str):
        """更新网站档案"""
        if url not in self.historical_data['website_profiles']:
            self.historical_data['website_profiles'][url] = {
                'total_requests': 0,
                'successful_requests': 0,
                'response_times': [],
                'strategies_used': defaultdict(int),
                'last_updated': datetime.now()
            }
        
        profile = self.historical_data['website_profiles'][url]
        profile['total_requests'] += 1
        
        if success:
            profile['successful_requests'] += 1
            profile['response_times'].append(latency)
            
            # 限制响应时间记录数量
            if len(profile['response_times']) > 100:
                profile['response_times'].pop(0)
        
        profile['strategies_used'][strategy] += 1
        profile['last_updated'] = datetime.now()
        
        # 计算反爬虫级别（基于失败率）
        failure_rate = 1 - (profile['successful_requests'] / profile['total_requests'])
        profile['anti_crawler_level'] = min(1.0, failure_rate * 2)  # 标准化到0-1
        
        # 计算平均响应时间
        if profile['response_times']:
            profile['avg_response_time'] = statistics.mean(profile['response_times'])
        else:
            profile['avg_response_time'] = 300.0
        
        # 计算稳定性分数
        if len(profile['response_times']) >= 5:
            std_dev = statistics.stdev(profile['response_times'])
            profile['stability_score'] = max(0.1, 1.0 - (std_dev / profile['avg_response_time']))
        else:
            profile['stability_score'] = 0.8
    
    def _update_proxy_performance(self, proxy_info: Dict, success: bool, latency: float):
        """更新代理性能"""
        proxy_key = f"{proxy_info.get('group', 'unknown')}_{proxy_info.get('proxy', 'unknown')}"
        
        if proxy_key not in self.historical_data['proxy_performance']:
            self.historical_data['proxy_performance'][proxy_key] = {
                'total_requests': 0,
                'successful_requests': 0,
                'latencies': [],
                'last_used': datetime.now(),
                'quality_score': 0.7
            }
        
        performance = self.historical_data['proxy_performance'][proxy_key]
        performance['total_requests'] += 1
        
        if success:
            performance['successful_requests'] += 1
            performance['latencies'].append(latency)
            
            # 限制延迟记录数量
            if len(performance['latencies']) > 50:
                performance['latencies'].pop(0)
        
        performance['last_used'] = datetime.now()
        
        # 计算质量分数
        success_rate = performance['successful_requests'] / performance['total_requests']
        
        if performance['latencies']:
            avg_latency = statistics.mean(performance['latencies'])
            latency_score = max(0.1, 1.0 - (avg_latency / 1000))  # 标准化
        else:
            latency_score = 0.7
        
        # 新鲜度分数
        time_since_used = (datetime.now() - performance['last_used']).total_seconds()
        freshness_score = max(0.1, 1.0 - (time_since_used / 3600))  # 1小时内为新鲜
        
        # 综合质量分数
        performance['quality_score'] = (success_rate * 0.6 + latency_score * 0.3 + freshness_score * 0.1)
        performance['geographic_fit'] = proxy_info.get('score', 0.8)  # 从代理信息获取
        performance['freshness_score'] = freshness_score
    
    def _update_temporal_patterns(self, timestamp: datetime, success: bool, latency: float):
        """更新时间模式"""
        hour_key = timestamp.hour
        
        if success:
            self.historical_data['temporal_patterns'][f'hour_{hour_key}_success'].append(1)
            self.historical_data['temporal_patterns'][f'hour_{hour_key}_latency'].append(latency)
        else:
            self.historical_data['temporal_patterns'][f'hour_{hour_key}_success'].append(0)
    
    def _train_models(self):
        """训练机器学习模型"""
        if len(self.historical_data['performance_records']) < 50:
            logger.info("数据不足，跳过模型训练")
            return
        
        try:
            # 准备训练数据
            X, y_success, y_latency = self._prepare_training_data()
            
            if len(X) < 20:
                logger.info("训练数据不足，跳过模型训练")
                return
            
            # 训练成功率预测模型
            self.models['success_rate_predictor'] = RandomForestRegressor(n_estimators=50, random_state=42)
            self.models['success_rate_predictor'].fit(X, y_success)
            
            # 训练延迟预测模型
            self.models['latency_predictor'] = RandomForestRegressor(n_estimators=50, random_state=42)
            self.models['latency_predictor'].fit(X, y_latency)
            
            # 更新模型状态
            self.model_status['last_trained'] = datetime.now()
            self.model_status['training_count'] += 1
            
            # 计算模型准确度
            self._evaluate_model_performance(X, y_success, y_latency)
            
            # 保存模型
            self._save_models()
            
            logger.info(f"模型训练完成，训练次数: {self.model_status['training_count']}")
            
        except Exception as e:
            logger.error(f"模型训练失败: {e}")
    
    def _prepare_training_data(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """准备训练数据"""
        X = []
        y_success = []
        y_latency = []
        
        for record in self.historical_data['performance_records']:
            # 提取特征向量
            features = list(record['features'].values())
            X.append(features)
            
            # 目标变量
            y_success.append(1.0 if record['success'] else 0.0)
            y_latency.append(record['latency'])
        
        return np.array(X), np.array(y_success), np.array(y_latency)
    
    def _evaluate_model_performance(self, X: np.ndarray, y_success: np.ndarray, y_latency: np.ndarray):
        """评估模型性能"""
        if len(X) < 10:
            return
        
        # 使用交叉验证评估（简化版）
        split_point = int(len(X) * 0.8)
        X_train, X_test = X[:split_point], X[split_point:]
        y_success_train, y_success_test = y_success[:split_point], y_success[split_point:]
        y_latency_train, y_latency_test = y_latency[:split_point], y_latency[split_point:]
        
        # 训练临时模型进行评估
        success_model = RandomForestRegressor(n_estimators=30, random_state=42)
        success_model.fit(X_train, y_success_train)
        success_predictions = success_model.predict(X_test)
        
        latency_model = RandomForestRegressor(n_estimators=30, random_state=42)
        latency_model.fit(X_train, y_latency_train)
        latency_predictions = latency_model.predict(X_test)
        
        # 计算准确度
        success_accuracy = np.mean(np.abs(success_predictions - y_success_test) < 0.3)
        latency_accuracy = np.mean(np.abs(latency_predictions - y_latency_test) < 50)
        
        self.model_status['model_accuracy'] = {
            'success_rate': round(success_accuracy, 3),
            'latency': round(latency_accuracy, 3)
        }
        
        # 计算特征重要性
        if hasattr(success_model, 'feature_importances_'):
            feature_names = list(self.historical_data['performance_records'][0]['features'].keys())
            importances = success_model.feature_importances_
            self.model_status['feature_importance'] = dict(zip(feature_names, importances))
    
    def _save_models(self):
        """保存模型到文件"""
        try:
            for model_name, model in self.models.items():
                if model is not None:
                    model_path = os.path.join(self.model_dir, f"{model_name}.joblib")
                    joblib.dump(model, model_path)
            
            # 保存模型状态
            status_path = os.path.join(self.model_dir, "model_status.json")
            with open(status_path, 'w', encoding='utf-8') as f:
                json.dump(self.model_status, f, indent=2, default=str, ensure_ascii=False)
            
            logger.info("模型保存成功")
        except Exception as e:
            logger.error(f"模型保存失败: {e}")
    
    def load_models(self):
        """从文件加载模型"""
        try:
            for model_name in self.models.keys():
                model_path = os.path.join(self.model_dir, f"{model_name}.joblib")
                if os.path.exists(model_path):
                    self.models[model_name] = joblib.load(model_path)
            
            # 加载模型状态
            status_path = os.path.join(self.model_dir, "model_status.json")
            if os.path.exists(status_path):
                with open(status_path, 'r', encoding='utf-8') as f:
                    self.model_status = json.load(f)
            
            logger.info("模型加载成功")
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
    
    def predict_performance(self, url: str, strategy: str, proxy_info: Dict = None) -> Dict[str, Any]:
        """预测性能"""
        if self.models['success_rate_predictor'] is None:
            return self._get_default_prediction()
        
        try:
            # 提取特征
            features = self._extract_features(url, strategy, datetime.now(), proxy_info)
            feature_vector = np.array([list(features.values())])
            
            # 预测
            success_prob = self.models['success_rate_predictor'].predict(feature_vector)[0]
            predicted_latency = self.models['latency_predictor'].predict(feature_vector)[0]
            
            # 计算置信度
            confidence = self._calculate_prediction_confidence(feature_vector)
            
            return {
                'success_probability': max(0.0, min(1.0, success_prob)),
                'predicted_latency': max(0.0, predicted_latency),
                'confidence': confidence,
                'recommendation': self._generate_recommendation(success_prob, predicted_latency),
                'features_used': list(features.keys())
            }
            
        except Exception as e:
            logger.error(f"性能预测失败: {e}")
            return self._get_default_prediction()
    
    def _calculate_prediction_confidence(self, feature_vector: np.ndarray) -> float:
        """计算预测置信度"""
        # 基于数据覆盖度和模型准确度计算置信度
        data_coverage = min(1.0, len(self.historical_data['performance_records']) / 100)
        model_accuracy = self.model_status.get('model_accuracy', {}).get('success_rate', 0.7)
        
        return min(1.0, data_coverage * model_accuracy)
    
    def _get_default_prediction(self) -> Dict[str, Any]:
        """获取默认预测值"""
        return {
            'success_probability': 0.7,
            'predicted_latency': 300.0,
            'confidence': 0.5,
            'recommendation': '使用平衡策略开始',
            'features_used': ['default']
        }
    
    def _generate_recommendation(self, success_prob: float, latency: float) -> str:
        """生成策略推荐"""
        thresholds = self.learning_config['performance_thresholds']
        
        if success_prob < thresholds['success_rate_low']:
            if latency > thresholds['latency_critical']:
                return "切换到保守策略，优化代理选择"
            else:
                return "增加重试次数，优化请求间隔"
        elif success_prob > thresholds['success_rate_high'] and latency < thresholds['latency_optimal']:
            return "可以尝试更激进的策略以提高效率"
        else:
            return "保持当前策略，继续监控性能"
    
    def optimize_strategy(self, url: str, current_strategy: str, 
                         proxy_info: Dict = None) -> Dict[str, Any]:
        """优化爬虫策略"""
        # 可用策略
        available_strategies = ['aggressive', 'balanced', 'conservative', 'ultra_conservative']
        
        # 探索新策略
        if random.random() < self.learning_config['exploration_rate']:
            exploration_strategy = random.choice(available_strategies)
            prediction = self.predict_performance(url, exploration_strategy, proxy_info)
            
            return {
                'recommended_strategy': exploration_strategy,
                'reason': '探索新策略',
                'prediction': prediction,
                'exploration': True
            }
        
        # 利用已知最佳策略
        best_strategy = current_strategy
        best_score = -1
        
        for strategy in available_strategies:
            prediction = self.predict_performance(url, strategy, proxy_info)
            
            # 计算策略分数
            strategy_score = self._calculate_strategy_score(prediction)
            
            if strategy_score > best_score:
                best_score = strategy_score
                best_strategy = strategy
        
        return {
            'recommended_strategy': best_strategy,
            'reason': '基于性能预测优化',
            'prediction': self.predict_performance(url, best_strategy, proxy_info),
            'exploration': False
        }
    
    def _calculate_strategy_score(self, prediction: Dict[str, Any]) -> float:
        """计算策略分数"""
        success_prob = prediction['success_probability']
        latency = prediction['predicted_latency']
        confidence = prediction['confidence']
        
        # 成功率权重最高
        score = success_prob * 0.6
        
        # 延迟惩罚
        latency_penalty = max(0, (latency - 200) / 800)  # 标准化惩罚
        score -= latency_penalty * 0.3
        
        # 置信度加成
        score += confidence * 0.1
        
        return max(0.0, score)
    
    def get_learning_report(self) -> Dict[str, Any]:
        """获取学习报告"""
        total_records = len(self.historical_data['performance_records'])
        
        if total_records == 0:
            return {
                'status': 'no_data',
                'message': '暂无学习数据'
            }
        
        # 计算总体性能
        success_count = sum(1 for record in self.historical_data['performance_records'] if record['success'])
        overall_success_rate = success_count / total_records if total_records > 0 else 0
        
        avg_latency = statistics.mean([r['latency'] for r in self.historical_data['performance_records']]) if total_records > 0 else 0
        
        # 策略使用统计
        strategy_stats = defaultdict(int)
        for record in self.historical_data['performance_records']:
            strategy_stats[record['strategy']] += 1
        
        return {
            'status': 'success',
            'summary': {
                'total_records': total_records,
                'overall_success_rate': round(overall_success_rate, 3),
                'average_latency': round(avg_latency, 2),
                'websites_tracked': len(self.historical_data['website_profiles']),
                'proxies_tracked': len(self.historical_data['proxy_performance']),
                'model_training_count': self.model_status.get('training_count', 0),
                'last_trained': self.model_status.get('last_trained')
            },
            'strategy_usage': dict(strategy_stats),
            'model_performance': self.model_status.get('model_accuracy', {}),
            'feature_importance': self.model_status.get('feature_importance', {}),
            'recommendations': self._generate_learning_recommendations()
        }
    
    def _generate_learning_recommendations(self) -> List[str]:
        """生成学习建议"""
        recommendations = []
        
        total_records = len(self.historical_data['performance_records'])
        
        if total_records < 50:
            recommendations.append("数据量不足，建议继续收集性能数据")
        
        if self.model_status.get('training_count', 0) == 0:
            recommendations.append("尚未进行模型训练，建议收集更多数据后训练模型")
        
        # 检查模型准确度
        model_accuracy = self.model_status.get('model_accuracy', {})
        if model_accuracy.get('success_rate', 0) < 0.7:
            recommendations.append("模型准确度较低，建议重新训练或收集更多样化的数据")
        
        # 检查特征重要性
        feature_importance = self.model_status.get('feature_importance', {})
        if feature_importance:
            top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:3]
            recommendations.append(f"最重要的特征: {', '.join([f[0] for f in top_features])}")
        
        return recommendations

# 使用示例
def test_adaptive_learning_engine():
    """测试自适应学习引擎"""
    engine = AdaptiveLearningEngine()
    
    # 模拟性能数据记录
    test_urls = [
        "https://www.news24.com",
        "https://www.nation.co.ke", 
        "https://www.punchng.com"
    ]
    
    strategies = ['aggressive', 'balanced', 'conservative']
    
    print("开始模拟性能数据记录...")
    
    for i in range(50):
        url = random.choice(test_urls)
        strategy = random.choice(strategies)
        success = random.random() > 0.3  # 70%成功率
        latency = random.uniform(100, 800)
        
        proxy_info = {
            'proxy': f"proxy{i%3}.example.com",
            'group': random.choice(['south-africa', 'kenya', 'nigeria']),
            'score': random.uniform(0.5, 0.9)
        }
        
        engine.record_performance(url, strategy, success, latency, proxy_info)
    
    print("性能数据记录完成")
    
    # 获取学习报告
    report = engine.get_learning_report()
    print("\n学习报告:")
    print(json.dumps(report, indent=2, default=str, ensure_ascii=False))
    
    # 测试策略优化
    test_url = "https://www.news24.com"
    current_strategy = "balanced"
    
    optimization = engine.optimize_strategy(test_url, current_strategy)
    print(f"\n策略优化建议:")
    print(json.dumps(optimization, indent=2, default=str, ensure_ascii=False))

if __name__ == "__main__":
    test_adaptive_learning_engine()