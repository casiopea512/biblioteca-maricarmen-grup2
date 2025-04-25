from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import escape, mark_safe
from django.forms.models import BaseInlineFormSet


from .models import *

class CategoriaAdmin(admin.ModelAdmin):
	list_display = ('nom','parent')
	ordering = ('parent','nom')


class UsuariAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
            ("Dades acadèmiques", {
                'fields': ('centre','cicle','telefon','imatge'),
            }),
    )

# Formset personalitzat per als exemplars
class ExemplarInlineFormSet(BaseInlineFormSet):
    def save_new(self, form, commit=True):
        instance = super().save_new(form, commit=False)
        # Si l'usuari no és superusuari, assigna el centre del bibliotecari
        request = self.request
        if not request.user.is_superuser and not instance.centre:
            instance.centre = request.user.centre
        if commit:
            instance.save()
        return instance

class CustomExemplarsInline(admin.TabularInline):
    model = Exemplar
    extra = 1
    formset = ExemplarInlineFormSet
    readonly_fields = ('pk',)
    fields = ('pk', 'registre', 'exclos_prestec', 'baixa')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Els bibliotecaris veuen només els exemplars del seu centre
        if request.user.is_superuser:
            return qs
        if request.user.centre:
            return qs.filter(centre=request.user.centre)
        return qs.none()
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        # Passar la petició al formset
        formset.request = request
        return formset

class LlibreAdmin(admin.ModelAdmin):
    filter_horizontal = ('tags',)
    inlines = [CustomExemplarsInline,]
    search_fields = ('titol', 'autor', 'CDU', 'signatura', 'ISBN', 'editorial', 'colleccio')
    list_display = ('titol', 'autor', 'editorial', 'num_exemplars')
    readonly_fields = ('thumb',)

    def num_exemplars(self, obj):
        return obj.exemplar_set.count()

    def thumb(self, obj):
        return "<img src='{}' />".format(obj.thumbnail_url)

    def has_change_permission(self, request, obj=None):
        return request.user.is_staff

admin.site.register(Usuari,UsuariAdmin)
admin.site.register(Categoria,CategoriaAdmin)
admin.site.register(Pais)
admin.site.register(Llengua)
admin.site.register(Llibre,LlibreAdmin)
admin.site.register(Revista)
admin.site.register(Dispositiu)
admin.site.register(Imatge)

class PrestecAdmin(admin.ModelAdmin):
    readonly_fields = ('data_prestec',)
    fields = ('exemplar','usuari','data_prestec','data_retorn','anotacions')
    list_display = ('exemplar','usuari','data_prestec','data_retorn')

admin.site.register(Centre)
admin.site.register(Cicle)
admin.site.register(Reserva)
admin.site.register(Prestec,PrestecAdmin)
admin.site.register(Peticio)
