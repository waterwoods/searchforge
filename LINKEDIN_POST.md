# 🚀 RAG系统优化：3个数字背后的故事

刚完成一轮RAG检索系统优化，通过Chunking策略、MMR多样性和HNSW参数三条线108次实验，取得了突破性成果：

📉 **P95延迟 -55%**（1250ms → 560ms）- 不是牺牲质量换速度  
📈 **Recall@10 +12%**（87.5% → 98.5%）- 延迟优化反而提升质量  
💰 **计算资源 -50%**（efSearch: 64→32）- 核心发现：32已足够，无需更高

**关键洞察**: efSearch=32 + warmup预热 + 低并发(4) = 最优组合。习惯性的"更高参数=更好性能"被数据打脸。

我们将3档策略（Fast/Balanced/Quality）固化为REST API，生产可一键切换。完整技术细节见图👇

![质量-延迟Pareto前沿](reports/chunk_charts/pareto_quality_latency.png)

#RAG #InformationRetrieval #MLOps #VectorSearch #HNSW #PerformanceOptimization #DataDriven

