from fastapi import FastAPI

app = FastAPI()

@app.get("/{id}")
def root(id:int):
    return {"id":id}