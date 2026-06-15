# WORKFLOWS.md

## How I work with coding agents

Claude Code is my primary coding agent, and I treat it as a senior engineering partner
rather than an autocomplete tool. I usually start by asking it to understand the
codebase, find the relevant files, and propose a plan before it writes any code. Once the
direction looks right, I hand off well scoped work: implementing features, refactoring
modules, writing tests, debugging failures. I keep the things that should stay with a
human, the architecture decisions, the API contracts, and the security review, and let
the agent carry a large part of the implementation. This whole take home is an example of
that split. I drove the decisions and the agent built against them, and the trail of who
decided what is in `decision.md` and `AGENT_LOG.md`.

## MCP powered workflow

A big part of how I work runs on MCP (Model Context Protocol). Instead of pasting the
same context into prompts over and over, I expose tools and project specific
capabilities through MCP servers so the agent can reach the information it needs directly.
That makes the back and forth feel natural, because Claude can query project data,
inspect resources, and run custom workflows without me switching context for it.

One project I am building right now is an MCP server for **AskNEU**, an AI powered
platform that helps Northeastern students navigate university resources. The server
exposes structured tools for the university specific knowledge, so the coding agent can
retrieve the right information directly instead of leaning on static prompts. The point is
to make both the development and the future AI interactions much more context aware.

## Custom skills

I keep a growing set of custom Claude Code skills for repetitive work. The one I reach for
most is a drafting assistant that mirrors my writing style, so when I am writing
documentation, proposals, emails, or pull request descriptions, the output follows my
structure and tone instead of reading like generic AI text. I have reusable skills for a
handful of common jobs too:

* generating REST endpoints
* writing unit tests
* reviewing pull requests
* producing technical documentation
* summarizing large code changes

These keep the output consistent across projects and cut down on repeating myself in
prompts. The harness in this repo is the same idea pushed further: the skills under
`.claude/skills/` (crawl, reason with its playbooks, synthesize, eval) are what turn a
plain coding agent into the Qosmic audit agent.

## Automation with n8n

Outside of coding, I lean on n8n to automate the small repetitive parts of my day. I run
several of these daily. Most of them connect APIs, trigger notifications, organize
information, and handle routine maintenance in the background. Each one is intentionally
lightweight, but together they save a real amount of time.

I also use n8n to automate parts of my job search. That workflow collects new openings,
filters them with AI powered criteria, enriches the company information, and only pings me
when a posting actually matches my profile. The repetitive work runs on its own, while I
stay responsible for judging the opportunity and tailoring the application.

## My philosophy

The goal is not to have AI write code for me. It is to take the friction out of building.
I use coding agents to speed up implementation, automate the repetitive work, and surface
the right context fast, while I stay responsible for the system design, the validation,
and the final engineering calls.
