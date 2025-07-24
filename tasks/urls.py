from django.urls import path
from tasks.views import manager_dashboard, Employee_dashboard, create_task, view_task, update_task, delete_task, task_details, dashboard, Greetings, HiGreetings, HiHowGreetings, CreateTask, ViewProject, TaskDetail, UpdateTask

urlpatterns = [
    path('manager-dashboard/', manager_dashboard.as_view(), name="manager-dashboard"),
    path('user-dashboard/', Employee_dashboard.as_view(), name='user-dashboard'),
    path('create-task/', CreateTask.as_view(), name='create-task'),
    path('view_task/', ViewProject.as_view(), name='view-task'),
    path('task/<int:task_id>/details/',
         TaskDetail.as_view(), name='task-details'),
    path('update-task/<int:id>/', UpdateTask.as_view(), name='update-task'),
    path('delete-task/<int:id>/', delete_task.as_view(), name='delete-task'),
    path('dashboard/', dashboard.as_view(), name='dashboard'),
    path('greetings/', HiHowGreetings.as_view(greetings='Hi Good Day!'), name='greetings')
]

