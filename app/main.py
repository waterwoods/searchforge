from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health(): return {"ok": True}

@app.get("/")
def hello(): return {"msg": "hello from WSL docker"}


