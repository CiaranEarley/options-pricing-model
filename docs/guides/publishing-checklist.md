# Publishing Checklist

Use this before pushing the repo public or deploying to Streamlit Community
Cloud.

## Repo Hygiene

- Run `python -m unittest discover`.
- Keep screenshots under `docs/assets/`.
- Confirm temporary outputs and logs are not tracked.
- Decide whether to add a license file.

## GitHub Presentation

- README opens with the app purpose and a strong screenshot.
- README explains every major app section.
- README links to setup, walkthrough, screenshots, and architecture docs.
- Screenshots are current, readable, and do not show local file paths or secrets.

## Streamlit Deployment

```text
Entry point: app.py
Secrets: none required
```

## Final Checks

- App loads locally.
- Screenshots render in GitHub markdown.
- Links in README work.
- Tests pass.
