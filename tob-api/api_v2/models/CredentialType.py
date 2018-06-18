from django.db import models
from django.utils import timezone
from django.contrib.postgres import fields as contrib

from auditable.models import Auditable

from .Issuer import Issuer
from .Schema import Schema


class CredentialType(Auditable):
    schema = models.ForeignKey(Schema, related_name="credential_types")
    issuer = models.ForeignKey(Issuer, related_name="credential_types")
    description = models.TextField(blank=True, null=True)
    source_claim = models.TextField()
    processor_config = contrib.JSONField(blank=True, null=True)

    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(blank=True, null=True)

    class Meta:
        db_table = "credential_type"
        unique_together = (("schema", "issuer"),)