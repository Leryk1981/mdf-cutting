import io
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import ezdxf
import matplotlib.pyplot as plt
import pandas as pd
import uvicorn

# Импортируем наш движок раскроя
from cutting_engine import cutting_engine
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from matplotlib.backends.backend_pdf import PdfPages
from pydantic import BaseModel

app = FastAPI(title="MDF Cutting API", version="1.0.0")

# Настройка CORS для веб-интерфейса
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3002",
        "http://localhost:3000",
        "http://localhost:3001",
    ],
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


class CuttingMapData(BaseModel):
    name: str
    material: str
    dimensions: str
    efficiency: float
    panels: int
    waste: float
    status: str = "completed"
    description: Optional[str] = None


class CuttingMapUpdate(BaseModel):
    name: Optional[str] = None
    material: Optional[str] = None
    dimensions: Optional[str] = None
    efficiency: Optional[float] = None
    panels: Optional[int] = None
    waste: Optional[float] = None
    status: Optional[str] = None
    description: Optional[str] = None


# Хранилище данных (в реальном приложении - база данных)
uploaded_files = {}
materials_data = []
optimization_results = {}
cutting_maps = []

# Путь к папке с картами раскроя
OUTPUT_DIR = Path("../../output")


def dxf_to_pdf(dxf_path: str, pdf_path: str):
    """Конвертирует DXF файл в PDF с сохранением всех слоев"""
    try:
        # Загружаем DXF файл
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()

        # Создаем PDF
        with PdfPages(pdf_path) as pdf:
            fig, ax = plt.subplots(figsize=(16, 12))
            ax.set_aspect("equal")

            # Цвета для разных слоев
            layer_colors = {
                "0": "#2E86AB",  # Основной слой - синий
                "work_area": "#2E86AB",  # Рабочая область - синий
                "details": "#A23B72",  # Детали - розовый
                "dimensions": "#FF6B35",  # Размеры - оранжевый
                "cuts": "#FF0000",  # Линии реза - красный
            }

            # Собираем все координаты для определения границ
            all_x = []
            all_y = []

            # Обрабатываем все сущности
            for entity in msp:
                if entity.dxftype() == "LWPOLYLINE":
                    layer = entity.dxf.layer
                    color = layer_colors.get(layer, "#000000")

                    # Получаем точки полилинии
                    points = list(entity.get_points())
                    if points:
                        x_coords = [p[0] for p in points]
                        y_coords = [p[1] for p in points]

                        all_x.extend(x_coords)
                        all_y.extend(y_coords)

                        # Рисуем полилинию
                        ax.plot(
                            x_coords,
                            y_coords,
                            color=color,
                            linewidth=1.5,
                            label=layer,
                        )

                elif entity.dxftype() == "LINE":
                    layer = entity.dxf.layer
                    color = layer_colors.get(layer, "#000000")

                    start = entity.dxf.start
                    end = entity.dxf.end

                    all_x.extend([start[0], end[0]])
                    all_y.extend([start[1], end[1]])

                    ax.plot(
                        [start[0], end[0]],
                        [start[1], end[1]],
                        color=color,
                        linewidth=1.5,
                        label=layer,
                    )

                elif entity.dxftype() == "TEXT":
                    layer = entity.dxf.layer
                    color = layer_colors.get(layer, "#000000")

                    pos = entity.dxf.insert
                    text = entity.dxf.text

                    all_x.append(pos[0])
                    all_y.append(pos[1])

                    ax.text(
                        pos[0],
                        pos[1],
                        text,
                        color=color,
                        fontsize=8,
                        ha="center",
                        va="center",
                    )

            # Устанавливаем границы с небольшим отступом
            if all_x and all_y:
                margin = (
                    max(max(all_x) - min(all_x), max(all_y) - min(all_y))
                    * 0.05
                )
                ax.set_xlim(min(all_x) - margin, max(all_x) + margin)
                ax.set_ylim(min(all_y) - margin, max(all_y) + margin)

            # Настройки графика
            ax.grid(True, alpha=0.3)
            ax.set_title(
                f"Карта раскроя - {Path(dxf_path).stem}", fontsize=14, pad=20
            )
            ax.set_xlabel("X (мм)", fontsize=12)
            ax.set_ylabel("Y (мм)", fontsize=12)

            # Легенда
            handles, labels = ax.get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            if by_label:
                ax.legend(
                    by_label.values(), by_label.keys(), loc="upper right"
                )

            plt.tight_layout()
            pdf.savefig(fig, dpi=300, bbox_inches="tight")
            plt.close()

    except Exception as e:
        print(f"Ошибка конвертации DXF в PDF: {e}")
        raise


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
        df = pd.read_csv(io.StringIO(content.decode("utf-8")))

        # Создаем ID для файла
        file_id = f"file_{datetime.now().timestamp()}"

        # Сохраняем данные
        uploaded_files[file_id] = {
            "id": file_id,
            "filename": file.filename,
            "uploaded_at": datetime.now().isoformat(),
            "details": df.to_dict("records"),
            "total_details": len(df),
        }

        return {
            "success": True,
            "file_id": file_id,
            "filename": file.filename,
            "total_details": len(df),
            "details": df.to_dict("records")[
                :5
            ],  # Первые 5 деталей для предпросмотра
        }
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Ошибка загрузки файла: {str(e)}"
        )


