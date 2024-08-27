from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session,selectinload
import os
from dotenv import load_dotenv
import uuid
from datetime import datetime, timedelta
import csv
import io

from app.models import Base, Store, StoreStatus, StoreBusinessHours, Report
from app.database import SessionLocal, get_db

load_dotenv()

app = FastAPI()



@app.post("/trigger_report")
async def trigger_report(background_tasks: BackgroundTasks,db: Session = Depends(get_db)):
    report_id = str(uuid.uuid4())
    new_report = Report(id=report_id, status="running", generated_at=datetime.utcnow())
    db.add(new_report)
    db.commit()
    
    background_tasks.add_task(generate_report,report_id)
    
    return {"report_id": report_id}

@app.get("/get_report/{report_id}")
async def get_report(report_id: str, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if report.status != "completed":
        return {"status": report.status}
    else:
        return {"status": "completed", "csv_file": report.report_csv}

def generate_report(report_id: str):
    db = SessionLocal()
    stores = db.query(Store).options(
        selectinload(Store.statuses),
        selectinload(Store.business_hours)
    ).all()
    
    report_data = []  
    
    for store in stores:
        uptime_last_hour = 60
        uptime_last_day = 24
        uptime_last_week = 168
        
        
        report_data.append({
            "store_id": store.id,
            "uptime_last_hour": uptime_last_hour,
            "uptime_last_day": uptime_last_day,
            "uptime_last_week": uptime_last_week,
            "downtime_last_hour": 60 - uptime_last_hour,
            "downtime_last_day": 24 - uptime_last_day,
            "downtime_last_week": 168 - uptime_last_week
        })
        
    os.makedirs("reports", exist_ok=True)
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=report_data[0].keys())
    writer.writeheader()
    writer.writerows(report_data)
    
    report_filename = f"{report_id}.csv"
    report_path = os.path.join("reports", report_filename)  
    with open(report_path, "w", newline='') as csvfile:
        csvfile.write(output.getvalue())

    report = db.query(Report).filter(Report.id == report_id).first()
    report.status = "completed"
    report.report_csv = report_path  
    db.commit()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)