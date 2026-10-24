import os

import books as K


def papers(project):
    project = os.path.realpath(project)
    books = K.address(project)
    return [os.path.join(project, K.WORKING_DOCUMENT),
            os.path.join(project, K.RESULTS),
            os.path.join(books, K.PROCESS_LOG),
            os.path.join(books, K.ISSUES)]


def ours(project, payload):
    import gate as S8
    owner = S8.bound(project)
    if owner is None:
        return True
    session = (payload or {}).get("session_id")
    if not session:
        return True
    return session == owner


def above(project):
    try:
        if K.running(project):
            return None
    except K.BadBooks:
        return None
    import gate as S8
    found = S8.live_run_above(project)
    return None if found is None else os.path.realpath(found)


def under(path, root):
    path = os.path.realpath(path)
    root = os.path.realpath(root)
    return path == root or path.startswith(root + os.sep)
