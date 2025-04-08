from typing import Optional
from fastapi import HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import joinedload, selectinload
from models import (
    User, Role, RoleEnum, UserRole, Module,
    Teacher, Discipline, DisciplineFormatEnum, TeacherDiscipline)


async def appoint_admin(target_user_id: str, current_user: dict, db: AsyncSession):
    if "SUPER-ADMIN" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Only super-admin can appoint admin")

    target = await db.execute(
        select(User)
        .options(joinedload(User.user_roles).joinedload(UserRole.role))
        .where(User.id == target_user_id)
    )
    target_user = target.scalars().first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")

    role = await db.execute(
        select(Role).where(Role.name == RoleEnum.admin)
    )
    admin_role = role.scalars().first()
    if not admin_role:
        raise HTTPException(status_code=500, detail="Admin role not found in the system")

    if target_user.user_roles:
        existing_assignment = target_user.user_roles[0]
        if existing_assignment.role.name == RoleEnum.admin:
            raise HTTPException(status_code=400, detail="User is already an admin")
        existing_assignment.role_id = admin_role.id
        await db.commit()
    else:
        new_assignment = UserRole(user_id=target_user_id, role_id=admin_role.id)
        db.add(new_assignment)
        await db.commit()

    await db.refresh(target_user)
    return target_user.get_dto()


async def remove_admin(target_user_id: str, current_user: dict, db: AsyncSession):
    if "SUPER-ADMIN" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Only super-admin can remove admin role")

    user = await db.execute(
        select(User)
        .options(joinedload(User.user_roles).joinedload(UserRole.role))
        .where(User.id == target_user_id)
    )
    target_user = user.scalars().first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")

    role_result = await db.execute(
        select(Role).where(Role.name == RoleEnum.user)
    )
    default_role = role_result.scalars().first()
    if not default_role:
        raise HTTPException(status_code=500, detail="Default user role not found in the system")

    updated = False
    for user_role in target_user.user_roles:
        if user_role.role.name == RoleEnum.admin:
            user_role.role_id = default_role.id
            updated = True
            break

    if not updated:
        raise HTTPException(status_code=400, detail="User is not an admin")

    await db.commit()
    await db.refresh(target_user)
    return target_user.get_dto()


async def add_module(module_name: str, current_user: dict, db: AsyncSession):
    if not ("SUPER-ADMIN" in current_user.get("roles", []) or "ADMIN" in current_user.get("roles", [])):
        raise HTTPException(status_code=403, detail="Only super-admin or admin can add module")

    is_exist = await db.execute(
        select(Module).where(Module.name == module_name)
    )
    module = is_exist.scalars().first()
    if module:
        raise HTTPException(status_code=500, detail="Module is already exist")

    new_module = Module(name=module_name)
    db.add(new_module)
    await db.commit()
    await db.refresh(new_module)

    return new_module.get_dto()


async def update_module(module_id: str, new_name: str, current_user: dict, db: AsyncSession):
    if not ("SUPER-ADMIN" in current_user.get("roles", []) or "ADMIN" in current_user.get("roles", [])):
        raise HTTPException(status_code=403, detail="Only super-admin or admin can update module")

    result = await db.execute(select(Module).where(Module.name == new_name))
    existing_module = result.scalars().first()
    if existing_module and str(existing_module.id) != module_id:
        raise HTTPException(status_code=400, detail="Module with this name already exists")

    result = await db.execute(select(Module).where(Module.id == module_id))
    module = result.scalars().first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    module.name = new_name
    await db.commit()
    await db.refresh(module)

    return module.get_dto()


async def delete_module(module_id: str, current_user: dict, db: AsyncSession):
    if not ("SUPER-ADMIN" in current_user.get("roles", []) or "ADMIN" in current_user.get("roles", [])):
        raise HTTPException(status_code=403, detail="Only super-admin or admin can delete module")

    result = await db.execute(select(Module).where(Module.id == module_id))
    module = result.scalars().first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    result = await db.execute(select(Discipline).where(Discipline.module_id == module_id))
    discipline = result.scalars().first()
    if discipline:
        raise HTTPException(
            status_code=400,
            detail="Module cannot be deleted because there are associated disciplines"
        )

    await db.delete(module)
    await db.commit()

    return {"detail": "Module deleted successfully"}


