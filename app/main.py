from fastapi import FastAPI, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app.database import get_db
from app.operations import trigger_report, get_report

load_dotenv()

app = FastAPI()



@app.post("/trigger_report")
async def api_trigger_report(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    return trigger_report(background_tasks, db)

@app.get("/get_report/{report_id}")
async def api_get_report(report_id: str, db: Session = Depends(get_db)):
    return get_report(report_id, db)
