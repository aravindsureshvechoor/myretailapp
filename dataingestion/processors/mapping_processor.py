import csv
import pandas as pd
from django.db import transaction
from django.utils import timezone
from datetime import datetime

from dataingestion.models import User, Store, PermanentJourneyPlan, RowError, FileUploadTracking
from dataingestion.processors.user_processor import generate_error_csv, normalize_bool


def validate_date(value):
    try:
        datetime.strptime(str(value).strip(), "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


def process_mapping_csv(tracking: FileUploadTracking):
    try:
        file_path = tracking.file.path

        existing_users = set(User.objects.values_list("username", flat=True))
        existing_stores = set(Store.objects.values_list("store_id", flat=True))
        existing_combinations = set(
            PermanentJourneyPlan.objects.values_list("user__username", "store__store_id", "date")
        )

        error_buffer = []
        mappings_to_create = []
        seen_in_csv = set()

        success_count = 0
        failure_count = 0
        row_number = 1
        chunk_size = 5000

        for chunk in pd.read_csv(file_path, chunksize=chunk_size):

            for idx, row in chunk.iterrows():
                row_number += 1

                username = str(row.get("username", "")).strip()
                store_id = str(row.get("store_id", "")).strip()
                date_str = str(row.get("date", "")).strip()
                is_active = normalize_bool(row.get("is_active"))

                row_errors = []

                if not username:
                    row_errors.append(("username", "Username missing"))
                elif username not in existing_users:
                    row_errors.append(("username", "User not found"))

                if not store_id:
                    row_errors.append(("store_id", "Store ID missing"))
                elif store_id not in existing_stores:
                    row_errors.append(("store_id", "Store not found"))

                if not date_str or date_str.lower() == "nan":
                    row_errors.append(("date", "Date missing"))
                elif not validate_date(date_str):
                    row_errors.append(("date", "Invalid date format, expected YYYY-MM-DD"))

                if row_errors:
                    failure_count += 1
                    for col, reason in row_errors:
                        error_buffer.append(
                            RowError(
                                upload=tracking,
                                row_number=row_number,
                                column_name=col,
                                reason=reason
                            )
                        )
                    continue

                parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                combination = (username, store_id, parsed_date)

                if combination in existing_combinations or combination in seen_in_csv:
                    failure_count += 1
                    error_buffer.append(
                        RowError(
                            upload=tracking,
                            row_number=row_number,
                            column_name="username/store_id/date",
                            reason="Duplicate mapping combination"
                        )
                    )
                    continue

                user_obj = User(username=username)
                store_obj = Store(store_id=store_id)

                user_obj = User.objects.only("id").get(username=username)
                store_obj = Store.objects.only("id").get(store_id=store_id)

                mapping_obj = PermanentJourneyPlan(
                    user=user_obj,
                    store=store_obj,
                    date=parsed_date,
                    is_active=is_active,
                )

                mappings_to_create.append(mapping_obj)
                seen_in_csv.add(combination)
                success_count += 1

        with transaction.atomic():
            if mappings_to_create:
                PermanentJourneyPlan.objects.bulk_create(mappings_to_create)
            if error_buffer:
                RowError.objects.bulk_create(error_buffer)

        tracking.success_count = success_count
        tracking.failure_count = failure_count
        tracking.save()

        generate_error_csv(tracking)

        tracking.status = FileUploadTracking.Status.COMPLETED
        tracking.completed_at = timezone.now()
        tracking.save()

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        tracking.status = FileUploadTracking.Status.FILE_CORRUPTED
        tracking.save()