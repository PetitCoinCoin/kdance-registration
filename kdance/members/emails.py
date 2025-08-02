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

from enum import Enum
from typing import Callable

import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

_logger = logging.getLogger(__name__)


class EmailEnum(Enum):
    CREATE_USER = "create_user"
    DELETE_USER = "delete_user"
    UPDATE_USER_EMAIL = "email_user"
    CREATE_MEMBER = "create member"
    DELETE_MEMBER = "delete member"
    COURSE_CANCELLED = "course_cancelled"
    COURSES_UPDATE = "courses_update"
    PAYMENT_UNKNOWN = "payment_unknown"
    PRE_SIGNUP_WARNING = "pre signup warning"
    WAITING_TO_ACTIVE_COURSE = "waiting to active course"
    WAITING_LIST_INCONSISTENCY = "waiting_list_inconsistency"
    RESET_PWD = "reset_password"


class EmailSender:
    def __init__(self, email_type: EmailEnum) -> None:
        self.type = email_type
        self.build_subject = self.get_subject()
        self.build_text = self.get_build_text()
        self.build_html = self.get_build_html()

    def send_email(self, emails: list, **kwargs) -> None:
        _logger.info("Envoi d'un email: %s", self.type.value)
        mail = EmailMultiAlternatives(
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=emails,
            reply_to=[settings.DEFAULT_FROM_EMAIL],
            subject=self.build_subject(**kwargs),
            body=self.build_text(**kwargs),
        )
        mail.attach_alternative(self.build_html(**kwargs), "text/html")
        sent = mail.send()
        if not sent:
            _logger.warning(
                "Echec de l'envoi du mail %s pour %s",
                self.type.value,
                emails,
            )

    def get_subject(self) -> Callable:
        match self.type:
            case EmailEnum.CREATE_USER:
                return self.__subject_create_user
            case EmailEnum.DELETE_USER:
                return self.__subject_delete_user
            case EmailEnum.UPDATE_USER_EMAIL:
                return self.__subject_email_user
            case EmailEnum.CREATE_MEMBER:
                return self.__subject_create_member
            case EmailEnum.DELETE_MEMBER:
                return self.__subject_delete_member
            case EmailEnum.COURSE_CANCELLED:
                return self.__subject_course_cancelled
            case EmailEnum.COURSES_UPDATE:
                return self.__subject_courses_update
            case EmailEnum.PAYMENT_UNKNOWN:
                return self.__subject_payment_unknown
            case EmailEnum.PRE_SIGNUP_WARNING:
                return self.__subject_pre_signup_warning
            case EmailEnum.WAITING_TO_ACTIVE_COURSE:
                return self.__subject_waiting_active
            case EmailEnum.WAITING_LIST_INCONSISTENCY:
                return self.__subject_waiting_inconsistent
            case EmailEnum.RESET_PWD:
                return self.__subject_reset_password
            case _:
                raise ValueError("Type d'email inconnu")

    def get_build_text(self) -> Callable:
        match self.type:
            case EmailEnum.CREATE_USER:
                return self.__build_text_create_user
            case EmailEnum.DELETE_USER:
                return self.__build_text_delete_user
            case EmailEnum.UPDATE_USER_EMAIL:
                return self.__build_text_email_user
            case EmailEnum.CREATE_MEMBER:
                return self.__build_text_create_member
            case EmailEnum.DELETE_MEMBER:
                return self.__build_text_delete_member
            case EmailEnum.COURSE_CANCELLED:
                return self.__build_text_course_cancelled
            case EmailEnum.COURSES_UPDATE:
                return self.__build_text_courses_update
            case EmailEnum.PAYMENT_UNKNOWN:
                return self.__build_text_payment_unknown
            case EmailEnum.PRE_SIGNUP_WARNING:
                return self.__build_text_pre_signup_warning
            case EmailEnum.WAITING_TO_ACTIVE_COURSE:
                return self.__build_text_waiting_active
            case EmailEnum.WAITING_LIST_INCONSISTENCY:
                return self.__build_text_waiting_inconsistent
            case EmailEnum.RESET_PWD:
                return self.__build_text_reset_password
            case _:
                raise ValueError("Type d'email inconnu")

    def get_build_html(self) -> Callable:
        match self.type:
            case EmailEnum.CREATE_USER:
                return self.__build_html_create_user
            case EmailEnum.DELETE_USER:
                return self.__build_html_delete_user
            case EmailEnum.UPDATE_USER_EMAIL:
                return self.__build_html_email_user
            case EmailEnum.CREATE_MEMBER:
                return self.__build_html_create_member
            case EmailEnum.DELETE_MEMBER:
                return self.__build_html_delete_member
            case EmailEnum.COURSE_CANCELLED:
                return self.__build_html_course_cancelled
            case EmailEnum.COURSES_UPDATE:
                return self.__build_html_courses_update
            case EmailEnum.PAYMENT_UNKNOWN:
                return self.__build_html_payment_unknown
            case EmailEnum.PRE_SIGNUP_WARNING:
                return self.__build_html_pre_signup_warning
            case EmailEnum.WAITING_TO_ACTIVE_COURSE:
                return self.__build_html_waiting_active
            case EmailEnum.WAITING_LIST_INCONSISTENCY:
                return self.__build_html_waiting_inconsistent
            case EmailEnum.RESET_PWD:
                return self.__build_html_reset_password
            case _:
                raise ValueError("Type d'email inconnu")

    @staticmethod
    def __subject_create_user(**_k) -> str:
        return "Création d'un compte K'Dance"

    @staticmethod
    def __subject_delete_user(**_k) -> str:
        return "Suppression de votre compte K'Dance"

    @staticmethod
    def __subject_email_user(**_k) -> str:
        return "Mise à jour d'un email utilisateur"

    @staticmethod
    def __subject_create_member(**kwargs) -> str:
        if not kwargs.get("season_year"):
            raise ValueError("Un argument season_year est nécessaire pour cet email")
        return (
            f"Inscription d'un adhérent K'Dance pour la saison {kwargs['season_year']}"
        )

    @staticmethod
    def __subject_delete_member(**kwargs) -> str:
        if not kwargs.get("season_year"):
            raise ValueError("Un argument season_year est nécessaire pour cet email")
        return (
            f"Suppression d'un adhérent K'Dance pour la saison {kwargs['season_year']}"
        )

    @staticmethod
    def __subject_course_cancelled(**kwargs) -> str:
        if not kwargs.get("course_name"):
            raise ValueError("Un argument course_name est nécessaire pour cet email")
        return f"Votre inscription au cours {kwargs['course_name']} a été annulée"

    @staticmethod
    def __subject_courses_update(**kwargs) -> str:
        return "Mise à jour de vos cours K'Dance"

    @staticmethod
    def __subject_pre_signup_warning(**kwargs) -> str:
        return "Suspicion de pré-inscription frauduleuse: à vérifier"

    @staticmethod
    def __subject_waiting_active(**kwargs) -> str:
        if not kwargs.get("course_name"):
            raise ValueError("Un argument course_name est nécessaire pour cet email")
        return f"Vous avez obtenu une place pour le cours {kwargs['course_name']}!"

    @staticmethod
    def __subject_waiting_inconsistent(**kwargs) -> str:
        return "Problème d'incohérence entre les listes d'attente"

    @staticmethod
    def __subject_reset_password(**_k) -> str:
        return "Réinitialisation du mot de passe K'Dance"

    @staticmethod
    def __subject_payment_unknown(**_k) -> str:
        return "Statut de paiement inconnu"

    @staticmethod
    def __build_text_create_user(**kwargs) -> str:
        if not kwargs.get("username"):
            raise ValueError("Un argument username est nécessaire pour cet email")
        return f"""
Bonjour,

Vous venez de créer votre compte K'Dance! Utilisez votre email ({kwargs["username"]}) comme identifiant pour vous connecter.
Vous pouvez désormais ajouter et gérer les adhérents de votre famille pour chaque nouvelle saison.
N'oubliez pas d'utiliser également cet espace pour mettre à jour vos coordonnées en cas de changement.

Bonne journée et à bientôt,
Tech K'Dance
"""

    @staticmethod
    def __build_text_delete_user(**kwargs) -> str:
        if not kwargs.get("username"):
            raise ValueError("Un argument username est nécessaire pour cet email")
        return f"""
Bonjour,

Votre compte K'Dance associé à l'adresse {kwargs["username"]} a bien été supprimé.

Bonne journée et à bientôt,
Tech K'Dance
"""

    @staticmethod
    def __build_text_email_user(**kwargs) -> str:
        if not kwargs.get("username"):
            raise ValueError("Un argument username est nécessaire pour cet email")
        if not isinstance(kwargs.get("members"), list):
            raise ValueError("Un argument members est nécessaire pour cet email")
        return f"""
Bonjour,

Le responsable de {", ".join(kwargs["members"])} a mis à jour son adresse email: {kwargs["username"]}.

Bonne journée et à bientôt,
Tech K'Dance
"""

    @staticmethod
    def __build_text_create_member(**kwargs) -> str:
        if not kwargs.get("full_name"):
            raise ValueError("Un argument full_name est nécessaire pour cet email")
        if not kwargs.get("season_year"):
            raise ValueError("Un argument season_year est nécessaire pour cet email")
        course_message = "Vous n'avez cependant pas de cours pour le moment."
        if kwargs.get("active_courses"):
            course_message = f"""
Cours choisi(s):
{chr(10).join([c.name for c in kwargs["active_courses"]])}
Notez que l'inscription ne sera validée qu'après réception du paiement.
"""
        if kwargs.get("waiting_courses"):
            course_message += f"""

Cours en liste d'attente:
{chr(10).join([c.name for c in kwargs["waiting_courses"]])}
Nous reviendrons vers vous si une place se libère ou si le cours est dédoublé.
"""
        message = f"""
Bonjour,

Vous venez d'inscrire {kwargs["full_name"]} pour la saison {kwargs["season_year"]}.
{course_message}

Bonne journée et à bientôt,
Tech K'Dance
"""
        return message

    @staticmethod
    def __build_text_delete_member(**kwargs) -> str:
        if not kwargs.get("full_name"):
            raise ValueError("Un argument full_name est nécessaire pour cet email")
        if not kwargs.get("season_year"):
            raise ValueError("Un argument season_year est nécessaire pour cet email")
        return f"""
Bonjour,

L'adhérent {kwargs["full_name"]} a été supprimé pour la saison {kwargs["season_year"]}.
Si c'est une erreur, vous pouvez toujours refaire l'inscription ou contacter l'équipe K'Dance.

Bonne journée et à bientôt,
Tech K'Dance
"""

    @staticmethod
    def __build_text_course_cancelled(**kwargs) -> str:
        if not kwargs.get("full_name"):
            raise ValueError("Un argument full_name est nécessaire pour cet email")
        if not kwargs.get("course_name"):
            raise ValueError("Un argument course_name est nécessaire pour cet email")
        if kwargs.get("cancel_refund") is None:
            raise ValueError("Un argument cancel_refund est nécessaire pour cet email")
        refund = kwargs["cancel_refund"]
        msg_refund = (
            ""
            if not refund
            else f" Un remboursement de {refund}€ sera effectué. Merci de nous faire parvenir un RIB."
        )
        return f"""
Bonjour,

L'inscription de {kwargs["full_name"]} au cours {kwargs["course_name"]} a bien été annulée.{msg_refund}
Si cette annulation est une erreur, merci de contacter l'équipe K'Dance.

Bonne journée et à bientôt,
Tech K'Dance
"""

    @staticmethod
    def __build_text_courses_update(**kwargs) -> str:
        if not kwargs.get("full_name"):
            raise ValueError("Un argument full_name est nécessaire pour cet email")
        if kwargs.get("courses_removed") is None:
            raise ValueError(
                "Un argument courses_removed est nécessaire pour cet email"
            )
        if kwargs.get("courses_added_active") is None:
            raise ValueError(
                "Un argument courses_added_active est nécessaire pour cet email"
            )
        if kwargs.get("courses_added_waiting") is None:
            raise ValueError(
                "Un argument courses_added_waiting est nécessaire pour cet email"
            )
        course_message = ""
        if kwargs.get("courses_added_active"):
            course_message += f"""
Cours choisi(s):
{chr(10).join([c.name for c in kwargs["courses_added_active"]])}
"""
        if kwargs.get("courses_added_waiting"):
            course_message += f"""
Cours en liste d'attente:
{chr(10).join([c.name for c in kwargs["courses_added_waiting"]])}
Nous reviendrons vers vous si une place se libère ou si le cours est dédoublé.
"""
        if kwargs.get("courses_removed"):
            course_message += f"""
Cours supprimé(s):
{chr(10).join([c.name for c in kwargs["courses_removed"]])}
"""
        message = f"""
Bonjour,

Les cours de danse de {kwargs["full_name"]} ont été mis à jour.
{course_message}
Bonne journée et à bientôt,
Tech K'Dance
"""
        return message

    @staticmethod
    def __build_text_pre_signup_warning(**kwargs) -> str:
        if not kwargs.get("username"):
            raise ValueError("Un argument username est nécessaire pour cet email")
        if not kwargs.get("full_name"):
            raise ValueError("Un argument full_name est nécessaire pour cet email")
        if not kwargs.get("birthday"):
            raise ValueError("Un argument birthday est nécessaire pour cet email")
        return f"""
Bonjour,

L'utilisateur {kwargs["username"]} a effectué une pré-inscription douteuse. L'adhérent suivant n'a pas été retrouvé dans les données de la saison précédente:
{kwargs["full_name"]}, né(e) le {kwargs["birthday"]}

Bonne journée et à bientôt,
Tech K'Dance
"""

    @staticmethod
    def __build_text_waiting_active(**kwargs) -> str:
        if not kwargs.get("full_name"):
            raise ValueError("Un argument full_name est nécessaire pour cet email")
        if not kwargs.get("course_name"):
            raise ValueError("Un argument course_name est nécessaire pour cet email")
        if not kwargs.get("weekday"):
            raise ValueError("Un argument weekday est nécessaire pour cet email")
        if not kwargs.get("start_hour"):
            raise ValueError("Un argument start_hour est nécessaire pour cet email")
        return f"""
Bonjour,

Une place s'est libérée, et {kwargs["full_name"]} a pu être inscrit(e) au cours {kwargs["course_name"]} du {kwargs["weekday"]} à {kwargs["start_hour"]}.
L'inscription ne sera finalisée qu'à réception du paiement et des éventuels documents restants. {"Si le paiement n'est pas effectué avant votre prochain cours, l'inscription sera annulée et votre place donnée à la personne suivante sur la liste d'attente. " if kwargs.get("with_next_course_warning") else ""}Connectez vous à votre compte (https://adherents.association-kdance.fr/) pour un statut détaillé.

Bonne journée et à bientôt,
Tech K'Dance
"""

    @staticmethod
    def __build_text_waiting_inconsistent(**kwargs) -> str:
        if not kwargs.get("member"):
            raise ValueError("Un argument member est nécessaire pour cet email")
        if not kwargs.get("course"):
            raise ValueError("Un argument course est nécessaire pour cet email")
        member = kwargs["member"]
        return f"""
Bonjour,

Il y a des incohérences dans la gestion des listes d'attente.
Cours concerné: {kwargs["course"]}
Membre concerné: {member}
course.members_waiting:{ ", ".join(kwargs["course"].members_waiting.all())}
member.waiting_courses: {"aucun" if isinstance(member, str) else ", ".join(kwargs["member"].waiting_courses.all())}

Tech K'Dance
"""

    @staticmethod
    def __build_text_reset_password(**kwargs) -> str:
        if not kwargs.get("url"):
            raise ValueError("Un argument url est nécessaire pour cet email")
        return f"""
Bonjour,

Vous venez de faire une demande de réinitialisation de mot de passe pour votre compte K'Dance ?
Veuillez cliquer sur le lien suivant, ou le copier-coller dans votre navigateur: {kwargs["url"]}
Ce lien restera valide 30 minutes.

Si vous n'êtes pas à l'origine de cette demande, vous pouvez ignorer cet email, votre mot de passe restera inchangé.

Bonne journée et à bientôt,
Tech K'Dance
"""

    @staticmethod
    def __build_text_payment_unknown(**kwargs) -> str:
        if not kwargs.get("username"):
            raise ValueError("Un argument username est nécessaire pour cet email")
        return f"""
Bonjour,

Il semble que le paiement de {kwargs["username"]} soit revenu avec "STATUS_UNKNOWN". Merci d'investiguer.

Bonne journée et à bientôt,
Tech K'Dance
"""

    @staticmethod
    def __build_html_create_user(**kwargs) -> str:
        if not kwargs.get("username"):
            raise ValueError("Un argument username est nécessaire pour cet email")
        return f"""
<p>Bonjour,</p>
<p>
  Vous venez de créer votre compte K'Dance! Utilisez votre email ({kwargs["username"]}) comme identifiant pour vous connecter.
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

    @staticmethod
    def __build_html_delete_user(**kwargs) -> str:
        if not kwargs.get("username"):
            raise ValueError("Un argument username est nécessaire pour cet email")
        return f"""
