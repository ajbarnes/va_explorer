from django.urls import path

from . import views

app_name = "data_management"

urlpatterns = [
    path("", view=views.index, name="index"),
    path("show/<int:id>", view=views.show, name="show"),
    path("edit/<int:id>", view=views.edit, name="edit"),
    path("save/<int:id>", view=views.save, name="save"),
    path("reset/<int:id>", view=views.reset, name="reset"),
    path("revert_latest/<int:id>", view=views.revert_latest, name="revert_latest"),
    path("run_coding_algorithms", view=views.run_coding_algorithms, name="run_coding_algorithms"),
    path("import_from_odk", view=views.import_from_odk, name="import_from_odk")
]
