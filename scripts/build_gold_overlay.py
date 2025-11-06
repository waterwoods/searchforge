import argparse, json, random, time
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct
from sentence_transformers import SentenceTransformer
from pathlib import Path

QUERIES = [
  "fast usb c cable charging",
  "wireless charger",
  "usb c hub",
  # 你可再加 10–30 条
]

# 新增 30 个查询的多样化表达
SMALL_QUERY_SET = [
    # USB-C 充电相关
    "usb c fast charging cable",
    "type c charger cable",
    "usb c power cord",
    "quick charge usb c",
    "pd usb c cable",
    "usb c charging cord",
    "fast charge type c",
    "usb c cable 100w",
    "usb c to usb c cable",
    "usb c charging wire",
    
    # 无线充电相关
    "wireless phone charger",
    "qi wireless charger",
    "wireless charging pad",
    "magsafe wireless charger",
    "wireless charging stand",
    "wireless charging dock",
    "portable wireless charger",
    "wireless charging mat",
    "wireless phone stand",
    "wireless charger 20w",
    
    # USB-C Hub 相关
    "usb c hub adapter",
    "usb c docking station",
    "type c hub multiport",
    "usb c splitter hub",
    "usb c hub hdmi",
    "usb c hub ethernet",
    "usb c hub sd card",
    "usb c hub vga",
    "usb c hub usb a",
    "usb c hub power delivery"
]

# 每个 query 生成 6~8 条"相关"片段，混入同义词/改写
TEMPLATES = {
  "fast usb c cable charging": [
    "High-speed USB-C cable supports {watt}W fast charging for phones and laptops.",
    "USB-C fast charge cable with {amp}A current and durable braided design.",
    "PD {watt}W USB Type-C charging cable compatible with iPhone/Android.",
    "USB-C quick charge cable for {device}, reinforced connector, low resistance.",
    "Fast charging type-c cord with E-marker chip, stable power delivery.",
    "USB-C to USB-C cable, {length}m, supports PD3.0 and QC4 fast charging.",
  ],
  "wireless charger": [
    "Qi-certified wireless charger pad for smartphones, {watt}W fast charge.",
    "MagSafe compatible wireless charging stand for {device}, silent cooling.",
    "Slim wireless charging mat with overheat protection, USB-C input.",
    "3-in-1 wireless charging dock for phone, earbuds and watch.",
    "Aluminum wireless charger with foreign object detection and LED indicator.",
    "Foldable travel wireless charger, supports {watt}W EPP fast mode."
  ],
  "usb c hub": [
    "USB-C hub with HDMI 4K, 2x USB 3.0 and PD {watt}W passthrough.",
    "7-in-1 type-C adapter: SD/TF reader, USB-A ports, Gigabit Ethernet.",
    "USB-C docking station for {device}, dual display, 100W charging.",
    "Compact USB-C splitter with data ports and power delivery.",
    "Aluminum USB-C multiport hub, heat dissipation, plug and play.",
    "USB-C hub with VGA/HDMI, Audio jack, PD pass-through {watt}W."
  ]
}

# 为新增查询添加模板
for query in SMALL_QUERY_SET:
    if "usb c" in query.lower() and "cable" in query.lower():
        TEMPLATES[query] = [
            "USB-C cable for fast charging, supports {watt}W power delivery.",
            "Type-C charging cable with {amp}A current, durable design.",
            "USB-C power cord for {device}, quick charge compatible.",
            "Fast charge USB-C cable, {length}m length, braided jacket.",
            "USB-C charging wire with E-marker, supports PD charging.",
            "USB-C to USB-C cable, {watt}W power delivery, reinforced connector."
        ]
    elif "wireless" in query.lower():
        TEMPLATES[query] = [
            "Wireless charger for {device}, {watt}W fast charging support.",
            "Qi wireless charging pad, compatible with most smartphones.",
            "Wireless charging stand with LED indicator, silent operation.",
            "Portable wireless charger, slim design, overheat protection.",
            "Wireless charging dock for phone and accessories.",
            "Wireless charging mat with anti-slip surface, USB-C input."
        ]
    elif "hub" in query.lower():
        TEMPLATES[query] = [
            "USB-C hub adapter with multiple ports, {watt}W power delivery.",
            "Type-C docking station for {device}, dual display support.",
            "USB-C multiport hub, HDMI, Ethernet, USB-A ports.",
            "USB-C hub with SD card reader, compact aluminum design.",
            "USB-C splitter hub, plug and play, heat dissipation.",
            "USB-C hub with VGA/HDMI output, power pass-through."
        ]
    else:
        # 默认模板
        TEMPLATES[query] = [
            "USB-C device for {device}, {watt}W power delivery.",
            "Type-C accessory with {amp}A current, durable design.",
            "USB-C product for {device}, quick charge compatible.",
            "Fast charge USB-C device, {length}m cable, braided jacket.",
            "USB-C accessory with E-marker, supports PD charging.",
            "USB-C device, {watt}W power delivery, reinforced connector."
        ]

