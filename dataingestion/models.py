from django.db import models
import os
from datetime import datetime


def upload_csv_path(instance, filename):
    today = datetime.now().strftime("%Y/%m/%d")
    return os.path.join(
        "uploads",
        "csv",
        today,
        filename
    )


def upload_error_path(instance, filename):
    today = datetime.now().strftime("%Y/%m/%d")
    return os.path.join(
        today,
        filename
    )

class LookupBase(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class StoreBrand(LookupBase):
    class Meta:
        db_table = "store_brands"


class StoreType(LookupBase):
    class Meta:
        db_table = "store_types"


class City(LookupBase):
    class Meta:
        db_table = "cities"


class State(LookupBase):
    class Meta:
        db_table = "states"


class Country(LookupBase):
    class Meta:
        db_table = "countries"


class Region(LookupBase):
    class Meta:
        db_table = "regions"


class Store(models.Model):
    store_id          = models.CharField(max_length=255, unique=True)
    store_external_id = models.CharField(max_length=255, default="", blank=True)
    name              = models.CharField(max_length=255)
    title             = models.CharField(max_length=255)
    store_brand       = models.ForeignKey(StoreBrand, null=True, blank=True, on_delete=models.SET_NULL)
    store_type        = models.ForeignKey(StoreType, null=True, blank=True, on_delete=models.SET_NULL)
    city              = models.ForeignKey(City, null=True, blank=True, on_delete=models.SET_NULL)
    state             = models.ForeignKey(State, null=True, blank=True, on_delete=models.SET_NULL)
    country           = models.ForeignKey(Country, null=True, blank=True, on_delete=models.SET_NULL)
    region            = models.ForeignKey(Region, null=True, blank=True, on_delete=models.SET_NULL)
    latitude          = models.FloatField(default=0.0)
    longitude         = models.FloatField(default=0.0)
    created_on        = models.DateTimeField(auto_now_add=True)
    modified_on       = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "stores"

    def __str__(self):
        return self.store_id


class User(models.Model):
    username     = models.CharField(max_length=255, unique=True)
    first_name   = models.CharField(max_length=255, blank=True)
    last_name    = models.CharField(max_length=255, blank=True)
    email        = models.EmailField()
    user_type    = models.IntegerField()
    phone_number = models.CharField(max_length=20)
    supervisor   = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    is_active    = models.BooleanField(default=True)
    created_on   = models.DateTimeField(auto_now_add=True)
    modified_on  = models.DateTimeField(auto_now=True)
    

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.username

class PermanentJourneyPlan(models.Model):
    user        = models.ForeignKey("User", on_delete=models.CASCADE)
    store       = models.ForeignKey("Store", on_delete=models.CASCADE)
    date        = models.DateField(null=True, blank=True)
    is_active   = models.BooleanField(default=True)
    created_on  = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table        = "permanent_journey_plans"
        unique_together = ("user", "store", "date")

    def __str__(self):
        return f"{self.user} - {self.store} - {self.date}"

class FileUploadTracking(models.Model):

    class UploadType(models.TextChoices):
        USERS   = "users"
        STORES  = "stores"
        MAPPING = "mapping"

    class Status(models.TextChoices):
        PROCESSING     = "PROCESSING"
        COMPLETED      = "COMPLETED"
        FILE_CORRUPTED = "FILE_CORRUPTED"

    file                     = models.FileField(upload_to=upload_csv_path)
    status                   = models.CharField(max_length=20, choices=Status.choices, default=Status.PROCESSING)
    upload_type              = models.CharField(max_length=20, choices=UploadType.choices, default="")
    total_rows               = models.PositiveIntegerField(default=0)
    success_count            = models.PositiveIntegerField(default=0)
    failure_count            = models.PositiveIntegerField(default=0)
    error_file               = models.FileField(upload_to=upload_error_path, null=True, blank=True)
    error_threshold_exceeded = models.BooleanField(default=False)
    result_message           = models.TextField(null=True, blank=True)
    created_at               = models.DateTimeField(auto_now_add=True)
    completed_at             = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.id} - {self.status}"


class RowError(models.Model):
    upload      = models.ForeignKey(FileUploadTracking, on_delete=models.CASCADE)
    row_number  = models.PositiveIntegerField()
    column_name = models.CharField(max_length=255)
    reason      = models.TextField()
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Row {self.row_number} - {self.column_name}"