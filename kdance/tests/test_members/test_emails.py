from copy import deepcopy
from datetime import date, time, timedelta
from unittest.mock import patch

import pytest

from django.conf import settings
from django.utils import timezone

from members.emails import EmailEnum, EmailSender
from members.models import Course, Season
from django.core.mail import EmailMultiAlternatives


USERNAME = "michel@plop.com"
NAME = "Michel"
SEASON = "2000-2001"
COURSE = "Eveil"
WEEKDAY = "Lundi"
START = "12h12"
URL = "www.plop.com"
TODAY = date.today()


class TestEmailSender:
    """Tests emails sending."""

    __test__ = False

    email_sender: EmailSender
    expected_kwargs: dict
    expected_subject: str
    expected_text: str
    expected_html: str

    def test_missing_kwargs(self):
        for field in self.expected_kwargs.keys():
            partial_kwargs = deepcopy(self.expected_kwargs)
            partial_kwargs.pop(field)
            with pytest.raises(
                ValueError, match=f"Un argument {field} est nécessaire pour cet email"
            ):
                self.email_sender.send_email([], **partial_kwargs)

    def test_build_subject(self):
        subject = self.email_sender.get_subject()(**self.expected_kwargs)
        assert subject == self.expected_subject

    def test_build_text(self):
        text = self.email_sender.get_build_text()(**self.expected_kwargs)
        assert text == self.expected_text

    def test_build_html(self):
        html = self.email_sender.get_build_html()(**self.expected_kwargs)
        assert html == self.expected_html

    @patch.object(EmailMultiAlternatives, "send")
    def test_send(self, mock_send):
        mock_send.return_value = True
        self.email_sender.send_email([], **self.expected_kwargs)
        assert mock_send.called is True


class TestEmailCreateUser(TestEmailSender):
    __test__ = True

    email_sender = EmailSender(EmailEnum.CREATE_USER)
    expected_kwargs = {"username": USERNAME}
    expected_subject = "Création d'un compte K'Dance"
    expected_text = f"""
Bonjour,

Vous venez de créer votre compte K'Dance! Utilisez votre email ({USERNAME}) comme identifiant pour vous connecter.
Vous pouvez désormais ajouter et gérer les adhérents de votre famille pour chaque nouvelle saison.
N'oubliez pas d'utiliser également cet espace pour mettre à jour vos coordonnées en cas de changement.

Bonne journée et à bientôt,
Tech K'Dance
"""
    expected_html = f"""
<p>Bonjour,</p>
<p>
  Vous venez de créer votre compte K'Dance! Utilisez votre email ({USERNAME}) comme identifiant pour vous connecter.
  Vous pouvez désormais ajouter et gérer les adhérents de votre famille pour chaque nouvelle saison.
</p>
<p>
  N'oubliez pas d'utiliser également cet espace pour mettre à jour vos coordonnées en cas de changement.
</p>
<p>
  Bonne journée et à bientôt,<br />
  Tech K'Dance
</p>
"""


class TestEmailDeleteUser(TestEmailSender):
    __test__ = True

    email_sender = EmailSender(EmailEnum.DELETE_USER)
    expected_kwargs = {"username": USERNAME}
    expected_subject = "Suppression de votre compte K'Dance"
    expected_text = f"""
Bonjour,

Votre compte K'Dance associé à l'adresse {USERNAME} a bien été supprimé.

Bonne journée et à bientôt,
Tech K'Dance
"""
    expected_html = f"""
<p>Bonjour,</p>
<p>
  Votre compte K'Dance associé à l'adresse {USERNAME} a bien été supprimé.
</p>
<p>
  Bonne journée et à bientôt,<br />
  Tech K'Dance
</p>
"""