async def get_modules(db: AsyncSession):
    result = await db.execute(select(Module))
    modules = result.unique().scalars().all()
    return [module.get_dto() for module in modules]


async def create_teacher(
        db: AsyncSession,
        current_user: dict,
        first_name: str,
        surname: str,
        patronymic: Optional[str]
):
    if not ("SUPER-ADMIN" in current_user.get("roles", []) or "ADMIN" in current_user.get("roles", [])):
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
    await db.refresh(new_teacher)
    return new_teacher.get_dto()


async def edit_teacher(
        db: AsyncSession,
        current_user: dict,
        teacher_id: str,
        first_name: str | None = None,
        surname: str | None = None,
        patronymic: str | None = None,
):
    if not ("SUPER-ADMIN" in current_user.get("roles", []) or "ADMIN" in current_user.get("roles", [])):
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
    return teacher.get_dto()


async def delete_teacher(
        db: AsyncSession,
        current_user: dict,
        teacher_id: str,
):
    if not ("SUPER-ADMIN" in current_user.get("roles", []) or "ADMIN" in current_user.get("roles", [])):
        raise HTTPException(status_code=403, detail="Only super-admin or admin can delete teacher")

    result = await db.execute(select(Teacher).where(Teacher.id == teacher_id))
    teacher = result.scalars().first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    await db.delete(teacher)
    await db.commit()
    return {"detail": "Teacher deleted successfully"}


async def get_teachers(db: AsyncSession):
    result = await db.execute(
        select(Teacher).options(
            selectinload(
                Teacher.teacher_disciplines
            ).joinedload(TeacherDiscipline.discipline)
        )
    )
    teachers = result.unique().scalars().all()
    return [teacher.get_dto() for teacher in teachers]


async def create_discipline(
        db: AsyncSession,
        current_user: dict,
        name: str,
        format_value: str,
        module_id: str,
        description: Optional[str] = None,
        modeus_link: Optional[str] = None,
        presentation_link: Optional[str] = None,
):
    if not ("SUPER-ADMIN" in current_user.get("roles", []) or "ADMIN" in current_user.get("roles", [])):
        raise HTTPException(status_code=403, detail="Only super-admin or admin can create discipline")

    try:
        discipline_format = DisciplineFormatEnum(format_value)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Неверный формат дисциплины. Ожидалось одно из: 'онлайн', 'традиционный' или 'смешанный'"
        )

    try:
        result = await db.execute(select(Module).where(Module.id == module_id))
    except DBAPIError as e:
        raise HTTPException(
            status_code=400,
            detail="Invalid module_id. Please provide a valid UUID."
        ) from e

    module = result.scalars().first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    result = await db.execute(
        select(Discipline).where(
            Discipline.name == name,
            Discipline.module_id == module_id
        )
    )
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Discipline already exists in this module")

    new_discipline = Discipline(
        name=name,
        format=discipline_format,
        description=description,
        modeus_link=modeus_link,
        presentation_link=presentation_link,
        module_id=module_id
    )
    db.add(new_discipline)
    await db.commit()
    await db.refresh(new_discipline)
    return new_discipline.get_dto()


async def update_discipline(
    db: AsyncSession,
    current_user: dict,
    discipline_id: str,
    name: Optional[str] = None,
    format_value: Optional[str] = None,
    module_id: Optional[str] = None,
    description: Optional[str] = None,
    modeus_link: Optional[str] = None,
    presentation_link: Optional[str] = None,
):
    if not ("SUPER-ADMIN" in current_user.get("roles", []) or "ADMIN" in current_user.get("roles", [])):
        raise HTTPException(
            status_code=403,
            detail="Only super-admin or admin can update discipline"
        )

    result = await db.execute(select(Discipline).where(Discipline.id == discipline_id))
    discipline = result.scalars().first()
    if not discipline:
        raise HTTPException(status_code=404, detail="Discipline not found")

    if module_id:
        try:
            result = await db.execute(select(Module).where(Module.id == module_id))
        except DBAPIError as e:
            raise HTTPException(
                status_code=400, detail="Invalid module_id. Please provide a valid UUID."
            ) from e
        module = result.scalars().first()
        if not module:
            raise HTTPException(status_code=404, detail="Module not found")
        discipline.module_id = module_id

    if format_value:
        try:
            discipline_format = DisciplineFormatEnum(format_value)
        except ValueError:
            raise HTTPException
        discipline.format = discipline_format

    if name:
        check_module_id = module_id if module_id else discipline.module_id
        result = await db.execute(
            select(Discipline).where(
                and_(
                    Discipline.name == name,
                    Discipline.module_id == check_module_id,
                    Discipline.id != discipline_id
                )
            )
        )
        existing = result.scalars().first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Discipline with this name already exists in this module"
            )
        discipline.name = name

    if description is not None:
        discipline.description = description
    if modeus_link is not None:
        discipline.modeus_link = modeus_link
    if presentation_link is not None:
        discipline.presentation_link = presentation_link

    await db.commit()
    await db.refresh(discipline)
    return discipline.get_dto()


