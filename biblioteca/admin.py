from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import escape, mark_safe
from django.forms.models import BaseInlineFormSet
from django import forms
from django.contrib.auth.models import Group

from .models import *

# Widget per a <datalist> dinàmic en camps de text
class DatalistTextInput(forms.TextInput):
    """
    TextInput que genera un <input list=> i el corresponent <datalist> amb opcions.
    """
    def __init__(self, datalist_id, options, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.datalist_id = datalist_id
        self.options = options

    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}
        attrs['list'] = self.datalist_id
        input_html = super().render(name, value, attrs, renderer)
        options_html = "\n".join(f'<option value="{opt}"/>' for opt in self.options)
        datalist_html = f'<datalist id="{self.datalist_id}">\n{options_html}\n</datalist>'
        return mark_safe(input_html + datalist_html)


class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nom', 'parent')
    ordering = ('parent', 'nom')


class UsuariAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Dades acadèmiques", {
            'fields': ('centre', 'grup', 'telefon', 'imatge'),
        }),
    )


# Formset personalitzat per als exemplars
class ExemplarInlineFormSet(BaseInlineFormSet):
    def save_new(self, form, commit=True):
        instance = super().save_new(form, commit=False)
        request = getattr(self, 'request', None)
        if request and not request.user.is_superuser and not instance.centre:
            instance.centre = request.user.centre
        if commit:
            instance.save()
        return instance


class CustomExemplarsInline(admin.TabularInline):
    model = Exemplar
    extra = 1
    formset = ExemplarInlineFormSet
    readonly_fields = ('pk',)
    fields = ('pk', 'registre', 'exclos_prestec', 'baixa', 'centre')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.centre:
            return qs.filter(centre=request.user.centre)
        return qs.none()

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.request = request
        return formset


class LlibreAdmin(admin.ModelAdmin):
    filter_horizontal = ('tags',)
    inlines = [CustomExemplarsInline]
    search_fields = ('titol', 'autor', 'CDU', 'signatura', 'ISBN', 'editorial', 'colleccio')
    list_display = ('titol', 'autor', 'editorial', 'num_exemplars')
    readonly_fields = ('thumb',)

    def num_exemplars(self, obj):
        return obj.exemplar_set.count()

    def thumb(self, obj):
        return mark_safe(f"<img src='{escape(obj.thumbnail_url)}' />")

    def has_change_permission(self, request, obj=None):
        return request.user.is_staff

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name in ('autor', 'editorial'):
            # Cambiar Cataleg.objects por Llibre.objects
            qs = Llibre.objects.exclude(**{f"{db_field.name}__isnull": True}) \
                        .exclude(**{f"{db_field.name}": ""})
            opts = list(qs.values_list(db_field.name, flat=True)
                            .distinct().order_by(db_field.name))
            field.widget = DatalistTextInput(
                datalist_id=f'datalist_{db_field.name}',
                options=opts,
            )
        return field


# Registre d'admins
admin.site.register(Usuari, UsuariAdmin)
admin.site.register(Categoria, CategoriaAdmin)
admin.site.register(Pais)
admin.site.register(Llengua)
admin.site.register(Llibre, LlibreAdmin)
# Si vols autocomplete també per a Revistes, descomenta i registra:
# class RevistaAdmin(LlibreAdmin):
#     pass
# admin.site.register(Revista, RevistaAdmin)

admin.site.register(Revista)
admin.site.register(Dispositiu)
admin.site.register(Imatge)

class PrestecAdmin(admin.ModelAdmin):
    readonly_fields = ('data_prestec',)
    fields = ('exemplar', 'usuari', 'data_prestec', 'data_retorn', 'anotacions')
    list_display = ('exemplar', 'usuari', 'data_prestec', 'data_retorn')

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        if request.user.groups.filter(name="bibliotecario").exists():
            if request.user.centre:
                return qs.filter(exemplar__centre=request.user.centre)

        return qs.none()

admin.site.register(Centre)
admin.site.register(Grup)
admin.site.register(Reserva)
admin.site.register(Prestec, PrestecAdmin)
admin.site.register(Peticio)