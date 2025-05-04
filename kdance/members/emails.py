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
    WAITING_TO_ACTIVE_COURSE = "waiting to active course"
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
            case EmailEnum.WAITING_TO_ACTIVE_COURSE:
                return self.__subject_waiting_active
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
            case EmailEnum.WAITING_TO_ACTIVE_COURSE:
                return self.__build_text_waiting_active
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
            case EmailEnum.WAITING_TO_ACTIVE_COURSE:
                return self.__build_html_waiting_active
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
    def __subject_waiting_active(**kwargs) -> str:
        if not kwargs.get("course_name"):
            raise ValueError("Un argument course_name est nécessaire pour cet email")
        return f"Vous avez obtenu une place pour le cours {kwargs['course_name']}!"

    @staticmethod
    def __subject_reset_password(**_k) -> str:
        return "Réinitialisation du mot de passe K'Dance"

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
L'inscription ne sera finalisée qu'à réception du paiement et des éventuels documents restants. Connectez vous à votre compte (https://adherents.association-kdance.fr/) pour un statut détaillé.

Bonne journée et à bientôt,
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
            course_message = f"""
</p>
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
    def __build_html_waiting_active(**kwargs) -> str:
        if not kwargs.get("full_name"):
            raise ValueError("Un argument full_name est nécessaire pour cet email")
        if not kwargs.get("course_name"):
            raise ValueError("Un argument course_name est nécessaire pour cet email")
        if not kwargs.get("weekday"):
            raise ValueError("Un argument weekday est nécessaire pour cet email")
        if not kwargs.get("start_hour"):
            raise ValueError("Un argument start_hour est nécessaire pour cet email")
        return f"""
<p>Bonjour,</p>
<p>
  Une place s'est libérée, et {kwargs["full_name"]} a pu être inscrit(e) au cours {kwargs["course_name"]} du {kwargs["weekday"]} à {kwargs["start_hour"]}.<br />
  L'inscription ne sera finalisée qu'à réception du paiement et des éventuels documents restants. Connectez vous à <a href="https://adherents.association-kdance.fr/" target="_blank">votre compte</a> pour un statut détaillé.
</p>
<p>
  Bonne journée et à bientôt,<br />
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
