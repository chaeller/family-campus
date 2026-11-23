# Source module: Moodle

Fetches upcoming exams, assignments and their attachments from
[**Moodle**](https://moodle.org), the open-source learning platform used by
many schools – in Switzerland especially by vocational schools. Read
[../README.md](../README.md) first – in particular "Legal and responsible use".

**Status: tested with one school (Moodle 4.5, 2026-11-22)** – token, check,
fetch and attachments work; other schools may enter exams differently.

## Whose account?

In Moodle, **the learner** (e.g. an apprentice) has the account, not the
parents. The module is therefore used **by the learner or with the learner's
consent**: the learner runs `token` and types the password; the password is
never stored, only the token. Parents never use a learner's password.

## What it accesses

With the learner's token (web service of the Moodle app, `moodle_mobile_app`):

- `core_webservice_get_site_info` – site name, the learner's user id, allowed functions
- `core_enrol_get_users_courses` – the learner's own courses
- `core_calendar_get_calendar_events` – course, site and own events in the time range
- `core_calendar_get_action_events_by_timesort` – due dates of activities (assignments, quizzes)
- `mod_assign_get_assignments` – text and attachments of assignments due in the range
- attachments through `webservice/pluginfile.php` (only those of the selected entries)

Or, without a token, only the **calendar export link** (iCal) the learner
creates in Moodle: dates, titles, descriptions; no documents.

Nothing else: no course pages are crawled, no forum posts, grades or other
users; teachers' names are not stored; external links are only listed.

Moodle has no "exam" type. An entry counts as an exam if it is a quiz or if
its title or description contains a word such as Prüfung, Test, LZK,
Klausur, Examen, épreuve, verifica (`EXAM_WORDS` in `moodle.py`); `fetch
--all` keeps every entry.

## Legal status

Moodle is software, not a service: **every school runs its own Moodle with
its own rules**. There are no central terms of use by Moodle HQ that apply to
learners. Checked on 2026-11-22 in the official documentation
([Mobile web services](https://docs.moodle.org/en/Mobile_web_services),
[Security keys](https://docs.moodle.org/en/Security_keys),
[Calendar](https://docs.moodle.org/en/Using_Calendar)). **This is a summary,
not legal advice.**

- **Official, documented interfaces.** The web service of the Moodle app is
  part of Moodle; it is enabled by default on https sites, and the school can
  switch it off ("If your site uses HTTPS, mobile web services are enabled by
  default"). Security keys for external applications are a user feature in
  the preferences, if the school allows it. The calendar export is a normal
  user feature "so they may be imported into other calendar programs". The
  module uses only these – it does not scrape web pages.
- **The school's rules decide.** Many schools show a site policy or terms of
  use at the first login (in Moodle under the user menu → Policies) and have
  an ICT usage regulation. Read them: some forbid passing on credentials or
  using the platform for other than school purposes. Preparing for one's own
  exams is a school purpose.
- **Own account, own data.** Only the learner's own courses and dates are
  read. The credentials are the learner's; never share them.
- **Copyright.** Course material belongs to the teachers or the school; it
  stays in `material/moodle/` and is never copied into tiles.
- **Consequence for you:** using the documented interfaces with your own
  account for your own exam preparation is what they are made for, but your
  school may have its own rules. Check the site policy; if in doubt, ask the
  school; stop if the school objects or switches the service off.

## Setup

In Family Campus's `.env` (copy `.env.example`, never committed), per learner (first name as in
`campus.json`, in capitals):

```text
MOODLE_PEOPLE=Ben
MOODLE_BEN_URL=https://moodle.your-school.ch
MOODLE_BEN_ICAL=https://moodle.your-school.ch/calendar/export_execute.php?…   # optional
MOODLE_BEN_TOKEN=…                                                           # optional, see below
```

Then the learner, in the Family Campus folder (the module uses `my-family/`):

```bash
python3 sources/moodle/moodle.py token --person Ben   # types username and password once
python3 sources/moodle/moodle.py check
```

The token is saved in `material/moodle/ben/.token` (mode 600, never
committed).

- **Single sign-on** (login with Microsoft, edu-ID …): `token` fails. Then the
  learner copies the key "Moodle mobile web service" from Moodle's
  preferences → *Security keys* into `MOODLE_BEN_TOKEN` (if the school shows
  it; the row appears after the first login in the Moodle app), or uses the
  calendar link. **Not the RSS key** on the same page – it looks the same but
  works only for RSS feeds (`invalidtoken`).
- **Calendar link:** Moodle → Calendar → *Export calendar* (or *Import or
  export calendars*): "All events", "Recent and next 60 days" (or custom) →
  *Get calendar URL*. The link contains a personal key – treat it like a
  password.

Python 3.10+, standard library only.

## Use

```bash
python3 sources/moodle/moodle.py fetch                   # exams of the next 120 days, all learners
python3 sources/moodle/moodle.py fetch --person Ben --all # every event (assignments too)
python3 sources/moodle/moodle.py fetch --days 60 --past-days 14 --no-documents
```

Per learner: `material/moodle/<person>/exams.json` (`id`, `date`,
`subject` = course name, `type` (`exam`, `assign`, `quiz`, `course` …),
`title`, `goals` (description), `links`, `documents`; earlier fetches are
merged) and the attachments in `material/moodle/<person>/documents/`. Then
`/fc-ingest --from moodle` compares them with my-family's exams and tiles.

## Side effects

- `token` logs in once; Moodle may log it as a login from the "Moodle app".
  No notification e-mail is known.
- Every run makes a handful of requests (pause of 0.5 s between them) with
  the user agent `FamilyCampus-SourceModule/1.0`; once a week is enough.

## Experience

- **Exams are often quizzes** taken in class ("Prüfung … beginnt"); they
  appear in the calendar only once the teacher sets the opening time, often
  shortly before. Fetch regularly; earlier fetches are merged, so nothing is
  lost. Many courses also have practice quizzes ("Probetest"); their
  questions are not fetched (that would mean starting an attempt).
- Assignments come with their task sheets as attachments – often the best
  material for a tile.
- The two calendar functions give `instance` differently (instance id vs.
  course module id); the module merges entries by event id.
- `check` reads the site's public app settings first (no login): whether the
  web service is on and whether the login is username/password or single
  sign-on.
