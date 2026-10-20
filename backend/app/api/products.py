"""
Products API Router (/api/v1/products).
Implements Products CRUD with real DB persistence, image upload (DECISION-D18),
and AI suggestion (DECISION-D19).
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import logging
from uuid import UUID
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from contracts.schemas import (
    ErrorCode,
    ExtractProfileRequest,
    PriceSegment,
    Product,
    ProductAttributes,
    ProductCreate,
    ProductInput,
    ProductUpdate,
)
from backend.ai.service import get_ai_service
from backend.app.auth.deps import CurrentUser, current_user
from backend.app.core.errors import AppError
from backend.app.core.storage import get_storage_service
from backend.app.db.models import (
    AICallLogModel,
    LeadEvidenceModel,
    LeadModel,
    MarketHypothesisModel,
    OutreachDraftModel,
    ProductModel,
    ProviderCallModel,
    ResearchRunModel,
    TasteAnchorModel,
)
from backend.app.db.session import get_db_session

logger = logging.getLogger(__name__)

products_router = APIRouter(prefix="/products", tags=["Products"])

ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def _to_price_segment(val: str | PriceSegment) -> PriceSegment:
    if isinstance(val, PriceSegment):
        return val
    try:
        return PriceSegment(str(val))
    except ValueError:
        return PriceSegment.MID_PREMIUM


def _product_model_to_schema(model: ProductModel) -> Product:
    return Product(
        id=model.id,
        owner_id=model.owner_id,
        name=model.name,
        category=model.category,
        description=model.description,
        materials=list(model.materials or []),
        style=list(model.style or []),
        motifs=list(model.motifs or []),
        colours=list(model.colours or []),
        price_segment=_to_price_segment(model.price_segment),
        price_min=model.price_min,
        price_max=model.price_max,
        currency=model.currency,
        moq=model.moq,
        monthly_capacity=model.monthly_capacity,
        target_retailer_types=list(model.target_retailer_types or []),
        images=list(model.images or []),
        is_demo=model.is_demo,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


@products_router.get("", response_model=list[Product])
async def list_products(
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[Product]:
    """
    List all products belonging to the authenticated seller.
    Ordered deterministically by created_at desc, id desc.
    """
    stmt = (
        select(ProductModel)
        .where(ProductModel.owner_id == user.id)
        .order_by(ProductModel.created_at.desc(), ProductModel.id.desc())
    )
    result = await session.execute(stmt)
    records = result.scalars().all()
    return [_product_model_to_schema(m) for m in records]


@products_router.post("", response_model=Product, status_code=201)
async def create_product(
    payload: ProductCreate,
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Product:
    """
    Create a new product record stamped with owner_id = current_user.id.
    Validates price_min <= price_max and moq >= 1.
    """
    if payload.moq < 1:
        raise AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message="moq must be >= 1",
            status_code=422,
            details={"field": "moq", "reason": "must be >= 1", "moq": "must be >= 1"},
        )

    if payload.price_min is not None and payload.price_max is not None:
        if payload.price_min > payload.price_max:
            raise AppError(
                code=ErrorCode.VALIDATION_ERROR,
                message="price_min must be <= price_max",
                status_code=422,
                details={
                    "field": "price_min",
                    "reason": "must be <= price_max",
                    "price_min": "must be <= price_max",
                },
            )

    price_segment_val = (
        payload.price_segment.value
        if hasattr(payload.price_segment, "value")
        else str(payload.price_segment)
    )

    product = ProductModel(
        owner_id=user.id,
        name=payload.name,
        category=payload.category,
        description=payload.description,
        materials=list(payload.materials or []),
        style=list(payload.style or []),
        motifs=list(payload.motifs or []),
        colours=list(payload.colours or []),
        price_segment=price_segment_val,
        price_min=payload.price_min,
        price_max=payload.price_max,
        currency=payload.currency,
        moq=payload.moq,
        monthly_capacity=payload.monthly_capacity,
        target_retailer_types=list(payload.target_retailer_types or []),
        images=list(payload.images or []),
        is_demo=payload.is_demo,
    )
    session.add(product)
    await session.commit()
    await session.refresh(product)

    return _product_model_to_schema(product)


@products_router.get("/{id}", response_model=Product)
async def get_product(
    id: UUID,
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Product:
    """
    Retrieve a single product by ID.
    Enforces owner_id == current_user.id.
    Returns 404 not_found if not found or belongs to another user.
    """
    stmt = select(ProductModel).where(
        ProductModel.id == id,
        ProductModel.owner_id == user.id,
    )
    product = (await session.execute(stmt)).scalar_one_or_none()
    if product is None:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"Product with id '{id}' not found",
            status_code=404,
        )
    return _product_model_to_schema(product)


@products_router.put("/{id}", response_model=Product)
async def update_product(
    id: UUID,
    payload: ProductUpdate,
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Product:
    """
    Update a product record.
    Enforces owner_id == current_user.id (returns 404 if belongs to another user).
    Validates price_min <= price_max and moq >= 1.
    """
    stmt = select(ProductModel).where(
        ProductModel.id == id,
        ProductModel.owner_id == user.id,
    )
    product = (await session.execute(stmt)).scalar_one_or_none()
    if product is None:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"Product with id '{id}' not found",
            status_code=404,
        )

    # Validate price range combining existing and updated values
    effective_min = payload.price_min if payload.price_min is not None else product.price_min
    effective_max = payload.price_max if payload.price_max is not None else product.price_max
    if effective_min is not None and effective_max is not None and effective_min > effective_max:
        raise AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message="price_min must be <= price_max",
            status_code=422,
            details={
                "field": "price_min",
                "reason": "must be <= price_max",
                "price_min": "must be <= price_max",
            },
        )

    if payload.moq is not None and payload.moq < 1:
        raise AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message="moq must be >= 1",
            status_code=422,
            details={"field": "moq", "reason": "must be >= 1", "moq": "must be >= 1"},
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        if field == "price_segment" and val is not None:
            val = val.value if hasattr(val, "value") else str(val)
        setattr(product, field, val)

    product.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(product)
    return _product_model_to_schema(product)


@products_router.delete("/{id}", response_model=dict[str, str])
async def delete_product(
    id: UUID,
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    """
    Delete a product record and cascade delete all child records (DECISION-D12).
    Enforces owner_id == current_user.id (returns 404 if belongs to another user).
    """
    stmt = select(ProductModel).where(
        ProductModel.id == id,
        ProductModel.owner_id == user.id,
    )
    product = (await session.execute(stmt)).scalar_one_or_none()
    if product is None:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"Product with id '{id}' not found",
            status_code=404,
        )

    # 1. Fetch lead IDs for this product to clean up dependent child records
    lead_ids_stmt = select(LeadModel.id).where(LeadModel.product_id == id)
    lead_ids = (await session.execute(lead_ids_stmt)).scalars().all()

    if lead_ids:
        # Clear duplicate_of references pointing to any leads about to be deleted
        await session.execute(
            update(LeadModel)
            .where(LeadModel.duplicate_of.in_(lead_ids))
            .values(duplicate_of=None)
        )
        # Delete evidence items for these leads
        await session.execute(
            delete(LeadEvidenceModel).where(LeadEvidenceModel.lead_id.in_(lead_ids))
        )

    # 2. Fetch run IDs for this product
    run_ids_stmt = select(ResearchRunModel.id).where(ResearchRunModel.product_id == id)
    run_ids = (await session.execute(run_ids_stmt)).scalars().all()

    if run_ids:
        await session.execute(
            delete(TasteAnchorModel).where(TasteAnchorModel.run_id.in_(run_ids))
        )
        await session.execute(
            delete(MarketHypothesisModel).where(MarketHypothesisModel.run_id.in_(run_ids))
        )
        await session.execute(
            delete(AICallLogModel).where(AICallLogModel.run_id.in_(run_ids))
        )
        await session.execute(
            delete(ProviderCallModel).where(ProviderCallModel.run_id.in_(run_ids))
        )

    # 3. Delete outreach drafts
    await session.execute(
        delete(OutreachDraftModel).where(OutreachDraftModel.product_id == id)
    )

    # 4. Delete leads
    await session.execute(
        delete(LeadModel).where(LeadModel.product_id == id)
    )

    # 5. Delete research runs
    await session.execute(
        delete(ResearchRunModel).where(ResearchRunModel.product_id == id)
    )

    # 6. Delete the product itself
    await session.delete(product)
    await session.commit()

    return {"status": "deleted", "id": str(id)}


@products_router.post("/{id}/images", response_model=list[str])
async def upload_product_image(
    id: UUID,
    file: UploadFile = File(...),
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[str]:
    """
    Upload an image for a product.
    Validates MIME type (jpeg, png, webp) and size <= 5MB.
    Uploads under per-user path, appends URL to product.images, and returns list[str] (DECISION-D18).
    Enforces owner_id == current_user.id (returns 404 if belongs to another user).
    """
    stmt = select(ProductModel).where(
        ProductModel.id == id,
        ProductModel.owner_id == user.id,
    )
    product = (await session.execute(stmt)).scalar_one_or_none()
    if product is None:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"Product with id '{id}' not found",
            status_code=404,
        )

    # Validate image MIME type
    content_type = (file.content_type or "").lower().strip()
    if content_type not in ALLOWED_IMAGE_MIME_TYPES:
        allowed_str = ", ".join(sorted(ALLOWED_IMAGE_MIME_TYPES))
        raise AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message=f"Invalid image type '{content_type}'. Allowed types: {allowed_str}",
            status_code=422,
            details={
                "field": "file",
                "reason": f"Allowed MIME types are: {allowed_str}",
                "file": f"Allowed MIME types are: {allowed_str}",
            },
        )

    # Read and validate image size
    content = await file.read()
    if len(content) == 0:
        raise AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message="Uploaded image file is empty",
            status_code=422,
            details={
                "field": "file",
                "reason": "File cannot be empty",
                "file": "File cannot be empty",
            },
        )
    if len(content) > MAX_IMAGE_SIZE_BYTES:
        raise AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message="File size exceeds maximum allowed limit of 5MB",
            status_code=422,
            details={
                "field": "file",
                "reason": "File size exceeds 5MB limit",
                "file": "File size exceeds 5MB limit",
            },
        )

    # Upload via Storage Service (Supabase or local/mock adapter)
    storage = get_storage_service()
    image_url = await storage.upload_product_image(
        user_id=user.id,
        product_id=product.id,
        filename=file.filename or "image.jpg",
        content=content,
        content_type=content_type,
    )

    # Append to product.images and persist
    updated_images = list(product.images or [])
    updated_images.append(image_url)
    product.images = updated_images
    product.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(product)

    return list(product.images or [])


@products_router.post("/extract-profile", response_model=ProductAttributes)
async def extract_product_profile(
    payload: ExtractProfileRequest,
    user: CurrentUser = Depends(current_user),
) -> ProductAttributes:
    """
    AI Task A: Suggest structured product attributes from free-text description.
    Calls get_ai_service().structure_product(description, known).
    Does NOT persist to database (seller review required).
    Maps ai_output_invalid or timeouts to Appendix A.5 error codes.
    """
    service = get_ai_service()
    known_fields = payload.known or ProductInput()

    try:
        return await service.structure_product(payload.description, known_fields)
    except asyncio.TimeoutError as exc:
        raise AppError(
            code=ErrorCode.UPSTREAM_TIMEOUT,
            message="AI extraction service timed out",
            status_code=504,
        ) from exc
    except AppError:
        raise
    except Exception as exc:
        err_msg = str(exc)
        err_lower = err_msg.lower()
        if "timeout" in err_lower:
            raise AppError(
                code=ErrorCode.UPSTREAM_TIMEOUT,
                message="AI extraction service timed out",
                status_code=504,
            ) from exc
        elif (
            "output_invalid" in err_lower
            or "ai_output_invalid" in err_lower
            or isinstance(exc, ValueError)
        ):
            raise AppError(
                code=ErrorCode.AI_OUTPUT_INVALID,
                message=f"AI output validation failed: {err_msg}",
                status_code=502,
                details={"field": "description", "reason": err_msg},
            ) from exc
        else:
            raise AppError(
                code=ErrorCode.UPSTREAM_UNAVAILABLE,
                message=f"AI service unavailable: {err_msg}",
                status_code=503,
            ) from exc
