#!/usr/bin/env python3
"""
Skatetrax Admin -- Data restore, migration, and import tool.

Replaces the manual newUser.py -> load_skeletor.py -> STLdb.py workflow
with a single CLI that reads YAML fixtures and CSV files.

Usage:
  python admin/admin.py restore sparkles --all
  python admin/admin.py restore sparkles --step auth --step equipment
  python admin/admin.py migrate sparkles --csv admin/migrations/sparkles/ice_time.csv
  python admin/admin.py import-sessions sparkles admin/sessions/sparkles/2026_01.csv
  python admin/admin.py import-maintenance sparkles path/to/maintenance.csv
  python admin/admin.py validate sparkles
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone

import yaml

from skatetrax.models.cyberconnect2 import Session, engine
from skatetrax.models.t_auth import uAuthTable
from skatetrax.models.ops.pencil import (
    Location_Data, Coach_Data, User_Data,
    Equipment_Data, Ice_Session, Club_Data
)

ADMIN_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = ADMIN_DIR / 'fixtures'
MIGRATIONS_DIR = ADMIN_DIR / 'migrations'
SESSIONS_DIR = ADMIN_DIR / 'sessions'


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_yaml(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def drop_invalid_dates(df, date_col='date', label=''):
    """Filter out rows with zero or unparseable dates, log them, return the clean DataFrame."""
    import pandas as pd

    zero_mask = df[date_col].astype(str).str.match(r'^0{4}[-/]0{2}[-/]0{2}')
    parsed = pd.to_datetime(df[date_col], errors='coerce', format='mixed')
    bad_mask = zero_mask | parsed.isna()
    bad_rows = df[bad_mask]

    if not bad_rows.empty:
        print(f"  SKIPPED {len(bad_rows)} row(s) with invalid dates{f' ({label})' if label else ''}:")
        for idx, row in bad_rows.iterrows():
            row_summary = f"    row {idx}: {date_col}={row[date_col]!r}"
            if 'ice_time' in row.index:
                row_summary += f", ice_time={row['ice_time']}"
            if 'rink_id' in row.index:
                row_summary += f", rink_id={row['rink_id']}"
            print(row_summary)

    return df[~bad_mask].copy()


def filter_by_user(df, expected_uuid, uuid_col='uSkaterUUID', label=''):
    """Keep only rows belonging to expected_uuid, log and drop the rest."""
    if uuid_col not in df.columns:
        return df

    match_mask = df[uuid_col].astype(str) == str(expected_uuid)
    other_rows = df[~match_mask]

    if not other_rows.empty:
        other_uuids = other_rows[uuid_col].unique()
        print(f"  FILTERED {len(other_rows)} row(s) belonging to other user(s){f' ({label})' if label else ''}:")
        for uid in other_uuids:
            count = (other_rows[uuid_col] == uid).sum()
            print(f"    {uid}: {count} row(s)")

    return df[match_mask].copy()


def get_user_dir(username):
    user_dir = FIXTURES_DIR / 'users' / username
    if not user_dir.exists():
        print(f"Error: No fixture directory found at {user_dir}")
        sys.exit(1)
    return user_dir


def get_user_uuid(username):
    auth = load_yaml(get_user_dir(username) / 'auth.yaml')
    return auth['uSkaterUUID']


# ---------------------------------------------------------------------------
# Restore steps -- each reads YAML fixtures and writes to the database
# ---------------------------------------------------------------------------

def pooled_already_loaded():
    """Return True if pooled reference data is already in the database
    (i.e. more than just the setup_db defaults exist)."""
    session = Session()
    try:
        from skatetrax.models.t_coaches import Coaches
        from skatetrax.models.t_locations import Locations
        from skatetrax.models.t_memberships import Club_Directory
        coaches = session.query(Coaches).count()
        locations = session.query(Locations).count()
        clubs = session.query(Club_Directory).count()
        return coaches > 1 and locations > 1 and clubs > 1
    finally:
        session.close()


def restore_pooled(username):
    """Load shared reference data: coaches, locations, clubs.

    Ice types and skater roles are system enums owned by setup_db and
    are NOT loaded here.  Skips entirely if pooled data is already
    present in the database (e.g. from a previous user restore).
    """
    if pooled_already_loaded():
        print("  Pooled data already present, skipping")
        return

    pooled_dir = FIXTURES_DIR / 'pooled'
    now = datetime.now(timezone.utc)

    coaches = load_yaml(pooled_dir / 'coaches.yaml')
    Coach_Data.add_coaches(coaches)
    print(f"  Loaded {len(coaches)} coaches")

    locations = load_yaml(pooled_dir / 'locations.yaml')
    for loc in locations:
        if 'date_created' not in loc:
            loc['date_created'] = now
    Location_Data.add_ice_rink(locations)
    print(f"  Loaded {len(locations)} locations")

    clubs = load_yaml(pooled_dir / 'clubs.yaml')
    Club_Data.add_club(clubs)
    print(f"  Loaded {len(clubs)} clubs")


def restore_auth(username):
    """Create uAuthTable row from auth.yaml, hashing the password."""
    auth_data = load_yaml(get_user_dir(username) / 'auth.yaml')

    session = Session()
    try:
        user = uAuthTable()
        user.aLogin = auth_data['aLogin']
        user.aEmail = auth_data['aEmail']
        user.phone_number = auth_data.get('phone_number')
        user.uSkaterUUID = auth_data['uSkaterUUID']
        user.set_password(auth_data['password'])

        session.add(user)
        session.commit()
        print(f"  Created auth for '{auth_data['aLogin']}' ({auth_data['uSkaterUUID']})")
    except Exception as e:
        session.rollback()
        print(f"  Auth failed: {e}")
    finally:
        session.close()


def restore_profile(username):
    """Create uSkaterConfig row from profile.yaml."""
    uuid = get_user_uuid(username)
    profile = load_yaml(get_user_dir(username) / 'profile.yaml')
    profile['uSkaterUUID'] = uuid
    User_Data.add_skater([profile])
    print(f"  Loaded profile for {profile['uSkaterFname']} {profile['uSkaterLname']}")


def restore_equipment(username):
    """Create boots, blades, and skate config rows from equipment.yaml."""
    uuid = get_user_uuid(username)
    data = load_yaml(get_user_dir(username) / 'equipment.yaml')

    boots = data.get('boots', [])
    for b in boots:
        b['uSkaterUUID'] = uuid
    Equipment_Data.add_boots(boots)
    print(f"  Loaded {len(boots)} boots")

    blades = data.get('blades', [])
    for b in blades:
        b['uSkaterUUID'] = uuid
    Equipment_Data.add_blades(blades)
    print(f"  Loaded {len(blades)} blades")

    configs = data.get('configs', [])
    for c in configs:
        c['uSkaterUUID'] = uuid
    Equipment_Data.add_combo(configs)
    print(f"  Loaded {len(configs)} skate configs")


def restore_memberships(username):
    """Create memberships, punch cards, and LTS classes from memberships.yaml."""
    uuid = get_user_uuid(username)
    data = load_yaml(get_user_dir(username) / 'memberships.yaml')

    members = data.get('club_memberships', [])
    for m in members:
        m['uSkaterUUID'] = uuid
    Club_Data.add_member(members)
    print(f"  Loaded {len(members)} club memberships")

    punch_cards = data.get('punch_cards', [])
    for p in punch_cards:
        p['uSkaterUUID'] = uuid
    Location_Data.add_punchcard(punch_cards)
    print(f"  Loaded {len(punch_cards)} punch cards")

    lts = data.get('lts_classes', [])
    for entry in lts:
        entry['uSkaterUUID'] = uuid
    Ice_Session.add_skate_school(lts)
    print(f"  Loaded {len(lts)} LTS classes")


def restore_maintenance(username):
    """Create maintenance rows from maintenance.yaml."""
    maint_file = get_user_dir(username) / 'maintenance.yaml'
    if not maint_file.exists():
        print(f"  No maintenance.yaml found for {username}, skipping")
        return
    uuid = get_user_uuid(username)
    data = load_yaml(maint_file)
    for m in data:
        m['uSkaterUUID'] = uuid
    Equipment_Data.add_maintenance(data)
    print(f"  Loaded {len(data)} maintenance records")


def restore_sessions(username):
    """Load post-migration session CSVs from sessions/<username>/."""
    import pandas as pd

    sessions_dir = SESSIONS_DIR / username
    if not sessions_dir.exists():
        print(f"  No sessions directory at {sessions_dir}")
        return

    csv_files = sorted(sessions_dir.glob('*.csv'))
    if not csv_files:
        print(f"  No CSV files found in {sessions_dir}")
        return

    uuid = get_user_uuid(username)
    total = 0
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        if 'ice_time_id' in df.columns:
            df.drop(columns='ice_time_id', inplace=True)
        df = drop_invalid_dates(df, date_col='date', label=csv_file.name)
        df = filter_by_user(df, uuid, label=csv_file.name)
        df.to_sql('ice_time', con=engine, index=False, if_exists='append')
        total += len(df)
        print(f"  Loaded {len(df)} sessions from {csv_file.name}")
    print(f"  Total: {total} session rows")


# ---------------------------------------------------------------------------
# Migrate -- one-time MariaDB CSV -> Postgres with ID translation
# ---------------------------------------------------------------------------

def migrate_user(username, csv_path):
    """Read a MariaDB-exported CSV, apply ID mappings, and insert into Postgres."""
    import pandas as pd

    shared_path = MIGRATIONS_DIR / 'shared_mappings.yaml'
    user_path = MIGRATIONS_DIR / username / 'user_mappings.yaml'

    if not shared_path.exists():
        print(f"Error: Shared mappings not found at {shared_path}")
        sys.exit(1)
    if not user_path.exists():
        print(f"Error: User mappings not found at {user_path}")
        sys.exit(1)

    shared = load_yaml(shared_path)
    user_maps = load_yaml(user_path)

    column_mappings = {
        'uSkaterUUID': {int(k): v for k, v in user_maps.get('users', {}).items()},
        'rink_id': {int(k): v for k, v in shared.get('locations', {}).items()},
        'coach_id': {int(k): v for k, v in shared.get('coaches', {}).items()},
        'skate_type': {int(k): v for k, v in shared.get('skate_types', {}).items()},
        'uSkaterConfig': {},
    }

    # skate_configs may be referenced as int or float in CSV (pandas quirk)
    for k, v in user_maps.get('skate_configs', {}).items():
        column_mappings['uSkaterConfig'][int(k)] = v
        column_mappings['uSkaterConfig'][float(k)] = v

    df = pd.read_csv(csv_path)
    print(f"  Read {len(df)} rows from {csv_path}")

    for col, mapping in column_mappings.items():
        if col in df.columns:
            unmapped = set()
            def apply_map(val):
                if pd.isna(val):
                    return val
                key = int(val) if float(val) == int(val) else val
                result = mapping.get(key, mapping.get(float(key), None))
                if result is None:
                    unmapped.add(key)
                    return val
                return result
            df[col] = df[col].apply(apply_map)
            if unmapped:
                print(f"  Warning: {col} had unmapped values: {unmapped}")

    for drop_col in ('ice_time_id', 'id'):
        if drop_col in df.columns:
            df.drop(columns=drop_col, inplace=True)

    uuid = get_user_uuid(username)
    df = drop_invalid_dates(df, date_col='date', label=csv_path)
    df = filter_by_user(df, uuid, label=csv_path)
    df.to_sql('ice_time', con=engine, index=False, if_exists='append')
    print(f"  Migrated {len(df)} rows into ice_time")


# ---------------------------------------------------------------------------
# Import -- ongoing bulk loads (post-migration, UUIDs already correct)
# ---------------------------------------------------------------------------

def import_sessions(username, csv_path):
    """Import a post-migration session CSV directly into ice_time."""
    import pandas as pd

    uuid = get_user_uuid(username)
    df = pd.read_csv(csv_path)
    for drop_col in ('ice_time_id', 'id'):
        if drop_col in df.columns:
            df.drop(columns=drop_col, inplace=True)
    df = drop_invalid_dates(df, date_col='date', label=csv_path)
    df = filter_by_user(df, uuid, label=csv_path)
    df.to_sql('ice_time', con=engine, index=False, if_exists='append')
    print(f"  Imported {len(df)} sessions from {csv_path}")


def import_maintenance(username, csv_path):
    """Import a maintenance CSV, injecting user UUID if not present."""
    import pandas as pd

    uuid = get_user_uuid(username)
    df = pd.read_csv(csv_path)
    if 'uSkaterUUID' not in df.columns:
        df['uSkaterUUID'] = uuid
    df.to_sql('maintenance', con=engine, index=False, if_exists='append')
    print(f"  Imported {len(df)} maintenance records from {csv_path}")


# ---------------------------------------------------------------------------
# Validate -- dry-run that parses fixtures and checks FK references
# ---------------------------------------------------------------------------

def validate_pooled_refs(username):
    """Check that every coach/location/club UUID referenced by this user
    exists in the pooled YAML files.  Returns a list of issue strings
    (empty means all clear).
    """
    pooled_dir = FIXTURES_DIR / 'pooled'
    user_dir = get_user_dir(username)

    coach_ids = {c['coach_id'] for c in load_yaml(pooled_dir / 'coaches.yaml')}
    location_ids = {loc['rink_id'] for loc in load_yaml(pooled_dir / 'locations.yaml')}
    club_ids = {c['club_id'] for c in load_yaml(pooled_dir / 'clubs.yaml')}

    issues = []

    def check(uuid_val, kind, known_set, source):
        if uuid_val and str(uuid_val) not in known_set:
            issues.append(f"{source}: references {kind} {uuid_val} "
                          f"which is not in pooled/{kind}s.yaml")

    # Profile
    profile_path = user_dir / 'profile.yaml'
    if profile_path.exists():
        profile = load_yaml(profile_path)
        check(profile.get('activeCoach'), 'coach', coach_ids, 'profile.yaml')
        check(profile.get('uSkaterRinkPref'), 'location', location_ids, 'profile.yaml')
        check(profile.get('org_Club'), 'club', club_ids, 'profile.yaml')

    # Memberships
    memb_path = user_dir / 'memberships.yaml'
    if memb_path.exists():
        memb = load_yaml(memb_path)
        for cm in (memb.get('club_memberships') or []):
            check(cm.get('club_id'), 'club', club_ids, 'memberships.yaml')
        for pc in (memb.get('punch_cards') or []):
            check(pc.get('rink_id'), 'location', location_ids, 'memberships.yaml')
        for lts in (memb.get('lts_classes') or []):
            check(lts.get('location_id'), 'location', location_ids, 'memberships.yaml')

    # Maintenance
    maint_path = user_dir / 'maintenance.yaml'
    if maint_path.exists():
        for m in load_yaml(maint_path):
            check(m.get('m_location'), 'location', location_ids, 'maintenance.yaml')

    return issues


def validate_user(username):
    """Parse all fixtures for a user and report issues without touching the DB."""
    user_dir = get_user_dir(username)
    issues = []
    boot_ids = set()
    blade_ids = set()
    config_ids = set()

    # Auth
    try:
        auth = load_yaml(user_dir / 'auth.yaml')
        for field in ['aLogin', 'password', 'aEmail', 'uSkaterUUID']:
            if field not in auth:
                issues.append(f"auth.yaml: missing required field '{field}'")
        print(f"  auth.yaml: OK ({auth.get('aLogin', '?')})")
    except Exception as e:
        issues.append(f"auth.yaml: {e}")

    # Profile
    try:
        profile = load_yaml(user_dir / 'profile.yaml')
        print(f"  profile.yaml: OK ({profile.get('uSkaterFname', '?')} {profile.get('uSkaterLname', '?')})")
    except FileNotFoundError:
        issues.append("profile.yaml: not found")

    # Equipment
    equip_path = user_dir / 'equipment.yaml'
    if equip_path.exists():
        try:
            equip = load_yaml(equip_path)
            boots = equip.get('boots', [])
            blades = equip.get('blades', [])
            configs = equip.get('configs', [])

            boot_ids = {b['bootsID'] for b in boots}
            blade_ids = {b['bladesID'] for b in blades}
            config_ids = {c['sConfigID'] for c in configs}

            for c in configs:
                if c['uSkaterBootsID'] not in boot_ids:
                    issues.append(
                        f"equipment.yaml: config {c['sConfigID'][:8]}... "
                        f"references unknown boot {c['uSkaterBootsID'][:8]}..."
                    )
                if c['uSkaterBladesID'] not in blade_ids:
                    issues.append(
                        f"equipment.yaml: config {c['sConfigID'][:8]}... "
                        f"references unknown blade {c['uSkaterBladesID'][:8]}..."
                    )

            print(f"  equipment.yaml: {len(boots)} boots, {len(blades)} blades, {len(configs)} configs")
        except Exception as e:
            issues.append(f"equipment.yaml: {e}")
    else:
        print("  equipment.yaml: not found (skipping)")

    # Maintenance
    maint_path = user_dir / 'maintenance.yaml'
    if maint_path.exists():
        try:
            maint = load_yaml(maint_path)
            for m in maint:
                bid = m.get('uSkaterBladesID')
                cid = m.get('uSkateConfig')
                if bid and blade_ids and bid not in blade_ids:
                    issues.append(f"maintenance.yaml: references unknown blade {bid[:8]}...")
                if cid and config_ids and cid not in config_ids:
                    issues.append(f"maintenance.yaml: references unknown config {cid[:8]}...")
            print(f"  maintenance.yaml: {len(maint)} records")
        except Exception as e:
            issues.append(f"maintenance.yaml: {e}")
    else:
        print("  maintenance.yaml: not found (skipping)")

    # Memberships
    memb_path = user_dir / 'memberships.yaml'
    if memb_path.exists():
        try:
            memb = load_yaml(memb_path)
            counts = []
            for key in ['club_memberships', 'punch_cards', 'lts_classes']:
                items = memb.get(key, [])
                counts.append(f"{len(items)} {key}")
            print(f"  memberships.yaml: {', '.join(counts)}")
        except Exception as e:
            issues.append(f"memberships.yaml: {e}")
    else:
        print("  memberships.yaml: not found (skipping)")

    # Sessions directory
    sess_dir = SESSIONS_DIR / username
    if sess_dir.exists():
        csv_count = len(list(sess_dir.glob('*.csv')))
        print(f"  sessions/: {csv_count} CSV file(s)")
    else:
        print("  sessions/: no directory (skipping)")

    # Migration files
    mig_dir = MIGRATIONS_DIR / username
    if mig_dir.exists():
        print(f"  migrations/: found ({username}/)")
    else:
        print("  migrations/: no directory (legacy migration not configured)")

    # Pooled reference cross-check
    ref_issues = validate_pooled_refs(username)
    issues.extend(ref_issues)

    # Summary
    print()
    if issues:
        print(f"  ISSUES ({len(issues)}):")
        for issue in issues:
            print(f"    - {issue}")
        return False
    else:
        print(f"  All fixtures valid for '{username}'")
        return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

STEP_ORDER = [
    'pooled', 'auth', 'profile', 'equipment',
    'memberships', 'maintenance', 'sessions'
]

STEP_FUNCS = {
    'pooled': restore_pooled,
    'auth': restore_auth,
    'profile': restore_profile,
    'equipment': restore_equipment,
    'memberships': restore_memberships,
    'maintenance': restore_maintenance,
    'sessions': restore_sessions,
}


def main():
    parser = argparse.ArgumentParser(
        description='Skatetrax Admin -- data restore, migration, and import tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  Disaster recovery (full restore):
    python admin/admin.py restore sparkles --all

  Individual steps:
    python admin/admin.py restore sparkles --step pooled --step auth --step profile

  One-time MariaDB migration:
    python admin/admin.py migrate sparkles --csv path/to/ice_time.csv

  Ongoing bulk imports:
    python admin/admin.py import-sessions sparkles admin/sessions/sparkles/2026_01.csv
    python admin/admin.py import-maintenance sparkles path/to/maintenance.csv

  Validate fixtures (dry-run):
    python admin/admin.py validate sparkles
        """
    )

    sub = parser.add_subparsers(dest='command', required=True)

    # -- restore --
    p_restore = sub.add_parser(
        'restore',
        help='Restore user data from YAML fixtures into the database'
    )
    p_restore.add_argument('username', help='User fixture directory name (e.g. sparkles)')
    p_restore.add_argument(
        '--all', action='store_true',
        help='Run all restore steps in dependency order'
    )
    p_restore.add_argument(
        '--step', action='append', choices=STEP_ORDER,
        metavar='STEP',
        help=f'Run specific step(s). Options: {", ".join(STEP_ORDER)}'
    )

    # -- migrate --
    p_migrate = sub.add_parser(
        'migrate',
        help='Migrate MariaDB CSV export into Postgres with ID translation'
    )
    p_migrate.add_argument('username', help='User migration directory name')
    p_migrate.add_argument('--csv', required=True, help='Path to MariaDB-exported CSV')

    # -- import-sessions --
    p_import_sess = sub.add_parser(
        'import-sessions',
        help='Import post-migration session data from CSV'
    )
    p_import_sess.add_argument('username', help='Username for UUID lookup')
    p_import_sess.add_argument('csv_path', help='Path to CSV file with Postgres UUIDs')

    # -- import-maintenance --
    p_import_maint = sub.add_parser(
        'import-maintenance',
        help='Import maintenance records from CSV'
    )
    p_import_maint.add_argument('username', help='Username for UUID lookup')
    p_import_maint.add_argument('csv_path', help='Path to CSV file')

    # -- validate --
    p_validate = sub.add_parser(
        'validate',
        help='Validate user fixtures without touching the database'
    )
    p_validate.add_argument('username', help='User fixture directory name')

    args = parser.parse_args()

    if args.command == 'restore':
        steps = STEP_ORDER if args.all else (args.step or [])
        if not steps:
            p_restore.error("Requires --all or at least one --step")

        print(f"Validating pooled references for '{args.username}'...")
        ref_issues = validate_pooled_refs(args.username)
        if ref_issues:
            print(f"\n  ABORT -- {len(ref_issues)} missing pooled reference(s):\n")
            for issue in ref_issues:
                print(f"    - {issue}")
            print("\n  Add the missing entries to admin/fixtures/pooled/ and try again.")
            sys.exit(1)
        print("  All references OK\n")

        print(f"Restoring '{args.username}': {', '.join(steps)}\n")
        for step in steps:
            print(f"[{step}]")
            STEP_FUNCS[step](args.username)
            print()
        print("Done.")

    elif args.command == 'migrate':
        print(f"Migrating MariaDB data for '{args.username}'...\n")
        migrate_user(args.username, args.csv)
        print("\nDone.")

    elif args.command == 'import-sessions':
        print(f"Importing sessions for '{args.username}'...\n")
        import_sessions(args.username, args.csv_path)
        print("\nDone.")

    elif args.command == 'import-maintenance':
        print(f"Importing maintenance for '{args.username}'...\n")
        import_maintenance(args.username, args.csv_path)
        print("\nDone.")

    elif args.command == 'validate':
        print(f"Validating fixtures for '{args.username}'...\n")
        validate_user(args.username)


if __name__ == '__main__':
    main()
