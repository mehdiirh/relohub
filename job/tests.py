from unittest.mock import MagicMock

from django.test import TestCase
from django.utils import timezone

from job.models import JobTitle, Job, JobLocation


class JobTitleModelTest(TestCase):

    def test_get_other_names_empty(self):
        job_title = JobTitle(other_names=None)
        self.assertEqual(job_title.get_other_names(), [])

    def test_get_other_names_single_name(self):
        job_title = JobTitle(other_names="Software Engineer")
        self.assertEqual(job_title.get_other_names(), ["Software Engineer"])

    def test_get_other_names_multiple_names(self):
        job_title = JobTitle(other_names="Software Engineer;Programmer;Developer")
        self.assertEqual(
            job_title.get_other_names(),
            ["Software Engineer", "Programmer", "Developer"],
        )

    def test_other_names_cleanup_process(self):
        job_title = JobTitle(
            title="Software Engineer",
            linkedin_id="123",
            other_names=";;Software Engineer;;;Programmer;;Developer;;;;",
        )
        job_title.save()

        self.assertEqual(
            job_title.get_other_names(),
            ["Software Engineer", "Programmer", "Developer"],
        )

        self.assertEqual(
            job_title.other_names, "Software Engineer;Programmer;Developer"
        )

    def test_other_names_uniqueness(self):
        job_title = JobTitle(
            title="Software Engineer",
            linkedin_id="123",
            other_names="Software Engineer;Python Developer",
        )
        job_title.save = MagicMock()

        job_title.add_other_name("Python Developer")
        job_title.add_other_name("PHP Developer")

        job_title.save.assert_called()

        self.assertEqual(
            job_title.get_other_names(),
            ["Software Engineer", "Python Developer", "PHP Developer"],
        )

        self.assertEqual(
            job_title.other_names, "Software Engineer;Python Developer;PHP Developer"
        )

    def test_add_other_name_new_name(self):
        job_title = JobTitle(other_names="Software Engineer")
        job_title.save = MagicMock()

        job_title.add_other_name("Programmer")
        job_title.save.assert_called_once()

        self.assertIn("Programmer", job_title.other_names.split(";"))

    def test_add_other_name_existing_name(self):
        job_title = JobTitle(other_names="Software Engineer")
        job_title.save = MagicMock()

        job_title.add_other_name("Software Engineer")
        job_title.save.assert_called_once()

        self.assertEqual(job_title.other_names, "Software Engineer")

    def test_get_children_recursive(self):
        job_title_1 = JobTitle.objects.create(
            title="Title 1",
            linkedin_id="123",
        )
        job_title_2 = JobTitle.objects.create(
            title="Title 2",
            linkedin_id="234",
            parent=job_title_1,
        )
        job_title_3 = JobTitle.objects.create(
            title="Title 3",
            linkedin_id="345",
            parent=job_title_1,
        )

        job_title_4 = JobTitle.objects.create(
            title="Title 4",
            linkedin_id="456",
            parent=job_title_2,
        )
        job_title_5 = JobTitle.objects.create(
            title="Title 5",
            linkedin_id="567",
            parent=job_title_3,
        )

        children = job_title_1.get_children(recursive=True)

        self.assertEqual(
            set(children),
            {
                job_title_2,
                job_title_3,
                job_title_4,
                job_title_5,
            },
        )

    def test_save_with_other_names(self):
        job_title = JobTitle(other_names="Software Engineer;Programmer;Developer")
        job_title.save()
        self.assertEqual(
            job_title.other_names, "Software Engineer;Programmer;Developer"
        )

    def test_save_without_other_names(self):
        job_title = JobTitle(other_names=None)
        job_title.save()
        self.assertIsNone(job_title.other_names)


class JobModelTest(TestCase):

    def setUp(self):
        self.location = JobLocation.objects.create(
            title="TEST LOCATION",
            iso_code="TS",
            linkedin_geo_id="1234",
            flag_emoji=":TS:",
        )
        self.job = Job.objects.create(
            title="TEST JOB",
            linkedin_id="1234",
            location=self.location,
        )

    def test_save_with_int_listed_at(self):
        timestamp = 1618920000
        self.job.listed_at = timestamp
        self.job.save()

        self.assertIsInstance(self.job.listed_at, timezone.datetime)

    def test_save_with_float_listed_at(self):
        timestamp = 1618920000.0
        self.job.listed_at = timestamp
        self.job.save()

        self.assertIsInstance(self.job.listed_at, timezone.datetime)

    def test_save_with_milliseconds_int_listed_at(self):
        timestamp = 1618920000000
        self.job.listed_at = timestamp
        self.job.save()

        self.assertIsInstance(self.job.listed_at, timezone.datetime)

    def test_save_with_milliseconds_float_listed_at(self):
        timestamp = 1618920000000.0
        self.job.listed_at = timestamp
        self.job.save()

        self.assertIsInstance(self.job.listed_at, timezone.datetime)

    def test_with_valid_datetime(self):
        datetime = timezone.now()
        self.job.listed_at = datetime
        self.job.save()

        self.assertEqual(self.job.listed_at, datetime)
