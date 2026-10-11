# Word list

The technical words used in these docs, in plain language.

| Word | What it means |
|---|---|
| Ambiguous ticket | A labeled ticket whose expected label the person labeling could not decide. It is kept but left out of every score. |
| API | A way for one program to ask another program to do something. |
| API key | A long secret string that proves the caller is allowed to use the service. Treat it like a password. |
| Assigned team | The team the model suggests should handle a ticket, for example `devops` or `frontend`. |
| Backend | The part that actually reads the tickets: the local model, the hosted Jev service, or a fake one for tests. |
| Batch | Several tickets sent in one request. |
| Category | The kind of problem a ticket describes, for example `security` or `ui`. |
| Confidence | A number from 0 to 1 that says how sure the model is about a label. |
| Container (Docker) | A sealed package that runs the service the same way on any computer. |
| Endpoint | One address of the API that does one job, such as `/api/v1/ticket-analyses`. |
| `.env` file | A private text file on your machine that holds those settings. It is never shared or committed. |
| Environment variable | A setting handed to the program from outside, such as `JEV_BACKEND=jev`. |
| Expected label | The label a person decided is right for a ticket. The service's answers are checked against it. |
| F1 | One score from 0 to 100% that combines a label's precision and recall. It is low if either one is low. |
| Header | Extra information sent along with a request, such as the API key. |
| Health check | A tiny address that tells you whether the service is running and ready. |
| Held-out set | Labeled tickets never used while editing label descriptions, so their accuracy is a fair report. |
| Image | The packed copy of the service that Docker starts containers from. |
| JSON | A text format for structured data, written with names and values inside `{ }`. |
| Labeled set | Tickets that have expected labels, used to measure how accurate the service is. |
| Log | The running record the service writes about what it did, used to find problems. |
| Macro-F1 | The average F1 over the labels of one question, so every label counts equally. Labels with no F1 are left out of the average. |
| Milestone | A saved run of the check with a name, such as `baseline`, so later runs can be compared with it. |
| Missing prediction | A ticket the model gave no answer for. It counts as wrong, never as dropped. |
| Model | The language model that reads a ticket and picks the labels. |
| Precision | When the model gives a label, how often it is right. |
| Problem details (RFC 9457) | The standard shape the service uses for every error: a title, a plain sentence, and a stable `code`. It is sent as `application/problem+json`. |
| Proxy | A middleman server that receives requests first and passes them on to the service. |
| Recall | Of the tickets that should have a label, how many the model found. |
| Request / response | What you send to the service, and what it sends back. |
| Request ID | A short code attached to each request, used to find it in the logs. |
| Severity | How serious a ticket is: `critical`, `high`, `medium`, `low` or `unknown`. |
| Smoke set | The first 8 labeled tickets. They only catch breakage and do not measure accuracy, because their descriptions were adjusted after seeing the results. |
| Status code | The number in every answer: 2xx worked, 4xx your request has a problem, 5xx the service has a problem. |
| Tuning set | Labeled tickets you may look at while editing label descriptions. |
| Validation | Checking that a request is complete and within limits before any work is done. |
| Volume (Docker) | Storage that lives outside the container, so files such as the downloaded model survive a restart. |
