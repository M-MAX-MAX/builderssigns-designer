from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from . import emails
from .forms import DetailsForm, LogoDecisionForm
from .models import DesignRequest, DesignRequestFile, Template, TemplateGroup


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
        form = DetailsForm(request.POST, request.FILES, group=group)
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

            style_guide = cleaned.get('style_guide_upload')
            if style_guide:
                DesignRequestFile.objects.create(
                    design_request=design_request, field_key='style_guide_upload', file=style_guide
                )
            for field in group.field_schema:
                if field['type'] == 'choice_or_upload':
                    upload = cleaned.get(f"{field['key']}_upload")
                    if upload:
                        DesignRequestFile.objects.create(
                            design_request=design_request, field_key=field['key'], file=upload
                        )

            emails.notify_admin_of_details(design_request)
            request.session['design_request_id'] = design_request.id
            return redirect('designer:logo')
    else:
        form = DetailsForm(group=group)

    return render(request, 'designer/step2_details.html', {'form': form, 'template': template})


def logo(request):
    design_request_id = request.session.get('design_request_id')
    if not design_request_id:
        return redirect('designer:gallery')
    design_request = get_object_or_404(DesignRequest, id=design_request_id)

    if request.method == 'POST':
        form = LogoDecisionForm(request.POST, request.FILES)
        if form.is_valid():
            if form.cleaned_data['decision'] == LogoDecisionForm.NOW:
                design_request.logo_file = form.cleaned_data['logo_file']
                design_request.status = DesignRequest.Status.LOGO_UPLOADED
                design_request.save()
                emails.notify_admin_of_logo(design_request)
            else:
                design_request.status = DesignRequest.Status.LOGO_DEFERRED
                design_request.logo_deferred_at = timezone.now()
                design_request.save()
            return redirect('designer:done')
    else:
        form = LogoDecisionForm()

    return render(request, 'designer/step3_logo.html', {'form': form, 'design_request': design_request})


def done(request):
    design_request_id = request.session.get('design_request_id')
    design_request = DesignRequest.objects.filter(id=design_request_id).first()
    request.session.pop('template_id', None)
    request.session.pop('design_request_id', None)
    return render(request, 'designer/step4_done.html', {'design_request': design_request})