<p>Bonjour,</p>
<p>
  Votre compte K'Dance associé à l'adresse {kwargs["username"]} a bien été supprimé.
</p>
<p>
  Bonne journée et à bientôt,<br />
  Tech K'Dance
</p>
"""

    @staticmethod
    def __build_html_email_user(**kwargs) -> str:
        if not kwargs.get("username"):
            raise ValueError("Un argument username est nécessaire pour cet email")
        if not isinstance(kwargs.get("members"), list):
            raise ValueError("Un argument members est nécessaire pour cet email")
        return f"""
<p>Bonjour,</p>
<p>
  Le responsable de {", ".join(kwargs["members"])} a mis à jour son adresse email: {kwargs["username"]}.
</p>
<p>
  Bonne journée et à bientôt,<br />
  Tech K'Dance
</p>
"""

    @staticmethod
    def __build_html_create_member(**kwargs) -> str:
        if not kwargs.get("full_name"):
            raise ValueError("Un argument full_name est nécessaire pour cet email")
        if not kwargs.get("season_year"):
            raise ValueError("Un argument season_year est nécessaire pour cet email")
        course_message = "Vous n'avez cependant pas de cours pour le moment."
        if kwargs.get("active_courses"):
            course_message = f"""</p>
<p>
  Cours choisi(s):<br />
  {"<br />".join([c.name for c in kwargs["active_courses"]])}<br />
  Notez que l'inscription ne sera validée qu'après réception du paiement.
