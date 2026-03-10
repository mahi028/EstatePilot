from app import db

def adddb(obj: object) -> None:
    db.session.add(obj)

def addBulkdb(objs: list[object]) -> None:
    db.session.add_all(objs)

def deletedb(obj: object) -> None:
    db.session.delete(obj)

def commitdb() -> None:
    db.session.commit()

def rollbackdb() -> None:
    db.session.rollback()