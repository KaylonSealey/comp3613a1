from app.models.degree_program import DegreeProgram
from app.repositories.degree_program import DegreeProgramRepository


class DegreeProgramService:
    def __init__(self, degree_program_repo: DegreeProgramRepository):
        self.degree_program_repo = degree_program_repo

    def list_programs(self) -> list[DegreeProgram]:
        return self.degree_program_repo.list_all()