"""
        if kwargs.get("waiting_courses"):
            course_message += f"""
</p>
<p>
  Cours en liste d'attente:<br />
  {"<br />".join([c.name for c in kwargs["waiting_courses"]])}<br />
  Nous reviendrons vers vous si une place se libère ou si le cours est dédoublé.
"""
        message = f"""
<p>Bonjour,</p>
<p>
  Vous venez d'inscrire {kwargs["full_name"]} pour la saison {kwargs["season_year"]}.<br />
  {course_message}
</p>
<p>
  Bonne journée et à bientôt,<br />
  Tech K'Dance
</p>
"""
        return message

    @staticmethod
    def __build_html_delete_member(**kwargs) -> str:
        if not kwargs.get("full_name"):
            raise ValueError("Un argument full_name est nécessaire pour cet email")
        if not kwargs.get("season_year"):
            raise ValueError("Un argument season_year est nécessaire pour cet email")
        return f"""
<p>Bonjour,</p>
<p>
  L'adhérent {kwargs["full_name"]} a été supprimé pour la saison {kwargs["season_year"]}.
  Si c'est une erreur, vous pouvez toujours refaire l'inscription ou contacter l'équipe K'Dance.
</p>
<p>
  Bonne journée et à bientôt,<br />
  Tech K'Dance
