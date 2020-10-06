from django.urls import path

from . import views

app_name = "data_management"

urlpatterns = [
    path("", view=views.index, name="index"),
    path("show/<int:id>", view=views.show, name="show"),
    path("edit/<int:id>", view=views.edit, name="edit"),
    path("save/<int:id>", view=views.save, name="save")
]
