from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import VerbalAutopsy, CauseOfDeath, CauseCodingIssue, Location
from .forms import VerbalAutopsyForm
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

@login_required
def index(request, page_size=15):
    # active page - default to 1 if not active page
    absolute_page = request.GET.get('page', 1)

    # query to retrive all VAs
    va_list = (VerbalAutopsy.objects
        .prefetch_related("location", "causes", "coding_issues")
        .order_by("id")
    )

    # create paginator from query and bucket vas into pages of size page_size
    paginator = Paginator(va_list, page_size)

    # hone in on active page objects
    current_page = paginator.get_page(absolute_page)

    # pull out fields we want from active page objects
    current_page.object_list = [{
        "id": va.id,
        "name": va.Id10007,
        "facility": va.location.name,
        "cause": va.causes.all()[0].cause if len(va.causes.all()) > 0 else "",
        "warnings": len([issue for issue in va.coding_issues.all() if issue.severity == 'warning']),
        "errors": len([issue for issue in va.coding_issues.all() if issue.severity == 'error'])
    } for va in current_page.object_list]

    # return current page of paginator, as well as the absolute page
    context = {"va_data": current_page, "page": absolute_page}
    return render(request, "va_data_management/index.html", context)

# TODO: Use standard django CRUD conventions; e.g. see https://stackoverflow.com/questions/4673985/how-to-update-an-object-from-edit-form-in-django

# TODO: Is the convention to use pk instead of id in django?
@login_required
def show(request, id):
    va = VerbalAutopsy.objects.get(id=id)
    form = VerbalAutopsyForm(None, instance=va)
    coding_issues = va.coding_issues.all()
    warnings = [issue for issue in coding_issues if issue.severity == 'warning']
    errors = [issue for issue in coding_issues if issue.severity == 'error']
    history = va.history.all().reverse()
    history_pairs = zip(history, history[1:])
    diffs = [new.diff_against(old) for (old, new) in history_pairs]
    # TODO: date in diff info should be formatted in local time
    # TODO: history should eventually show user who made the change
    context = { "id": id, "form": form, "warnings": warnings, "errors": errors, "diffs": diffs }
    return render(request, "va_data_management/show.html", context)

@login_required
def edit(request, id):
    # TODO: We only want to allow editing of some fields
    # TODO: We want to provide context for all the fields
    va = VerbalAutopsy.objects.get(id=id)
    form = VerbalAutopsyForm(None, instance=va)
    context = { "id": id, "form": form }
    return render(request, "va_data_management/edit.html", context)

@login_required
def save(request, id):
    # TODO: There are probably more appropriate ways to handle form editing in django
    # TODO: When a record is changed, should it automatically be recoded if it was already coded?
    va = VerbalAutopsy.objects.get(id=id)
    form = VerbalAutopsyForm(request.POST, instance=va)
    if form.is_valid():
        form.save()
    return redirect("va_data_management:show", id=id)

# Reset to the first historical record
# TODO: If a record is reset, should it automatically be recoded?
@login_required
def reset(request, id):
    va = VerbalAutopsy.objects.get(id=id)
    earliest = va.history.earliest()
    latest = va.history.latest()
    if earliest and len(latest.diff_against(earliest).changes) > 0:
        earliest.instance.save()
    return redirect("va_data_management:show", id=id)

# Revert the most recent change
# TODO: Should record automatically be recoded?
@login_required
def revert_latest(request, id):
    va = VerbalAutopsy.objects.get(id=id)
    if va.history.count() > 1:
        previous = va.history.all()[1]
        latest = va.history.latest()
        if len(latest.diff_against(previous).changes) > 0:
            previous.instance.save()
        return redirect("va_data_management:show", id=id)
