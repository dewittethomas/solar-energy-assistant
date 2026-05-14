from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile

from responses.data_upload_result import CsvColumnsResult, DataUploadResult
from responses.dataset_result import DatasetResult
from services.dataset_service import DatasetService
from services.data_upload_service import DataUploadService
from services.dependencies import get_data_upload_service, get_dataset_service

router = APIRouter(prefix='/datasets', tags=['datasets'])

DataUploadServiceDep = Annotated[
    DataUploadService,
    Depends(get_data_upload_service)
]
DatasetServiceDep = Annotated[
    DatasetService,
    Depends(get_dataset_service)
]

@router.get(
    '',
    operation_id='list_datasets',
    response_model=list[DatasetResult]
)
async def list_datasets(
    dataset_service: DatasetServiceDep,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
) -> list[DatasetResult]:
    return dataset_service.list_datasets(limit=limit, offset=offset)

@router.get(
    '/{dataset_id}',
    operation_id='get_dataset',
    response_model=DatasetResult
)
async def get_dataset(
    dataset_id: str,
    dataset_service: DatasetServiceDep
) -> DatasetResult:
    dataset = dataset_service.get_dataset(dataset_id)

    if not dataset:
        raise HTTPException(status_code=404, detail='Dataset not found')

    return dataset

@router.post(
    '',
    operation_id='create_dataset',
    response_model=DataUploadResult
)
async def create_dataset(
    data_upload_service: DataUploadServiceDep,
    file: list[UploadFile] = File(...),
    installation_id: str = Form(...),
    mapping: str | None = Form(None),
    date_column: str | None = Form(None),
    time_column: str | None = Form(None),
    measurement_column: str | None = Form(None),
    unit: str | None = Form(None)
) -> DataUploadResult:
    return await _process_upload(
        data_upload_service,
        file,
        installation_id,
        mapping,
        date_column,
        time_column,
        measurement_column,
        unit
    )

@router.post(
    '/inspect',
    operation_id='inspect_dataset',
    response_model=CsvColumnsResult
)
async def inspect_dataset(
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

async def _process_upload(
    data_upload_service: DataUploadService,
    files: list[UploadFile],
    installation_id: str,
    mapping: str | None,
    date_column: str | None,
    time_column: str | None,
    measurement_column: str | None,
    unit: str | None
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
            for index, upload in enumerate(files, start=1)
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
