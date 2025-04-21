from .user import user
from .admin import admin
from .discipline import discipline
from .teacher import teacher
from .review_discipline import review_discipline

routes = [
    user.user_router,
    admin.admin_router,
    discipline.discipline_router,
    teacher.teacher_router,
    review_discipline.review_discipline_router
]
