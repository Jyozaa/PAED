# Execution notes

The initial complete numerical pipeline ran successfully and produced all descriptive outputs. The first full test invocation had 3 failing assertions because tests compared binary floating-point percentage conversions with exact decimal equality (0.7329000000000001 versus 0.7329). Those assertions were corrected to numerical tolerances; the analysis values and scientific decisions did not change.

A hash-verification attempt made after that failed test invocation correctly detected outputs newer than the prior successful manifest. The complete pipeline was rerun after the assertion fixes to regenerate a consistent manifest. The final recorded test and verification results supersede those initial failures; see `run_manifest.json` and the final publication handover.

No inferential model failed to converge: both statistical workflows stopped at evidence eligibility, before an optimizer was invoked. R fitting paths are conditional and have not been executed on eligible evidence in this project.

The in-app browser preview could not initialize because its installed client referenced a missing `browser-service.mjs` runtime module. HTML report headings, local links, image paths and styling hooks were checked by an automated structural test. All six generated PNG figures were visually inspected; crowded SROC and comparability labels were corrected and re-rendered. No successful browser screenshot of the HTML is claimed.

The first pre-commit whitespace check flagged Matplotlib SVG path formatting and standard CSV CRLF serialization. These generated formats are excluded from code-style whitespace checks through `.gitattributes`; their numerical values, embedded source strings and renderings are preserved. Source-code whitespace checks remain enabled. This check stopped the initial publication command before any output commit or push; publication was retried only after it passed.
