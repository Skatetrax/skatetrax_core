import pytest
from uuid import uuid4, UUID as PyUUID
from datetime import datetime, timezone
from sqlalchemy import create_engine, JSON, String, UUID as SA_UUID
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import JSONB

from skatetrax.models.base import Base

# ---------------------------------------------------------------------------
# Well-known UUIDs for test fixtures (real UUID objects for SQLite compat)
# ---------------------------------------------------------------------------
NO_COACH_UUID = PyUUID("487d43b5-0a4d-4dc4-8cc2-ab06870a10bf")
OFF_ICE_RINK_UUID = PyUUID("b261166b-9e7c-4a96-ab06-ec630deb3321")
NO_CLUB_UUID = PyUUID("c4dd2b9c-50f1-4f5b-a439-fd8f36a654d6")

FREESTYLE_WALKON_UUID = PyUUID("dc812842-a9a9-4902-b680-361420baffe5")
FREESTYLE_PUNCH_UUID = PyUUID("0bcb0d7a-f5f0-41e2-bccb-78e80eb6673f")
GROUP_CLASS_UUID = PyUUID("db32094e-9b0d-42a5-b87f-cd47729b6c65")
PUBLIC_UUID = PyUUID("cedbb4e9-ab5b-4a14-a273-fd9783aaac86")

TEST_RINK_UUID = uuid4()
TEST_COACH_UUID = uuid4()
NEW_USER_UUID = uuid4()
NEW_BLADE_UUID = uuid4()
NEW_BOOT_UUID = uuid4()
NEW_CONFIG_UUID = uuid4()


class _TestSession:
    """Wraps a real Session so aggregator `with session as s:` won't close it."""

    def __init__(self, real):
        self._real = real

    def __enter__(self):
        return self._real

    def __exit__(self, *args):
        pass

    def __bool__(self):
        return True

    def __getattr__(self, name):
        return getattr(self._real, name)


def _swap_pg_types_for_sqlite():
    """Replace Postgres-specific types and defaults for SQLite compatibility."""
    for table in Base.metadata.tables.values():
        for col in table.columns:
            if isinstance(col.type, JSONB):
                col.type = JSON()
                if col.server_default is not None:
                    col.server_default = None


def _import_all_models():
    """Import every model module so Base.metadata knows about all tables."""
    import skatetrax.models.t_auth          # noqa: F401
    import skatetrax.models.t_skaterMeta    # noqa: F401
    import skatetrax.models.t_equip         # noqa: F401
    import skatetrax.models.t_coaches       # noqa: F401
    import skatetrax.models.t_locations     # noqa: F401
    import skatetrax.models.t_icetype       # noqa: F401
    import skatetrax.models.t_ice_time      # noqa: F401
    import skatetrax.models.t_maint         # noqa: F401
    import skatetrax.models.t_memberships   # noqa: F401
    import skatetrax.models.t_classes       # noqa: F401
    import skatetrax.models.t_journal       # noqa: F401
    import skatetrax.models.t_events        # noqa: F401
    import skatetrax.models.t_tests         # noqa: F401


@pytest.fixture(scope="session")
def engine():
    _import_all_models()
    _swap_pg_types_for_sqlite()
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture()
def db_session(engine):
    """Yield a session that rolls back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture()
def seeded_session(db_session):
    """Session pre-loaded with minimal defaults + a fresh test user."""
    from skatetrax.models.t_icetype import IceType
    from skatetrax.models.t_coaches import Coaches
    from skatetrax.models.t_locations import Locations
    from skatetrax.models.t_memberships import Club_Directory
    from skatetrax.models.t_skaterMeta import uSkaterConfig
    from skatetrax.models.t_equip import uSkateConfig, uSkaterBlades, uSkaterBoots

    now = datetime.now(timezone.utc)

    ice_types = [
        IceType(FREESTYLE_WALKON_UUID, "Free Style (Walk On)"),
        IceType(FREESTYLE_PUNCH_UUID, "Free Style (Punch Card)"),
        IceType(GROUP_CLASS_UUID, "Group Class"),
        IceType(PUBLIC_UUID, "Public"),
    ]
    for it in ice_types:
        db_session.add(it)

    db_session.add(Locations(
        rink_id=OFF_ICE_RINK_UUID, rink_name="Off Ice",
        rink_address="-", rink_city="-", rink_state="-",
        rink_country="-", rink_zip="00000", rink_url="-", rink_phone="-",
    ))
    db_session.add(Locations(
        rink_id=TEST_RINK_UUID, rink_name="Test Rink",
        rink_address="1 Ice Ln", rink_city="Testville", rink_state="NC",
        rink_country="USA", rink_zip="27601", rink_url="-", rink_phone="-",
        rink_tz="America/New_York",
    ))

    db_session.add(Coaches(
        coach_id=NO_COACH_UUID, coach_Fname="-", coach_Lname="-",
        coach_rate=0, coach_phone=None, coach_email=None,
        coach_ijs_id=None, coach_usfsa_id=None,
    ))
    db_session.add(Coaches(
        coach_id=TEST_COACH_UUID, coach_Fname="Test", coach_Lname="Coach",
        coach_rate=35, coach_phone=None, coach_email=None,
        coach_ijs_id=None, coach_usfsa_id=None,
    ))

    db_session.add(Club_Directory(
        club_id=NO_CLUB_UUID, club_name="No Club",
        club_home_rink=None, club_cost=0,
    ))

    db_session.add(uSkaterConfig(
        date_created=now, uSkaterUUID=NEW_USER_UUID,
        uSkaterFname="New", uSkaterMname="", uSkaterLname="Skater",
        uSkaterZip=27601, uSkaterCity="Testville",
        uSkaterState="NC", uSkaterCountry="USA",
        uSkaterComboIce=NEW_CONFIG_UUID, uSkaterComboOff=None,
        uSkaterRinkPref=OFF_ICE_RINK_UUID, uSkaterMaintPref=21,
        activeCoach=NO_COACH_UUID, org_Club=NO_CLUB_UUID,
        org_Club_Join_Date=None, org_USFSA_number=None,
        uSkaterTZ="America/New_York", uSkaterRoles=[1],
    ))

    db_session.add(uSkaterBoots(
        bootsID=NEW_BOOT_UUID, date_created=now,
        bootsName="Generic", bootsModel="Rental",
        bootsSize="10", bootsPurchaseAmount=0,
        uSkaterUUID=NEW_USER_UUID,
    ))
    db_session.add(uSkaterBlades(
        bladesID=NEW_BLADE_UUID, date_created=now,
        bladesName="Generic", bladesModel="Rental",
        bladesSize="10", bladesPurchaseAmount=0,
        uSkaterUUID=NEW_USER_UUID,
    ))
    db_session.add(uSkateConfig(
        sConfigID=NEW_CONFIG_UUID, date_created=now,
        uSkaterUUID=NEW_USER_UUID,
        uSkaterBladesID=NEW_BLADE_UUID,
        uSkaterBootsID=NEW_BOOT_UUID,
        sConfigType=1, sActiveFlag=1,
    ))

    db_session.flush()
    return _TestSession(db_session)
