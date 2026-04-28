from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from ..security import get_password_hash
from .auth import get_current_user, require_admin
import pandas as pd
import io
from typing import Dict, Any, List, Type, Union
from pydantic import ValidationError

router = APIRouter(prefix="/bulk", tags=["bulk", "admin"])

# Mapping from entity name to model and schema for creation
ENTITY_MAP: Dict[str, Dict[str, Any]] = {
    "clients": {
        "model": models.Client,
        "schema": schemas.ClientCreate,
    },
    "collaborators": {
        "model": models.User,  # Note: collaborators are users with role collaborator
        "schema": schemas.UserCreate,  # We'll handle password and role specially
    },
    # Add more entities as needed
}

def get_entity_info(entity: str):
    info = ENTITY_MAP.get(entity)
    if not info:
        raise HTTPException(status_code=404, detail=f"Entity '{entity}' not supported for bulk upload")
    return info

def get_example_value(field_name: str, field_type: Any) -> Any:
    """
    Generate an example value for a given field name and type.
    This is used to fill the template's example row.
    """
    # Handle common field names
    if field_name.lower() == "email":
        return "example@example.com"
    if field_name.lower() in ["cuit", "cuil"]:
        return "20-12345678-9"
    if field_name.lower() in ["name", "last_name", "first_name"]:
        return "Juan"
    if field_name.lower() in ["password"]:
        return "password123"
    if field_name.lower() in ["role"]:
        return "colaborador"
    if field_name.lower() in ["status"]:
        return "active"  # or pending? We'll use active for example, but the schema default may be pending.
    # Handle types
    if field_type == str or (hasattr(field_type, '__origin__') and field_type.__origin__ is str):
        return "example text"
    if field_type == int or (hasattr(field_type, '__origin__') and field_type.__origin__ is int):
        return 42
    if field_type == float or (hasattr(field_type, '__origin__') and field_type.__origin__ is float):
        return 3.14
    if field_type == bool or (hasattr(field_type, '__origin__') and field_type.__origin__ is bool):
        return True
    # For datetime, date, etc., we return a string example
    if "date" in str(field_type).lower():
        return "2026-01-01"
    if "datetime" in str(field_type).lower():
        return "2026-01-01T10:00:00"
    # Fallback
    return "example"

@router.get("/template/{entity}")
def get_template(entity: str, current_user: models.User = Depends(require_admin)):
    """
    Generate and return an Excel template for the given entity.
    The template will have the column headers and one row of example data.
    """
    info = get_entity_info(entity)
    schema: Type[schemas.BaseModel] = info["schema"]
    
    # Get the schema fields
    field_names = list(schema.model_fields.keys())
    
    # Build a dictionary of example values for each field
    example_data = {}
    for field_name in field_names:
        field = schema.model_fields[field_name]
        # Try to get the type; if it's a Union, we take the first non-None type (simplistic)
        field_type = field.annotation
        # Handle Optional[X] which is Union[X, None]
        if hasattr(field_type, '__origin__') and field_type.__origin__ is Union:
            args = field_type.__args__
            # Take the first non-None type
            non_none_args = [arg for arg in args if arg is not type(None)]
            if non_none_args:
                field_type = non_none_args[0]
            else:
                field_type = str  # fallback
        example_data[field_name] = get_example_value(field_name, field_type)
    
    # Create a DataFrame with the column headers and one row of example data.
    df = pd.DataFrame([example_data])
    
    # Convert to Excel in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={entity}_template.xlsx"}
    )

@router.post("/upload/{entity}")
async def upload_bulk(
    entity: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """
    Upload an Excel or CSV file, validate each row against the entity's schema,
    and insert the valid rows into the database.
    """
    info = get_entity_info(entity)
    Model: Type[models.Base] = info["model"]
    Schema: Type[schemas.BaseModel] = info["schema"]
    
    # Read the file
    contents = await file.read()
    try:
        if file.filename.endswith('.xlsx') or file.filename.endswith('.xls'):
            df = pd.read_excel(io.BytesIO(contents))
        elif file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Use .xlsx, .xls, or .csv")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
    
    # We'll validate each row
    errors = []
    valid_objects = []
    
    for index, row in df.iterrows():
        # Convert the row to a dictionary, handling NaN (which becomes None in Pydantic if the field is optional)
        row_dict = {}
        for col in df.columns:
            val = row[col]
            if pd.isna(val):
                row_dict[col] = None
            else:
                row_dict[col] = val
        
        try:
            # Validate the row with the schema
            validated = Schema(**row_dict)
            # Convert the validated schema to a dictionary for the model
            # We need to exclude any fields that are not in the model (if any) and handle special cases.
            model_columns = [c.key for c in Model.__table__.columns]
            data_for_model = {k: v for k, v in validated.model_dump().items() if k in model_columns}
            
            # Special handling for collaborators: hash password and set role to collaborator.
            if entity == "collaborators":
                # Hash the password if provided
                if "password" in data_for_model and data_for_model["password"]:
                    data_for_model["password_hash"] = get_password_hash(data_for_model["password"])
                    # Remove the plain password from the data for model because we don't store it.
                    data_for_model.pop("password", None)
                else:
                    # If no password provided, we cannot create a user. We'll add an error.
                    errors.append({
                        "row": index + 2,  # +2 because index is 0-based and we have a header row
                        "field": "password",
                        "message": "Password is required for collaborator creation",
                        "value": None
                    })
                    continue  # Skip this row
                # Set the role to collaborator (ignore any role provided in the template)
                data_for_model["role"] = models.UserRole.colaborador
            
            # Create the model instance
            obj = Model(**data_for_model)
            valid_objects.append(obj)
        except ValidationError as e:
            # Pydantic validation error
            for error in e.errors():
                errors.append({
                    "row": index + 2,  # +2 for header row and 0-based index
                    "field": ".".join(str(loc) for loc in error["loc"]),
                    "message": error["msg"],
                    "value": error.get("input")
                })
        except Exception as e:
            # Other errors
            errors.append({
                "row": index + 2,
                "field": "",
                "message": str(e),
                "value": None
            })
    
    if errors:
        # If there are any errors, we do not insert any objects and return the errors.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "detail": "Validation errors",
                "errors": errors
            }
        )
    
    # If there are valid objects, insert them in bulk.
    if valid_objects:
        try:
            db.add_all(valid_objects)
            db.commit()
            # Refresh the objects to get their IDs and any other database-generated fields.
            for obj in valid_objects:
                db.refresh(obj)
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error inserting data: {str(e)}"
            )
    
    return {
        "inserted": len(valid_objects),
        "message": f"Successfully inserted {len(valid_objects)} {entity} records."
    }