from celery import shared_task
from .models import FileUploadTracking
from .processors.user_processor import process_user_csv
from .processors.store_processor import process_store_csv
from .processors.mapping_processor import process_mapping_csv


@shared_task
def process_uploaded_file(tracking_id):
    
    tracking = FileUploadTracking.objects.get(id=tracking_id)

    upload_type = tracking.upload_type
    
    try:
        if upload_type == "users":
            process_user_csv(tracking)

        elif upload_type == "stores":
            process_store_csv(tracking)

        elif upload_type == "mapping":
            process_mapping_csv(tracking)

    except Exception as e:
        tracking.status = "COMPLETED"
        tracking.result_message = str(e)
        tracking.save()