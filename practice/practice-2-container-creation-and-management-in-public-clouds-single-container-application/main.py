"""Веб-калькулятор для одноконтейнерного приложения практики 2."""

import math
import operator
from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse

app = FastAPI(title="Калькулятор", version="1.0")
OPERATIONS = {
    "add": operator.add,
    "subtract": operator.sub,
    "multiply": operator.mul,
    "divide": operator.truediv,
}


@app.get("/", response_class=FileResponse)
def index() -> FileResponse:
    """Возвращает страницу калькулятора независимо от рабочего каталога."""
    return FileResponse(Path(__file__).with_name("index.html"))


@app.get("/health")
def health() -> dict[str, str]:
    """Подтверждает, что приложение отвечает на HTTP-запросы."""
    return {"status": "ok"}


@app.get("/api/calculate")
def calculate(
    a: Annotated[float, Query(allow_inf_nan=False)],
    b: Annotated[float, Query(allow_inf_nan=False)],
    operation: Literal["add", "subtract", "multiply", "divide"],
) -> dict[str, float]:
    """Вычисляет результат операции над двумя конечными числами."""
    if operation == "divide" and b == 0:
        raise HTTPException(status_code=400, detail="Деление на ноль невозможно.")
    result = OPERATIONS[operation](a, b)
    if not math.isfinite(result):
        raise HTTPException(status_code=400, detail="Результат слишком велик: переполнение числа.")
    return {"result": result}