class TestEmailCreateMember(TestEmailSender):
    __test__ = True

    email_sender = EmailSender(EmailEnum.CREATE_MEMBER)
    expected_kwargs = {"full_name": NAME, "season_year": SEASON}
    expected_subject = f"Inscription d'un adhérent K'Dance pour la saison {SEASON}"
    expected_text = f"""
Bonjour,

Vous venez d'inscrire {NAME} pour la saison {SEASON}.
Vous n'avez cependant pas de cours pour le moment.

Bonne journée et à bientôt,
Tech K'Dance
"""
    expected_html = f"""
<p>Bonjour,</p>
<p>
  Vous venez d'inscrire {NAME} pour la saison {SEASON}.<br />
  Vous n'avez cependant pas de cours pour le moment.
</p>
<p>
  Bonne journée et à bientôt,<br />
  Tech K'Dance
</p>
"""

    def set_course(self):
        season, _ = Season.objects.get_or_create(
            year="1900-1901",
            pre_signup_start=(timezone.now() - timedelta(days=2)).strftime(
                settings.DATE_FORMAT
            ),
            pre_signup_end=(timezone.now() + timedelta(days=2)).strftime(
                settings.DATE_FORMAT
            ),
            ffd_a_amount=0,
            ffd_b_amount=0,
            ffd_c_amount=0,
            ffd_d_amount=0,
        )
        course, _ = Course.objects.get_or_create(
            name=COURSE,
            season=season,
            price=10,
            weekday=0,
            start_hour=time(10, 0),
            end_hour=time(11, 0),
        )
        return course

    @pytest.mark.django_db
    def test_build_text_with_active(self):
        active_courses = [self.set_course()]
        text = self.email_sender.get_build_text()(
            **self.expected_kwargs,
            active_courses=active_courses,
        )
        assert (
            text
            == f"""
Bonjour,

Vous venez d'inscrire {NAME} pour la saison {SEASON}.

Cours choisi(s):
{COURSE}
Notez que l'inscription ne sera validée qu'après réception du paiement.


Bonne journée et à bientôt,
Tech K'Dance
"""
        )

    @pytest.mark.django_db
    def test_build_html_with_active(self):
        active_courses = [self.set_course()]
        html = self.email_sender.get_build_html()(
            **self.expected_kwargs,
            active_courses=active_courses,
        )
        assert (
            html
            == f"""
<p>Bonjour,</p>
<p>
  Vous venez d'inscrire {NAME} pour la saison {SEASON}.<br />
  </p>
<p>
  Cours choisi(s):<br />
  {COURSE}<br />
  Notez que l'inscription ne sera validée qu'après réception du paiement.

</p>
<p>
  Bonne journée et à bientôt,<br />
  Tech K'Dance
</p>
"""
        )

    @pytest.mark.django_db
    def test_build_text_with_waiting(self):
        waiting_courses = [self.set_course()]
        text = self.email_sender.get_build_text()(
            **self.expected_kwargs,
            waiting_courses=waiting_courses,
        )
        assert (
            text
            == f"""
Bonjour,

Vous venez d'inscrire {NAME} pour la saison {SEASON}.
Vous n'avez cependant pas de cours pour le moment.

Cours en liste d'attente:
{COURSE}
Nous reviendrons vers vous si une place se libère ou si le cours est dédoublé.


Bonne journée et à bientôt,
Tech K'Dance
"""
        )

    @pytest.mark.django_db
    def test_build_html_with_waiting(self):
        waiting_courses = [self.set_course()]
        html = self.email_sender.get_build_html()(
            **self.expected_kwargs,
            waiting_courses=waiting_courses,
        )
        assert (
            html
            == f"""
<p>Bonjour,</p>
<p>
  Vous venez d'inscrire {NAME} pour la saison {SEASON}.<br />
  Vous n'avez cependant pas de cours pour le moment.
</p>
<p>
  Cours en liste d'attente:<br />
  {COURSE}<br />
  Nous reviendrons vers vous si une place se libère ou si le cours est dédoublé.

</p>
<p>
  Bonne journée et à bientôt,<br />
  Tech K'Dance
</p>
"""
        )

    @pytest.mark.django_db
    def test_build_text_with_both(self):
        course = self.set_course()
        active_courses = [course, course]
        waiting_courses = [course, course]
        text = self.email_sender.get_build_text()(
            **self.expected_kwargs,
            active_courses=active_courses,
            waiting_courses=waiting_courses,
        )
        assert (
            text
            == f"""
Bonjour,

Vous venez d'inscrire {NAME} pour la saison {SEASON}.

Cours choisi(s):
{COURSE}
{COURSE}
Notez que l'inscription ne sera validée qu'après réception du paiement.


Cours en liste d'attente:
{COURSE}
{COURSE}
Nous reviendrons vers vous si une place se libère ou si le cours est dédoublé.


Bonne journée et à bientôt,
Tech K'Dance
"""
        )

    @pytest.mark.django_db
    def test_build_html_with_both(self):
        course = self.set_course()
        active_courses = [course, course]
        waiting_courses = [course, course]
        html = self.email_sender.get_build_html()(
            **self.expected_kwargs,
            active_courses=active_courses,
            waiting_courses=waiting_courses,
        )
        assert (
            html
            == f"""
<p>Bonjour,</p>
<p>
  Vous venez d'inscrire {NAME} pour la saison {SEASON}.<br />
  </p>
<p>
  Cours choisi(s):<br />
  {COURSE}<br />{COURSE}<br />
  Notez que l'inscription ne sera validée qu'après réception du paiement.

</p>
<p>
  Cours en liste d'attente:<br />
  {COURSE}<br />{COURSE}<br />
  Nous reviendrons vers vous si une place se libère ou si le cours est dédoublé.

</p>
<p>
  Bonne journée et à bientôt,<br />
  Tech K'Dance
</p>
"""
        )


