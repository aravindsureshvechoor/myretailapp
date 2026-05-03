import pandas as pd
import re
import csv
from django.db import transaction
from django.utils import timezone

from dataingestion.models import User, RowError, FileUploadTracking

EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

def validate_email(email):
    return bool(email and EMAIL_REGEX.match(email))


def validate_phone(phone):
    return bool(phone and re.fullmatch(r"\+?\d{10,15}", str(phone)))


def normalize_bool(value):
    return str(value).strip().lower() == "true"


def validate_user_type(value):
    try:
        return int(value) in [1, 2, 3, 7]
    except:
        return False
    

def process_user_csv(tracking: FileUploadTracking):
    try:
        file_path = tracking.file.path


        error_buffer = []
        success_count = 0
        failure_count = 0
        row_number = 1
        chunk_size = 5000

        for chunk in pd.read_csv(file_path, chunksize=chunk_size):
            existing_users = set(
                User.objects.filter(
                    username__in=chunk["username"].tolist()
                ).values_list("username", flat=True)
            )
            users_to_create = []
            supervisor_map = {}

            for idx, row in chunk.iterrows():
                row_number += 1
                username = str(row.get("username", "")).strip()

                first_name = str(row.get("first_name", "") or "")
                last_name = str(row.get("last_name", "") or "")

                email = str(row.get("email", "")).strip()
                user_type = row.get("user_type")
                phone = str(row.get("phone_number", "")).strip()
                supervisor_username = str(row.get("supervisor_username", "")).strip()
                is_active = normalize_bool(row.get("is_active"))
                
                row_errors = []

                if not username:
                    row_errors.append(("username", "Username missing"))
                elif username in existing_users:
                    row_errors.append(("username", "Duplicate username"))

                if not validate_email(email):
                    row_errors.append(("email", "Invalid email format"))

                if not validate_user_type(user_type):
                    row_errors.append(("user_type", "Invalid user_type"))

                if not validate_phone(phone):
                    row_errors.append(("phone_number", "Invalid phone number"))
                
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
                print(f"{len(error_buffer)} error buffer length")
                user_obj = User(
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    user_type=int(user_type),
                    phone_number=phone,
                    supervisor=None,
                    is_active=is_active
                )

                users_to_create.append(user_obj)
                existing_users.add(username)
                success_count += 1
                print(f"{len(users_to_create)}")
                if supervisor_username and supervisor_username.lower() != "nan":
                    supervisor_map[username] = supervisor_username
            
            with transaction.atomic():
                if users_to_create:
                    User.objects.bulk_create(users_to_create)

                if supervisor_map:
                    all_supervisor_usernames = set(supervisor_map.values())
                    supervisors = User.objects.only('id', 'username').filter(username__in=all_supervisor_usernames)
                    supervisor_lookup = {s.username: s for s in supervisors}

                    users_needing_supervisor = User.objects.filter(username__in=supervisor_map.keys())
                    for user in users_needing_supervisor:
                        sup_username = supervisor_map.get(user.username)
                        user.supervisor = supervisor_lookup.get(sup_username)

                    User.objects.bulk_update(users_needing_supervisor, ['supervisor'])

                if error_buffer:
                    RowError.objects.bulk_create(error_buffer)

            tracking.success_count += success_count
            tracking.failure_count += failure_count
            tracking.save()

            error_buffer = []
            success_count = 0
            failure_count = 0

        generate_error_csv(tracking)

        tracking.status = FileUploadTracking.Status.COMPLETED
        tracking.completed_at = timezone.now()
        tracking.save()
    except Exception as e:
        print(str(e))

def generate_error_csv(tracking):

    errors = RowError.objects.filter(upload=tracking)

    file_path = f"/tmp/error_{tracking.id}.csv"

    with open(file_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["row_number", "column_name", "reason"])

        for e in errors:
            writer.writerow([e.row_number, e.column_name, e.reason])

    tracking.error_file.save(
        f"error_{tracking.id}.csv",
        open(file_path, "rb")
    )