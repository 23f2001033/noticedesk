from pathlib import Path


def resolve_webapp_file(full_path: str, dist_dir: Path) -> Path:
    """Path-traversal-safe resolution of a request path against the built
    webapp directory.

    Returns the matching static asset if one exists under dist_dir,
    otherwise index.html (SPA client-side routing fallback -- so direct
    navigation/refresh on a React Router route like /login still works).
    """
    candidate = (dist_dir / full_path).resolve()
    if full_path and candidate.is_file() and dist_dir in candidate.parents:
        return candidate
    return dist_dir / "index.html"