class TestEmailDeleteMember(TestEmailSender):
    __test__ = True

    email_sender = EmailSender(EmailEnum.DELETE_MEMBER)
    expected_kwargs = {"full_name": NAME, "season_year": SEASON}
    expected_subject = f"Suppression d'un adhérent K'Dance pour la saison {SEASON}"
    expected_text = f"""
Bonjour,

L'adhérent {NAME} a été supprimé pour la saison {SEASON}.
Si c'est une erreur, vous pouvez toujours refaire l'inscription ou contacter l'équipe K'Dance.

Bonne journée et à bientôt,
Tech K'Dance
"""
    expected_html = f"""
<p>Bonjour,</p>
<p>
  L'adhérent {NAME} a été supprimé pour la saison {SEASON}.
  Si c'est une erreur, vous pouvez toujours refaire l'inscription ou contacter l'équipe K'Dance.
</p>
<p>
  Bonne journée et à bientôt,<br />
  Tech K'Dance
</p>
"""


class TestEmailPreSignupWarning(TestEmailSender):
    __test__ = True

    email_sender = EmailSender(EmailEnum.PRE_SIGNUP_WARNING)
    expected_kwargs = {"username": USERNAME, "full_name": NAME, "birthday": TODAY}
    expected_subject = "Suspicion de pré-inscription frauduleuse: à vérifier"
    expected_text = f"""
Bonjour,

L'utilisateur {USERNAME} a effectué une pré-inscription douteuse. L'adhérent suivant n'a pas été retrouvé dans les données de la saison précédente:
{NAME}, né(e) le {TODAY}

Bonne journée et à bientôt,
Tech K'Dance
"""
    expected_html = f"""
<p>Bonjour,</p>
<p>
  L'utilisateur {USERNAME} a effectué une pré-inscription douteuse. L'adhérent suivant n'a pas été retrouvé dans les données de la saison précédente:<br />
  {NAME}, né(e) le {TODAY}
</p>
<p>
  Bonne journée et à bientôt,<br />
  Tech K'Dance
</p>
"""


