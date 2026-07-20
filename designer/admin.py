from datetime import timedelta

from django.contrib import admin
from django.utils import timezone

from .models import DesignRequest, Template, TemplateGroup


class TemplateInline(admin.TabularInline):
    model = Template
    extra = 1


class DeferredAgeFilter(admin.SimpleListFilter):
    title = 'deferred logo age'
    parameter_name = 'deferred_age'

    def lookups(self, request, model_admin):
        return [
            ('1', 'Deferred over 1 day'),
            ('3', 'Deferred over 3 days'),
            ('7', 'Deferred over 7 days'),
        ]

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        cutoff = timezone.now() - timedelta(days=int(self.value()))
        return queryset.filter(
            status=DesignRequest.Status.LOGO_DEFERRED, logo_deferred_at__lte=cutoff
        )


@admin.register(TemplateGroup)
class TemplateGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [TemplateInline]


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'order', 'is_active')
    list_filter = ('group', 'is_active')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(DesignRequest)
class DesignRequestAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'client_email', 'template', 'status', 'logo_deferred_at', 'created_at')
    list_filter = ('status', 'template__group', DeferredAgeFilter)
    search_fields = ('order_number', 'client_email')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['mark_logo_received']

    @admin.action(description='Mark logo received (e.g. arrived via the standalone uploader)')
    def mark_logo_received(self, request, queryset):
        updated = queryset.update(status=DesignRequest.Status.LOGO_UPLOADED)
        self.message_user(request, f'{updated} request(s) marked as logo received.')
