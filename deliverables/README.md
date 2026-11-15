# Submission package

Prepared on 15 November 2026. This package describes and demonstrates the actual local prototype.

Production deployment preparation is now available in the root `DEPLOYMENT.md`, Dockerfile, Compose configuration, Render blueprint, and separate `NetSim_Lite_Deploy.zip`. The newer production checks pass 18 backend/core/production tests and nine browser scenarios against the compiled single-service app. The report's 14-test figure records the earlier development audit. No cloud deployment has been performed; the Docker image has not been built locally because Docker is unavailable.

| File | Purpose |
| --- | --- |
| NetSim_Lite_Report.docx | Editable project report; replace identity placeholders |
| NetSim_Lite_Report.pdf | Shareable report generated from the same content |
| NetSim_Lite_Presentation.pptx | 14 slides with presenter notes |
| NetSim_Lite_Demo.webm | Captioned browser demo; no spoken narration |
| screenshots/ | Eight actual app captures: topology, animation, primary route, reroute, unreachable, properties, subnet, invalid input |
| demo-script.md | Live walkthrough and suggested narration |
| viva-notes.md | Questions and answers grounded in the implementation |
| verification/ | Captured test/build outputs and document validation |
| submission-details.json | Identity placeholders used by the document generator |
| NetSim_Lite_Source.zip | Clean source snapshot without installed dependencies, logs, or generated submission media |

## Your remaining review

1. Replace student names, roll numbers, college, department, guide, and semester placeholders. Confirm the deadline and institution’s required format.
2. Open the DOCX and PPTX in Word/PowerPoint or compatible software and inspect pagination, fonts, and slide layout on your machine. No native Office rendering was used to verify those formats.
3. Read the report, practice explaining the code, and rehearse using demo-script.md. Follow your institution’s attribution requirements.
4. Review the captioned video. Record your own voice or convert its format if the college requires narration or MP4.
5. Add institution-provided certificates, declarations, and signatures only after receiving the proper wording/approval. None are fabricated here.
6. Submit a copy of the deliverables and source archive in the required portal or medium. No submission has been made for you.

## Regenerate documents

Edit submission-details.json, then from the project root:

```powershell
.venv\Scripts\python -m pip install -r scripts/requirements-deliverables.txt
.venv\Scripts\python scripts/build_deliverables.py
```

To recapture screenshots/video, keep both servers running, then run `node scripts/capture-demo.mjs` inside frontend. Capturing takes roughly 75 seconds and uses its own browser context. It does not change the topology saved in your normal browser.

Editing the DOCX or PPTX directly is also supported, but regeneration will overwrite those edits. Keep a separate final copy.
