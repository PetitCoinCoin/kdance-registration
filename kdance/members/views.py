"""
Copyright 2024, 2025 Andréa Marnier

This file is part of KDance registration.

KDance registration is free software: you can redistribute it and/or modify it
under the terms of the GNU Affero General Public License as published by the
Free Software Foundation, either version 3 of the License, or any later version.

KDance registration is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License
for more details.

You should have received a copy of the GNU Affero General Public License along
with KDance registration. If not, see <https://www.gnu.org/licenses/>.
"""

from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from onlinepayments.sdk.communicator_configuration import CommunicatorConfiguration
from onlinepayments.sdk.domain.create_hosted_checkout_request import (
    CreateHostedCheckoutRequest,
)
from onlinepayments.sdk.factory import Factory
from onlinepayments.sdk.merchant.i_merchant_client import IMerchantClient

from members.emails import EmailEnum, EmailSender
from members.models import GeneralSettings, Payment, Season, CBPayment


def _is_teacher(request: HttpRequest) -> bool:
    return request.user.groups.filter(name=settings.TEACHER_GROUP_NAME).exists()


def _create_cawl_client() -> IMerchantClient:
    communicator_configuration = CommunicatorConfiguration(
        api_endpoint=settings.CAWL_URL,
        api_key_id=settings.CAWL_API_ID,
        secret_api_key=settings.CAWL_API_KEY,
        authorization_type="v1HMAC",
        integrator="K'Dance",
        connect_timeout=5000,
        socket_timeout=10000,
        max_connections=10,
    )

    client = Factory.create_client_from_configuration(communicator_configuration)
    return client.merchant(settings.CAWL_PSPID)


def _get_total_due(request_user: User) -> int:
    if isinstance(request_user, AnonymousUser):
        raise Http404

    current_payment = Payment.objects.filter(
        user=request_user, season__is_current=True
    ).first()
    if not current_payment:
        raise Http404

    return current_payment.due - current_payment.paid + current_payment.refund


@require_http_methods(["GET"])
@login_required()
def index(request: HttpRequest) -> HttpResponse:
    current_season = Season.objects.filter(is_current=True).first()
    general_settings = GeneralSettings.get_solo()
    return render(
        request,
        "pages/index.html",
        context={
            "user": request.user,
            "is_teacher": _is_teacher(request),
            "allow_new_member": general_settings.allow_new_member,
            "current_season": current_season,
            "pre_signup_payment_end": current_season.pre_signup_end
            + timedelta(days=general_settings.pre_signup_payment_delta_days)
            if current_season
            else "",
            "signup_payment_end": current_season.signup_end
            + timedelta(days=general_settings.signup_payment_delta_days)
            if current_season and current_season.signup_end
            else "",
            "previous_season": current_season.previous_season if current_season else "",
        },
    )


@require_http_methods(["GET"])
@login_required()
def checkout(request: HttpRequest) -> HttpResponse:
    total_due = _get_total_due(request.user)
    if total_due <= 0:
        return render(request, "403.html", status=403)

    return render(
        request,
        "pages/checkout.html",
        context={
            "user": request.user,
            "season": Season.objects.get(is_current=True),
        },
    )


@require_http_methods(["GET"])
@login_required()
def online_checkout(request: HttpRequest) -> HttpResponse:
    total_due = _get_total_due(request.user)
    if total_due <= 0:
        return render(request, "403.html", status=403)

    merchant_client = _create_cawl_client()
    order_dict = {
        "order": {
            "amountOfMoney": {"currencyCode": "EUR", "amount": total_due * 100},
            "references": {"merchantReference": request.user.email},
        },
        "hostedCheckoutSpecificInput": {
            "locale": "fr_FR",
            "returnUrl": request.build_absolute_uri(reverse("session_status")),
            "showResultPage": False,
        },
    }

    hosted_checkout_client = merchant_client.hosted_checkout()
    hosted_checkout_request = CreateHostedCheckoutRequest()

    hosted_checkout_request.from_dictionary(order_dict)

    hosted_checkout_response = hosted_checkout_client.create_hosted_checkout(
        hosted_checkout_request
    )

    return HttpResponseRedirect(hosted_checkout_response.redirect_url)


