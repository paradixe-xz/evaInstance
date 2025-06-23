from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import subprocess

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello"}

class CreateRepresentativeRequest(BaseModel):
    model_name: str
    from_model: str
    temperature: float
    num_ctx: int
    system_prompt: str

@app.post("/createRepresentative")
def create_representative(req: CreateRepresentativeRequest):
    models_dir = "models"
    os.makedirs(models_dir, exist_ok=True)
    modelfile_path = os.path.join(models_dir, f"{req.model_name}.Modelfile")
    try:
        with open(modelfile_path, "w") as f:
            f.write(f"FROM {req.from_model}\n\n")
            f.write(f"PARAMETER temperature {req.temperature}\n")
            f.write(f"PARAMETER num_ctx {req.num_ctx}\n\n")
            f.write(f'SYSTEM """\n{req.system_prompt}\n"""\n')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating Modelfile: {e}")

    # Run ollama create command
    try:
        result = subprocess.run(
            ["ollama", "create", req.model_name, "-f", modelfile_path],
            capture_output=True, text=True, check=True
        )
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Error running ollama create: {e.stderr}")

    return {"message": f"Representative '{req.model_name}' created successfully.", "output": result.stdout}