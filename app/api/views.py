from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import CreateModelMixin
from .serializers import LessonViewSerializer, ProductStatsSerializer, UserRegistrationSerializer, \
    UserRetrieveSerializer, UserListSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin
from django.contrib.auth.models import User
from rest_framework.decorators import action
from django.db.models import Count, Sum, F, ExpressionWrapper, FloatField
from django.db.models.functions import Cast
from rest_framework.views import APIView

from ..models import Lesson, LessonView, Product


class UserViewSet(CreateModelMixin, ListModelMixin,
                  RetrieveModelMixin, GenericViewSet):
    queryset = User.objects.all().order_by("-id")

    # serializer_class = UserRegistrationSerializer

    def get_serializer_class(self):
        if self.action == "create":
            return UserRegistrationSerializer
        if self.action == ["retrieve", "me"]:
            return UserRetrieveSerializer
        return UserListSerializer

    def get_permissions(self):
        if self.action == "create":
            self.permission_classes = [AllowAny]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        instance = self.request.user
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_queryset(self):
        queryset = User.objects.all()
        return queryset


class UserLessonsView(viewsets.ViewSet):
    """
    возвращает список уроков с информацией о статусе и времени просмотра для данного пользователя
    """
    serializer_class = LessonViewSerializer

    def list(self, request):
        user = request.user

        user_lessons = LessonView.objects.filter(user=user)

        serializer = LessonViewSerializer(user_lessons, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


# class Subscribe(viewsets.ViewSet):
#     serializer_class = LessonViewSerializer

#     def create(self, request):
#         user = request.user
#         lesson_id = request.data.get('lesson')

#         try:
#             lesson = Lesson.objects.get(id=lesson_id)
#         except Lesson.DoesNotExist:
#             return Response({'error': 'Урок не найден'}, status=status.HTTP_404_NOT_FOUND)

#         # Проверяем, не записан ли пользователь уже на этот урок
#         existing_record = LessonView.objects.filter(user=user, lesson=lesson).first()
#         if existing_record:
#             return Response({'error': 'Вы уже записаны на этот урок'}, status=status.HTTP_400_BAD_REQUEST)

#         # Создаем запись пользователя на урок
#         lesson_view = LessonView.objects.create(user=user, lesson=lesson)

#         serializer = LessonViewSerializer(lesson_view)
#         return Response(serializer.data, status=status.HTTP_201_CREATED)
class Subscribe(viewsets.ViewSet):
    serializer_class = LessonViewSerializer

    def create(self, request):
        user = request.user
        lesson_id = request.data.get('lesson')

        try:
            lesson = Lesson.objects.get(id=lesson_id)
        except Lesson.DoesNotExist:
            return Response({'error': 'Урок не найден'}, status=status.HTTP_404_NOT_FOUND)

        # Проверяем, существует ли уже запись пользователя для данного урока
        existing_record = LessonView.objects.filter(user=user, lesson=lesson).first()

        if existing_record:
            # Если запись существует, обновляем данные
            existing_record.viewed_time_seconds = request.data.get('viewed_time_seconds',
                                                                   existing_record.viewed_time_seconds)
            existing_record.save()
            serializer = LessonViewSerializer(existing_record)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            # Если записи нет, создаем новую
            lesson_view = LessonView.objects.create(
                user=user,
                lesson=lesson,
                viewed_time_seconds=request.data.get('viewed_time_seconds', 0)
            )
            serializer = LessonViewSerializer(lesson_view)
            return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductStatsViewSet(viewsets.ViewSet):
    def list(self, request):
        products = Product.objects.annotate(
            total_views=Count('lessons__lessonview', filter=F('lessons__lessonview__viewed')),
            total_view_time=Sum('lessons__lessonview__viewed_time_seconds', filter=F('lessons__lessonview__viewed')),
            total_students=Count('lessons__lessonview__user', distinct=True, filter=F('lessons__lessonview__viewed')),
        )

        total_users = User.objects.count()

        for product in products:
            if total_users == 0:
                product.purchase_percentage = 0
            else:
                product.purchase_percentage = (
                        product.total_students / total_users * 100
                )

        serializer = ProductStatsSerializer(products, many=True)
        return Response(serializer.data)