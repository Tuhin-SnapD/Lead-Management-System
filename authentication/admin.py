from django.contrib import admin
from .models import user


@admin.action(description='approve new user')
def make_published(modeladmin, request, queryset):
    queryset.update(status='a')

class userAdmin(admin.ModelAdmin):
    list_display = ['username','email','status']
    ordering = ['username']
    actions = [make_published]

    
admin.site.register(user,userAdmin)







