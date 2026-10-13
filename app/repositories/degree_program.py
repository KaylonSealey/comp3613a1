from sqlmodel import Session, select

from app.models.degree_program import DegreeProgram


class DegreeProgramRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, degree_program_id: int) -> DegreeProgram | None:
        return self.db.get(DegreeProgram, degree_program_id)

    def list_all(self) -> list[DegreeProgram]:
        statement = select(DegreeProgram).order_by(DegreeProgram.name)
        return self.db.exec(statement).all()
