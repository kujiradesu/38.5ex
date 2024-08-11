from sqlalchemy.orm import Session
from . import models, schemas

def get_items(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.TestItem).offset(skip).limit(limit).all()

def create_item(db: Session, item: schemas.ItemCreate):
    db_item = models.TestItem(name=item.name)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