# API для оптимизации раскроя
@app.post("/api/optimize-cutting")
async def optimize_cutting(request: CuttingRequest):
    global materials_data
    try:
        if request.file_id not in uploaded_files:
            raise HTTPException(status_code=404, detail="Файл не найден")

        # Получаем данные из загруженного файла
        file_data = uploaded_files[request.file_id]
        details_data = file_data["details"]

        # Получаем материалы (используем стандартные, если нет загруженных)
        materials_data = (
            materials_data
            if materials_data
            else [
                {
                    "sheet_id": "sheet_1",
                    "length_mm": 2440,
                    "width_mm": 1220,
                    "thickness_mm": 16,
                    "material": "S",
                    "quantity": 10,
                }
            ]
        )

        # Запускаем реальную оптимизацию через движок
        result = cutting_engine.optimize_cutting(
            details_data=details_data,
            materials_data=materials_data,
            margin=request.params.get("margin", 5.0),
            kerf=request.params.get("kerf", 3.0),
        )

        # Сохраняем результаты
        optimization_results[request.file_id] = result
        return result

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка оптимизации: {str(e)}"
        )


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
        df = pd.read_csv(io.StringIO(content.decode("utf-8")))

        # Очищаем существующие данные
        materials_data.clear()

        # Добавляем новые данные
        for index, row in df.iterrows():
            material = {
                "id": index + 1,
                "name": row.get("name", f"Материал {index + 1}"),
                "category": row.get("category", "Общие"),
                "width": float(row.get("width", 2440)),
                "height": float(row.get("height", 1220)),
                "thickness": float(row.get("thickness", 16)),
                "price": float(row.get("price", 2500)),
                "quantity": int(row.get("quantity", 1)),
                "description": row.get("description", ""),
                "created_at": datetime.now().isoformat(),
            }
            materials_data.append(material)

        return {
            "success": True,
            "message": f"Загружено {len(materials_data)} материалов",
            "materials": materials_data,
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Ошибка загрузки файла материалов: {str(e)}",
        )


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
                "description": f"AI предложение {i + 1} с улучшенной эффективностью",
            }
            for i in range(3)
        ]

        return {
            "suggestions": suggestions,
            "best_suggestion": suggestions[0],
            "optimization_time": 2.5,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка AI оптимизации: {str(e)}"
        )


# API для обратной связи
@app.post("/api/ai/feedback")
async def submit_feedback(feedback: FeedbackData):
    try:
        # В реальном приложении здесь была бы логика сохранения обратной связи
        return {
            "success": True,
            "message": "Обратная связь сохранена",
            "feedback_id": f"feedback_{datetime.now().timestamp()}",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка сохранения обратной связи: {str(e)}",
        )


