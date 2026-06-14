from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.database import get_db
from backend.models import Template, TemplateItem, User
from backend.schemas.template import (
    TemplateCreate, TemplateUpdate, TemplateResponse,
    TemplateItemResponse, PresetResponse,
)
from backend.core.auth import get_current_user
from backend.core.normalization import get_presets, normalize_metric_name, get_metric_info

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/catalog")
async def get_catalog():
    presets = get_presets()
    return {"presets": presets}


@router.get("/normalize")
async def normalize(raw_name: str):
    standard = normalize_metric_name(raw_name)
    if standard is None:
        return {"standard_name": None, "found": False}
    info = get_metric_info(standard)
    return {"standard_name": standard, "found": True, "info": info}


@router.get("/templates/presets", response_model=list[PresetResponse])
async def get_preset_templates():
    return get_presets()


@router.get("/templates", response_model=list[TemplateResponse])
async def list_templates(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Template)
        .options(selectinload(Template.items))
        .where(Template.user_id == user.id, Template.is_preset == False)
        .order_by(Template.created_at.desc())
    )
    templates = result.scalars().all()
    return templates


@router.post("/templates", response_model=TemplateResponse)
async def create_template(
    data: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not data.name or not data.items:
        raise HTTPException(status_code=400, detail="模板名称和指标不能为空")

    template = Template(user_id=user.id, name=data.name, is_preset=False)
    db.add(template)
    await db.flush()

    for idx, item in enumerate(data.items):
        db.add(TemplateItem(
            template_id=template.id,
            metric_name=item.metric_name,
            unit=item.unit or "",
            ref_min=item.ref_min,
            ref_max=item.ref_max,
            notes=item.notes,
            sort_order=idx,
        ))

    await db.flush()

    rr = await db.execute(
        select(Template).options(selectinload(Template.items)).where(Template.id == template.id)
    )
    return rr.scalar_one()


@router.put("/templates/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    data: TemplateUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Template).where(Template.id == template_id, Template.user_id == user.id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    if data.name is not None:
        template.name = data.name

    if data.items is not None:
        await db.execute(delete(TemplateItem).where(TemplateItem.template_id == template_id))
        for idx, item in enumerate(data.items):
            db.add(TemplateItem(
                template_id=template.id,
                metric_name=item.metric_name,
                unit=item.unit or "",
                ref_min=item.ref_min,
                ref_max=item.ref_max,
                notes=item.notes,
                sort_order=idx,
            ))

        await db.flush()

    rr = await db.execute(
        select(Template).options(selectinload(Template.items)).where(Template.id == template_id)
    )
    return rr.scalar_one()



@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Template).where(
        Template.id == template_id,
        Template.user_id == user.id,
        Template.is_preset == False,
    ))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在或为预置模板不可删除")

    await db.execute(delete(TemplateItem).where(TemplateItem.template_id == template_id))
    await db.delete(template)
    await db.flush()
    return {"message": "删除成功"}
