import csv
import re
import pandas as pd
from django.db import transaction, IntegrityError
from django.utils import timezone

from dataingestion.models import (
    Store, StoreBrand, StoreType, City, State, Country, Region,
    RowError, FileUploadTracking
)
from dataingestion.processors.user_processor import generate_error_csv


def validate_number(value):
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def get_or_create_lookup(model, name):
    if not name or str(name).strip().lower() == "nan":
        return None
    obj, _ = model.objects.get_or_create(name=str(name).strip())
    return obj


def process_store_csv(tracking: FileUploadTracking):
    
    file_path = tracking.file.path

    error_buffer = []
    success_count = 0
    failure_count = 0
    row_number = 1
    chunk_size = 5

    for chunk in pd.read_csv(file_path, chunksize=chunk_size):

        stores_to_create = []

    #     existing_store_ids = set(
    #         Store.objects.filter(
    #             store_id__in=chunk["store_id"].tolist()
    #         ).values_list("store_id", flat=True)
    #     )

    #     for idx, row in chunk.iterrows():
    #         row_number += 1
    #         print(row_number)
    #         store_id          = str(row.get("store_id", "")).strip()
    #         store_external_id = str(row.get("store_external_id", "") or "").strip()
    #         name              = str(row.get("name", "")).strip()
    #         title             = str(row.get("title", "")).strip()
    #         store_brand       = str(row.get("store_brand", "") or "").strip()
    #         store_type        = str(row.get("store_type", "") or "").strip()
    #         city              = str(row.get("city", "") or "").strip()
    #         state             = str(row.get("state", "") or "").strip()
    #         country           = str(row.get("country", "") or "").strip()
    #         region            = str(row.get("region", "") or "").strip()
    #         latitude          = row.get("latitude")
    #         longitude         = row.get("longitude")
            
    #         row_errors = []

    #         if not store_id:
    #             row_errors.append(("store_id", "Store ID missing"))
    #         elif store_id in existing_store_ids:
    #             row_errors.append(("store_id", "Duplicate store_id"))

    #         if not name:
    #             row_errors.append(("name", "Name is missing"))

    #         if not title:
    #             row_errors.append(("title", "Title is missing"))

    #         if latitude and not validate_number(latitude):
    #             row_errors.append(("latitude", "Invalid latitude value"))

    #         if longitude and not validate_number(longitude):
    #             row_errors.append(("longitude", "Invalid longitude value"))
            
    #         if row_errors:
    #             failure_count += 1
    #             for col, reason in row_errors:
    #                 error_buffer.append(
    #                     RowError(
    #                         upload=tracking,
    #                         row_number=row_number,
    #                         column_name=col,
    #                         reason=reason
    #                     )
    #                 )
    #             continue

    #         store_brand_obj = get_or_create_lookup(StoreBrand, store_brand)
    #         store_type_obj  = get_or_create_lookup(StoreType, store_type)
    #         city_obj        = get_or_create_lookup(City, city)
    #         state_obj       = get_or_create_lookup(State, state)
    #         country_obj     = get_or_create_lookup(Country, country)
    #         region_obj      = get_or_create_lookup(Region, region)

    #         store_obj = Store(
    #             store_id=store_id,
    #             store_external_id=store_external_id,
    #             name=name,
    #             title=title,
    #             store_brand=store_brand_obj,
    #             store_type=store_type_obj,
    #             city=city_obj,
    #             state=state_obj,
    #             country=country_obj,
    #             region=region_obj,
    #             latitude=float(latitude) if latitude and validate_number(latitude) else 0.0,
    #             longitude=float(longitude) if longitude and validate_number(longitude) else 0.0,
    #         )

    #         stores_to_create.append(store_obj)
    #         existing_store_ids.add(store_id)
    #         success_count += 1
        

    #     with transaction.atomic():
    #         if stores_to_create:
    #             Store.objects.bulk_create(stores_to_create)
    #         if error_buffer:
    #             RowError.objects.bulk_create(error_buffer)

    #     tracking.success_count += success_count
    #     tracking.failure_count += failure_count
    #     tracking.save()

    #     error_buffer = []
    #     success_count = 0
    #     failure_count = 0

    # generate_error_csv(tracking)

    # tracking.status = FileUploadTracking.Status.COMPLETED
    # tracking.completed_at = timezone.now()
    # tracking.save()