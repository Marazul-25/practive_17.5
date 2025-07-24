from django.shortcuts import render, redirect
from django.http import HttpResponse
from tasks.forms import TaskForm, TaskModelForm, TaskDetailModelForm
from tasks.models import Task, TaskDetail, Project
from datetime import date
from django.db.models import Q, Count, Max, Min, Avg
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test, login_required, permission_required
from users.views import is_admin
from django.http import HttpResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic.base import ContextMixin
from django.views.generic import ListView, DetailView, UpdateView


class Greetings(View):
    greetings = 'Hello Everyone'

    def get(self, request):
        return HttpResponse(self.greetings)

class HiGreetings(Greetings):
    greetings = 'Hi Everyone'

class HiHowGreetings(Greetings):
    greetings = 'Hi Everyone, How are you'

def is_manager(user):
    return user.groups.filter(name='Manager').exists()

def is_employee(user):
    return user.groups.filter(name='Manager').exists()

@method_decorator(user_passes_test(is_manager, login_url='no-permission'), name='dispatch')
class manager_dashboard(View):
    def get(self, request):
        type = request.GET.get('type', 'all')

        counts = Task.objects.aggregate(
            total=Count('id'),
            completed=Count('id', filter=Q(status='COMPLETED')),
            in_progress=Count('id', filter=Q(status='IN_PROGRESS')),
            pending=Count('id', filter=Q(status='PENDING')),
        )

        base_query = Task.objects.select_related('details').prefetch_related('assigned_to')

        if type == 'completed':
            tasks = base_query.filter(status='COMPLETED')
        elif type == 'in-progress':
            tasks = base_query.filter(status='IN_PROGRESS')
        elif type == 'pending':
            tasks = base_query.filter(status='PENDING')
        else:
            tasks = base_query.all()

        context = {
            "tasks": tasks,
            "counts": counts,
            "role": 'manager',
        }
        return render(request, "dashboard/manager-dashboard.html", context)
    


@method_decorator(user_passes_test(is_employee), name='dispatch')
class Employee_dashboard(View):
    def get(self, request):
        return render(request, "dashboard/user-dashboard.html")

class CreateTask(ContextMixin, LoginRequiredMixin, PermissionRequiredMixin, View):
    """ For creating task """
    permission_required = 'tasks.add_task'
    login_url = 'sign-in'
    template_name = 'task_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['task_form'] = kwargs.get('task_form', TaskModelForm())
        context['task_detail_form'] = kwargs.get(
            'task_detail_form', TaskDetailModelForm())
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        task_form = TaskModelForm(request.POST)
        task_detail_form = TaskDetailModelForm(request.POST, request.FILES)

        if task_form.is_valid() and task_detail_form.is_valid():

            """ For Model Form Data """
            task = task_form.save()
            task_detail = task_detail_form.save(commit=False)
            task_detail.task = task
            task_detail.save()

            messages.success(request, "Task Created Successfully")
            context = self.get_context_data(
                task_form=task_form, task_detail_form=task_detail_form)
            return render(request, self.template_name, context)

class UpdateTask(UpdateView):
    model = Task
    form_class = TaskModelForm
    template_name = 'task_form.html'
    context_object_name = 'task'
    pk_url_kwarg = 'id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['task_form'] = self.get_form()
        # print(context)
        if hasattr(self.object, 'details') and self.object.details:
            context['task_detail_form'] = TaskDetailModelForm(
                instance=self.object.details)
        else:
            context['task_detail_form'] = TaskDetailModelForm()

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        task_form = TaskModelForm(request.POST, instance=self.object)

        task_detail_form = TaskDetailModelForm(
            request.POST, request.FILES, instance=getattr(self.object, 'details', None))

        if task_form.is_valid() and task_detail_form.is_valid():

            """ For Model Form Data """
            task = task_form.save()
            task_detail = task_detail_form.save(commit=False)
            task_detail.task = task
            task_detail.save()

            messages.success(request, "Task Updated Successfully")
            return redirect('update-task', self.object.id)
        return redirect('update-task', self.object.id)

@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required("tasks.delete_task", login_url='no-permission'), name='dispatch')
class delete_task(View):
    def post(self, request, id):
        try:
            task = Task.objects.get(id=id)
            task.delete()
            messages.success(request, 'Task Deleted Successfully')
            return redirect('manager-dashboard')
        except Task.DoesNotExist:
            messages.error(request, 'Task not found')
            return redirect('manager-dashboard')
        except Exception as e:
            messages.error(request, f'Something went wrong: {str(e)}')
            return redirect('manager-dashboard')

view_project_decorators = [login_required, permission_required(
    "projects.view_project", login_url='no-permission')]

@method_decorator(view_project_decorators, name='dispatch')
class ViewProject(ListView):
    model = Project
    context_object_name = 'projects'
    template_name = 'show_task.html'

    def get_queryset(self):
        queryset = Project.objects.annotate(
            num_task=Count('task')).order_by('num_task')
        return queryset

class TaskDetail(DetailView):
    model = Task
    template_name = 'task_details.html'
    context_object_name = 'task'
    pk_url_kwarg = 'task_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)  # {"task": task}
        # {"task": task, 'status_choices': status_choices}
        context['status_choices'] = Task.STATUS_CHOICES
        return context

    def post(self, request, *args, **kwargs):
        task = self.get_object()
        selected_status = request.POST.get('task_status')
        task.status = selected_status
        task.save()
        return redirect('task-details', task.id)

@method_decorator(login_required, name='dispatch')
class dashboard(View):
    def get(self, request):
        user = request.user

        if is_manager(user):
            return redirect('manager-dashboard')
        elif is_employee(user):
            return redirect('user-dashboard')
        elif is_admin(user):
            return redirect('admin-dashboard')

        return redirect('no-permission')
