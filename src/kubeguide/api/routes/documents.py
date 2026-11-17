"""Document endpoints for querying and retrieving Kubernetes docs."""

from typing import Any
from fastapi import APIRouter, Depends, Query, Request
from kubeguide.api.deps import get_document_store
from kubeguide.api.errors import NotFoundProblem
from kubeguide.store import DocumentStore

router = APIRouter(prefix="/v1/documents", tags=["documents"])


@router.get("")
def list_documents(
    q: str | None = Query(default=None, description="Search query string matching documents"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination start"),
    limit: int = Query(default=10, ge=1, le=100, description="Maximum number of items to return"),
    page: str | None = Query(default=None, description="Optional filter by page name"),
    store: DocumentStore = Depends(get_document_store),
) -> dict[str, Any]:
    """List and search documents with pagination."""
    items, total = store.search(query=q, offset=offset, limit=limit)
    if page:
        items = [item for item in items if item.get("page", "").lower() == page.lower()]
        total = len(items)

    return {
        "items": items,
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@router.get("/{doc_id}")
def get_document(
    doc_id: str,
    request: Request,
    store: DocumentStore = Depends(get_document_store),
) -> dict[str, Any]:
    """Retrieve a single document by its identifier."""
    doc = store.get_by_id(doc_id)
    if not doc:
        raise NotFoundProblem(
            detail=f"No document with id '{doc_id}'.",
            instance=request.url.path,
        )
    return doc
