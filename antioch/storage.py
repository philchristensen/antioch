from django.contrib.staticfiles.storage import ManifestFilesMixin

from storages.backends.s3boto3 import S3Boto3Storage

class S3Boto3ManifestStorage(ManifestFilesMixin, S3Boto3Storage):
    pass