</p>
"""

    @staticmethod
    def __build_html_course_cancelled(**kwargs) -> str:
        if not kwargs.get("full_name"):
            raise ValueError("Un argument full_name est nécessaire pour cet email")
        if not kwargs.get("course_name"):
            raise ValueError("Un argument course_name est nécessaire pour cet email")
        if kwargs.get("cancel_refund") is None:
            raise ValueError("Un argument cancel_refund est nécessaire pour cet email")
        refund = kwargs["cancel_refund"]
        msg_refund = (
            ""
            if not refund
            else f" Un remboursement de {refund}€ sera effectué. Merci de nous faire parvenir un RIB."
        )
        return f"""
<p>Bonjour,</p>
<p>
  L'inscription de {kwargs["full_name"]} au cours {kwargs["course_name"]} a bien été annulée.{msg_refund}<br />
  Si cette annulation est une erreur, merci de contacter l'équipe K'Dance.
</p>
<p>
  Bonne journée et à bientôt,<br />
  Tech K'Dance
</p>
"""

    @staticmethod
    def __build_html_courses_update(**kwargs) -> str:
        if not kwargs.get("full_name"):
            raise ValueError("Un argument full_name est nécessaire pour cet email")
        if kwargs.get("courses_removed") is None:
            raise ValueError(
                "Un argument courses_removed est nécessaire pour cet email"
            )
        if kwargs.get("courses_added_active") is None:
            raise ValueError(
                "Un argument courses_added_active est nécessaire pour cet email"
            )
        if kwargs.get("courses_added_waiting") is None:
            raise ValueError(
                "Un argument courses_added_waiting est nécessaire pour cet email"
            )
        course_message = ""
        if kwargs.get("courses_added_active"):
            course_message += f"""</p>