# API для статистики
@app.get("/api/materials/stats")
async def get_materials_stats():
    if not materials_data:
        return {
            "total_materials": 0,
            "categories": [],
            "total_value": 0,
            "low_stock": 0,
        }

    categories = list(set(mat["category"] for mat in materials_data))
    total_value = sum(mat["price"] * mat["quantity"] for mat in materials_data)
    low_stock = len([mat for mat in materials_data if mat["quantity"] < 5])

    return {
        "total_materials": len(materials_data),
        "categories": categories,
        "total_value": total_value,
        "low_stock": low_stock,
    }


# API для статистики оптимизации
@app.get("/api/optimization/stats")
async def get_optimization_stats():
    """Получение статистики оптимизации раскроя."""
    return cutting_engine.get_optimization_stats()


def scan_output_directory():
    """Сканирует папку output и возвращает список карт раскроя."""
    cutting_maps = []

    print(f"Сканируем папку: {OUTPUT_DIR}")
    print(f"Папка существует: {OUTPUT_DIR.exists()}")

    if not OUTPUT_DIR.exists():
        print("Папка OUTPUT_DIR не существует!")
        return cutting_maps

    # Проходим по всем папкам толщин
    for thickness_dir in OUTPUT_DIR.iterdir():
        if thickness_dir.is_dir():
            thickness = thickness_dir.name
            print(f"Найдена папка толщины: {thickness}")

            # Проходим по всем DXF файлам в папке
            dxf_files = list(thickness_dir.glob("*.dxf"))
            print(f"Найдено DXF файлов в {thickness}: {len(dxf_files)}")

            for dxf_file in dxf_files:
                if dxf_file.is_file():
                    print(f"Обрабатываем файл: {dxf_file.name}")
                    # Получаем информацию о файле
                    stat = dxf_file.stat()

                    # Создаем объект карты раскроя
                    cutting_map = {
                        "id": len(cutting_maps),
                        "name": dxf_file.stem,  # Имя файла без расширения
                        "filename": dxf_file.name,
                        "material": f"МДФ {thickness}",
                        "thickness": thickness,
                        "dimensions": "2440x1220",  # Стандартные размеры листа
                        "efficiency": 85.0,  # Примерная эффективность
                        "panels": 20,  # Примерное количество панелей
                        "waste": 15.0,  # Примерные отходы
                        "status": "completed",
                        "date": datetime.fromtimestamp(
                            stat.st_mtime
                        ).isoformat(),
                        "file_path": str(dxf_file.relative_to(OUTPUT_DIR)),
                        "file_size": stat.st_size,
                        "thumbnail": f"/api/cutting-maps/{len(cutting_maps)}/thumbnail",
                        "download_pdf": f"/api/cutting-maps/{len(cutting_maps)}/pdf",
                        "download_dxf": f"/api/cutting-maps/{len(cutting_maps)}/dxf",
                    }
                    cutting_maps.append(cutting_map)

    print(f"Всего найдено карт раскроя: {len(cutting_maps)}")
    return cutting_maps


# API для карт раскроя
@app.get("/api/cutting-maps")
async def get_cutting_maps():
    """Получить все карты раскроя из папки output."""
    return scan_output_directory()


@app.get("/api/cutting-maps/{map_id}")
async def get_cutting_map(map_id: int):
    """Получить карту раскроя по ID."""
    all_maps = scan_output_directory()
    if map_id < 0 or map_id >= len(all_maps):
        raise HTTPException(status_code=404, detail="Карта раскроя не найдена")
    return all_maps[map_id]


