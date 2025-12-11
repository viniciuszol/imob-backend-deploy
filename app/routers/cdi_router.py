from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import get_current_user
from app.models import User, CDI
from app import schemas

router = APIRouter(prefix="/cdi", tags=["CDI"])

@router.post("/", response_model=schemas.CDIOut)
def create_cdi(cdi: schemas.CDICreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_cdi = CDI(**cdi.model_dump())
    db.add(new_cdi)
    db.commit()
    db.refresh(new_cdi)
    return new_cdi

@router.post("/bulk", response_model=list[schemas.CDIOut])
def create_cdi_bulk(
    cdis: list[schemas.CDICreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not cdis:
        raise HTTPException(status_code=400, detail="A lista está vazia")

    created = []

    for item in cdis:
        obj = CDI(**item.model_dump())
        db.add(obj)
        created.append(obj)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao salvar CDI: {e}")

    for obj in created:
        db.refresh(obj)

    return created

@router.get("/", response_model=list[schemas.CDIOut])
def list_cdi(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(CDI).order_by(CDI.data.desc()).all()

@router.get("/{cdi_id}", response_model=schemas.CDIOut)
def get_cdi(cdi_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cdi = db.query(CDI).filter(CDI.id == cdi_id).first()
    if not cdi:
        raise HTTPException(status_code=404, detail="CDI não encontrado")
    return cdi

@router.put("/{cdi_id}", response_model=schemas.CDIOut)
def update_cdi(cdi_id: int, cdi_data: schemas.CDIUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cdi = db.query(CDI).filter(CDI.id == cdi_id).first()
    if not cdi:
        raise HTTPException(status_code=404, detail="CDI não encontrado")

    for key, value in cdi_data.dict(exclude_unset=True).items():
        setattr(cdi, key, value)

    db.commit()
    db.refresh(cdi)
    return cdi

@router.delete("/{cdi_id}")
def delete_cdi(cdi_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cdi = db.query(CDI).filter(CDI.id == cdi_id).first()
    if not cdi:
        raise HTTPException(status_code=404, detail="CDI não encontrado")

    db.delete(cdi)
    db.commit()
    return {"detail": "CDI deletado com sucesso"}
