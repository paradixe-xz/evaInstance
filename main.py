from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hola"}

# Para correr el servidor usa:
# uvicorn main:app --host 0.0.0.0 --port 4000