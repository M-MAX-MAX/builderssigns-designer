import uuid

from django.db import models


class TemplateGroup(models.Model):
    """A tier of templates that all share the same set of required fields
    (e.g. 'Logo only' vs 'Logo + Contact + Builders No.')."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    order = models.PositiveIntegerField(default=0)

    # Group-specific extra fields rendered on step 2, on top of the universal
    # fields (email, order number, colour, font, comments) every group gets.
    # e.g. [{"key": "phone", "label": "Phone Number", "type": "text", "required": True}, ...]
    # Supported types: text, url, social, choice
    field_schema = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Template(models.Model):
    group = models.ForeignKey(TemplateGroup, on_delete=models.PROTECT, related_name='templates')
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    svg_asset = models.FileField(upload_to='templates/svg/')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class DesignRequest(models.Model):
    class Status(models.TextChoices):
        DETAILS_SUBMITTED = 'details_submitted', 'Details submitted'
        LOGO_UPLOADED = 'logo_uploaded', 'Logo uploaded'
        COMPLETE = 'complete', 'Complete'

    # Opaque identifier for the upload page link (emailed to clients who
    # defer, so it has to work without relying on their session).
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    template = models.ForeignKey(Template, on_delete=models.PROTECT, related_name='design_requests')
    client_email = models.EmailField()
    order_number = models.CharField(max_length=100)

    # All step-2 field answers, keyed by the group's field_schema keys.
    field_values = models.JSONField(default=dict, blank=True)
    background_colour = models.CharField(max_length=20, blank=True)
    comments = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DETAILS_SUBMITTED)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_number} — {self.client_email} ({self.template.name})"


class UploadedFile(models.Model):
    """A logo (or extra file, e.g. a custom association logo) uploaded to
    Dropbox for a DesignRequest via the internal uploader."""

    design_request = models.ForeignKey(DesignRequest, on_delete=models.CASCADE, related_name='uploaded_files')
    filename = models.CharField(max_length=300)
    dropbox_path = models.CharField(max_length=500)
    dropbox_link = models.URLField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at']

    def __str__(self):
        return self.filename
