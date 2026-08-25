from fastapi import FastAPI

app = FastAPI(title="Mausam Personalized Homepage API - Milestone 0 Placeholder")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Backend is running"}
