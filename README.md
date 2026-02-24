# Skatetrax Core
Provides decorators, classes, and functions specific to Skatetrax. Additionally, this module should be able to assist in first time setup, dev environments, and database initialization.  Everything the body needs.


## Requires
``` bash
sudo yum install python3 python3-pip libpq libpq-devel python3-psycopg2 postgresql15
pip install pipenv --user
```

### To Install
#### For Development
``` bash
git clone https://github.com/kami-nashi/skatetrax_core.git
cd skatetrax_core
pipenv shell
pipenv install
```

#### For General Use
```bash
git clone https://github.com/kami-nashi/skatetrax_core.git
cd skatetrax_core
pip install -r requirements.txt --user
```

### Contributing & Release Process
Anything in the `main` branch should work as expected with as little effort as possible.  The `dev` branch is where new features, defined by milestones, can be added prior to a release.  Currently, there is no schedule for releases, but once all items in a milestone are completed, they should be merged into `main`, with the exception of bug/break fixes.

If you're interested in suggesting changes, please fork the repo, check out the `dev` branch, and create a feature branch from that.  Once a PR is opened against our `dev` branch, it can be reviewed and pulled into `main`. There are no naming requirements for PR's or branches, though the project default relies on a year/week_numberPushIdentifier, `2024_47A` for example indicates the 2024 year, week 47, first push/merge (A) for that week. If a second feature is worked on that week, the branch for that would be `2024_47B`.

Input/comments/feedback for any open PR is always welcome.
