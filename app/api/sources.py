# app/api/sources.py
from fastapi import APIRouter, HTTPException

from app.models.schema import SourceCreate, SourceUpdate, SourceResponse
from app.models.database import SourceDB

router = APIRouter()


@router.get("/sources")
async def list_sources():
    sources = await SourceDB.get_all()
    return {
        "sources": [
            SourceResponse(
                id=s["id"],
                name=s["name"],
                type=s["type"],
                url=s["url"],
                enabled=s["enabled"],
                filter_keywords=eval(s["filter_keywords"]) if s["filter_keywords"] else None
            )
            for s in sources
        ]
    }


@router.post("/sources", response_model=SourceResponse)
async def create_source(source: SourceCreate):
    try:
        source_id = await SourceDB.create(
            name=source.name,
            type=source.type,
            url=source.url,
            enabled=source.enabled,
            filter_keywords=source.filter_keywords
        )
        created = await SourceDB.get_by_id(source_id)
        return SourceResponse(
            id=created["id"],
            name=created["name"],
            type=created["type"],
            url=created["url"],
            enabled=created["enabled"],
            filter_keywords=eval(created["filter_keywords"]) if created["filter_keywords"] else None
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/sources/{source_id}", response_model=SourceResponse)
async def update_source(source_id: int, source: SourceUpdate):
    updated = await SourceDB.update(
        source_id,
        name=source.name,
        type=source.type,
        url=source.url,
        enabled=source.enabled,
        filter_keywords=source.filter_keywords
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Source not found")

    result = await SourceDB.get_by_id(source_id)
    return SourceResponse(
        id=result["id"],
        name=result["name"],
        type=result["type"],
        url=result["url"],
        enabled=result["enabled"],
        filter_keywords=eval(result["filter_keywords"]) if result["filter_keywords"] else None
    )


@router.delete("/sources/{source_id}")
async def delete_source(source_id: int):
    deleted = await SourceDB.delete(source_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Source not found")
    return {"status": "deleted"}