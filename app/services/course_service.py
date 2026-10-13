from app.repositories.course import CourseRepository
from app.models.course import Course


class CourseService:
    def __init__(self, course_repo: CourseRepository):
        self.course_repo = course_repo

    def search_catalog(
        self,
        query: str | None = None,
        faculty: str | None = None,
    ) -> list[Course]:
        normalized_query = (query or "").strip()
        return self.course_repo.search_catalog(normalized_query, faculty)

    def list_faculties(self) -> list[str]:
        return self.course_repo.list_faculties()