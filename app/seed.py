import csv
from datetime import datetime
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine,text
from models import Base, Store, StoreStatus, StoreBusinessHours
from dotenv import load_dotenv
import os

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(SQLALCHEMY_DATABASE_URL)

Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def parse_csv(file_name):
    with open(f'./csv/{file_name}.csv', 'r') as file:
        reader = csv.reader(file)
        return list(reader)

def create_store_if_not_exists(db: Session, store_id: int, timezone: str = "America/Chicago"):
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        store = Store(id=store_id, timezone=timezone)
        db.add(store)
        db.commit()
    return store

def seed_store(db: Session):
    data = parse_csv("store_timezone")
    for row in data[1:]: 
        store_id = int(row[0])
        timezone = row[1] if row[1] else "America/Chicago"
        try:
            create_store_if_not_exists(db, store_id, timezone)
        except Exception as e:
            print(f"Error seeding store {store_id}: {e}")

def seed_store_hours(db: Session):
    data = parse_csv("menu_hours")
    for row in data[1:]: 
        store_id = int(row[0])
        try:
            create_store_if_not_exists(db, store_id)
            existing_hours = db.query(StoreBusinessHours).filter(
                StoreBusinessHours.store_id == store_id,
                StoreBusinessHours.day_of_week == int(row[1])
            ).first()
            if not existing_hours:
                today = datetime.now().date()
                start_time = datetime.combine(today, datetime.strptime(row[2], "%H:%M:%S").time())
                end_time = datetime.combine(today, datetime.strptime(row[3], "%H:%M:%S").time())
                
                business_hours = StoreBusinessHours(
                    store_id=store_id,
                    day_of_week=int(row[1]),
                    start_time_local=start_time,
                    end_time_local=end_time
                )
                db.add(business_hours)
                db.commit()
        except Exception as e:
            print(f"Error seeding store hours for store {store_id}: {e}")
            db.rollback()  

def seed_store_status(db: Session):
    
    data = parse_csv("store_status")
    # for row in data[1:]: 
    #     store_id = int(row[0])
    #     timezone = row[1] if row[1] else "America/Chicago"
    #     try:
    #         create_store_if_not_exists(db, store_id, timezone)
    #     except Exception as e:
    #         print(f"Error seeding store {store_id}: {e}")
    batch_size = 100000
    status_entries = []
    db.execute(text("TRUNCATE TABLE store_statuses"))
    for row in data[1:]: 
        timestamp_str = row[2].replace(" UTC", "")
        if '.' in timestamp_str:
            timestamp_utc = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
        else:
            timestamp_utc = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        
        status_entries.append({
            "store_id": int(row[0]),
            "timestamp_utc": timestamp_utc,
            "status": row[1]
        })
        
        if len(status_entries) >= batch_size:
            db.bulk_insert_mappings(StoreStatus, status_entries)
            db.commit()
            status_entries = []
            print(f"Pushed {batch_size} entries")
    
    if status_entries:
        db.bulk_insert_mappings(StoreStatus, status_entries)
        db.commit()
        print(f"Pushed final {len(status_entries)} entries")
        
        
def main():
    db = SessionLocal()
    try:
        # print("Seeding stores...")
        # seed_store(db)
        # print("Seeding store hours...")
        # seed_store_hours(db)
        print("Seeding store status...")
        seed_store_status(db)
        print("Seeding completed successfully!")
    except Exception as e:
        print(f"An error occurred during seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()