<p>
  Cours choisi(s):<br />
  {"<br />".join([c.name for c in kwargs["courses_added_active"]])}
"""
        if kwargs.get("courses_added_waiting"):
            course_message += f"""</p>
<p>
  Cours en liste d'attente:<br />
  {"<br />".join([c.name for c in kwargs["courses_added_waiting"]])}<br />
  Nous reviendrons vers vous si une place se libère ou si le cours est dédoublé.
"""
        if kwargs.get("courses_added_waiting"):
            course_message += f"""</p>
<p>
  Cours supprimé(s):<br />
  {"<br />".join([c.name for c in kwargs["courses_removed"]])}
"""
        message = f"""
<p>Bonjour,</p>
<p>
  Les cours de danse de {kwargs["full_name"]} ont été mis à jour.
{course_message}
</p>
<p>
  Bonne journée et à bientôt,<br />
  Tech K'Dance
</p>
"""
        return message

    @staticmethod
    def __build_html_pre_signup_warning(**kwargs) -> str:
        if not kwargs.get("username"):
            raise ValueError("Un argument username est nécessaire pour cet email")
        if not kwargs.get("full_name"):
            raise ValueError("Un argument full_name est nécessaire pour cet email")
        if not kwargs.get("birthday"):
            raise ValueError("Un argument birthday est nécessaire pour cet email")
        return f"""