class TestEmailWaitingToActive(TestEmailSender):
    __test__ = True

    email_sender = EmailSender(EmailEnum.WAITING_TO_ACTIVE_COURSE)
    expected_kwargs = {
        "full_name": NAME,
        "course_name": COURSE,
        "weekday": WEEKDAY,
        "start_hour": START,
        "with_next_course_warning": False,
    }
    expected_subject = f"Vous avez obtenu une place pour le cours {COURSE}!"
    expected_text = f"""
Bonjour,

Une place s'est libérée, et {NAME} a pu être inscrit(e) au cours {COURSE} du {WEEKDAY} à {START}.
L'inscription ne sera finalisée qu'à réception du paiement et des éventuels documents restants. Connectez vous à votre compte (https://adherents.association-kdance.fr/) pour un statut détaillé.

Bonne journée et à bientôt,
Tech K'Dance
"""
    expected_html = f"""
<p>Bonjour,</p>
<p>
  Une place s'est libérée, et {NAME} a pu être inscrit(e) au cours {COURSE} du {WEEKDAY} à {START}.<br />
  L'inscription ne sera finalisée qu'à réception du paiement et des éventuels documents restants. Connectez vous à <a href="https://adherents.association-kdance.fr/" target="_blank">votre compte</a> pour un statut détaillé.
</p>
<p>
  Bonne journée et à bientôt,<br />
  Tech K'Dance
</p>
"""

    @pytest.mark.django_db
    def test_build_text_with_warning(self):
        self.expected_kwargs["with_next_course_warning"] = True
        text = self.email_sender.get_build_text()(
            **self.expected_kwargs,
        )
        assert (
            text
            == f"""
Bonjour,

Une place s'est libérée, et {NAME} a pu être inscrit(e) au cours {COURSE} du {WEEKDAY} à {START}.
L'inscription ne sera finalisée qu'à réception du paiement et des éventuels documents restants. Si le paiement n'est pas effectué avant votre prochain cours, l'inscription sera annulée et votre place donnée à la personne suivante sur la liste d'attente. Connectez vous à votre compte (https://adherents.association-kdance.fr/) pour un statut détaillé.

Bonne journée et à bientôt,
Tech K'Dance
"""
        )
        self.expected_kwargs["with_next_course_warning"] = False

    @pytest.mark.django_db
    def test_build_html_with_warning(self):
        self.expected_kwargs["with_next_course_warning"] = True
        html = self.email_sender.get_build_html()(
            **self.expected_kwargs,
        )
        assert (
            html
            == f"""
<p>Bonjour,</p>
<p>
  Une place s'est libérée, et {NAME} a pu être inscrit(e) au cours {COURSE} du {WEEKDAY} à {START}.<br />
  L'inscription ne sera finalisée qu'à réception du paiement et des éventuels documents restants. <strong>Si le paiement n'est pas effectué avant votre prochain cours, l'inscription sera annulée et votre place donnée à la personne suivante sur la liste d'attente. </strong>Connectez vous à <a href="https://adherents.association-kdance.fr/" target="_blank">votre compte</a> pour un statut détaillé.
</p>
<p>
  Bonne journée et à bientôt,<br />
  Tech K'Dance
</p>
"""
        )
        self.expected_kwargs["with_next_course_warning"] = False


class TestEmailResetPassword(TestEmailSender):
    __test__ = True

    email_sender = EmailSender(EmailEnum.RESET_PWD)
    expected_kwargs = {"url": URL}
    expected_subject = "Réinitialisation du mot de passe K'Dance"
    expected_text = f"""
Bonjour,

Vous venez de faire une demande de réinitialisation de mot de passe pour votre compte K'Dance ?
Veuillez cliquer sur le lien suivant, ou le copier-coller dans votre navigateur: {URL}
Ce lien restera valide 30 minutes.

Si vous n'êtes pas à l'origine de cette demande, vous pouvez ignorer cet email, votre mot de passe restera inchangé.

Bonne journée et à bientôt,
Tech K'Dance
"""
    expected_html = f"""
<p>Bonjour,</p>
<p>
  Vous venez de faire une demande de réinitialisation de mot de passe pour votre compte K'Dance ?
  Veuillez cliquer sur le lien suivant, qui restera valide pendant 30 minutes:
  <a href="{URL}">
    {URL}
  </a>
</p>
<p>Si vous n'êtes pas à l'origine de cette demande, vous pouvez ignorer cet email, votre mot de passe restera
  inchangé.</p>
<p>
  Bonne journée et à bientôt,<br />
  Tech K'Dance
</p>
"""


class TestEmailPaymentUnknown(TestEmailSender):
    __test__ = True

    email_sender = EmailSender(EmailEnum.PAYMENT_UNKNOWN)
    expected_kwargs = {"username": USERNAME}
    expected_subject = "Statut de paiement inconnu"
    expected_text = f"""
Bonjour,

Il semble que le paiement de {USERNAME} soit revenu avec "STATUS_UNKNOWN". Merci d'investiguer.

Bonne journée et à bientôt,
Tech K'Dance
"""
    expected_html = f"""
<p>Bonjour,</p>
<p>
  Il semble que le paiement de {USERNAME} soit revenu avec "STATUS_UNKNOWN". Merci d'investiguer.
</p>
<p>
  Bonne journée et à bientôt,<br />
  Tech K'Dance
</p>
"""
