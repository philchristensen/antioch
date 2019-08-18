import sys
import logging
import os
import os.path

from django.conf import settings

from antioch.core.models import Repository, Verb

log = logging.getLogger(__name__)

def deploy_all(repo):
    r = checkout_repo(repo)
    for verb in Verb.objects.filter(repo=repo):
        verb.code = get_source(repo, r, verb.filename, verb.ref)
        verb.save()

def checkout_repo(obj):
    import git
    
    os.makedirs(settings.DEFAULT_GIT_WORKSPACE, exist_ok=True)
    
    r = git.Repo.init(os.path.join(settings.DEFAULT_GIT_WORKSPACE, obj.slug))
    if('origin' in r.remotes):
        origin = r.remotes['origin']
    else:
        origin = r.create_remote('origin', url=obj.url)
    for info in origin.fetch():
        log.debug("Updated %s to %s" % (info.ref, info.commit))
    return r

def get_source(repo, r, filename, ref='master'):
    origin = r.remotes['origin']
    branch = getattr(origin.refs, ref)
    head = r.create_head(ref, branch)
    head.set_tracking_branch(branch)
    head.checkout()
    
    with open(os.path.join(settings.DEFAULT_GIT_WORKSPACE, repo.slug, repo.prefix, filename)) as f:
        return f.read()