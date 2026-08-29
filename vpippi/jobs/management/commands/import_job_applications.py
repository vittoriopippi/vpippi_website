import datetime
import json

from django.core.management.base import BaseCommand, CommandError

from jobs.models import JobApplication


class Command(BaseCommand):
    help = 'One-off import of job applications from a job_tracker_app-style JSON export.'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str)

    def handle(self, *args, **options):
        path = options['json_file']
        try:
            with open(path, 'r') as f:
                records = json.load(f)
        except FileNotFoundError:
            raise CommandError(f"File not found: {path}")

        created = 0
        skipped = 0
        for r in records:
            title = r.get('title', '').strip()
            company = r.get('company', '').strip()
            if not title or not company:
                skipped += 1
                continue
            if JobApplication.objects.filter(title=title, company=company).exists():
                skipped += 1
                continue

            applied_date = None
            raw_date = r.get('applied_date')
            if raw_date:
                try:
                    applied_date = datetime.date.fromisoformat(str(raw_date)[:10])
                except ValueError:
                    applied_date = None

            JobApplication.objects.create(
                title=title,
                company=company,
                status=r.get('status') or JobApplication.STATUS_APPLIED,
                location=r.get('location') or 'Zurich',
                applied_date=applied_date,
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f'Imported {created} application(s), skipped {skipped} duplicate/invalid.'))
