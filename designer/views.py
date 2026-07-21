import json
import os

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from . import emails
from .dropbox_service import upload_to_dropbox
from .forms import FONT_OPTIONS, DetailsForm
from .models import DesignRequest, Template, TemplateGroup, UploadedFile

ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'ai', 'eps', 'svg', 'zip', 'tif', 'tiff', 'psd'}
MAX_FILE_MB = 50


def template_gallery(request):
    groups = TemplateGroup.objects.prefetch_related('templates').all()
    return render(request, 'designer/step1_gallery.html', {'groups': groups})


def select_template(request, slug):
    template = get_object_or_404(Template, slug=slug, is_active=True)
    request.session['template_id'] = template.id
    request.session.pop('design_request_id', None)
    return redirect('designer:details')


def details(request):
    template_id = request.session.get('template_id')
    if not template_id:
        return redirect('designer:gallery')
    template = get_object_or_404(Template, id=template_id)
    group = template.group

    if request.method == 'POST':
        form = DetailsForm(request.POST, group=group)
        if form.is_valid():
            cleaned = form.cleaned_data
            design_request = DesignRequest.objects.create(
                template=template,
                client_email=cleaned['client_email'],
                order_number=cleaned['order_number'],
                background_colour=cleaned['background_colour'],
                comments=cleaned.get('comments', ''),
                field_values=form.extract_field_values(cleaned),
            )
            emails.notify_admin_of_details(design_request)
            request.session['design_request_id'] = design_request.id

            upload_url = request.build_absolute_uri(
                reverse('designer:upload_page', args=[design_request.token])
            )
            if request.POST.get('upload_choice') == 'later':
                emails.notify_client_uploader_link(design_request, upload_url)
                return redirect('designer:upload_later')
            return redirect('designer:upload_page', token=design_request.token)
    else:
        form = DetailsForm(group=group)

    return render(request, 'designer/step2_details.html', {
        'form': form, 'template': template, 'font_options': FONT_OPTIONS,
    })


def upload_later(request):
    design_request_id = request.session.get('design_request_id')
    if not design_request_id:
        return redirect('designer:gallery')
    design_request = get_object_or_404(DesignRequest, id=design_request_id)
    return render(request, 'designer/upload_later.html', {'design_request': design_request})


@ensure_csrf_cookie
def upload_page(request, token):
    design_request = get_object_or_404(DesignRequest, token=token)
    return render(request, 'designer/upload.html', {
        'design_request': design_request,
        'allowed_types': ', '.join(sorted(ALLOWED_EXTENSIONS)).upper(),
        'max_file_mb': MAX_FILE_MB,
    })


@require_POST
def upload_file(request, token):
    design_request = get_object_or_404(DesignRequest, token=token)

    if 'file' not in request.FILES:
        return JsonResponse({'success': False, 'message': 'No file received.'}, status=400)

    f = request.FILES['file']
    ext = os.path.splitext(f.name)[1].lstrip('.').lower()

    if ext not in ALLOWED_EXTENSIONS:
        return JsonResponse({
            'success': False, 'message': f'{f.name}: .{ext} files are not accepted.',
        }, status=400)

    max_bytes = MAX_FILE_MB * 1024 * 1024
    if f.size > max_bytes:
        return JsonResponse({
            'success': False, 'message': f'{f.name}: Exceeds the {MAX_FILE_MB}MB size limit.',
        }, status=400)

    try:
        path, link = upload_to_dropbox(f, design_request.order_number, f.name)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Upload failed: {str(e)}'}, status=500)

    return JsonResponse({'success': True, 'filename': f.name, 'dropbox_path': path, 'dropbox_link': link})


@require_POST
def upload_submit(request, token):
    design_request = get_object_or_404(DesignRequest, token=token)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=400)

    message = data.get('message', '').strip()
    files = data.get('files', [])

    if not files:
        return JsonResponse({'success': False, 'message': 'No files were uploaded.'}, status=400)

    for file_data in files:
        UploadedFile.objects.create(
            design_request=design_request,
            filename=file_data.get('filename', ''),
            dropbox_path=file_data.get('dropbox_path', ''),
            dropbox_link=file_data.get('dropbox_link', ''),
        )

    if message:
        design_request.comments = (design_request.comments + '\n\n' if design_request.comments else '') \
            + f'Upload note: {message}'
    design_request.status = DesignRequest.Status.LOGO_UPLOADED
    design_request.save()

    emails.notify_admin_of_upload(design_request, files)

    return JsonResponse({
        'success': True,
        'redirect_url': reverse('designer:upload_thanks', args=[token]),
    })


def upload_thanks(request, token):
    design_request = get_object_or_404(DesignRequest, token=token)
    return render(request, 'designer/upload_thanks.html', {'design_request': design_request})