async def delete_discipline(
    db: AsyncSession,
    current_user: dict,
    discipline_id: str
):
    if not ("SUPER-ADMIN" in current_user.get("roles", []) or "ADMIN" in current_user.get("roles", [])):
        raise HTTPException(
            status_code=403,
            detail="Only super-admin or admin can delete discipline"
        )

    result = await db.execute(select(Discipline).where(Discipline.id == discipline_id))
    discipline = result.scalars().first()
    if not discipline:
        raise HTTPException(status_code=404, detail="Discipline not found")

    await db.delete(discipline)
    await db.commit()

    return {"detail": "Discipline deleted successfully"}


async def get_disciplines(db: AsyncSession):
    discipline = await db.execute(select(Discipline))
    disciplines = discipline.unique().scalars().all()
    return [discipline.get_dto() for discipline in disciplines]


# узнать зачем нам teacherDescipline
# и так далее по списку,не забыть добавить возможность репортов на отзывы и тд, чекнуть заметки
async def appoint_teacher_discipline(
        db: AsyncSession,
        current_user: dict,
        teacher_id: str,
        discipline_id: str,
):
    if not ("SUPER-ADMIN" in current_user.get("roles", []) or "ADMIN" in current_user.get("roles", [])):
        raise HTTPException(
            status_code=403,
            detail="Only super-admin or admin can assign a teacher to a discipline"
        )

    teacher_result = await db.execute(select(Teacher).where(Teacher.id == teacher_id))
    teacher = teacher_result.scalars().first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    discipline_result = await db.execute(select(Discipline).where(Discipline.id == discipline_id))
    discipline = discipline_result.scalars().first()
    if not discipline:
        raise HTTPException(status_code=404, detail="Discipline not found")

    existing_result = await db.execute(
        select(TeacherDiscipline).where(
            and_(
                TeacherDiscipline.teacher_id == teacher_id,
                TeacherDiscipline.discipline_id == discipline_id
            )
        )
    )
    existing_link = existing_result.scalars().first()
    if existing_link:
        raise HTTPException(status_code=400, detail="Teacher is already assigned to this discipline")

    new_assignment = TeacherDiscipline(
        teacher_id=teacher_id,
        discipline_id=discipline_id
    )
    db.add(new_assignment)
    await db.commit()
    await db.refresh(new_assignment)

    teacher_result = await db.execute(
        select(Teacher).options(
            selectinload(Teacher.teacher_disciplines).joinedload(TeacherDiscipline.discipline)
        ).where(Teacher.id == teacher_id)
    )
    teacher = teacher_result.scalars().first()

    return teacher.get_dto()


async def remove_teacher_discipline(
        db: AsyncSession,
        current_user: dict,
        teacher_id: str,
        discipline_id: str
):
    if not ("SUPER-ADMIN" in current_user.get("roles", []) or "ADMIN" in current_user.get("roles", [])):
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
        raise HTTPException(status_code=404, detail="Teacher is not assigned to this discipline")

    await db.delete(assignment)
    await db.commit()

    teacher_result = await db.execute(
        select(Teacher).options(
            selectinload(Teacher.teacher_disciplines).joinedload(TeacherDiscipline.discipline)
        ).where(Teacher.id == teacher_id)
    )
    teacher = teacher_result.scalars().first()
    return teacher.get_dto()
