from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas, crud
import database
import uvicorn
from datetime import datetime
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/",
         summary="Main_Page",
         tags=["Основные ручки"])
def get_home():
    return "Main Page"


@app.get("/rolls/",
         response_model=list[schemas.MetalRoll],
         summary="Получить все объекты",
         tags=["GET"])
def get_rolls(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    rolls = crud.get_metal_rolls(db, skip=skip, limit=limit)
    return rolls


@app.get("/rolls/{roll_id}",
         response_model=schemas.MetalRoll,
         summary="Получить конкретный объект",
         tags=["GET"])
def get_roll(roll_id: int, db: Session = Depends(get_db)):
    roll = crud.get_metal_roll(db, roll_id)
    return roll


@app.post("/rolls/",
          response_model=schemas.MetalRoll,
          summary="Добавить объект",
          tags=["UPDATE"])
def create_roll(roll: schemas.MetalRoll, db: Session = Depends(get_db)):
    return crud.create_metal_roll(db, roll)


@app.delete("/rolls/{roll_id}",
            response_model=schemas.MetalRoll,
            summary="Удалить конкретный объект",
            tags=["DELETE"])
def delete_roll(roll_id: int, db: Session = Depends(get_db)):
    db_roll = crud.delete_metal_roll(db, roll_id)
    if db_roll is None:
        raise HTTPException(status_code=404, detail="Рулон не найден")
    return db_roll

@app.get("/stats/",
         response_model=schemas.StatisticsResponse,
         summary="Статистика по заданному временному диапазону",
         tags=["GET"])
def get_stats(start_date: datetime,end_date: datetime,
    db: Session = Depends(get_db)):
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="Начальная дата не может быть позже конечной")
    return crud.get_roll_statistics(db, start_date, end_date)


if __name__ == "__main__":
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, dest='config')
    args = parser.parse_args()

    server_host = config['SERVER_HOST']
    server_port = int(config['SERVER_PORT'])
    '''
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)