@app.post("/api/cutting-maps")
async def create_cutting_map(cutting_map: CuttingMapData):
    """Создать новую карту раскроя."""
    map_id = len(cutting_maps)
    new_map = {
        "id": map_id,
        "name": cutting_map.name,
        "material": cutting_map.material,
        "dimensions": cutting_map.dimensions,
        "efficiency": cutting_map.efficiency,
        "panels": cutting_map.panels,
        "waste": cutting_map.waste,
        "status": cutting_map.status,
        "description": cutting_map.description,
        "date": datetime.now().isoformat(),
        "thumbnail": f"/api/cutting-maps/{map_id}/thumbnail",
    }
    cutting_maps.append(new_map)
    return new_map


@app.put("/api/cutting-maps/{map_id}")
async def update_cutting_map(map_id: int, cutting_map: CuttingMapUpdate):
    """Обновить карту раскроя."""
    if map_id < 0 or map_id >= len(cutting_maps):
        raise HTTPException(status_code=404, detail="Карта раскроя не найдена")

    map_data = cutting_maps[map_id]
    update_data = cutting_map.dict(exclude_unset=True)

    for key, value in update_data.items():
        map_data[key] = value

    return map_data


@app.delete("/api/cutting-maps/{map_id}")
async def delete_cutting_map(map_id: int):
    """Удалить карту раскроя."""
    if map_id < 0 or map_id >= len(cutting_maps):
        raise HTTPException(status_code=404, detail="Карта раскроя не найдена")

    deleted_map = cutting_maps.pop(map_id)
    return {"message": "Карта раскроя удалена", "deleted_map": deleted_map}


@app.get("/api/cutting-maps/{map_id}/image")
async def get_cutting_map_image(map_id: int):
    """Получить изображение карты раскроя."""
    all_maps = scan_output_directory()
    if map_id < 0 or map_id >= len(all_maps):
        raise HTTPException(status_code=404, detail="Карта раскроя не найдена")

    map_data = all_maps[map_id]
    file_path = OUTPUT_DIR / map_data["file_path"]

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")

    # В реальном приложении здесь можно генерировать превью DXF файла
    # Пока возвращаем информацию о файле
    return {
        "map_id": map_id,
        "filename": map_data["filename"],
        "file_size": map_data["file_size"],
        "file_path": map_data["file_path"],
        "material": map_data["material"],
        "dimensions": map_data["dimensions"],
        "efficiency": map_data["efficiency"],
        "panels": map_data["panels"],
        "waste": map_data["waste"],
        "date": map_data["date"],
    }


@app.get("/api/cutting-maps/{map_id}/pdf")
async def download_cutting_map_pdf(map_id: int):
    """Скачать карту раскроя в PDF."""
    all_maps = scan_output_directory()
    if map_id < 0 or map_id >= len(all_maps):
        raise HTTPException(status_code=404, detail="Карта раскроя не найдена")

    map_data = all_maps[map_id]
    dxf_path = OUTPUT_DIR / map_data["file_path"]

    if not dxf_path.exists():
        raise HTTPException(status_code=404, detail="DXF файл не найден")

    # Создаем путь для PDF файла
    pdf_path = dxf_path.with_suffix(".pdf")

    # Конвертируем DXF в PDF если PDF еще не существует
    if not pdf_path.exists():
        dxf_to_pdf(str(dxf_path), str(pdf_path))

    # Используем только латинские символы в имени файла
    filename = f"cutting_map_{map_data['name']}_{map_data['thickness']}.pdf"

    return FileResponse(
        path=pdf_path,
        filename=filename,
        media_type="application/octet-stream",  # Принудительное скачивание
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )


@app.get("/api/cutting-maps/{map_id}/dxf")
async def download_cutting_map_dxf(map_id: int):
    """Скачать карту раскроя в DXF."""
    all_maps = scan_output_directory()
    if map_id < 0 or map_id >= len(all_maps):
        raise HTTPException(status_code=404, detail="Карта раскроя не найдена")

    map_data = all_maps[map_id]
    file_path = OUTPUT_DIR / map_data["file_path"]

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")

    return FileResponse(
        path=file_path,
        filename=map_data["filename"],
        media_type="application/dxf",
    )


