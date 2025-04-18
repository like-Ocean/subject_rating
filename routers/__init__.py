from .user import user
from .admin import admin
from .discipline import discipline
from .teacher import teacher

routes = [
    user.user_router,
    admin.admin_router,
    discipline.discipline_router,
    teacher.teacher_router
]
