"""Importing this package registers every API route. The order of the imports is the order of the routes."""
from . import account, jobs, applications, recruiter, platform  # noqa: F401
