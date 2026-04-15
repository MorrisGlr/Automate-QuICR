import json

from fastapi import APIRouter, HTTPException, Query

from server.config import settings

router = APIRouter()


@router.get("/guidelines")
def get_guidelines(condition: str | None = Query(default=None)):
    path = settings.guidelines_path
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Guidelines database not found")

    with open(path, "r", encoding="utf-8") as f:
        guidelines = json.load(f)

    if condition:
        term = condition.lower()
        guidelines = [
            g for g in guidelines
            if any(term in c.lower() for c in g.get("conditions", []))
        ]

    return guidelines
