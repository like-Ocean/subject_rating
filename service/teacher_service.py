from typing import Optional
from fastapi import HTTPException, Response
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from models import Teacher, TeacherDiscipline, Discipline, User, RoleEnum, ReviewDiscipline


async def create_teacher(
        db: AsyncSession,
        current_user: User,
        first_name: str,
        surname: str,
        patronymic: Optional[str]
):
    if current_user["role"] not in {RoleEnum.admin.value, RoleEnum.super_admin.value}:
        raise HTTPException(status_code=403, detail="Only super-admin or admin can create teachers")

    teacher = await db.execute(select(Teacher).where(
        Teacher.first_name == first_name, Teacher.surname == surname)
    )
    if teacher.scalars().first():
        raise HTTPException(status_code=400, detail="Teacher already exists")

    new_teacher = Teacher(
        first_name=first_name,
        surname=surname,
        patronymic=patronymic
    )
    db.add(new_teacher)
    await db.commit()

    result = await db.execute(
        Teacher.get_joined_data().where(Teacher.id == new_teacher.id)
    )
    updated_teacher = result.scalars().first()

    return updated_teacher.get_dto()


async def edit_teacher(
        db: AsyncSession,
        current_user: User,
        teacher_id: str,
        first_name: str | None = None,
        surname: str | None = None,
        patronymic: str | None = None,
):
    if current_user["role"] not in {RoleEnum.admin.value, RoleEnum.super_admin.value}:
        raise HTTPException(status_code=403, detail="Only super-admin or admin can update teacher")

    result = await db.execute(
        select(Teacher).where(Teacher.id == teacher_id)
    )
    teacher = result.scalars().first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    if first_name is not None:
        teacher.first_name = first_name
    if surname is not None:
        teacher.surname = surname
    if patronymic is not None:
        teacher.patronymic = patronymic

    await db.commit()
    await db.refresh(teacher)

    refreshed = await db.execute(
        Teacher.get_joined_data().where(Teacher.id == teacher_id)
    )
    updated_teacher = refreshed.scalars().first()

    return updated_teacher.get_dto()


async def delete_teacher(
        db: AsyncSession,
        current_user: User,
        teacher_id: str,
):
    if current_user["role"] not in {RoleEnum.admin.value, RoleEnum.super_admin.value}:
        raise HTTPException(status_code=403, detail="Only super-admin or admin can delete teacher")

    result = await db.execute(select(Teacher).where(Teacher.id == teacher_id))
    teacher = result.scalars().first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    await db.execute(
        update(ReviewDiscipline)
        .where(ReviewDiscipline.lector_id == teacher_id)
        .values(lector_id=None)
    )
    await db.execute(
        update(ReviewDiscipline)
        .where(ReviewDiscipline.practic_id == teacher_id)
        .values(practic_id=None)
    )

    await db.delete(teacher)
    await db.commit()
    return Response(status_code=200)


async def get_teachers(
        db: AsyncSession,
        page: int = 1,
        size: int = 20,
        name_search: Optional[str] = None,
        sort_field: str = "surname",
        sort_order: str = "asc"
):
    data = Teacher.get_joined_data()
    filtered_query = Teacher.apply_filters(data, name_search)
    sorted_query = Teacher.apply_sorting(filtered_query, sort_field, sort_order)

    count_query = select(func.count(Teacher.id.distinct())).select_from(Teacher)
    count_query = Teacher.apply_filters(count_query, name_search)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    total_pages = (total + size - 1) // size
    paginated_query = sorted_query.limit(size).offset((page - 1) * size)

    result = await db.execute(paginated_query)
    teachers = result.unique().scalars().all()

    return {
        "data": [teacher.get_dto() for teacher in teachers],
        "pagination": {
            "total": total,
            "total_pages": total_pages,
            "page": page,
            "size": size
        }
    }


