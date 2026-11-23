# Source module: Escola

Fetches the upcoming exams ("Lernzielkontrollen") of your own children,
their learning goals and the attached documents from [**Escola**](https://www.escola.ch), a school
administration platform used by schools in Switzerland. Read
[../README.md](../README.md) first – in particular "Legal and responsible use".

## What it accesses

- Your school's Escola web site (`ESCOLA_URL`), logged in with **your parent
  account** – the same pages you see in the browser: the children of your
  account, their homework list ("Hausaufgaben") filtered to exams, and
  attachments of those entries.
- Nothing else: no other users, no external links (they are only listed), no
  teachers' names stored.

## Legal status

Checked on 2026-11-22 against the public documents of the operator, Escola
GmbH, Zürich: the [general terms (AGB)](https://dateien.escola.ch/website/Escola_AGB.pdf)
and the [privacy statement for web platform and app](https://www.escola.ch/datenschutz)
(version of 19.03.2026). **This is a summary, not legal advice.**

- **No rule on automated access.** The AGB and the privacy statement say
  nothing about scripts, bots, scraping or using an account with software
  other than the browser or Family Campus. There is no API or data export for
  parents.
- **School purposes only.** The AGB: users "dürfen die Escola-Software
  ausschliesslich für schulische Zwecke verwenden". Preparing your own
  children for their exams is a school purpose; use the module for nothing
  else.
- **No copying or passing on.** The AGB forbid "die Escola-Software oder Teile
  davon zu kopieren, anderweitig zu verbreiten oder unberechtigten Dritten
  zugänglich zu machen". The module does not copy the software; it reads
  what your account shows. Keep the fetched data and documents to yourself
  and never pass on your access.
- **The contract is between the school and Escola**; parents use Escola
  because their school invited them, under the AGB. The school decides about
  the use of Escola and is responsible for informing users. Requests about
  personal data (access, correction, deletion) go **through the school**.
- **Consequence for you:** nothing in these documents forbids reading your own
  family's data with a script, but nothing expressly allows it either, and
  your school may have its own rules. Tell your school that you fetch your
  children's exams with a script for private exam preparation, and stop if
  the school or Escola objects.

The operator's terms can change; check them again from time to time.

## Side effects

- **Every new login sends a security e-mail** to the parents ("Web-Login von
  einem bislang unbekannten Gerät"). The module therefore keeps the session
  (`material/escola/.escola-session.txt`, never committed) and logs in again
  only when it has expired (`ESCOLA_LOGIN_HOURS`, default 720 = 30 days).
- Use it rarely – once a week is enough.

## Setup

In Family Campus's `.env` (copy `.env.example`, never committed):

```text
ESCOLA_URL=https://www.your-school.ch
ESCOLA_USERNAME=…
ESCOLA_PASSWORD=…
ESCOLA_CHILDREN=Anna,Ben          # first names as shown in Escola
```

Python 3.10+, standard library only (`discover` also needs Playwright and
Chromium).

## Use

In the Family Campus folder (the module uses `my-family/`; another campus: `--campus <dir>`):

```bash
python3 sources/escola/escola.py check            # is the saved session valid? (logs in only if needed)
python3 sources/escola/escola.py fetch            # future exams and the current month
python3 sources/escola/escola.py fetch --months 3 # also the last 3 months (--all-months, --all-types)
python3 sources/escola/escola.py fetch --no-documents # without downloading the attachments
```

Per child: `material/escola/<child>/exams.json` (`date`, `subject`, `type`,
`title`, `class`, `goals`, `links`, `documents`; earlier fetches are merged)
and the attachments in `material/escola/<child>/documents/`. Then
`/fc-ingest --from escola` (or `/fc-ingest <person>`) compares them with the
my-family's exams and tiles.

## If Escola changes

The module uses the same requests as the web site: login `POST login.php`,
the children from `guardianMode.children` of the start page, per child
`inc/ajax/eltern/loadEducatorGui.php?kid=…`,
`inc/ajax/homework/application.php` (class and month selection),
`inc/ajax/homework/show_entries.php` (`date=0` = future entries, otherwise the
month's timestamp). If something breaks, `escola.py discover [--headed]`
records the browser's requests (no passwords) into
`material/escola/discover-*/`; analyse them and delete the recording
afterwards. `discover` (like `check --new`) always logs in anew and therefore
sends a security e-mail; that is fine for occasional troubleshooting.
