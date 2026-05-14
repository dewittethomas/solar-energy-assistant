from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from responses.data_upload_result import CsvColumnsResult, DataUploadResult
from services.data_upload_service import DataUploadService
from services.dependencies import get_data_upload_service

router = APIRouter(prefix='/data', tags=['data'])

DataUploadServiceDep = Annotated[
    DataUploadService,
    Depends(get_data_upload_service)
]

@router.post(
    '/columns',
    operation_id='get_csv_columns',
    response_model=CsvColumnsResult
)
async def get_csv_columns(
    data_upload_service: DataUploadServiceDep,
    file: UploadFile = File(...)
) -> CsvColumnsResult:
    try:
        return data_upload_service.get_csv_columns(
            filename=file.filename or 'upload.csv',
            contents=await file.read()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Could not read CSV columns: {str(e)}'
        )

@router.post(
    '/upload',
    operation_id='upload_solar_data',
    response_model=DataUploadResult
)
async def upload_solar_data(
    data_upload_service: DataUploadServiceDep,
    file: list[UploadFile] = File(...),
    installation_id: str = Form(...),
    mapping: str | None = Form(None),
    date_column: str | None = Form(None),
    time_column: str | None = Form(None),
    measurement_column: str | None = Form(None),
    unit: str | None = Form(None)
) -> DataUploadResult:
    try:
        mapping_payload = mapping or {
            'date_column': date_column,
            'time_column': time_column,
            'measurement_column': measurement_column,
            'unit': unit
        }
        uploads = [
            (upload.filename or f'upload-{index}.csv', await upload.read())
            for index, upload in enumerate(file, start=1)
        ]

        return data_upload_service.process_csv_uploads(
            uploads=uploads,
            installation_id=installation_id,
            mapping=mapping_payload
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Upload processing failed: {str(e)}'
        )