async def get_teachers_by_discipline(
    db: AsyncSession,
    discipline_id: str,
    page: int = 1,
    size: int = 20,
    name_search: Optional[str] = None,
    sort_field: str = "surname",
    sort_order: str = "asc"
):
    discipline_exists = await db.execute(
        select(Discipline.id).where(Discipline.id == discipline_id)
    )
    if not discipline_exists.scalar():
        raise HTTPException(404, "Discipline not found")

    data = (
        Teacher.get_joined_data()
        .where(TeacherDiscipline.discipline_id == discipline_id)
    )

    if name_search:
        data = Teacher.apply_filters(data, name_search)

    count_query = (
        select(func.count(Teacher.id.distinct()))
        .select_from(Teacher).join(TeacherDiscipline)
        .where(TeacherDiscipline.discipline_id == discipline_id)
    )
    if name_search:
        count_query = Teacher.apply_filters(count_query, name_search)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    sorted_query = Teacher.apply_sorting(data, sort_field, sort_order)

    total_pages = (total + size - 1) // size
    paginated_query = sorted_query.limit(size).offset((page - 1) * size)

    result = await db.execute(paginated_query)
    teachers = result.unique().scalars().all()

    return {
        "data": [teacher.get_dto() for teacher in teachers],
        "pagination": {
            "total": total,
            "total_pages": total_pages,
            "page": page,
            "size": size
        }
    }


async def appoint_teacher_disciplines(
        db: AsyncSession,
        current_user: User,
        teacher_id: str,
        discipline_ids: list[str],
):
    if current_user["role"] not in {RoleEnum.admin.value, RoleEnum.super_admin.value}:
        raise HTTPException(403, "Only admins can assign teachers")

    teacher = await db.execute(select(Teacher).where(Teacher.id == teacher_id))
    teacher = teacher.scalars().first()
    if not teacher:
        raise HTTPException(404, "Teacher not found")

    disciplines = await db.execute(
        select(Discipline).where(Discipline.id.in_(discipline_ids))
    )
    found_disciplines = disciplines.scalars().all()

    if len(found_disciplines) != len(discipline_ids):
        found_ids = {str(d.id) for d in found_disciplines}
        not_found = [id for id in discipline_ids if id not in found_ids]
        raise HTTPException(404, f"Disciplines not found: {', '.join(not_found)}")

    existing_links = await db.execute(
        select(TeacherDiscipline).where(
            TeacherDiscipline.teacher_id == teacher_id,
            TeacherDiscipline.discipline_id.in_(discipline_ids)
        )
    )
    existing = existing_links.scalars().all()

    if existing:
        existing_name = {str(link.discipline.name) for link in existing}
        raise HTTPException(
            400,
            f"Teacher already assigned to: {', '.join(existing_name)}"
        )

    new_assignments = [
        TeacherDiscipline(teacher_id=teacher_id, discipline_id=discipline_id)
        for discipline_id in discipline_ids
    ]

    db.add_all(new_assignments)
    await db.commit()

    result = await db.execute(
        Teacher.get_joined_data().where(Teacher.id == teacher_id)
    )
    updated_teacher = result.scalars().first()

    return updated_teacher.get_dto()


async def remove_teacher_discipline(
        db: AsyncSession,
        current_user: User,
        teacher_id: str,
        discipline_id: str
):
    if current_user["role"] not in {RoleEnum.admin.value, RoleEnum.super_admin.value}:
        raise HTTPException(
            status_code=403,
            detail="Only super-admin or admin can remove a teacher from a discipline"
        )

    teacher_result = await db.execute(select(Teacher).where(Teacher.id == teacher_id))
    teacher = teacher_result.scalars().first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    result = await db.execute(
        select(TeacherDiscipline).where(
            TeacherDiscipline.teacher_id == teacher_id,
            TeacherDiscipline.discipline_id == discipline_id
        )
    )
    assignment = result.scalars().first()
    if not assignment:
        raise HTTPException(
            status_code=404,
            detail="Teacher is not assigned to this discipline"
        )

    await db.delete(assignment)
    await db.commit()

    teacher_result = await db.execute(
        Teacher.get_joined_data().where(Teacher.id == teacher_id)
    )
    teacher = teacher_result.scalars().first()

    return teacher.get_dto()