@login_required
@require_http_methods(["GET"])
def session_status(request: HttpRequest) -> HttpResponse:
    merchant_client = _create_cawl_client()
    hosted_checkout_status = merchant_client.hosted_checkout().get_hosted_checkout(
        request.GET.get("hostedCheckoutId", "")
    )
    status = hosted_checkout_status.created_payment_output.payment_status_category
    if status == "SUCCESSFUL":
        amount = (
            hosted_checkout_status.created_payment_output.payment.payment_output.amount_of_money.amount
            or 0
        )
        current_season = Season.objects.get(is_current=True)
        current_payment = Payment.objects.get(season=current_season, user=request.user)  # type: ignore [misc]
        if hasattr(current_payment, "cb_payment"):
            current_payment.cb_payment.amount += amount / 100
            current_payment.cb_payment.save()
        else:
            CBPayment(
                amount=amount / 100,
                transaction_type="CAWL",
                payment=current_payment,
            ).save()
        current_payment.save()  # Only to validate members
    elif status == "STATUS_UNKNOWN":
        email_sender = EmailSender(EmailEnum.PAYEMENT_UNKNOWN)
        email_sender.send_email(
            emails=[settings.DEFAULT_FROM_EMAIL, settings.SUPERUSER_EMAIL],
            username=request.user.username,
        )
    return render(
        request,
        "pages/session_status.html",
        context={
            "user": request.user,
            "status": status,
        },
    )


@require_http_methods(["GET"])
@login_required()
def user_edit(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "pages/user_edit.html",
        context={
            "user": request.user,
            "is_teacher": _is_teacher(request),
        },
    )


@require_http_methods(["GET"])
@login_required()
def user_edit_pwd(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "pages/user_edit_pwd.html",
        context={
            "user": request.user,
            "is_teacher": _is_teacher(request),
        },
    )


@require_http_methods(["GET"])
@login_required()
def user_delete(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "pages/user_delete.html",
        context={
            "user": request.user,
            "is_teacher": _is_teacher(request),
        },
    )


@require_http_methods(["GET"])
@login_required()
def member(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "pages/member.html",
        context={
            "user": request.user,
            "season": Season.objects.get(is_current=True),
            "is_teacher": _is_teacher(request),
        },
    )


@require_http_methods(["GET"])
@login_required()
def super_index(request: HttpRequest) -> HttpResponse:
    if request.user.is_superuser or _is_teacher(request):
        return render(
            request,
            "pages/index_super.html",
            context={
                "user": request.user,
                "is_teacher": _is_teacher(request),
            },
        )
    raise PermissionDenied


@require_http_methods(["GET"])
@login_required()
def course_mgmt(request: HttpRequest) -> HttpResponse:
    if request.user.is_superuser:
        return render(
            request,
            "pages/course_mgmt.html",
            context={"user": request.user, "is_teacher": _is_teacher(request)},
        )
    raise PermissionDenied


@require_http_methods(["GET"])
@login_required()
def member_mgmt(request: HttpRequest) -> HttpResponse:
    if request.user.is_superuser:
        return render(
            request,
            "pages/member_mgmt.html",
            context={
                "user": request.user,
                "season": Season.objects.get(is_current=True),
                "is_teacher": _is_teacher(request),
            },
        )
    raise PermissionDenied


@require_http_methods(["GET"])
@login_required()
def admin_mgmt(request: HttpRequest) -> HttpResponse:
    if request.user.is_superuser:
        return render(
            request,
            "pages/admin_mgmt.html",
            context={"user": request.user, "is_teacher": _is_teacher(request)},
        )
    raise PermissionDenied


@require_http_methods(["GET"])
@login_required()
def site_mgmt(request: HttpRequest) -> HttpResponse:
    if request.user.is_superuser:
        return render(
            request,
            "pages/site_mgmt.html",
            context={"user": request.user, "is_teacher": _is_teacher(request)},
        )
    raise PermissionDenied


@require_http_methods(["GET"])
@login_required()
def list_dl(request: HttpRequest) -> HttpResponse:
    if request.user.is_superuser:
        return render(
            request,
            "pages/list_dl.html",
            context={
                "user": request.user,
                "season": Season.objects.get(is_current=True),
                "is_teacher": _is_teacher(request),
            },
        )
    raise PermissionDenied


@require_http_methods(["GET"])
def about(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "pages/about.html",
        context={"user": request.user, "is_teacher": _is_teacher(request)},
    )


@require_http_methods(["GET"])
@login_required()
def download_pdf(request: HttpRequest) -> HttpResponse:
    filename = request.GET.get("doc")
    if not filename:
        raise Http404
    file_path = Path(f"{settings.STATIC_ROOT}/pdf/{filename}.pdf")
    if file_path.exists():
        with file_path.open("rb") as f:
            response = HttpResponse(f.read(), content_type="application/pdf")
            response["Content-Disposition"] = "inline; filename=" + filename
            return response
    raise Http404
