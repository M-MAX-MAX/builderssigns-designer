from datetime import timedelta

from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from .models import DesignRequest, Product, Template, TemplateGroup, UploadedFile


def _image_preview(file_field, height):
    if not file_field:
        return '(no image)'
    return format_html(
        '<img src="{}" style="height:{}px; max-width:100%; object-fit:contain; '
        'border:1px solid #ddd; border-radius:6px; background:#fff;">',
        file_field.url, height,
    )


class TemplateGroupInline(admin.TabularInline):
    model = TemplateGroup
    extra = 1
    fields = ('name', 'slug', 'order')
    show_change_link = True


class TemplateInline(admin.TabularInline):
    model = Template
    extra = 1
    fields = ('svg_preview', 'internal_number', 'name', 'slug', 'svg_asset', 'order', 'is_active')
    readonly_fields = ('svg_preview',)

    @admin.display(description='Preview')
    def svg_preview(self, obj):
        return _image_preview(obj.svg_asset, 100)


class UploadedFileInline(admin.TabularInline):
    model = UploadedFile
    extra = 0
    readonly_fields = ('filename', 'dropbox_path', 'dropbox_link', 'uploaded_at')
    can_delete = False


class AwaitingLogoAgeFilter(admin.SimpleListFilter):
    title = 'awaiting logo age'
    parameter_name = 'awaiting_age'

    def lookups(self, request, model_admin):
        return [
            ('1', 'Submitted over 1 day ago'),
            ('3', 'Submitted over 3 days ago'),
            ('7', 'Submitted over 7 days ago'),
        ]

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        cutoff = timezone.now() - timedelta(days=int(self.value()))
        return queryset.filter(
            status=DesignRequest.Status.DETAILS_SUBMITTED, created_at__lte=cutoff
        )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'card_image_thumb', 'slug', 'order', 'is_active')
    readonly_fields = ('card_image_preview',)
    prepopulated_fields = {'slug': ('name',)}
    inlines = [TemplateGroupInline]

    @admin.display(description='Card image')
    def card_image_thumb(self, obj):
        return _image_preview(obj.card_image, 60)

    @admin.display(description='Card image preview')
    def card_image_preview(self, obj):
        return _image_preview(obj.card_image, 300)


@admin.register(TemplateGroup)
class TemplateGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'product', 'slug', 'order')
    list_filter = ('product',)
    prepopulated_fields = {'slug': ('name',)}
    inlines = [TemplateInline]


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ('thumb', 'name', 'internal_number', 'group', 'order', 'is_active')
    list_editable = ('internal_number',)
    list_filter = ('group__product', 'group', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('svg_preview',)

    @admin.display(description='Preview')
    def thumb(self, obj):
        return _image_preview(obj.svg_asset, 60)

    @admin.display(description='Preview')
    def svg_preview(self, obj):
        return _image_preview(obj.svg_asset, 400)


@admin.register(DesignRequest)
class DesignRequestAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'client_email', 'template', 'status', 'created_at')
    list_filter = ('status', 'template__group__product', 'template__group', AwaitingLogoAgeFilter)
    search_fields = ('order_number', 'client_email')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['mark_logo_received']
    inlines = [UploadedFileInline]

    @admin.action(description='Mark logo received (e.g. a client emailed it directly instead of using the uploader)')
    def mark_logo_received(self, request, queryset):
        updated = queryset.update(status=DesignRequest.Status.LOGO_UPLOADED)
        self.message_user(request, f'{updated} request(s) marked as logo received.')
