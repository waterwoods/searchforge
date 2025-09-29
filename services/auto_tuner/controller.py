import os, time
from prometheus_client import Counter, Gauge, start_http_server
ACTIONS=Counter("auto_tuner_actions_total","tuner actions",["reason","param"])
TOPK=Gauge("auto_tuner_topk","current topk")
BATCH=Gauge("auto_tuner_batch_size","current batch")
if __name__=="__main__":
    start_http_server(8085)
    TOPK.set(100); BATCH.set(10)
    while True:
        # placeholder: fake decision every minute
        ACTIONS.labels("warmup","topk").inc()
        time.sleep(60)
