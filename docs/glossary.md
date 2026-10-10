# Word list

The technical words used in these docs, in plain language.

| Word | What it means |
|---|---|
| API | A way for one program to ask another program to do something. |
| API key | A long secret string that proves the caller is allowed to use the service. Treat it like a password. |
| Backend | The part that actually reads the tickets: the local model, the hosted Jev service, or a fake one for tests. |
| Batch | Several tickets sent in one request. |
| Category | The kind of problem a ticket describes, for example `security` or `ui`. |
| Confidence | A number from 0 to 1 that says how sure the model is about a label. |
| Container (Docker) | A sealed package that runs the service the same way on any computer. |
| Endpoint | One address of the API that does one job, such as `/api/v1/ticket-analyses`. |
| `.env` file | A private text file on your machine that holds those settings. It is never shared or committed. |
| Environment variable | A setting handed to the program from outside, such as `JEV_BACKEND=jev`. |
| Header | Extra information sent along with a request, such as the API key. |
| Health check | A tiny address that tells you whether the service is running and ready. |
| Image | The packed copy of the service that Docker starts containers from. |
| JSON | A text format for structured data, written with names and values inside `{ }`. |
| Log | The running record the service writes about what it did, used to find problems. |
| Model | The language model that reads a ticket and picks the labels. |
| Problem details (RFC 9457) | The standard shape the service uses for every error: a title, a plain sentence, and a stable `code`. It is sent as `application/problem+json`. |
| Proxy | A middleman server that receives requests first and passes them on to the service. |
| Request ID | A short code attached to each request, used to find it in the logs. |
| Request / response | What you send to the service, and what it sends back. |
| Severity | How serious a ticket is: `critical`, `high`, `medium`, `low` or `unknown`. |
| Status code | The number in every answer: 2xx worked, 4xx your request has a problem, 5xx the service has a problem. |
| Validation | Checking that a request is complete and within limits before any work is done. |
| Volume (Docker) | Storage that lives outside the container, so files such as the downloaded model survive a restart. |