<p>Bonjour,</p>
<p>
  L'utilisateur {kwargs["username"]} a effectué une pré-inscription douteuse. L'adhérent suivant n'a pas été retrouvé dans les données de la saison précédente:<br />
  {kwargs["full_name"]}, né(e) le {kwargs["birthday"]}
</p>
<p>
  Bonne journée et à bientôt,<br />
  Tech K'Dance
</p>
"""

    @staticmethod
    def __build_html_waiting_active(**kwargs) -> str:
        if not kwargs.get("full_name"):
            raise ValueError("Un argument full_name est nécessaire pour cet email")
        if not kwargs.get("course_name"):
            raise ValueError("Un argument course_name est nécessaire pour cet email")
        if not kwargs.get("weekday"):
            raise ValueError("Un argument weekday est nécessaire pour cet email")
        if not kwargs.get("start_hour"):
            raise ValueError("Un argument start_hour est nécessaire pour cet email")
        if kwargs.get("with_next_course_warning") is None:
            raise ValueError(
                "Un argument with_next_course_warning est nécessaire pour cet email"
            )
        return f"""
<p>Bonjour,</p>
<p>
  Une place s'est libérée, et {kwargs["full_name"]} a pu être inscrit(e) au cours {kwargs["course_name"]} du {kwargs["weekday"]} à {kwargs["start_hour"]}.<br />
  L'inscription ne sera finalisée qu'à réception du paiement et des éventuels documents restants. {"<strong>Si le paiement n'est pas effectué avant votre prochain cours, l'inscription sera annulée et votre place donnée à la personne suivante sur la liste d'attente. </strong>" if kwargs.get("with_next_course_warning") else ""}Connectez vous à <a href="https://adherents.association-kdance.fr/" target="_blank">votre compte</a> pour un statut détaillé.
