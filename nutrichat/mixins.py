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
        customer_id = self.kwargs['id']
        user = self.request.user
        return (
            user.role == User.Role.NUTRITIONIST
            and user.customers.filter(pk=customer_id).exists()
        )
