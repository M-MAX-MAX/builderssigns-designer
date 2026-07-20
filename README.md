# Builders Signs — Banner Designer

Post-purchase wizard: template gallery → dynamic details form → logo upload (now or later) → confirmation.

## Local development

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_templates   # placeholder SVGs for local testing only
python manage.py createsuperuser
python manage.py runserver
```

## Deploying to cPanel (builderssigns.com.au, account `focusban`)

Target: `design.builderssigns.com.au`, Python 3.9.23 via cPanel's Setup Python App (Passenger).

1. **Push this repo to GitHub** (a new repo, e.g. `builderssigns-designer`), so cPanel's Git Version
   Control can clone from it.

2. **Create the subdomain** — cPanel → Domains → Create A New Domain → `design.builderssigns.com.au`.
   Note the document root it creates.

3. **Software → Setup Python App → Create Application**
   - Python version: 3.9.23
   - Application root: the subdomain's document root from step 2
   - Application URL: `design.builderssigns.com.au`
   - Application startup file: `passenger_wsgi.py`
   - Application Entry point: `application`

   This generates a virtualenv and a placeholder `passenger_wsgi.py` in that folder.

4. **Files → Git™ Version Control → Clone Repository**, pointing at the GitHub repo from step 1,
   with the repository path set to the *same* application root from step 3. If cPanel refuses to
   clone into a non-empty directory (the Python App setup will have already put files there), clear
   the placeholder files first (keep note of the venv path shown in Setup Python App) and clone,
   then re-run pip install as below. If you hit this, let me know exactly what cPanel shows and I'll
   adjust these steps.

5. **Install dependencies** — in Setup Python App, copy the "Enter to the virtual environment"
   command, run it in Advanced → Terminal, `cd` into the app root, then:
   ```
   pip install -r requirements.txt
   ```

6. **Environment variables** — in Setup Python App's environment variables section, set:
   - `SECRET_KEY` (generate a real one, don't reuse the dev default)
   - `DEBUG=False`
   - `ALLOWED_HOSTS=design.builderssigns.com.au`
   - `CSRF_TRUSTED_ORIGINS=https://design.builderssigns.com.au`
   - `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_PORT`, `EMAIL_USE_TLS` — your
     mailbox's SMTP details (or whichever provider you want to send admin notifications through)
   - `DEFAULT_FROM_EMAIL`
   - `ADMIN_NOTIFY_EMAIL`

7. **Migrate + collect static** — still inside the activated virtualenv, in Terminal:
   ```
   python manage.py migrate
   python manage.py collectstatic --noinput
   python manage.py createsuperuser
   ```
   Then add real templates via `/admin/` (TemplateGroup → Template, uploading the actual SVGs) rather
   than running `seed_templates`, which is placeholder data for local dev only.

8. **Restart** the app from Setup Python App.

Deferred logos are tracked manually for now: the admin list shows `logo_deferred_at` for each
request, and there's a "Mark logo received" bulk action once you've matched an upload from the
standalone uploader to its order.
