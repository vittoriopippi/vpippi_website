"""Tools for JobApplication — job hunt tracking. Same validate_*/apply_* split as
cv_content.py: `validate_*` runs immediately when the model invokes the tool (checks
input, returns a human-readable summary plus normalized arguments, touches no data),
`apply_*` runs only once the write is confirmed (delete_job_application stages a
PendingAction; every other write here applies immediately, same as the CV tools).
"""
import datetime

from jobs.models import JobApplication

VALID_STATUSES = [choice[0] for choice in JobApplication.STATUS_CHOICES]


def _get_application(id):
    try:
        return JobApplication.objects.get(pk=id)
    except (JobApplication.DoesNotExist, ValueError, TypeError):
        raise ValueError(f"No job application with id {id!r}. Call list_job_applications to see what exists.")


def _parse_date(value, field_name='applied_date'):
    if value in (None, ''):
        return None
    try:
        return datetime.date.fromisoformat(str(value)[:10])
    except ValueError:
        raise ValueError(f"{field_name} must be an ISO date string 'YYYY-MM-DD', got {value!r}.")


def _check_status(status):
    if status not in VALID_STATUSES:
        raise ValueError(f"status must be one of {VALID_STATUSES}, got {status!r}.")


def _serialize(a):
    return {
        'id': a.id,
        'title': a.title,
        'company': a.company,
        'status': a.status,
        'location': a.location,
        'applied_date': a.applied_date.isoformat() if a.applied_date else None,
        'job_url': a.job_url,
        'notes': a.notes,
        'updated_at': a.updated_at.isoformat(),
    }


# --- read tools -----------------------------------------------------------

def list_job_applications(status=None):
    qs = JobApplication.objects.all()
    if status:
        _check_status(status)
        qs = qs.filter(status=status)
    return [_serialize(a) for a in qs]


def get_job_application(id):
    return _serialize(_get_application(id))


# --- write tools ------------------------------------------------------------

def validate_create_job_application(title, company, status='Applied', location='Zurich', applied_date=None, job_url='', notes=''):
    _check_status(status)
    parsed_date = _parse_date(applied_date)
    args = dict(
        title=title, company=company, status=status,
        location=location or 'Zurich',
        applied_date=parsed_date.isoformat() if parsed_date else None,
        job_url=job_url or '', notes=notes or '',
    )
    text = f"Add job application '{title}' at {company} (status: {status})"
    return text, args


def apply_create_job_application(title, company, status, location, applied_date, job_url, notes):
    a = JobApplication.objects.create(
        title=title, company=company, status=status, location=location,
        applied_date=_parse_date(applied_date), job_url=job_url, notes=notes,
    )
    return f"Added job application '{a.title}' at {a.company} (id: {a.id})."


def validate_update_job_application(id, title=None, company=None, status=None, location=None, applied_date=None, job_url=None, notes=None):
    a = _get_application(id)
    changes = {}
    if title is not None:
        changes['title'] = title
    if company is not None:
        changes['company'] = company
    if status is not None:
        _check_status(status)
        changes['status'] = status
    if location is not None:
        changes['location'] = location
    if applied_date is not None:
        parsed = _parse_date(applied_date)
        changes['applied_date'] = parsed.isoformat() if parsed else None
    if job_url is not None:
        changes['job_url'] = job_url
    if notes is not None:
        changes['notes'] = notes
    if not changes:
        raise ValueError('No fields to update were provided.')
    args = dict(id=a.id, changes=changes)
    text = f"Update job application '{a.title}' at {a.company} (id: {a.id}): " + ', '.join(f'{k}={v!r}' for k, v in changes.items())
    return text, args


def apply_update_job_application(id, changes):
    a = _get_application(id)
    for field, value in changes.items():
        if field == 'applied_date':
            value = _parse_date(value)
        setattr(a, field, value)
    a.save()
    return f"Updated job application '{a.title}' at {a.company} (id: {a.id})."


def validate_delete_job_application(id):
    a = _get_application(id)
    args = dict(id=a.id)
    text = f"Delete job application '{a.title}' at {a.company} (id: {a.id}) entirely"
    return text, args


def apply_delete_job_application(id):
    a = _get_application(id)
    label = f"{a.title} at {a.company}"
    a.delete()
    return f"Deleted job application '{label}'."
