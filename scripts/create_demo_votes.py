#!/usr/bin/env python3
"""
创建演示投票数据，让Judge Report页面能显示内容
"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path

def create_demo_votes():
    """为mined batch创建演示投票数据"""
    reports_dir = Path(__file__).parent.parent / "reports"
    votes_file = reports_dir / "judge_votes_mined.jsonl"
    
    # 创建一些演示投票数据
    demo_votes = [
        {"batch_id": "mined", "qid": 2, "pick": "on", "reason": "ON版本结果更准确", "timestamp": time.time(), "ts_iso": datetime.now(timezone.utc).isoformat()},
        {"batch_id": "mined", "qid": 3, "pick": "same", "reason": "两个版本结果相似", "timestamp": time.time(), "ts_iso": datetime.now(timezone.utc).isoformat()},
        {"batch_id": "mined", "qid": 5, "pick": "on", "reason": "ON版本排序更好", "timestamp": time.time(), "ts_iso": datetime.now(timezone.utc).isoformat()},
        {"batch_id": "mined", "qid": 6, "pick": "off", "reason": "OFF版本更简洁", "timestamp": time.time(), "ts_iso": datetime.now(timezone.utc).isoformat()},
        {"batch_id": "mined", "qid": 8, "pick": "on", "reason": "ON版本信息更全面", "timestamp": time.time(), "ts_iso": datetime.now(timezone.utc).isoformat()},
        {"batch_id": "mined", "qid": 9, "pick": "same", "reason": "无明显差异", "timestamp": time.time(), "ts_iso": datetime.now(timezone.utc).isoformat()},
        {"batch_id": "mined", "qid": 11, "pick": "on", "reason": "ON版本相关性更高", "timestamp": time.time(), "ts_iso": datetime.now(timezone.utc).isoformat()},
        {"batch_id": "mined", "qid": 13, "pick": "off", "reason": "OFF版本回答更直接", "timestamp": time.time(), "ts_iso": datetime.now(timezone.utc).isoformat()},
        {"batch_id": "mined", "qid": 14, "pick": "on", "reason": "ON版本解释更清楚", "timestamp": time.time(), "ts_iso": datetime.now(timezone.utc).isoformat()},
        {"batch_id": "mined", "qid": 16, "pick": "same", "reason": "两个版本都很好", "timestamp": time.time(), "ts_iso": datetime.now(timezone.utc).isoformat()},
    ]
    
    # 写入投票文件
    with open(votes_file, 'w') as f:
        for vote in demo_votes:
            f.write(json.dumps(vote, ensure_ascii=False) + '\n')
    
    print(f"✅ 创建了 {len(demo_votes)} 条演示投票数据")
    print(f"   文件: {votes_file}")
    print(f"   统计: ON更好={sum(1 for v in demo_votes if v['pick']=='on')}, "
          f"OFF更好={sum(1 for v in demo_votes if v['pick']=='off')}, "
          f"相当={sum(1 for v in demo_votes if v['pick']=='same')}")
    
    return len(demo_votes)

if __name__ == "__main__":
    create_demo_votes()
