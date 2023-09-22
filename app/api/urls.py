from rest_framework.routers import SimpleRouter

from .views import UserViewSet, UserLessonsView

router = SimpleRouter()
router.register(r'users', UserViewSet, basename="users")
router.register(r'lesson-status', UserLessonsView, basename="lesson-status")

urlpatterns = router.urls