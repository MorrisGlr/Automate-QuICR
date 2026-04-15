from fastapi import APIRouter, HTTPException, Query

from server.config import settings
from server.models import PatientDetail, PatientSummary
from server.services import patient_service

router = APIRouter()


@router.get("/models", response_model=list[str])
def get_models():
    return patient_service.list_models(settings.output_path)


@router.get("/patients", response_model=list[PatientSummary])
def list_patients(model: str = Query(default=None)):
    model_name = model or settings.default_model
    return patient_service.discover_patients(model_name, settings.output_path)


@router.get("/patients/{patient_id}", response_model=PatientDetail)
def get_patient(patient_id: str, model: str = Query(default=None)):
    model_name = model or settings.default_model
    detail = patient_service.get_patient_detail(
        patient_id, model_name, settings.output_path
    )
    if detail is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return detail
