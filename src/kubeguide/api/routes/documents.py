"""Document endpoints for querying and retrieving Kubernetes docs."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from kubeguide.api.deps import get_repo
from kubeguide.api.errors import NotFoundProblem
from kubeguide.db.repository import FILTER_KEY, DocumentRepository

router = APIRouter(prefix="/v1/documents", tags=["documents"])

RESERVED_PARAMS = {"q", "limit", "offset"}


@router.get("")
async def list_documents(
    repo: Annotated[DocumentRepository, Depends(get_repo)],
    request: Request,
    q: str | None = Query(default=None, description="Search query string matching documents"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination start"),
    limit: int = Query(default=10, ge=1, le=100, description="Maximum number of items to return"),
) -> dict[str, Any]:
    """List and search documents with pagination and metadata filters."""
    filters: dict[str, str] = {}
    for key, value in request.query_params.items():
        if key in RESERVED_PARAMS:
            continue
        if not FILTER_KEY.match(key):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid filter parameter '{key}'.",
            )
        filters[key] = value

    total, items = await repo.list(
        q=q,
        filters=filters,
        limit=limit,
        offset=offset,
    )

    return {
        "items": items,
        "total": total,
        "offset": offset,
        "limit": limit,
        "filters": filters,
    }


@router.get("/{doc_id}")
async def get_document(
    doc_id: str,
    request: Request,
    repo: Annotated[DocumentRepository, Depends(get_repo)],
) -> dict[str, Any]:
    """Retrieve a single document by its identifier."""
    doc = await repo.get(doc_id)
    if not doc:
        raise NotFoundProblem(
            detail=f"No document with id '{doc_id}'.",
            instance=request.url.path,
        )
    return doc
