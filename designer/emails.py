from django.conf import settings
from django.core.mail import EmailMessage


def _field_lines(design_request):
    template = design_request.template
    template_label = f"#{template.internal_number} — {template.name}" if template.internal_number else template.name
    lines = [
        f"Template: {template_label} ({template.group.name})",
        f"Order number: {design_request.order_number}",
        f"Client email: {design_request.client_email}",
        f"Background colour: {design_request.background_colour}",
    ]
    values = design_request.field_values
    if values.get('font_choice'):
        font_line = values['font_choice']
        if values.get('font_custom_text'):
            font_line += f" — {values['font_custom_text']}"
        lines.append(f"Font: {font_line}")

    for field in design_request.template.group.field_schema:
        key = field['key']
        val = values.get(key)
        if field['type'] == 'social' and val:
            platforms = ', '.join(val.get('platforms', []))
            lines.append(f"{field['label']}: {val.get('handle', '')} ({platforms})")
        elif field['type'] == 'choice' and val:
            choices = ', '.join(val.get('choices', []))
            if choices:
                lines.append(f"{field['label']}: {choices}")
        elif val:
            lines.append(f"{field['label']}: {val}")

    if design_request.comments:
        lines.append(f"Comments: {design_request.comments}")
    return lines


def notify_admin_of_details(design_request):
    subject = f"New banner design request — order {design_request.order_number}"
    body = "\n".join(_field_lines(design_request) + [
        "", "Logo (and any extra files) will come through the uploader separately.",
    ])
    EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.ADMIN_NOTIFY_EMAIL],
        reply_to=[design_request.client_email],
    ).send(fail_silently=False)


def notify_client_uploader_link(design_request, upload_url):
    subject = "Your logo upload link — Builders Signs"
    body = (
        f"Hi,\n\nThanks for your banner design details (order {design_request.order_number}). "
        "When you're ready, upload your logo (and anything else we'll need, like a different "
        f"association logo) here:\n\n{upload_url}\n\n"
        "We'll have your design with you within 4 hours of receiving it.\n\nThanks,\nBuilders Signs"
    )
    EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[design_request.client_email],
        reply_to=[settings.ADMIN_NOTIFY_EMAIL],
    ).send(fail_silently=False)


def notify_admin_of_upload(design_request, files):
    """files: list of dicts with 'filename' and 'dropbox_link'."""
    subject = f"Logo received — order {design_request.order_number}"
    file_lines = [
        f"- {f.get('filename', '')}" + (f" — {f['dropbox_link']}" if f.get('dropbox_link') else '')
        for f in files
    ]
    body = "\n".join(_field_lines(design_request) + ["", "Files uploaded:"] + file_lines)
    EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.ADMIN_NOTIFY_EMAIL],
        reply_to=[design_request.client_email],
    ).send(fail_silently=False)
