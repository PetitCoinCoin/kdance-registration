from pathlib import Path

import stripe
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.templatetags.static import static
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from members.models import GeneralSettings, Member, Payment, Season, CBPayment


def _is_teacher(request: HttpRequest) -> bool:
    return request.user.groups.filter(name=settings.TEACHER_GROUP_NAME).exists()


def __identify_products(user) -> tuple[list, int]:
    total_to_pay = 0
    adhesions = (
        Member.objects.annotate(num_courses=Count("active_courses"))
        .filter(
            user=user, season__is_current=True, is_validated=False, num_courses__gt=0
        )
        .count()
    )
    line_items = (
        [
            {
                "price": settings.STRIPE_ADHESION_ID,
                "quantity": adhesions,
            },
        ]
        if adhesions
        else []
    )
    total_to_pay += 10 * adhesions
    for member in user.member_set.filter(
        season__is_current=True, is_validated=False
    ).all():
        # Courses
        for course in member.active_courses.all():
            line_items.append(
                {
                    "price": course.stripe_price_id,
                    "quantity": 1,
                }
            )
            total_to_pay += course.price
        # Licenses
        if member.ffd_license:
            for licence in "abcd":
                if member.ffd_license == getattr(
                    member.season, f"ffd_{licence}_amount"
                ):
                    line_items.append(
                        {
                            "price": getattr(
                                member.season, f"ffd_{licence}_stripe_price_id"
                            ),
                            "quantity": 1,
                        }
                    )
                    total_to_pay += member.ffd_licence
                    break
    return line_items, total_to_pay


def __identify_discounts(user, total_before_discount) -> list:
    current_season = Season.objects.get(is_current=True)
    current_payment = Payment.objects.get(season=current_season, user=user)
    discount = total_before_discount - current_payment.due + current_payment.paid
    if discount:
        try:
            coupon = stripe.Coupon.create(
                duration="once",
                amount_off=int(discount * 100),
                currency="eur",
            )
            return [{"coupon": coupon.get("id", "")}]
        except Exception:
            return []
    return []


@require_http_methods(["GET"])
@login_required()
def index(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "pages/index.html",
        context={
            "user": request.user,
            "is_teacher": _is_teacher(request),
            "allow_new_member": GeneralSettings.get_solo().allow_new_member,
        },
    )


@require_http_methods(["GET"])
@login_required()
def checkout(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "pages/checkout.html",
        context={
            "user": request.user,
            "season": Season.objects.get(is_current=True),
            "stripe_pk": settings.STRIPE_PUBLIC_KEY,
            "bank_iban": settings.BANK_IBAN,
            "bank_bic": settings.BANK_BIC,
        },
    )


@csrf_exempt
@login_required()
@require_http_methods(["POST"])
def create_checkout_session(request: HttpRequest) -> JsonResponse:
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return_url = (
        f"{request.scheme}://{request.get_host()}"
        + "/session_status?session_id={CHECKOUT_SESSION_ID}"
    )
    line_items, total_before_discount = __identify_products(request.user)
    coupons = __identify_discounts(request.user, total_before_discount)
    try:
        checkout_session = stripe.checkout.Session.create(
            ui_mode="embedded",
            line_items=line_items,
            discounts=coupons,
            currency="eur",
            mode="payment",
            customer_email=request.user.email,  # type: ignore[union-attr]
            payment_method_types=["card"],
            return_url=return_url,
        )
        return JsonResponse({"clientSecret": checkout_session["client_secret"]})
    except Exception as e:
        return JsonResponse({"error": str(e)})


@login_required
@require_http_methods(["GET"])
def session_status(request: HttpRequest) -> HttpResponse:
    session = stripe.checkout.Session.retrieve(request.GET.get("session_id", ""))
    if session.status == "complete":
        amount = session.amount_total or 0
        current_season = Season.objects.get(is_current=True)
        current_payment = Payment.objects.get(season=current_season, user=request.user)  # type: ignore [misc]
        if hasattr(current_payment, "cb_payment"):
            current_payment.cb_payment.amount += amount / 100
            current_payment.cb_payment.save()
        else:
            CBPayment(
                amount=amount / 100,
                transaction_type="stripe",
                payment=current_payment,
            ).save()
        current_payment.save()  # Only to validate members
    return render(
        request,
        "pages/session_status.html",
        context={
            "user": request.user,
            "status": session.status,
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
    file_path = Path(static(f"pdf/{filename}.pdf"))
    file_path = Path(static(f"pdf/{filename}.pdf"))
    if file_path.exists():
        with file_path.open("rb") as f:
            response = HttpResponse(f.read(), content_type="application/pdf")
            response["Content-Disposition"] = "inline; filename=" + filename
            return response
    raise Http404
