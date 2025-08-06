from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import pandas as pd
import io
import json
from datetime import datetime

# Импортируем наш движок раскроя
from cutting_engine import cutting_engine

app = FastAPI(title="MDF Cutting API", version="1.0.0")

# Настройка CORS для веб-интерфейса
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3002", "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модели данных
class CuttingRequest(BaseModel):
    file_id: str
    params: dict

class MaterialData(BaseModel):
    name: str
    category: str
    width: float
    height: float
    thickness: float
    price: float
    quantity: int
    description: Optional[str] = None

class AIOptimizationRequest(BaseModel):
    file_id: str
    algorithm: str = "genetic"
    max_iterations: int = 1000
    population_size: int = 50
    mutation_rate: float = 0.1
    crossover_rate: float = 0.8

class FeedbackData(BaseModel):
    suggestion_id: str
    rating: int
    comment: Optional[str] = None

# Хранилище данных (в реальном приложении - база данных)
uploaded_files = {}
materials_data = []
optimization_results = {}

@app.get("/")
async def root():
    return {"message": "MDF Cutting API v1.0.0"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# API для загрузки файлов деталей
@app.post("/api/upload-details")
async def upload_details_file(file: UploadFile = File(...)):
    try:
        # Читаем файл
        content = await file.read()
        
        # Парсим CSV
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        
        # Создаем ID для файла
        file_id = f"file_{datetime.now().timestamp()}"
        
        # Сохраняем данные
        uploaded_files[file_id] = {
            "id": file_id,
            "filename": file.filename,
            "uploaded_at": datetime.now().isoformat(),
            "details": df.to_dict('records'),
            "total_details": len(df)
        }
        
        return {
            "success": True,
            "file_id": file_id,
            "filename": file.filename,
            "total_details": len(df),
            "details": df.to_dict('records')[:5]  # Первые 5 деталей для предпросмотра
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка загрузки файла: {str(e)}")

# API для оптимизации раскроя
@app.post("/api/optimize-cutting")
async def optimize_cutting(request: CuttingRequest):
    try:
        if request.file_id not in uploaded_files:
            raise HTTPException(status_code=404, detail="Файл не найден")
        
        # Получаем данные из загруженного файла
        file_data = uploaded_files[request.file_id]
        details_data = file_data["details"]
        
        # Получаем материалы (используем стандартные, если нет загруженных)
        materials_data = materials_data if materials_data else [
            {
                "sheet_id": "sheet_1",
                "length_mm": 2440,
                "width_mm": 1220,
                "thickness_mm": 16,
                "material": "S",
                "quantity": 10
            }
        ]
        
        # Запускаем реальную оптимизацию через движок
        result = cutting_engine.optimize_cutting(
            details_data=details_data,
            materials_data=materials_data,
            margin=request.params.get('margin', 5.0),
            kerf=request.params.get('kerf', 3.0)
        )
        
        # Сохраняем результаты
        optimization_results[request.file_id] = result
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка оптимизации: {str(e)}")

# API для материалов
@app.get("/api/materials")
async def get_materials():
    return materials_data

@app.post("/api/materials")
async def create_material(material: MaterialData):
    material_dict = material.dict()
    material_dict["id"] = len(materials_data) + 1
    material_dict["created_at"] = datetime.now().isoformat()
    materials_data.append(material_dict)
    return material_dict

@app.put("/api/materials/{material_id}")
async def update_material(material_id: int, material: MaterialData):
    for i, mat in enumerate(materials_data):
        if mat["id"] == material_id:
            material_dict = material.dict()
            material_dict["id"] = material_id
            material_dict["updated_at"] = datetime.now().isoformat()
            materials_data[i] = material_dict
            return material_dict
    raise HTTPException(status_code=404, detail="Материал не найден")

@app.delete("/api/materials/{material_id}")
async def delete_material(material_id: int):
    for i, mat in enumerate(materials_data):
        if mat["id"] == material_id:
            deleted_material = materials_data.pop(i)
            return {"message": "Материал удален", "material": deleted_material}
    raise HTTPException(status_code=404, detail="Материал не найден")

@app.post("/api/materials/upload")
async def upload_materials_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        
        # Очищаем существующие данные
        materials_data.clear()
        
        # Добавляем новые данные
        for index, row in df.iterrows():
            material = {
                "id": index + 1,
                "name": row.get('name', f'Материал {index + 1}'),
                "category": row.get('category', 'Общие'),
                "width": float(row.get('width', 2440)),
                "height": float(row.get('height', 1220)),
                "thickness": float(row.get('thickness', 16)),
                "price": float(row.get('price', 2500)),
                "quantity": int(row.get('quantity', 1)),
                "description": row.get('description', ''),
                "created_at": datetime.now().isoformat()
            }
            materials_data.append(material)
        
        return {
            "success": True,
            "message": f"Загружено {len(materials_data)} материалов",
            "materials": materials_data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка загрузки файла материалов: {str(e)}")

# API для AI оптимизации
@app.post("/api/ai/optimize")
async def ai_optimize(request: AIOptimizationRequest):
    try:
        if request.file_id not in uploaded_files:
            raise HTTPException(status_code=404, detail="Файл не найден")
        
        # Имитация AI оптимизации
        suggestions = [
            {
                "id": f"suggestion_{i}",
                "algorithm": request.algorithm,
                "efficiency": 85 + i * 2,
                "sheets_used": 3 - i,
                "waste": 15 - i * 2,
                "confidence": 0.8 + i * 0.05,
                "description": f"AI предложение {i + 1} с улучшенной эффективностью"
            }
            for i in range(3)
        ]
        
        return {
            "suggestions": suggestions,
            "best_suggestion": suggestions[0],
            "optimization_time": 2.5
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка AI оптимизации: {str(e)}")

# API для обратной связи
@app.post("/api/ai/feedback")
async def submit_feedback(feedback: FeedbackData):
    try:
        # В реальном приложении здесь была бы логика сохранения обратной связи
        return {
            "success": True,
            "message": "Обратная связь сохранена",
            "feedback_id": f"feedback_{datetime.now().timestamp()}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения обратной связи: {str(e)}")

# API для статистики
@app.get("/api/materials/stats")
async def get_materials_stats():
    if not materials_data:
        return {
            "total_materials": 0,
            "categories": [],
            "total_value": 0,
            "low_stock": 0
        }
    
    categories = list(set(mat["category"] for mat in materials_data))
    total_value = sum(mat["price"] * mat["quantity"] for mat in materials_data)
    low_stock = len([mat for mat in materials_data if mat["quantity"] < 5])
    
    return {
        "total_materials": len(materials_data),
        "categories": categories,
        "total_value": total_value,
        "low_stock": low_stock
    }


# API для статистики оптимизации
@app.get("/api/optimization/stats")
async def get_optimization_stats():
    """Получение статистики оптимизации раскроя."""
    return cutting_engine.get_optimization_stats()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8006) 