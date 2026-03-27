from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.views import View
from django.views.generic import CreateView, UpdateView
import django_tables2 as tables

from nutrichat.forms import CustomerCreateForm, CustomerEditForm
from nutrichat.mixins import CustomerEditAccessMixin, NutritionistOwnsCustomerMixin, NutritionistRequiredMixin
from nutrichat.models import User


def home_view(request):
    return render(request, 'home.html')


class CustomerTable(tables.Table):
    name = tables.Column()
    surname = tables.Column()
    username = tables.LinkColumn("customer-edit", kwargs={"pk": tables.A("pk")}, accessor="username", verbose_name="Email")
    plan = tables.Column(empty_values=(), orderable=False, verbose_name="Plan")

    def render_plan(self, record):
        attachment = record.attachments.first()
        if attachment:
            return format_html(
                '<a href="{}" target="_blank">'
                '<span class="material-symbols-outlined" style="font-size:20px;">description</span>'
                '</a>',
                attachment.file.url,
            )
        return mark_safe(
            '<span class="material-symbols-outlined" style="font-size:20px; color:#ccc;">description</span>',
        )

    class Meta:
        model = User
        fields = ("name", "surname", "username", "plan")
        empty_text = "No customers yet."
        attrs = {"class": "table table-striped"}


class CustomerEditView(SuccessMessageMixin, CustomerEditAccessMixin, UpdateView):
    model = User
    form_class = CustomerEditForm
    template_name = "customer_edit.html"
    success_message = "%(name)s %(surname)s was updated successfully"

    def get_queryset(self):
        return User.objects.filter(role=User.Role.CUSTOMER)

    def get_success_url(self):
        return reverse('customer-edit', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['attachment'] = self.object.attachments.first()
        return context


class CustomerCreateView(NutritionistRequiredMixin, SuccessMessageMixin, CreateView):
    model = User
    form_class = CustomerCreateForm
    template_name = 'customer_create.html'
    success_message = "Customer created successfully"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['nutritionist'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('customer-edit', kwargs={'pk': self.object.pk})


class CustomerRemoveView(NutritionistOwnsCustomerMixin, View):
    def post(self, request, pk):
        customer = get_object_or_404(User, pk=pk, role=User.Role.CUSTOMER)
        customer.is_active = False
        customer.save()
        return redirect(reverse('customers'))


class CustomersView(NutritionistRequiredMixin, tables.SingleTableView):
    table_class = CustomerTable
    template_name = "customers.html"

    def get_queryset(self):
        return self.request.user.customers.filter(is_active=True).prefetch_related('attachments')
