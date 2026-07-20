from django.conf import settings
from django.core.mail import EmailMessage


def _field_lines(design_request):
    lines = [
        f"Template: {design_request.template.name} ({design_request.template.group.name})",
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
        elif field['type'] == 'choice_or_upload' and val:
            choices = ', '.join(val.get('choices', []))
            lines.append(f"{field['label']}: {choices or '(see attached upload)'}")
        elif val:
            lines.append(f"{field['label']}: {val}")

    if design_request.comments:
        lines.append(f"Comments: {design_request.comments}")
    return lines


def _send_with_attachments(subject, body, design_request, include_files=True, include_logo=False):
    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.ADMIN_NOTIFY_EMAIL],
    )
    if include_files:
        for f in design_request.files.all():
            f.file.open('rb')
            email.attach(f.file.name.split('/')[-1], f.file.read(), None)
            f.file.close()
    if include_logo and design_request.logo_file:
        design_request.logo_file.open('rb')
        email.attach(design_request.logo_file.name.split('/')[-1], design_request.logo_file.read(), None)
        design_request.logo_file.close()
    email.send(fail_silently=False)


def notify_admin_of_details(design_request):
    subject = f"New banner design request — order {design_request.order_number}"
    body = "\n".join(_field_lines(design_request))
    _send_with_attachments(subject, body, design_request, include_files=True)


def notify_admin_of_logo(design_request):
    subject = f"Logo received — order {design_request.order_number}"
    body = "\n".join(_field_lines(design_request) + ["Logo file attached."])
    _send_with_attachments(subject, body, design_request, include_files=False, include_logo=True)


def notify_client_reminder(design_request):
    subject = "Reminder: we still need your logo — Builders Signs"
    body = (
        f"Hi,\n\nWe're ready to start on your banner design (order {design_request.order_number}) "
        "but we're still waiting on your logo. Please upload it here:\n"
        "https://fproof.au/upload/builders-signs/\n\n"
        "Thanks,\nBuilders Signs"
    )
    EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[design_request.client_email],
    ).send(fail_silently=False)


def notify_admin_escalation(design_request):
    subject = f"Lapsed design request — order {design_request.order_number}"
    body = "\n".join(_field_lines(design_request) + [
        "", "Client has not uploaded a logo despite a reminder. Manual follow-up may be required.",
    ])
    EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.ADMIN_NOTIFY_EMAIL],
    ).send(fail_silently=False)