# 难负例模板（词面近似但语义偏离）
HARD_NEGATIVE_TEMPLATES = [
    "USB-A cable for charging, {watt}W power delivery, micro USB connector.",
    "Lightning cable for iPhone, {length}m length, MFi certified.",
    "HDMI cable {length}m, 4K support, gold-plated connectors.",
    "Ethernet cable Cat6, {length}m, shielded twisted pair.",
    "Audio cable 3.5mm jack, {length}m, oxygen-free copper.",
    "VGA cable for monitor, {length}m, HD15 connector.",
    "Power adapter {watt}W, AC to DC converter, multiple plugs.",
    "Bluetooth speaker with {watt}W output, wireless connectivity.",
    "USB flash drive {size}GB, USB 3.0, plug and play.",
    "WiFi router with {watt}W power, dual band, gigabit ports."
]

def synth_text(q, is_negative=False):
    import random
    watt = random.choice([15, 18, 20, 30, 45, 60, 65, 100])
    amp = random.choice([2.4, 3.0, 5.0])
    length = random.choice([0.5, 1, 1.5, 2])
    device = random.choice(["iPhone", "Android", "laptop", "tablet", "Pixel"])
    size = random.choice([32, 64, 128, 256])
    
    if is_negative:
        tpl = random.choice(HARD_NEGATIVE_TEMPLATES)
        return tpl.format(watt=watt, amp=amp, length=length, device=device, size=size)
    else:
        tpl = random.choice(TEMPLATES[q])
        return tpl.format(watt=watt, amp=amp, length=length, device=device, size=size)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--collection", default="demo_5k")
    ap.add_argument("--per_query", type=int, default=8)
    ap.add_argument("--out", default="data/goldset.jsonl")
    args = ap.parse_args()

    Path("data").mkdir(exist_ok=True, parents=True)
    client = QdrantClient(url="http://localhost:6333")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    # 读取现有 goldset（如果存在）
    existing_gold = []
    existing_ids = set()
    if Path(args.out).exists():
        with open(args.out, "r") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    existing_gold.append(r)
                    existing_ids.update(r["relevant_ids"])

    gold = existing_gold.copy()  # 保留现有数据
    points = []
    ts = int(time.time())

    # 处理原有查询
    for qi, q in enumerate(QUERIES):
        if args.per_query > 0:  # 只有当 per_query > 0 时才生成
            ids = []
            for j in range(args.per_query):
                text = synth_text(q)
                vec = model.encode(text).tolist()
                pid = int(f"9{qi:02d}{j:02d}{ts%100}")  # 避免与现有ID撞车
                points.append(PointStruct(id=pid, vector=vec, payload={
                    "text": text, "category": "gold", "query_hint": q, "gold": True
                }))
                ids.append(pid)
            gold.append({"query": q, "relevant_ids": ids})

    # 处理新增的 30 个查询
    for qi, q in enumerate(SMALL_QUERY_SET):
        ids = []
        
        # 生成 10 个正例
        for j in range(10):
            text = synth_text(q, is_negative=False)
            vec = model.encode(text).tolist()
            # 使用不同的ID前缀避免冲突
            pid = int(f"8{qi:02d}{j:02d}{ts%100}")
            points.append(PointStruct(id=pid, vector=vec, payload={
                "text": text, "category": "gold", "query_hint": q, "gold": True
            }))
            ids.append(pid)
        
        # 生成 10 个难负例
        for j in range(10, 20):
            text = synth_text(q, is_negative=True)
            vec = model.encode(text).tolist()
            pid = int(f"7{qi:02d}{j:02d}{ts%100}")
            points.append(PointStruct(id=pid, vector=vec, payload={
                "text": text, "category": "hard_negative", "query_hint": q, "gold": False
            }))
            ids.append(pid)
        
        gold.append({"query": q, "relevant_ids": ids})

    # 批量写入到 Qdrant
    if points:
        client.upsert(collection_name=args.collection, points=points)
        print(f"Inserted {len(points)} docs into {args.collection}")
    
    # 写 goldset（append 模式，保留现有数据）
    with open(args.out, "w") as f:
        for r in gold:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    
    print(f"Goldset written to {args.out} with {len(gold)} queries total")

if __name__ == "__main__":
    main()
