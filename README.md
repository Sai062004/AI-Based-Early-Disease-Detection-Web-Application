# LifeLens AI

LifeLens AI is a full-stack disease prediction app built with a Python machine learning pipeline, a Node.js REST API, and a polished React frontend.

## Project structure

- `data/` real CSV dataset and metadata
- `model/` training and inference code
- `backend/` Express REST API
- `frontend/` React + Vite client

## Run locally

### 1. Train the model

```powershell
cd D:\Venkyyy\LifeLens-AI
& "C:\Users\Venkyyy\AppData\Local\Programs\Python\Python312\python.exe" model\train_model.py
```

### 2. Install backend packages

```powershell
cd D:\Venkyyy\LifeLens-AI\backend
npm.cmd install
```

### 3. Install frontend packages

```powershell
cd D:\Venkyyy\LifeLens-AI\frontend
npm.cmd install
```

### 4. Start the API

```powershell
cd D:\Venkyyy\LifeLens-AI\backend
npm.cmd run start
```

### 5. Start the frontend

```powershell
cd D:\Venkyyy\LifeLens-AI\frontend
npm.cmd run dev
```

Open `http://localhost:5173`.

## App flow

Landing Page -> Symptom Checker -> Results

## API

- `GET /health` returns model health and accuracy
- `GET /symptoms` returns the supported symptom catalog
- `POST /predict` accepts:

```json
{
  "symptoms": ["itching", "skin_rash", "nodal_skin_eruptions"]
}
```

## Notes

- This is a screening-style prototype, not a clinical diagnostic device.
- Predictions should be treated as informational guidance and followed up with qualified medical advice.