</p>
<p>
  Bonne journée et à bientôt,<br />
  Tech K'Dance
</p>
"""

    @staticmethod
    def __build_html_waiting_inconsistent(**kwargs) -> str:
        if not kwargs.get("member"):
            raise ValueError("Un argument member est nécessaire pour cet email")
        if not kwargs.get("course"):
            raise ValueError("Un argument course_name est nécessaire pour cet email")
        member = kwargs["member"]
        return f"""
<p>Bonjour,</p>
<p>
  Il y a des incohérences dans la gestion des listes d'attente.<br />
  Cours concerné: {kwargs["course"]}<br />
  Membre concerné: {member}<br />
  course.members_waiting: {", ".join(kwargs["course"].members_waiting.all())}<br />
  member.waiting_courses: {"aucun" if isinstance(member, str) else ", ".join(kwargs["member"].waiting_courses.all())}
</p>
<p>
  Tech K'Dance
</p>
"""

    @staticmethod
    def __build_html_reset_password(**kwargs) -> str:
        if not kwargs.get("url"):
            raise ValueError("Un argument url est nécessaire pour cet email")
        return f"""
<p>Bonjour,</p>
<p>
  Vous venez de faire une demande de réinitialisation de mot de passe pour votre compte K'Dance ?
  Veuillez cliquer sur le lien suivant, qui restera valide pendant 30 minutes:
  <a href="{kwargs["url"]}">
    {kwargs["url"]}
  </a>
</p>
<p>Si vous n'êtes pas à l'origine de cette demande, vous pouvez ignorer cet email, votre mot de passe restera
  inchangé.</p>
<p>
  Bonne journée et à bientôt,<br />
  Tech K'Dance
</p>
"""

    @staticmethod
    def __build_html_payment_unknown(**kwargs) -> str:
        if not kwargs.get("username"):
            raise ValueError("Un argument username est nécessaire pour cet email")
        return f"""
<p>Bonjour,</p>
<p>
  Il semble que le paiement de {kwargs["username"]} soit revenu avec "STATUS_UNKNOWN". Merci d'investiguer.
</p>
<p>
  Bonne journée et à bientôt,<br />
  Tech K'Dance
</p>
"""
