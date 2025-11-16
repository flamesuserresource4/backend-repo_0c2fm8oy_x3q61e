import os
from datetime import datetime
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents, update_document

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"

            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# ---------------- Ticketing Models (request bodies) -----------------
class CreateEventBody(BaseModel):
    title: str
    description: str | None = None
    date: datetime
    venue: str
    rows: int
    cols: int
    price: float


class CreateBookingBody(BaseModel):
    event_id: str
    seats: List[str]  # list of seat document ids
    name: str
    email: str


# ---------------- Ticketing Endpoints -----------------
@app.post("/api/events")
def create_event(body: CreateEventBody):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")

    # Create event
    event_id = create_document("event", body.model_dump())

    # Generate seats for grid rows x cols
    if not event_id:
        raise HTTPException(status_code=500, detail="Failed to create event")

    # Create seat documents: rows as letters A, B, C ...
    rows = body.rows
    cols = body.cols
    for r in range(rows):
        row_label = chr(ord('A') + r)
        for c in range(1, cols + 1):
            create_document("seat", {
                "event_id": event_id,
                "row": row_label,
                "number": c,
                "status": "available"
            })

    return {"id": event_id, "message": "Event created with seats"}


@app.get("/api/events")
def list_events():
    events = get_documents("event", {}, limit=50)
    return events


@app.get("/api/events/{event_id}/seats")
def get_seats(event_id: str):
    # list all seats for event
    seats = get_documents("seat", {"event_id": event_id})
    return seats


@app.post("/api/bookings")
def create_booking(body: CreateBookingBody):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")

    # Verify seats are available and lock them (simple check)
    from pymongo import ReturnDocument

    updated_seats: List[str] = []
    for seat_id in body.seats:
        try:
            oid = ObjectId(seat_id)
        except Exception:
            continue
        seat = db.seat.find_one_and_update(
            {"_id": oid, "status": "available"},
            {"$set": {"status": "booked", "updated_at": datetime.utcnow()}},
            return_document=ReturnDocument.AFTER,
        )
        if seat:
            updated_seats.append(str(seat["_id"]))

    if len(updated_seats) != len(body.seats):
        # rollback: set any updated seats back to available
        for sid in updated_seats:
            db.seat.update_one({"_id": ObjectId(sid)}, {"$set": {"status": "available", "updated_at": datetime.utcnow()}})
        raise HTTPException(status_code=409, detail="One or more seats are no longer available")

    # Create booking
    total_amount = len(body.seats) * (db.event.find_one({"_id": ObjectId(body.event_id)}) or {}).get("price", 0.0)
    booking_id = create_document("booking", {
        "event_id": body.event_id,
        "seat_ids": body.seats,
        "name": body.name,
        "email": body.email,
        "total_amount": total_amount,
        "status": "confirmed"
    })

    return {"id": booking_id, "message": "Booking confirmed"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
