from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services import product_service

router = APIRouter()


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(product_in: ProductCreate, db: Session = Depends(get_db)) -> ProductRead:
    if product_service.get_product_by_sku(db, product_in.sku):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SKU already exists")
    return product_service.create_product(db, product_in)


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, db: Session = Depends(get_db)) -> ProductRead:
    product = product_service.get_product(db, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


@router.get("", response_model=list[ProductRead])
def list_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> list[ProductRead]:
    return product_service.list_products(db, skip=skip, limit=limit)


@router.patch("/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int, product_in: ProductUpdate, db: Session = Depends(get_db)
) -> ProductRead:
    product = product_service.get_product(db, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product_service.update_product(db, product, product_in)
