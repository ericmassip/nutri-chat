from django.contrib.auth.mixins import UserPassesTestMixin

from nutrichat.models import User


class NutritionistRequiredMixin(UserPassesTestMixin):
    """Restricts access to nutritionist users. Returns 403 otherwise."""

    def test_func(self):
        return self.request.user.role == User.Role.NUTRITIONIST


class NutritionistOwnsCustomerMixin(UserPassesTestMixin):
    """
    Grants access if the logged-in user is a nutritionist who owns the customer.
    Returns 403 otherwise.
    """

    def test_func(self):
        pk = self.kwargs['pk']
        user = self.request.user
        return (
            user.role == User.Role.NUTRITIONIST
            and user.customers.filter(pk=pk).exists()
        )


class CustomerEditAccessMixin(NutritionistOwnsCustomerMixin):
    """
    Grants access if the logged-in user IS the customer, or is a nutritionist
    who owns the customer. Returns 403 otherwise.
    """

    def test_func(self):
        user = self.request.user
        if user.role == User.Role.CUSTOMER and user.pk == self.kwargs['pk']:
            return True
        return super().test_func()
