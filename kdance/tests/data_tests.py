from datetime import datetime, time, timedelta, timezone as tz
from django.utils import timezone

TESTUSER = "testuser"
TESTUSER_EMAIL = "test@kdance.com"
SUPERTESTUSER = "super_testuser"
SUPERTESTUSER_EMAIL = "testsuper@kdance.com"

COURSE = {
    "name": "Cha cha cha",
    "price": 10,
    "weekday": 0,
    "start_hour": time(10, 0),
    "end_hour": time(11, 0),
}

MEMBER = {
    "first_name": "Plip",
    "last_name": "Plop",
    "birthday": datetime(1900, 5, 1, tzinfo=tz.utc),
    "address": "Par ici",
    "city": "city",
    "postal_code": "31000",
    "email": "plip@plop.fr",
    "phone": "0987654321",
}

SEASON = {
    "pre_signup_start": timezone.now() - timedelta(days=4),
    "pre_signup_end": timezone.now() - timedelta(days=2),
    "signup_start": timezone.now() - timedelta(days=2),
    "signup_end": timezone.now() + timedelta(days=2),
    "ffd_a_amount": 0,
    "ffd_b_amount": 0,
    "ffd_c_amount": 0,
    "ffd_d_amount": 0,
}
