from .user import user
from .admin import admin

routes = [
    user.user_router,
    admin.admin_router
]
