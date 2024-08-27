from fastapi import Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session, selectinload
import uuid
from datetime import datetime,timedelta
import os
import io
import csv
from app.models import Report, Store
from app.database import SessionLocal
import pytz

def trigger_report(background_tasks: BackgroundTasks, db: Session):
    report_id = str(uuid.uuid4())
    new_report = Report(id=report_id, status="running", generated_at=datetime.utcnow())
    db.add(new_report)
    db.commit()
    
    background_tasks.add_task(generate_report, report_id)
    
    return {"report_id": report_id}

def get_report(report_id: str, db: Session):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if report.status != "completed":
        return {"status": report.status}
    else:
        return {"status": "completed", "csv_file": report.report_csv}

def generate_report(report_id: str):
    print("started report generation for report id", report_id)
    db = SessionLocal()
    try:
        stores = db.query(Store).options(
            selectinload(Store.statuses),
            selectinload(Store.business_hours)
        ).all()
        
        report_data = []  
        
        for store in stores:
            report_data.append(get_uptimes(store))
        
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
    finally:
        db.close()
        

def get_uptimes(store: Store):
    now = datetime.utcnow().replace(tzinfo=pytz.utc)
    one_hour_ago = now - timedelta(hours=1)
    one_day_ago = now - timedelta(days=1)
    one_week_ago = now - timedelta(weeks=1)

    uptime_last_hour = 1
    uptime_last_day = 24 
    uptime_last_week = 7 * 24

    print(store.timezone)
    store_tz = pytz.timezone(store.timezone)

    def is_within_business_hours(timestamp_local, business_hours):
        day_of_week = timestamp_local.weekday()  
        for hours in business_hours:
            if hours.day_of_week == day_of_week:
                start_time_local = store_tz.localize(datetime.combine(timestamp_local.date(), hours.start_time_local.time()))
                end_time_local = store_tz.localize(datetime.combine(timestamp_local.date(), hours.end_time_local.time()))
                if start_time_local <= timestamp_local <= end_time_local:
                    return True
        return False

    for status in store.statuses:
        timestamp_utc = status.timestamp_utc.replace(tzinfo=pytz.utc)
        timestamp_local = timestamp_utc.astimezone(store_tz)

        if status.status == 'inactive' and is_within_business_hours(timestamp_local, store.business_hours):
            if one_hour_ago <= timestamp_utc <= now:
                uptime_last_hour -= 1
            if one_day_ago <= timestamp_utc <= now:
                uptime_last_day -= 1 
            if one_week_ago <= timestamp_utc <= now:
                uptime_last_week -= 1  

    return {
        "store_id": store.id,
        "uptime_last_hour": max(0, uptime_last_hour),
        "uptime_last_day": max(0, uptime_last_day),
        "uptime_last_week": max(0, uptime_last_week),
        "downtime_last_hour": 1 - uptime_last_hour,
        "downtime_last_day": 24 - uptime_last_day,
        "downtime_last_week": 168- uptime_last_week 
    }