@app.get("/api/cutting-maps/stats")
async def get_cutting_maps_stats():
    """Получить статистику карт раскроя."""
    all_maps = scan_output_directory()

    if not all_maps:
        return {
            "total_maps": 0,
            "average_efficiency": 0,
            "total_panels": 0,
            "total_waste": 0,
            "status_distribution": {},
            "thickness_distribution": {},
        }

    total_maps = len(all_maps)
    average_efficiency = (
        sum(map["efficiency"] for map in all_maps) / total_maps
    )
    total_panels = sum(map["panels"] for map in all_maps)
    total_waste = sum(map["waste"] for map in all_maps)

    status_distribution = {}
    thickness_distribution = {}

    for map in all_maps:
        status = map["status"]
        thickness = map["thickness"]

        status_distribution[status] = status_distribution.get(status, 0) + 1
        thickness_distribution[thickness] = (
            thickness_distribution.get(thickness, 0) + 1
        )

    return {
        "total_maps": total_maps,
        "average_efficiency": round(average_efficiency, 2),
        "total_panels": total_panels,
        "total_waste": round(total_waste, 2),
        "status_distribution": status_distribution,
        "thickness_distribution": thickness_distribution,
    }


@app.get("/api/cutting-maps/search")
async def search_cutting_maps(q: str):
    """Поиск карт раскроя."""
    all_maps = scan_output_directory()

    if not q:
        return all_maps

    results = []
    query = q.lower()

    for map in all_maps:
        if (
            query in map["name"].lower()
            or query in map["material"].lower()
            or query in map["thickness"].lower()
            or query in map["dimensions"].lower()
        ):
            results.append(map)

    return results


@app.get("/api/cutting-maps/filter")
async def filter_cutting_maps(
    status: Optional[str] = None,
    material: Optional[str] = None,
    thickness: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    """Фильтрация карт раскроя."""
    all_maps = scan_output_directory()
    results = all_maps.copy()

    if status:
        results = [map for map in results if map["status"] == status]

    if material:
        results = [map for map in results if map["material"] == material]

    if thickness:
        results = [map for map in results if map["thickness"] == thickness]

    if date_from:
        results = [map for map in results if map["date"] >= date_from]

    if date_to:
        results = [map for map in results if map["date"] <= date_to]

    return results


@app.post("/api/cutting-maps/{map_id}/duplicate")
async def duplicate_cutting_map(map_id: int):
    """Дублировать карту раскроя."""
    if map_id < 0 or map_id >= len(cutting_maps):
        raise HTTPException(status_code=404, detail="Карта раскроя не найдена")

    original_map = cutting_maps[map_id]
    new_map_id = len(cutting_maps)

    duplicated_map = {
        **original_map,
        "id": new_map_id,
        "name": f"{original_map['name']} (копия)",
        "date": datetime.now().isoformat(),
        "thumbnail": f"/api/cutting-maps/{new_map_id}/thumbnail",
    }

    cutting_maps.append(duplicated_map)
    return duplicated_map


@app.get("/api/cutting-maps/export")
async def export_cutting_maps(format: str = "json"):
    """Экспорт карт раскроя."""
    if format == "json":
        return cutting_maps
    elif format == "csv":
        # В реальном приложении здесь будет экспорт в CSV
        return {"message": "CSV экспорт", "data": cutting_maps}
    else:
        raise HTTPException(status_code=400, detail="Неподдерживаемый формат")


@app.post("/api/cutting-maps/import")
async def import_cutting_maps(file: UploadFile = File(...)):
    """Импорт карт раскроя."""
    try:
        content = await file.read()
        data = json.loads(content.decode("utf-8"))

        if isinstance(data, list):
            for item in data:
                item["id"] = len(cutting_maps)
                item["date"] = datetime.now().isoformat()
                cutting_maps.append(item)
        else:
            data["id"] = len(cutting_maps)
            data["date"] = datetime.now().isoformat()
            cutting_maps.append(data)

        return {
            "message": "Карты раскроя импортированы",
            "imported_count": len(data) if isinstance(data, list) else 1,
        }
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Ошибка импорта: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8007)
