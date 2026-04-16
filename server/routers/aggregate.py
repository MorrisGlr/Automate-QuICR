# Copyright (c) 2024-2026 Morris A. Aguilar. All Rights Reserved.
# Licensed under the Apache License, Version 2.0.
from fastapi import APIRouter, Query

from server.config import settings
from server.models import AggregateResponse
from server.services import aggregate_service

router = APIRouter()


@router.get("/aggregate", response_model=AggregateResponse)
def get_aggregate(model: str = Query(default=None)):
    model_name = model or settings.default_model
    return aggregate_service.compute_aggregate(model_name, settings.output_path)
