# Open Agent

> **An uncompromised desktop AI Agent tool built exclusively for power users and geeks.**
>
> **一款真正属于极客的桌面端 AI 智能体工具。**

> It strips away all the fluff, delivering only the core infrastructure you truly need to collaborate with AI: **Chat, Tools, Cron Tasks, and Absolute Control.**
>
> 它拒绝一切花哨的伪需求，只提供你与 AI 协作时真正需要的核心底层：**对话、工具、定时任务，以及绝对的控制权。**

**🌐 [简体中文](./README-CN.md) | English**

---

## 💡 Product Philosophy: Pure, Minimalist, User-Sovereign

### 1. Radical Constraint is Our Core Principle

Every time we consider adding a feature, we ruthlessly ask ourselves: *“Is this absolutely necessary?”*
Open Agent never makes assumptions, never presets your workflow, and never injects hidden logic behind your back. It provides nothing but a solid, lightweight foundation. The rest is entirely up to you.

### 2. Zero System Prompts—Unless You Write Them

Open Agent **contains absolutely no built-in system prompts**.
When you open a new session, the AI carries no hardcoded persona, no behavioral bias, and no stylistic baggage. It is a completely blank canvas. Simply create an AGENTS.md file in your working directory, state your directives, and give the AI its "soul."
*Without this file, it remains a razor-sharp, silent tool waiting for your command.*

### 3. 100% Visibility: No Black Boxes

In Open Agent, every single step of the AI's cognition is exposed right before your eyes:

* How it breaks down complex tasks.
* What tools it decides to call.
* The exact parameters passed into those tools.
* The raw results returned.

This radical transparency isn't just a feature; it’s our stance: **As the architect of your workspace, you have the right to know exactly what your assistant is doing.**

### 4. Zero Bloat, Naked Architecture

The codebase is stripped down to its bare essentials, featuring a crystal-clear, intuitive directory structure.
No over-engineered abstractions. No nested architectural traps. Every file has one explicit responsibility. **Less code means zero friction to understand, effortless modification, and absolute trust.**

### 5. Absolute Sovereignty

In the ecosystem of Open Agent, you possess total control:

* **System Prompts** are strictly written by you.
* **Model Providers** and specific models can be switched instantly at your whim.
* **Working Directories** are hard-bounded to the exact paths you lock down.
* **Cron Tasks** trigger precisely when and how you dictate.
* **At any given millisecond**, you can hard-abort the AI’s execution.

> ⚠️ **Open Agent is your tool, not your proxy. It works FOR you, never INSTEAD of you.**

---

## ⚡ Core Capabilities

* 💬 **Pure Chat**
  Interact with AI via raw, unadulterated natural language. Every session maintains a pristine context history snapshot, allowing you to back-track, branch out, or permanently wipe history at any time.
* 📂 **Granular File IO**
  The AI manipulates, creates, and edits files via streaming operations with high precision—strictly confined within your **designated working directory**. Safe, deterministic, and isolated.
* 💻 **Native Shell Execution**
  Empower your AI with OS-level execution capabilities. It natively spins up PowerShell on Windows and Bash on Linux/macOS to seamlessly close the loop on automation tasks.
* 🧩 **Modular Skills**
  Abstract and reuse capability modules via a simple SKILL.md file. Instruct the AI to assemble and invoke specific skills for targeted scenarios. You author the skills; you govern their lifecycle.
* 🌐 **Full MCP Ecosystem Support**
  Connect seamlessly to external tools and services via the Model Context Protocol (MCP). Out-of-the-box support for HTTP, SSE (Server-Sent Events), and stdio communication pipelines.
* ⏱️ **Deterministic Cron Tasks**
  Breathe automation into your AI using standard Cron expressions. Whether it’s generating daily debriefs, running system health checks, or executing periodic pipelines, the AI works strictly on your schedule.
* 🤖 **Multi-Model Agility**
  Configure multiple model providers (OpenAI, Anthropic, Gemini, DeepSeek, etc.) concurrently. Fluidly hop between different "brains" depending on the complexity of the task.

---

## 🛠️ When to Use Open Agent

* **You are a control freak:** You cannot stand commercial AI wrappers with their shady background prompts, hidden telemetry, and black-box operations.
* **You are a heavy automation hacker:** You need a local agent that flawlessly understands your intent and can reliably execute scripts and manage local source files.
* **You are a minimalist:** You are exhausted by bloated UIs and endless configuration tabs. You want to return to the raw power of the "Input-Process-Execute" loop.
* **You are an AI/Full-Stack Developer:** You want a clean, unbloated open-source codebase to tinker with, extend, and hack into your ultimate custom AI workspace.

---

## 🚀 Get Started

1. **Configure**: Drop in your API keys and select your primary model.
2. **Isolate**: Define a local folder to serve as the AI's absolute working boundary.
3. **Animate (Optional)**: Drop an AGENTS.md file into the workspace and dictate your supreme instructions.

**Everything starts from a void—it is up to you to shape the world.**

---

## 🔑 Open Source Promise

Open Agent is 100% open-source. You can audit every single line of code to verify it does absolutely nothing behind your back.

[📦 View Source / Open an Issue] | [💬 Join the Developer Community]
