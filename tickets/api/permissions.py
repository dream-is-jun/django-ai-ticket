from rest_framework.permissions import (
    BasePermission,
)


class IsTicketOwnerOrStaff(BasePermission):
    """只有工单创建人或客服可以访问对象。"""

    def has_object_permission(
        self,
        request,
        view,
        obj,
    ) -> bool:
        return (
            request.user.is_staff
            or obj.creator_id
            == request.user.id
        )