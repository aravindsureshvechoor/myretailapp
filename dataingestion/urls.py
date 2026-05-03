from django.urls import path
from .views import DataIngestionAPIView, WorkerTaskStatus

urlpatterns = [
    path("dataingestion/", DataIngestionAPIView.as_view()),
    path("workertaskstatus/", WorkerTaskStatus.as_view()),
]