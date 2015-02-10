import datetime
import factory

from utils.factories import *
from teams.models import Partner
from teams.models import MembershipNarrowing
from teams.models import Invite
from teams.models import Application
from teams.models import TeamLanguagePreference
from teams.models import BillingReport
from auth.models import CustomUser 
from auth.models import UserLanguage
from messages.models import Message

class TeamManagerLanguageFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = MembershipNarrowing

class UserLangFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = UserLanguage


class CustomUserFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = CustomUser
    username = factory.Sequence(lambda d: 'TestUser_%d' % d)
    email = factory.LazyAttribute(lambda a: '{0}@example.com'.format(a.username).lower())
    notify_by_email = True
    valid_email = True 
    password = factory.PostGenerationMethodCall('set_password',
                                                'password')
    


class PartnerFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = Partner

class TeamInviteFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = Invite


class ApplicationFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = Application
    created = datetime.datetime.now()
    pk = factory.Sequence(lambda n: 100+n)


class TeamLangPrefFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = TeamLanguagePreference
    team = factory.SubFactory(TeamFactory)

class BillingFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = BillingReport 
    type = 2
