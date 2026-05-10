# LangSmith Tracing

This project uses LangSmith to capture execution traces for LangGraph runs in non-test
scenarios. Each node invocation (intent classifier, tool loops, and terminal responses)
appears as a separate span, which makes routing decisions and tool usage easy to inspect
and cite in the thesis.

## Setup

1. Create a LangSmith account and an API key.
2. Add the following to your environment (or .env file):

```
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your-langsmith-key-here
LANGCHAIN_PROJECT=assistant_agent
```

## How It Works

LangSmith is enabled through the `LANGCHAIN_TRACING_V2` environment variable. When it is
`true`, LangChain automatically records traces for every graph run, including:

- The input prompt and messages flowing through the graph
- Node-level routing decisions (intent classifier, task CRUD, briefing)
- Tool call inputs and outputs

Tests disable tracing to keep the suite isolated and deterministic. Traces are only
recorded for real runs launched from scripts or a REPL.

Example trace: https://eu.smith.langchain.com/public/b80c96ad-810a-432a-a5fc-67193223ab40/r
