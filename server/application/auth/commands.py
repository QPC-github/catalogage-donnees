from pydantic import EmailStr, SecretStr

from server.domain.common.types import ID
from server.domain.organizations.entities import LEGACY_ORGANIZATION_SIRET
from server.domain.organizations.types import Siret
from server.seedwork.application.commands import Command


class CreatePasswordUser(Command[ID]):
    organization_siret: Siret = LEGACY_ORGANIZATION_SIRET
    email: EmailStr
    password: SecretStr


class DeletePasswordUser(Command[None]):
    account_id: ID


class ChangePassword(Command[None]):
    email: EmailStr
    password: SecretStr
