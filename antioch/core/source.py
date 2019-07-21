import sys
import logging
import os
import os.path

from django.conf import settings

from antioch.core.models import Repository

log = logging.getLogger(__name__)

def checkout_repo(slug='default'):
    import git
    
    details = Repository.objects.get(slug=slug)
    
    os.path.makedirs(settings.DEFAULT_GIT_WORKSPACE, exist_ok=True)
    
    r = git.Repo.init(os.path.join(settings.DEFAULT_GIT_WORKSPACE, slug))
    origin = r.create_remote('origin', url=details.slug)
    for info in origin.fetch():
        print("Updated %s to %s" % (info.ref, info.commit))

def get_source(repo, filename, ref='master'):
    branch = getattr(origin.refs, ref)
    head = r.create_head(ref, branch)
    head.set_tracking_branch(branch)
    head.checkout()

    with open(os.path.join(settings.DEFAULT_GIT_WORKSPACE, slug, filename)) as f:
        return f.read()