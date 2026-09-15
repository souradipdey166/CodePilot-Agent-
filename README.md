---
title: CodePilot Agent
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: "4.44.1"
app_file: app.py
pinned: false
---

# CodePilot Agent

An agentic code-repair system built with LangGraph, LangChain, and Gradio.

The agent analyzes a bug report and error output, searches the codebase, identifies the likely root cause, generates a patch, applies the patch, and validates the result with tests.
