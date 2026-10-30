# How SMART's components fit together

SMART separates the task interface, compiler tools, and optional model client.

1. The **server** exposes REST endpoints and MCP tools. It owns uploaded inputs, task records, and the filesystem used by file-reading tools.
2. **Cetus** runs as a subprocess on that server. SMART selects its arguments from the server's configured profile JSON.
3. A **model client** is optional. The bundled CLI, or an external MCP client, can use a model to decide which server tools to call.
4. A **model host** serves inference. It may be local Ollama, OpenAI, or another supported OpenAI-compatible endpoint.

For a direct REST optimization:

```text
curl uploads C bytes → SMART task → Cetus → generated C → download
```

For a conversational optimization:

```text
user prompt → model client → MCP get_file_content on server
            → MCP optimize_code_snippet with source text → Cetus → C text
```

The model does not replace Cetus's transformation or correctness checks. A statement in the model's response is not sufficient evidence that compilation or optimization succeeded; inspect the tool result and generated program.

## Profiling and optimization are different tasks

- **Optimization** transforms C source using a named Cetus profile.
- **Classical C profiling** compiles and runs the program with GNU GCC and gprof.
- **Classical Python profiling** runs the program with Python's cProfile.

REST/MCP profiling currently uses the classical profiler. Internal LLM/augmented profiler implementations also exist, but the public request examples do not expose a selector for them.

Direct optimization and classical profiling need no running model service. A model is needed when you choose a conversational client.

## Source files and includes

MCP file paths refer to the server's filesystem, not the machine running a remote client. A read-only mount into the server can make a user directory available for file reading.

The current optimizer tool receives source text and stages it as a temporary file. It does not automatically collect adjacent headers or a multi-file build. The checked-in examples are self-contained and use system headers. Programs with `#include "project_header.h"` need an explicitly prepared input/header workflow; merely mounting the original directory does not stage that header for the snippet tool.

System headers are also input to Cetus's parser after preprocessing. Their syntax depends on the image's libc/compiler. The Java 21 image uses Debian/glibc; this avoids the previous Alpine/musl environment but does not promise that all C dialect extensions can be parsed. See [parser troubleshooting](../troubleshooting.md#cetus-parser-or-header-errors).

## What a successful example proves

The example scripts compare the original and generated programs' output. This is a correctness check for those inputs. Transformation evidence comes from inspecting generated loops and directives. Performance claims require separate timing experiments.

[Back to README](../../README.md)
