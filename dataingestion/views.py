from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import FileUploadTracking
from .tasks import process_uploaded_file

class DataIngestionAPIView(APIView):
    def post(self, request):

        file_obj = request.FILES.get("file")
        upload_type = request.data.get("upload_type")
       
        if not file_obj:
            return Response(
                {"error": "File is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if upload_type not in ["users", "stores", "mapping"]:
            return Response(
                {"error": "Invalid upload_type"},
                status=status.HTTP_400_BAD_REQUEST
            )
        tracking = FileUploadTracking.objects.create(
            file=file_obj,
            status=FileUploadTracking.Status.PROCESSING,
            upload_type=upload_type,
            result_message=f"{upload_type} upload started"
        )

        process_uploaded_file.delay(tracking.id)

        return Response({
            "message": "File uploaded successfully",
            "tracking_id": tracking.id,
            "status": tracking.status
        }, status=status.HTTP_201_CREATED)
    
class WorkerTaskStatus(APIView):
    def get(self, request):
        
        upload_type = request.GET.get("upload_type")
        
        if upload_type not in ["users", "stores", "mapping"]:
            return Response(
                {"error": "Invalid upload_type"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tracking = FileUploadTracking.objects.filter(
            upload_type=upload_type
        ).order_by("-created_at").first()
        
        if not tracking:
            return Response(
                {"error": "No upload found for this type"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({
            "status": tracking.status,
            "success_count": tracking.success_count,
            "failure_count": tracking.failure_count,
            "created_at": tracking.created_at,
            "completed_at": tracking.completed_at,
            # "error_file": request.build_absolute_uri(tracking.error_file.url) if tracking.error_file else None,
            "error_file": tracking.error_file.url if tracking.error_file else None,
        }, status=status.HTTP_200_OK)
        
