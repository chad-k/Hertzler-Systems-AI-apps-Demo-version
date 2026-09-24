# Hertzler demo suite

One GitHub repository containing the AI Solution Finder and ten standalone Streamlit demonstration apps. All analysis uses bundled or generated synthetic data. There are no file-upload widgets or live database connection controls. Existing analysis settings, charts, exports, and selector workflows are retained. Each demo has a detailed beginner guide at the top and an inquiry form at the end.

## Start here

1. Extract this ZIP on your computer.
2. Create a GitHub repository, for example `hertzler-demo-suite`.
3. Upload the **contents** of this folder to the repository root. `app.py`, `requirements.txt`, `common`, `apps`, and `guides` must be at the top level. Keep every subfolder and bundled data file. Do not upload only the ZIP.
4. Include `.streamlit/config.toml` and `.gitignore`. Never commit a real `.streamlit/secrets.toml` or email credentials.
5. In Streamlit Community Cloud, deploy each desired entry point below from the same repository and branch. Select Python **3.12**. Streamlit installs the root `requirements.txt`.
6. Add email credentials to **each deployed app's Secrets settings**, as explained below. A shared repository does not share deployment secrets automatically.
7. Open every deployed app, explore its demo, and check the form. After configuration, submit an inquiry you authorize and confirm it arrives in Chad's inbox. This package was tested with mocked delivery; it has not sent a live email.

The repository is shared; these are separate Streamlit deployments, preserving the option of a separate link for every demo. One deployment of the root app alone does not deploy all ten demos.

| Application | Main file path |
|---|---|
| AI Solution Finder | `app.py` |
| Predictive SPC | `apps/predictive_spc/app.py` |
| Batch Anomaly Detection | `apps/batch_anomaly/app.py` |
| Mislabel Detection | `apps/mislabel/app.py` |
| SPC Auto Interpretation | `apps/spc_interpretation/app.py` |
| Operator Data Integrity Checker | `apps/entry_integrity/app.py` |
| AI Database Health Assistant | `apps/database_health/app.py` |
| Certificate of Analysis Generator | `apps/coa/app.py` |
| Manufacturing Copilot | `apps/copilot/app.py` |
| Process Optimization | `apps/optimization/app.py` |
| Smart Inspection Frequency | `apps/inspection_frequency/app.py` |

If existing deployments point to separate repositories, copying this repository does not update those deployments. Deploy from the new repository using the matching main file paths. Streamlit may require deleting and recreating an app to change its repository coordinates. Record existing app names and secrets first; arrange the switchover before removing live apps. Reuse the existing custom subdomains if available, or update `demo_url` values in `app_catalog.json` to the new URLs. The catalog currently contains your original URLs, so until migration those links still lead to the original deployments.

## Make the contact forms send email

Every form sends to **chad@hertzler.com**, includes the app name, and sets Reply-To to the customer's email address. Customers can enter their name, email, optional company, and customization request. Email is sent only when the customer submits the form. Results and demo files are not attached.

Choose one configuration below. Use your provider's verified sending address; the customer's address is never used as the sender. When secrets are absent, the form is visibly disabled and shows Chad's address. It will not pretend a message was sent. An accepted message means the provider accepted it for delivery, not that inbox delivery is guaranteed.

### Option A: Resend HTTPS email API

Create a Resend account, verify a sending domain you control, and create a sending API key. In each Streamlit app's Secrets settings, paste:

```toml
[email]
provider = "resend"
api_key = "YOUR_REAL_API_KEY"
from_email = "Hertzler Demos <demos@YOUR_VERIFIED_DOMAIN>"
```

Replace both placeholders. A production verified sender is needed to send outside any provider test restrictions. This email service is independent of AI; no AI model or AI API key is required. Your provider's email limits and pricing apply.

### Option B: your existing SMTP provider

```toml
[email]
provider = "smtp"
host = "smtp.YOUR_PROVIDER.com"
port = 587
security = "starttls"
username = "YOUR_SMTP_USERNAME"
password = "YOUR_SMTP_PASSWORD"
from_email = "demos@YOUR_VERIFIED_DOMAIN"
```

Use `security = "ssl"` and port `465` if required by your provider. SMTP password authentication must be enabled for the account. If your host blocks SMTP or your organization requires OAuth instead, use the HTTPS option or ask your mail administrator for a supported relay. Plain unencrypted SMTP is not supported.

The form validates input, prevents repeat submission of the same message in the current session, and applies a 60-second session cooldown. Resend retries use an idempotency key. These are lightweight safeguards, not a global anti-spam service; for a high-traffic public site, provider limits and server-side abuse controls may be needed. SMTP retries after ambiguous network failures can duplicate a message. Provider rejection and delivery errors are shown as failures, without exposing credentials.

## Branding and inquiry subjects

Every app, including the solution finder, ends with **Powered by Hertzler Systems** and the supplied logo in `assets/hertzler_logo.png`. Keep the assets folder when uploading the repository. The contact section displays the app name automatically. Every inquiry includes it in both the subject (`Hertzler demo inquiry: <app name>`) and the message body; customers do not need to type it.

## What changed

- Removed public file-upload controls, including the CoA logo upload and optimization mapping-file upload.
- Forced every source chooser to the built-in demonstration path. Removed the database app's live connection interface.
- Included deterministic synthetic CSVs for optimization and synthetic Excel workbooks for inspection frequency.
- Added ten detailed guides: purpose, example, usage, terminology, output interpretation, limitations, and customization requirements.
- Added a shared end-of-page inquiry form to all eleven entry points, including the selector. It remains visible when an analysis is waiting for a button or input selection.
- Preserved the selector's guided questions, free-text parser, catalog, help, downloads, and existing Hertzler contact links. The embedded form is additional.
- Preserved analysis controls, report downloads, and the Copilot voice component. A customer may type a question, edit demo settings, or enter contact details, but cannot upload a data file.
- Corrected demo defaults for the mislabel numeric features and the inspection specification fields.

The selector retains its existing preview/approval settings. To remove its preview banner after reviewing the catalog, set `approved` to `true` for the entries you approve and `preview_mode` to `false`. Entries that are not approved are hidden outside preview mode.

## Repository layout and maintenance

`app.py` runs the selector. Each `apps/<id>/app.py` runs its app's `demo.py`. Shared modules live in `common/`. Long explanations are editable Markdown files in `guides/`. `app_catalog.json` controls selector descriptions and URLs. `deployment_manifest.json` records the source-to-entry-point mapping.

Python automatically finds `engine.py` next to the root selector. Nested entry points add the repository root to their import path so they can find `common`. Fixture paths are relative to the demo source, not the current working directory. Keep these files together.

To run locally with Python 3.12:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

For a specific demo:

```bash
python -m streamlit run apps/optimization/app.py
```

For local email configuration only, copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`, fill in real settings, and keep that file out of Git. Deployments should use the Streamlit Secrets editor instead.

Run the automated non-network checks:

```bash
python -m unittest discover -s tests -v
```

## Demo interpretation

The apps intentionally demonstrate different techniques. Some use statistical or machine-learning models; the selector and several assistants use rules. This package does not add a hosted generative AI connection. Batch anomaly scores are not future defect probabilities, mislabel suggestions are not verified identities, integrity flags do not establish misconduct, and optimization suggestions require engineering validation. Synthetic results and exported documents must not be used as production acceptance evidence.

Official deployment references:
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
- https://resend.com/docs/api-reference/emails/send-email
