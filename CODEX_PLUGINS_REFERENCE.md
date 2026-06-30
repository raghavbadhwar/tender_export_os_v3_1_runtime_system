# Codex Plugins Reference

Generated: 2026-06-30 02:24:25 IST

This file inventories the Codex plugins visible to this machine through `codex plugin list --available --json`, enriched from local plugin manifests, app connector files, MCP server files, README files, skills, commands, agents, references, and scripts where present.

Important: installed/enabled is inventory state. Actual tool exposure in a specific Codex thread can still depend on auth, feature flags, MCP startup health, and whether the current chat has loaded that plugin/app/tool.

## Summary

- Total known plugin entries: 272
- Installed: 143
- Enabled: 124
- Disabled but installed: 19
- Available but not installed: 129

### Marketplaces

| Marketplace | Plugins |
|---|---:|
| `claude-for-legal-india` | 13 |
| `local-codex-plugins` | 69 |
| `openai-bundled` | 5 |
| `openai-curated` | 180 |
| `openai-primary-runtime` | 5 |

### Status Counts

| Status | Count |
|---|---:|
| available, not installed | 129 |
| installed, disabled | 19 |
| installed, enabled | 124 |

### Main Categories Detected

| Category | Count |
|---|---:|
| Productivity | 101 |
| Developer Tools | 70 |
| Finance | 27 |
| Business & Operations | 15 |
| Data & Analytics | 14 |
| Education & Research | 12 |
| Communication | 12 |
| Creativity | 9 |
| Design | 2 |
| Business | 2 |
| Other | 2 |
| Travel | 2 |
| Marketing | 1 |
| Product Management | 1 |
| Engineering | 1 |
| Security | 1 |

## How To Read This

- `Interface capabilities` come from the plugin manifest and usually describe whether the plugin supports interactive use, read operations, write operations, or similar behavior.
- `App connectors` means the plugin routes through a Codex/ChatGPT app connector such as Gmail, Google Drive, Supabase, Vercel, or others. These usually need authentication before use.
- `MCP servers` means the plugin exposes local or remote MCP tools. Remote HTTP MCPs and local stdio MCPs can fail separately from install state.
- `Skills`, `commands`, `agents`, `references`, and `scripts` are local assets shipped with the plugin.
- Descriptions are extracted from manifests first, then README/CODEX files as fallback. Missing descriptions are marked as not found instead of guessed.

## Quick Index

| Plugin ID | Status | Category | What It Does |
|---|---|---|---|
| `ai-governance-legal@claude-for-legal-india` | installed, enabled | Productivity | Triages proposed AI use cases against your registry, runs impact assessments across the regimes in scope, reviews vendor AI terms for... |
| `cocounsel-legal@claude-for-legal-india` | installed, enabled | Productivity | CoCounsel Legal delivers comprehensive Westlaw Deep Research reports with inline, linked citations to Westlaw and Practical Law sources... |
| `commercial-legal@claude-for-legal-india` | installed, enabled | Productivity | Reviews vendor agreements, NDAs, and SaaS subscriptions against your sales-side or purchasing-side playbook, tracks renewals and cancel-by... |
| `corporate-legal@claude-for-legal-india` | installed, enabled | Productivity | Runs M&A diligence at scale with cited tabular review, builds disclosure schedules and closing checklists, drafts board consents and... |
| `employment-legal@claude-for-legal-india` | installed, enabled | Productivity | Reviews hires and terminations for jurisdiction-specific risk flags, classifies workers against the controlling state test, tracks leave... |
| `ip-legal@claude-for-legal-india` | installed, enabled | Productivity | Runs first-pass trademark clearance and freedom-to-operate triage, screens invention disclosures for initial patentability, drafts and... |
| `law-student@claude-for-legal-india` | installed, enabled | Productivity | Drills Socratically, briefs cases, builds outlines, runs bar prep sessions tuned to your jurisdiction, grades IRAC practice, and plans the... |
| `legal-builder-hub@claude-for-legal-india` | installed, enabled | Productivity | Finds, evaluates, and installs community legal skills - with a security review gate before anything lands in your environment... |
| `legal-clinic@claude-for-legal-india` | installed, enabled | Productivity | Sets up the clinic, onboards students, runs structured intake, tracks deadlines with malpractice-aware caution, and hands off cases at... |
| `litigation-legal@claude-for-legal-india` | installed, enabled | Productivity | Manages the litigation portfolio - matters, deadlines, holds, demands, outside counsel - and does the work: claim charts (patent and... |
| `privacy-legal@claude-for-legal-india` | installed, enabled | Productivity | Triages processing activities, generates PIAs, reviews DPAs as controller or processor, drafts DSAR responses within statutory timelines... |
| `product-legal@claude-for-legal-india` | installed, enabled | Productivity | Reviews product launches against your risk calibration, answers 'is this a problem?' questions in minutes, checks marketing copy for claims... |
| `regulatory-legal@claude-for-legal-india` | installed, enabled | Productivity | Watches regulatory feeds, diffs new rules against your policy library, tracks comment deadlines and open gaps, and writes the digest your... |
| `ai-elements@local-codex-plugins` | installed, enabled | Developer Tools | Install and compose Vercel AI Elements UI. |
| `ai-governance-legal@local-codex-plugins` | installed, enabled | Productivity | Triages proposed AI use cases against your registry, runs impact assessments across the regimes in scope, reviews vendor AI terms for... |
| `brand-design-studio@local-codex-plugins` | installed, enabled | Design | Packaging and brand identity design studio. |
| `claude-code-setup@local-codex-plugins` | installed, enabled | Developer Tools | Audit and upgrade repos with Codex/Claude automation, safe hooks, templates, runtime checks, and evidence scoring. |
| `claude-for-legal@local-codex-plugins` | installed, enabled | Productivity | Routes legal workflows to the installed India-adapted Codex practice plugins. |
| `claude-md-management@local-codex-plugins` | installed, enabled | Developer Tools | Tools to maintain and improve CLAUDE.md files - audit quality, capture session learnings, and keep project memory current. |
| `cli-printing-press-factory@local-codex-plugins` | installed, enabled | Developer Tools | Create production-grade CLIs from APIs, docs, HAR captures, and plans. |
| `cocounsel-legal@local-codex-plugins` | installed, enabled | Productivity | CoCounsel Legal delivers comprehensive Westlaw Deep Research reports with inline, linked citations to Westlaw and Practical Law sources... |
| `code-review@local-codex-plugins` | installed, enabled | Developer Tools | Automated code review for pull requests using multiple specialized agents with confidence-based scoring |
| `code-simplifier@local-codex-plugins` | installed, enabled | Developer Tools | Agent that simplifies and refines code for clarity, consistency, and maintainability while preserving functionality |
| `commercial-legal@local-codex-plugins` | installed, enabled | Productivity | Reviews vendor agreements, NDAs, and SaaS subscriptions against your sales-side or purchasing-side playbook, tracks renewals and cancel-by... |
| `commit-commands@local-codex-plugins` | installed, enabled | Developer Tools | Streamline your git workflow with simple commands for committing, pushing, and creating pull requests |
| `context7@local-codex-plugins` | installed, enabled | Developer Tools | Upstash Context7 MCP server for up-to-date documentation lookup. Pull version-specific documentation and code examples directly from source... |
| `copilot-sdk@local-codex-plugins` | installed, enabled | Developer Tools | Build applications with the GitHub Copilot SDK across multiple programming languages. Includes comprehensive instructions for C#, Go... |
| `corporate-legal@local-codex-plugins` | installed, enabled | Productivity | Runs M&A diligence at scale with cited tabular review, builds disclosure schedules and closing checklists, drafts board consents and... |
| `data@local-codex-plugins` | installed, enabled | Data & Analytics | India-aware data analysis workflows for SQL, exploration, validation, dashboards, visualizations, and stakeholder insigh |
| `database-data-management@local-codex-plugins` | installed, enabled | Developer Tools | Database administration, SQL optimization, and data management tools for PostgreSQL, SQL Server, and general database development best... |
| `design@local-codex-plugins` | installed, enabled | Design | India-aware design workflows for critique, accessibility, UX copy, design systems, research synthesis, and developer han |
| `employment-legal@local-codex-plugins` | installed, enabled | Productivity | Reviews hires and terminations for jurisdiction-specific risk flags, classifies workers against the controlling state test, tracks leave... |
| `enterprise-search@local-codex-plugins` | installed, enabled | Productivity | India-aware enterprise search across email, files, chat, tasks, and internal knowledge with privacy and privilege safegu |
| `feature-dev@local-codex-plugins` | installed, enabled | Developer Tools | Comprehensive feature development workflow with specialized agents for codebase exploration, architecture design, and quality review |
| `finance@local-codex-plugins` | installed, enabled | Productivity | India-aware finance workflows for journal entries, reconciliation, close, statements, variance analysis, audit support, |
| `frontend-design@local-codex-plugins` | installed, enabled | Developer Tools | Frontend design skill for UI/UX implementation |
| `frontend-web-dev@local-codex-plugins` | installed, enabled | Developer Tools | Essential prompts, instructions, and chat modes for modern frontend web development including React, Angular, Vue, TypeScript, and CSS... |
| `gem-team@local-codex-plugins` | installed, enabled | Developer Tools | Multi-agent orchestration framework for spec-driven development and automated verification. |
| `human-resources@local-codex-plugins` | installed, enabled | Productivity | India-aware HR workflows for recruiting, offers, onboarding, compensation, policies, people reports, and performance rev |
| `inventor-intelligence@local-codex-plugins` | installed, enabled | Productivity | Invent and stress-test breakthrough concepts. |
| `ip-legal@local-codex-plugins` | installed, enabled | Productivity | Runs first-pass trademark clearance and freedom-to-operate triage, screens invention disclosures for initial patentability, drafts and... |
| `karimo@local-codex-plugins` | installed, enabled | Developer Tools | PRD-driven autonomous agent orchestration |
| `law-student@local-codex-plugins` | installed, enabled | Productivity | Drills Socratically, briefs cases, builds outlines, runs bar prep sessions tuned to your jurisdiction, grades IRAC practice, and plans the... |
| `legal@local-codex-plugins` | installed, enabled | Productivity | India-aware legal productivity workflows for contract review, privacy, compliance, vendor checks, legal briefs, and appr |
| `legal-builder-hub@local-codex-plugins` | installed, enabled | Productivity | Finds, evaluates, and installs community legal skills - with a security review gate before anything lands in your environment... |
| `legal-clinic@local-codex-plugins` | installed, enabled | Productivity | Sets up the clinic, onboards students, runs structured intake, tracks deadlines with malpractice-aware caution, and hands off cases at... |
| `litigation-legal@local-codex-plugins` | installed, enabled | Productivity | Manages the litigation portfolio - matters, deadlines, holds, demands, outside counsel - and does the work: claim charts (patent and... |
| `marketing@local-codex-plugins` | installed, enabled | Marketing | India-aware marketing workflows for campaigns, content, brand review, SEO, email, competitor analysis, and performance r |
| `medconsumables-analyst@local-codex-plugins` | installed, enabled | Business | India medical consumables analyst for market, product, sourcing, sales, finance, and compliance workflows. |
| `operations@local-codex-plugins` | installed, enabled | Productivity | India-aware operations workflows for vendor review, process docs, compliance tracking, capacity planning, runbooks, risk |
| `polyglot-test-agent@local-codex-plugins` | installed, enabled | Developer Tools | Multi-agent pipeline for generating comprehensive unit tests across any programming language. Orchestrates research, planning, and... |
| `privacy-legal@local-codex-plugins` | installed, enabled | Productivity | Triages processing activities, generates PIAs, reviews DPAs as controller or processor, drafts DSAR responses within statutory timelines... |
| `product-legal@local-codex-plugins` | installed, enabled | Productivity | Reviews product launches against your risk calibration, answers 'is this a problem?' questions in minutes, checks marketing copy for claims... |
| `product-management@local-codex-plugins` | installed, enabled | Product Management | India-aware product workflows for PRDs, roadmaps, user research, metrics, competitive analysis, launch checks, and updat |
| `productivity@local-codex-plugins` | installed, enabled | Productivity | India-aware productivity workflows for tasks, memory, daily planning, and work context with privacy safeguards. |
| `project-planning@local-codex-plugins` | installed, enabled | Developer Tools | Tools and guidance for software project planning, feature breakdown, epic management, implementation planning, and task organization for... |
| `ralph-loop@local-codex-plugins` | installed, enabled | Developer Tools | Continuous self-referential AI loops for interactive iterative development, implementing the Ralph Wiggum technique. Run Claude in a... |
| `regulatory-legal@local-codex-plugins` | installed, enabled | Productivity | Watches regulatory feeds, diffs new rules against your policy library, tracks comment deadlines and open gaps, and writes the digest your... |
| `sales@local-codex-plugins` | installed, enabled | Productivity | India-aware sales workflows for account research, outreach drafts, call prep, pipeline review, forecasting, and sales as |
| `security-best-practices@local-codex-plugins` | installed, enabled | Developer Tools | Security frameworks, accessibility guidelines, performance optimization, and code quality best practices for building secure, maintainable... |
| `security-guidance@local-codex-plugins` | installed, enabled | Developer Tools | Security review for Claude-generated code. Pattern-based warnings on edits, LLM-powered diff review on Stop, and an agentic commit reviewer... |
| `small-business@local-codex-plugins` | installed, enabled | Productivity | India-aware small-business workflows for cash flow, invoices, GST/TDS, payroll planning, customer support, campaigns, an |
| `software-engineering-team@local-codex-plugins` | installed, enabled | Developer Tools | 7 specialized agents covering the full software development lifecycle from UX design and architecture to security and DevOps. |
| `sprecial-agent-loop@local-codex-plugins` | installed, enabled | Productivity | Build and package reliable agent loops. |
| `structured-autonomy@local-codex-plugins` | installed, enabled | Developer Tools | Premium planning, thrifty implementation |
| `technical-spike@local-codex-plugins` | installed, enabled | Developer Tools | Tools for creation, management and research of technical spikes to reduce unknowns and assumptions before proceeding to specification and... |
| `telegram@local-codex-plugins` | installed, enabled | Developer Tools | Telegram channel for Claude Code - messaging bridge with built-in access control. Manage pairing, allowlists, and policy via... |
| `testing-automation@local-codex-plugins` | installed, enabled | Developer Tools | Comprehensive collection for writing tests, test automation, and test-driven development including unit tests, integration tests, and... |
| `trading-desk@local-codex-plugins` | installed, enabled | Business | Invoke a multi-asset analyst team for source-backed paper-trading research. |
| `claude-desktop-apify@local-codex-plugins` | installed, disabled | Productivity | Extract data from any website with thousands of scrapers, crawlers, and automations on Apify Store. |
| `claude-desktop-commander@local-codex-plugins` | installed, disabled | Productivity | Build, explore, and automate on your local machine with access to files and terminal. |
| `claude-desktop-figma@local-codex-plugins` | installed, disabled | Productivity | The Figma MCP server helps you pull in Figma context and generate high-quality code that aligns with your codebase and design intent. |
| `claude-desktop-filesystem@local-codex-plugins` | installed, disabled | Productivity | Let Codex access your filesystem to read and write files. |
| `claude-desktop-osascript@local-codex-plugins` | installed, disabled | Productivity | Execute AppleScript to automate tasks on macOS. |
| `claude-desktop-pdf-toolkit@local-codex-plugins` | installed, disabled | Productivity | A local PDF workflow for Codex: fill forms, sign/date PDFs, fetch PDF URLs, merge/split files, extract data, and analyze documents. |
| `claude-desktop-pdf-viewer@local-codex-plugins` | installed, disabled | Productivity | Read, annotate, and interact with PDF files - interactive viewer with search, navigation, annotations, form filling, and text extraction |
| `claude-desktop-powerpoint@local-codex-plugins` | installed, disabled | Productivity | Control Microsoft PowerPoint with AppleScript automation |
| `claude-desktop-word@local-codex-plugins` | installed, disabled | Productivity | Control Microsoft Word with AppleScript automation |
| `fitness-hub-autopilot@local-codex-plugins` | installed, disabled | Developer Tools | Repo-native plan/build/test/fix loops for Fitness Hub AI. |
| `internship-outreach-automation@local-codex-plugins` | installed, disabled | Productivity | People-only, tracker-safe internship outreach |
| `pateintautomation@local-codex-plugins` | installed, disabled | Productivity | Google Form intake and appointment workflow plugin |
| `claude-desktop-chrome-control@local-codex-plugins` | available, not installed | Productivity | Control Google Chrome browser tabs, windows, and navigation |
| `browser@openai-bundled` | installed, enabled | Engineering | Control the in-app browser with Codex |
| `chrome@openai-bundled` | installed, enabled | Productivity | Control Chrome with Codex |
| `computer-use@openai-bundled` | installed, enabled | Productivity | Control Mac apps from Codex |
| `record-and-replay@openai-bundled` | installed, enabled | Productivity | Record what I'm doing on my Mac and turn it into a Skill |
| `latex@openai-bundled` | available, not installed | Education & Research | Compile LaTeX with Tectonic or TeX Live |
| `alpaca@openai-curated` | installed, enabled | Finance | Stop watching the markets. |
| `apollo@openai-curated` | installed, enabled | Business & Operations | Prospecting and outbound execution in Apollo |
| `binance@openai-curated` | installed, enabled | Finance | Binance for Codex lets you access and explore Binance public, read-only market data using natural language. |
| `biorender@openai-curated` | installed, enabled | Creativity | BioRender helps scientists create professional figures in minutes. |
| `build-ios-apps@openai-curated` | installed, enabled | Developer Tools | Build, refine, and debug iOS apps with App Intents, SwiftUI, and Xcode workflows |
| `build-macos-apps@openai-curated` | installed, enabled | Developer Tools | Build, debug, instrument, and implement macOS apps with SwiftUI and AppKit guidance |
| `build-web-apps@openai-curated` | installed, enabled | Developer Tools | Build frontend-focused web apps with generated assets, browser testing, payments, and databases |
| `build-web-data-visualization@openai-curated` | installed, enabled | Developer Tools | Design, build, test, and export web data visualizations |
| `canva@openai-curated` | installed, enabled | Creativity | Search, create, edit designs |
| `circleci@openai-curated` | installed, enabled | Developer Tools | Build, test, and deploy any application |
| `coderabbit@openai-curated` | installed, enabled | Developer Tools | Run AI-powered code review for your current changes |
| `codex-security@openai-curated` | installed, enabled | Security | Security scanning for your codebase |
| `daloopa@openai-curated` | installed, enabled | Finance | Institutional-grade financial analysis workflows. |
| `dow-jones-factiva@openai-curated` | installed, enabled | Education & Research | The Factiva Connector, enables authorized users to search Factiva's global news archive, including premium... |
| `expo@openai-curated` | installed, enabled | Developer Tools | Build, deploy, upgrade, and debug Expo and React Native apps |
| `figma@openai-curated` | installed, enabled | Creativity | Design-to-code workflows powered by the Figma integration |
| `game-studio@openai-curated` | installed, enabled | Developer Tools | Design, prototype, and ship browser games |
| `gmail@openai-curated` | installed, enabled | Communication | Read and manage Gmail |
| `google-calendar@openai-curated` | installed, enabled | Productivity | Manage Google Calendar events and schedules |
| `google-drive@openai-curated` | installed, enabled | Productivity | Work across Drive, Docs, Sheets, and Slides |
| `govtribe@openai-curated` | installed, enabled | Education & Research | Search government contracts, awards, and vendors directly from Codex. |
| `hugging-face@openai-curated` | installed, enabled | Developer Tools | Inspect models, datasets, Spaces, and research |
| `hyperframes@openai-curated` | installed, enabled | Creativity | Write HTML, render video |
| `jam@openai-curated` | installed, enabled | Productivity | Screen record with context |
| `life-science-research@openai-curated` | installed, enabled | Education & Research | General life-sciences research with routing, evidence synthesis, and optional parallel subagent analysis |
| `moody-s@openai-curated` | installed, enabled | Finance | Credit ratings, research, entity intelligence, ownership, financials, and filings. |
| `mt-newswires@openai-curated` | installed, enabled | Finance | MT Newswires brings real-time global financial news directly into Codex - providing original, unbiased an... |
| `neon-postgres@openai-curated` | installed, enabled | Developer Tools | Manage Neon Serverless Postgres projects and databases |
| `netlify@openai-curated` | installed, enabled | Developer Tools | Deploy projects and manage releases |
| `ngs-analysis@openai-curated` | installed, enabled | Education & Research | Guided NGS routing and local execution for sequencing analysis |
| `notion@openai-curated` | installed, enabled | Productivity | Notion workflows for specs, research, meetings, and knowledge capture |
| `openai-developers@openai-curated` | installed, enabled | Developer Tools | Develop AI apps, agents, and ChatGPT Apps with OpenAI best practices |
| `particl-market-research@openai-curated` | installed, enabled | Education & Research | Particl Market Research helps teams answer ecommerce research questions directly in Codex. |
| `pitchbook@openai-curated` | installed, enabled | Finance | PitchBook provides structured access to private capital market data across companies, investors, funds, de... |
| `plugin-eval@openai-curated` | installed, enabled | Developer Tools | Start from chat, then evaluate or benchmark locally |
| `ranked-ai@openai-curated` | installed, enabled | Productivity | Ranked AI provides industry leading AI SEO & PPC software, with a fully managed service integrated into it. |
| `razorpay@openai-curated` | installed, enabled | Finance | Connect your Razorpay account to access your payment data through conversation. |
| `remotion@openai-curated` | installed, enabled | Creativity | Create motion graphics from prompts |
| `render@openai-curated` | installed, enabled | Developer Tools | Deploy, debug, monitor, and migrate apps on Render. |
| `scite@openai-curated` | installed, enabled | Education & Research | Scite delivers answers grounded in peer-reviewed research you can verify. |
| `slack@openai-curated` | installed, enabled | Communication | Read and manage Slack |
| `supabase@openai-curated` | installed, enabled | Developer Tools | Supabase skills and MCP tools for Codex |
| `superpowers@openai-curated` | installed, enabled | Developer Tools | Planning, TDD, debugging, and delivery workflows for coding agents |
| `taxdown@openai-curated` | installed, enabled | Finance | TaxDown te ayuda a resolver dudas fiscales en Espana, tanto para particulares como autonomos: deducciones,... |
| `test-android-apps@openai-curated` | installed, enabled | Developer Tools | Reproduce issues, inspect UI, and capture performance evidence from Android emulators |
| `vercel@openai-curated` | installed, enabled | Developer Tools | Build and deploy web apps and agents |
| `cloudflare@openai-curated` | installed, disabled | Developer Tools | Cloudflare platform guidance with official MCP |
| `github@openai-curated` | installed, disabled | Developer Tools | Triage PRs, issues, CI, and publish flows |
| `midpage@openai-curated` | installed, disabled | Education & Research | Legal research with cited case law |
| `morningstar@openai-curated` | installed, disabled | Finance | Screen, summarize, and compare funds with the Morningstar app. |
| `readwise@openai-curated` | installed, disabled | Education & Research | The official app for Readwise and Reader. |
| `temporal@openai-curated` | installed, disabled | Developer Tools | Develop, run, and manage Temporal applications across the entire platform lifecycle |
| `third-bridge@openai-curated` | installed, disabled | Finance | Seamlessly incorporate critical context and trusted insights from industry experts as part of your financia... |
| `actively@openai-curated` | available, not installed | Business & Operations | Account agents for GTM intelligence |
| `aiera@openai-curated` | available, not installed | Finance | Institutional financial data and events |
| `airtable@openai-curated` | available, not installed | Productivity | Database and operations layer for your agents. |
| `alation@openai-curated` | available, not installed | Data & Analytics | Trusted enterprise data context and governance |
| `amplitude@openai-curated` | available, not installed | Data & Analytics | Product analytics and funnels |
| `asana@openai-curated` | available, not installed | Productivity | Read and manage Asana |
| `atlassian-rovo@openai-curated` | available, not installed | Productivity | Manage Jira and Confluence fast |
| `attio@openai-curated` | available, not installed | Business & Operations | Attio connects Codex directly to your CRM workspace, letting you manage customer relationships through na... |
| `base44@openai-curated` | available, not installed | Developer Tools | Build and deploy Base44 full-stack apps from Codex |
| `boltz-api-cli@openai-curated` | available, not installed | Education & Research | Predict structures, screen molecules and proteins, and design binders |
| `box@openai-curated` | available, not installed | Productivity | Search and reference your documents |
| `brand24@openai-curated` | available, not installed | Productivity | The Brand24 app in Codex lets marketing and PR teams instantly explore brand mentions, sentiment, and med... |
| `brex@openai-curated` | available, not installed | Finance | Connect Brex to Codex and review your company finances through natural conversation - at Codex speed. |
| `brighthire@openai-curated` | available, not installed | Productivity | Search and analyze BrightHire interviews, candidates, calls, and hiring data. |
| `calendly@openai-curated` | available, not installed | Productivity | Scheduling links, availability, and bookings |
| `carta-crm@openai-curated` | available, not installed | Business & Operations | Carta CRM helps investment teams stay on top of deal flow by keeping deals, companies, and relationships in... |
| `catalyst-by-zoho@openai-curated` | available, not installed | Developer Tools | Use Catalyst by Zoho capabilities in Codex. |
| `cb-insights@openai-curated` | available, not installed | Finance | Unleash Codex as your private markets research agent. |
| `channel99@openai-curated` | available, not installed | Productivity | Channel99 real time go to market intelligence connects Codex directly to Channel99's performance marketin... |
| `chronograph-gp@openai-curated` | available, not installed | Finance | Trusted portfolio data for private capital GP teams |
| `chronograph-lp@openai-curated` | available, not installed | Finance | Trusted portfolio data for private capital LP teams |
| `circleback@openai-curated` | available, not installed | Communication | Circleback helps teams get the most out of every conversation with AI-powered meeting notes, action items,... |
| `clay@openai-curated` | available, not installed | Business & Operations | Find and engage prospects |
| `clickup@openai-curated` | available, not installed | Productivity | Turn Codex into your ClickUp command center. |
| `close@openai-curated` | available, not installed | Business & Operations | Reference and update Close CRM |
| `cloudinary@openai-curated` | available, not installed | Developer Tools | Manage, search, and transform your Cloudinary media library - directly from Codex. |
| `cogedim@openai-curated` | available, not installed | Other | Cogedim is one of France's leading real estate developers. |
| `common-room@openai-curated` | available, not installed | Productivity | Embed complete buyer intelligence directly within Codex. |
| `conductor@openai-curated` | available, not installed | Productivity | The Conductor MCP server retrieves proprietary performance metrics regarding a brand's visibility, sentimen... |
| `convex@openai-curated` | available, not installed | Developer Tools | Add a backend to JS/TS apps. |
| `coupler-io@openai-curated` | available, not installed | Data & Analytics | Analyze multi-channel marketing, financial, sales, e-commerce, and other business data within Codex by co... |
| `coveo@openai-curated` | available, not installed | Productivity | Search your enterprise content |
| `cube@openai-curated` | available, not installed | Finance | With the Cube MCP Server, you can: - Query live Cube data from actuals, budgets, forecasts, variances, and... |
| `datadog@openai-curated` | available, not installed | Developer Tools | Investigate logs, metrics, traces, and incidents |
| `datasite@openai-curated` | available, not installed | Productivity | Manage secure M&A data rooms |
| `deepnote@openai-curated` | available, not installed | Data & Analytics | Explore data and automate analysis in Deepnote |
| `demandbase@openai-curated` | available, not installed | Business & Operations | Demandbase integration with Codex gives sales, marketing, and GTM teams seamless access to rich B2B data... |
| `digitalocean@openai-curated` | available, not installed | Developer Tools | Provision a droplet as a Codex workspace |
| `dnb-finance-analytics@openai-curated` | available, not installed | Finance | Commercial credit origination and risk workflows |
| `docket@openai-curated` | available, not installed | Productivity | Docket AI makes your sales knowledge your instant superpower. |
| `docusign@openai-curated` | available, not installed | Productivity | Automate contract creation and insights |
| `domotz-preview@openai-curated` | available, not installed | Productivity | Monitor and manage your network infrastructure through natural language. |
| `dovetail@openai-curated` | available, not installed | Productivity | Connect Dovetail inside Codex to turn customer feedback into decisions without leaving your conversation. |
| `egnyte@openai-curated` | available, not installed | Productivity | Work with documents and files stored in Egnyte directly from Codex. |
| `factset@openai-curated` | available, not installed | Finance | Connect financial data, analytics, and workflows |
| `fal@openai-curated` | available, not installed | Creativity | Generate and manage media with Fal models |
| `finn@openai-curated` | available, not installed | Travel | A FINN car subscription is a flexible way to stay mobile anytime - without long-term commitments like buyin... |
| `fireflies@openai-curated` | available, not installed | Communication | The Fireflies app brings your meetings and knowledge directly into Codex. |
| `fiscal-ai@openai-curated` | available, not installed | Finance | Audit-ready financial data and equity research |
| `fyxer@openai-curated` | available, not installed | Communication | Fyxer for Codex lets you write emails that sound like you, right from the chat. |
| `glean@openai-curated` | available, not installed | Productivity | Access enterprise knowledge with Glean |
| `granola@openai-curated` | available, not installed | Communication | Granola MCP connects your meeting history to Codex so your assistant can pull real context from past conv... |
| `happenstance@openai-curated` | available, not installed | Productivity | Happenstance searches your professional network using natural language to find the right people. |
| `hebbia@openai-curated` | available, not installed | Business & Operations | Institutional research and financial workflows |
| `help-scout@openai-curated` | available, not installed | Productivity | Connect to sync Help Scout mailboxes and conversations for use in Codex. |
| `hex@openai-curated` | available, not installed | Data & Analytics | Search Hex projects and ask Hex Threads questions |
| `heygen@openai-curated` | available, not installed | Creativity | Avatar videos and personalized video messages |
| `hg-insights@openai-curated` | available, not installed | Productivity | Prospect data and revenue intelligence |
| `highlevel@openai-curated` | available, not installed | Productivity | HighLevel gives agencies a unified CRM, automation, and client communication platform. |
| `hostinger@openai-curated` | available, not installed | Developer Tools | Hostinger Horizons lets you build real websites and apps just by describing what you want. |
| `hubspot@openai-curated` | available, not installed | Business & Operations | Work with your HubSpot data to analyze patterns, create and update records, and manage your CRM operations. |
| `intercom@openai-curated` | available, not installed | Business & Operations | Customer conversations, contacts, tickets, and support workflows from Intercom |
| `keybid-puls@openai-curated` | available, not installed | Finance | Unlock the profitability of short-term rental investments with our ROI Calculator app, tailored for platfor... |
| `linear@openai-curated` | available, not installed | Productivity | Find and reference issues and projects. |
| `lovable@openai-curated` | available, not installed | Developer Tools | Create full-stack web apps from prompts |
| `lseg@openai-curated` | available, not installed | Finance | Financial market data and analytics |
| `magicpath@openai-curated` | available, not installed | Developer Tools | Find, install, and author MagicPath UI components from Codex |
| `marcopolo@openai-curated` | available, not installed | Developer Tools | MarcoPolo spins up a secure container where Codex can work with your actual data. |
| `mem@openai-curated` | available, not installed | Productivity | Give Codex the full context of your second brain by connecting your Mem knowledge base. |
| `meticulate@openai-curated` | available, not installed | Productivity | Research companies and similar targets |
| `mixpanel@openai-curated` | available, not installed | Data & Analytics | Query and analyze Mixpanel |
| `mixpanel-headless@openai-curated` | available, not installed | Data & Analytics | Analyze Mixpanel data with Python |
| `monday-com@openai-curated` | available, not installed | Productivity | A powerful MCP connector enabling AI agents to seamlessly interact with monday.com. |
| `motherduck@openai-curated` | available, not installed | Data & Analytics | Connect AI assistants to your MotherDuck data warehouse. |
| `myregistry-com@openai-curated` | available, not installed | Other | MyRegistry.com helps make gift-giving easy for friends & family to get you the gifts you really want! |
| `network-solutions@openai-curated` | available, not installed | Productivity | The Network Solutions Domain Search Assistant makes finding an available domain fast, simple, and conversat... |
| `nvidia@openai-curated` | available, not installed | Developer Tools | Guided help for NVIDIA AI, GPU, robotics, simulation, and 3D workflows. |
| `omni-analytics@openai-curated` | available, not installed | Data & Analytics | Query Omni using the same semantic model, permissions, and logic defined by your data team directly from Codex. |
| `openai-ads-conversions@openai-curated` | available, not installed | Developer Tools | Set up OpenAI Ads Pixel and CAPI tracking |
| `otter-ai@openai-curated` | available, not installed | Communication | The Otter.ai MCP server connects Codex to your meeting intelligence, enabling search and retrieval of tra... |
| `outlook-calendar@openai-curated` | available, not installed | Productivity | Manage Outlook schedules and meeting changes |
| `outlook-email@openai-curated` | available, not installed | Communication | Triage Outlook inboxes and draft replies |
| `outreach@openai-curated` | available, not installed | Business & Operations | Revenue workflow automation with Outreach |
| `picsart@openai-curated` | available, not installed | Creativity | Generate videos, images, and audio |
| `pipedrive@openai-curated` | available, not installed | Business & Operations | Connect to sync Pipedrive deals and contacts for use in Codex. |
| `policynote@openai-curated` | available, not installed | Education & Research | Use the PolicyNote app to access structured policy and regulatory intelligence from around the world. |
| `posthog@openai-curated` | available, not installed | Data & Analytics | Analyze product data and manage experiments |
| `pylon@openai-curated` | available, not installed | Productivity | Access Pylon's customer support platform directly from Codex to search, manage, and resolve customer issues. |
| `quartr@openai-curated` | available, not installed | Finance | Public company IR data and earnings research |
| `quickbooks@openai-curated` | available, not installed | Finance | Analyze finances and manage QuickBooks records |
| `quicknode@openai-curated` | available, not installed | Developer Tools | Manage your Quicknode infrastructure directly in OpenAI. |
| `read-ai@openai-curated` | available, not installed | Communication | Read AI brings your meeting intelligence directly into your AI workflows. |
| `replayio@openai-curated` | available, not installed | Developer Tools | Record browser sessions and inspect Replay recordings or Replay QA results |
| `replit@openai-curated` | available, not installed | Developer Tools | Create and iterate Replit web apps |
| `responsive@openai-curated` | available, not installed | Productivity | The Responsive App makes it easy to work with your organization's data inside Codex. |
| `rox@openai-curated` | available, not installed | Productivity | Analyze sales data from Rox workspaces |
| `s-p@openai-curated` | available, not installed | Finance | Query S&P Global financial datasets |
| `semrush@openai-curated` | available, not installed | Productivity | The Semrush MCP provides structured, quantitative SEO and traffic data for domains, keywords, backlinks, an... |
| `sendgrid@openai-curated` | available, not installed | Developer Tools | Connector for interacting with the SendGrid email API. |
| `sentry@openai-curated` | available, not installed | Developer Tools | Inspect recent Sentry issues and events |
| `setu-bharat-connect-billpay@openai-curated` | available, not installed | Finance | This app helps you pay your utility bills through simple conversation. |
| `sharepoint@openai-curated` | available, not installed | Productivity | Summarize SharePoint sites and files |
| `shopify@openai-curated` | available, not installed | Developer Tools | Build Shopify apps, themes, storefronts, and APIs |
| `shutterstock@openai-curated` | available, not installed | Creativity | Search stock media libraries |
| `signnow@openai-curated` | available, not installed | Productivity | Get documents signed faster without switching between tools. |
| `similarweb@openai-curated` | available, not installed | Data & Analytics | Research web and app market intelligence |
| `skywatch@openai-curated` | available, not installed | Productivity | Search and explore satellite imagery from top providers including Vantor, Planet, Airbus, and more, all in... |
| `statsig@openai-curated` | available, not installed | Developer Tools | Bring your Statsig workspace into Codex. |
| `streak@openai-curated` | available, not installed | Business & Operations | Streak is a CRM built directly into Gmail, so you can track deals, contacts, and workflows from your inbox. |
| `stripe@openai-curated` | available, not installed | Finance | Payments and business tools |
| `superhuman@openai-curated` | available, not installed | Communication | The most productive email app ever, for Gmail & Outlook |
| `teams@openai-curated` | available, not installed | Communication | Summarize Teams and draft follow-ups |
| `teamwork-com@openai-curated` | available, not installed | Productivity | Connect to sync Teamwork projects and tasks for use in Codex. |
| `thoughtspot@openai-curated` | available, not installed | Data & Analytics | Trusted business data answers |
| `tinman-ai@openai-curated` | available, not installed | Finance | Tinman AI helps loan officers and underwriters quickly underwrite home financing scenarios and answer compl... |
| `twilio-developer-kit@openai-curated` | available, not installed | Developer Tools | Twilio Skills for building, debugging, and shipping on Twilio |
| `united-rentals@openai-curated` | available, not installed | Productivity | Get the right equipment for the job without guesswork. |
| `vantage@openai-curated` | available, not installed | Developer Tools | Vantage is a cloud observability and optimization platform that aggregates cloud infrastructure costs acros... |
| `waldo@openai-curated` | available, not installed | Productivity | Waldo is an AI-powered strategy platform for agencies and brands. |
| `weatherpromise@openai-curated` | available, not installed | Travel | Protect your trip with WeatherPromise and get back the full cost if it rains more than promised during your... |
| `windsor-ai@openai-curated` | available, not installed | Data & Analytics | Windsor.ai connects your marketing and business data sources to Codex so you can ask questions in natural... |
| `wix@openai-curated` | available, not installed | Developer Tools | Build Wix apps, headless websites, and manage your Wix business from Codex |
| `yepcode@openai-curated` | available, not installed | Developer Tools | YepCode lets you build custom AI tools using your own code with JSON Schema-defined inputs, executed in an... |
| `zoho@openai-curated` | available, not installed | Business & Operations | Manage Zoho CRM sales workflows |
| `zoom@openai-curated` | available, not installed | Communication | Use Zoom meeting context and build Zoom integrations. |
| `zoominfo@openai-curated` | available, not installed | Business & Operations | Prospecting and account research with ZoomInfo |
| `zotero@openai-curated` | available, not installed | Education & Research | Find papers and add citations from Zotero |
| `documents@openai-primary-runtime` | installed, enabled | Productivity | Create and edit document artifacts |
| `pdf@openai-primary-runtime` | installed, enabled | Productivity | Read, create, and verify PDF files |
| `presentations@openai-primary-runtime` | installed, enabled | Productivity | Create and edit presentations |
| `spreadsheets@openai-primary-runtime` | installed, enabled | Productivity | Create and edit spreadsheet files |
| `template-creator@openai-primary-runtime` | installed, enabled | Productivity | Create or update personal artifact templates |

## Installed And Enabled Plugins

### `ai-governance-legal@claude-for-legal-india`

- Display name: AI Governance Legal
- Marketplace: `claude-for-legal-india`
- Status: installed, enabled
- Version: `1.0.2`
- Category: Productivity
- What it does: Triages proposed AI use cases against your registry, runs impact assessments across the regimes in scope, reviews vendor AI terms for training-on-data and liabi
- More detail: Codex-local India adaptation of the Claude for Legal AI Governance Legal plugin. It preserves the upstream skills, agents, references, guardrails, and setup interview, while using Codex-local practice profile paths under ~/.codex and Indian jurisdiction defaults unless the matter profile says otherwise. Active Codex skills are compact router/wrapper surfaces; preserved upstream Claude skill text remains under...
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write, Research
  - Skills: 11 (ai-governance-legal-router, ai-inventory, aia-generation, cold-start-interview, customize, matter-workspace, policy-monitor, policy-starter, +3 more)
  - Keywords: legal, law, india, codex, attorney-review, ai-governance-legal
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/agent-repos/claude-for-legal-india/ai-governance-legal`
- Metadata files used: plugin manifest: `/Users/raghav/agent-repos/claude-for-legal-india/ai-governance-legal/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/agent-repos/claude-for-legal-india/ai-governance-legal/.mcp.json`; README/CODEX: `/Users/raghav/agent-repos/claude-for-legal-india/ai-governance-legal/README.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-for-legal; repository: https://github.com/anthropics/claude-for-legal; author/developer: Anthropic base; India adaptation by Raghav Badhwar

### `cocounsel-legal@claude-for-legal-india`

- Display name: Cocounsel Legal
- Marketplace: `claude-for-legal-india`
- Status: installed, enabled
- Version: `0.1.0`
- Category: Productivity
- What it does: CoCounsel Legal delivers comprehensive Westlaw Deep Research reports with inline, linked citations to Westlaw and Practical Law sources. India-localized default
- More detail: Codex-local India adaptation of the Claude for Legal Cocounsel Legal plugin. It preserves the upstream skills, agents, references, guardrails, and setup interview, while using Codex-local practice profile paths under ~/.codex and Indian jurisdiction defaults unless the matter profile says otherwise.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write, Research
  - Skills: 1 (deep-research)
  - Keywords: legal, law, india, codex, attorney-review, cocounsel-legal
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/agent-repos/claude-for-legal-india/external_plugins/cocounsel-legal`
- Metadata files used: plugin manifest: `/Users/raghav/agent-repos/claude-for-legal-india/external_plugins/cocounsel-legal/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/agent-repos/claude-for-legal-india/external_plugins/cocounsel-legal/.mcp.json`; README/CODEX: `/Users/raghav/agent-repos/claude-for-legal-india/external_plugins/cocounsel-legal/README.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-for-legal; repository: https://github.com/anthropics/claude-for-legal; author/developer: Thomson Reuters

### `commercial-legal@claude-for-legal-india`

- Display name: Commercial Legal
- Marketplace: `claude-for-legal-india`
- Status: installed, enabled
- Version: `1.0.2`
- Category: Productivity
- What it does: Reviews vendor agreements, NDAs, and SaaS subscriptions against your sales-side or purchasing-side playbook, tracks renewals and cancel-by deadlines before they
- More detail: Codex-local India adaptation of the Claude for Legal Commercial Legal plugin. It preserves the upstream skills, agents, references, guardrails, and setup interview, while using Codex-local practice profile paths under ~/.codex and Indian jurisdiction defaults unless the matter profile says otherwise. Active Codex skills are compact router/wrapper surfaces; preserved upstream Claude skill text remains under...
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write, Research
  - Skills: 13 (amendment-history, cold-start-interview, commercial-legal-router, customize, escalation-flagger, matter-workspace, nda-review, renewal-tracker, +5 more)
  - Keywords: legal, law, india, codex, attorney-review, commercial-legal
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/agent-repos/claude-for-legal-india/commercial-legal`
- Metadata files used: plugin manifest: `/Users/raghav/agent-repos/claude-for-legal-india/commercial-legal/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/agent-repos/claude-for-legal-india/commercial-legal/.mcp.json`; README/CODEX: `/Users/raghav/agent-repos/claude-for-legal-india/commercial-legal/README.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-for-legal; repository: https://github.com/anthropics/claude-for-legal; author/developer: Anthropic base; India adaptation by Raghav Badhwar

### `corporate-legal@claude-for-legal-india`

- Display name: Corporate Legal
- Marketplace: `claude-for-legal-india`
- Status: installed, enabled
- Version: `1.0.2`
- Category: Productivity
- What it does: Runs M&A diligence at scale with cited tabular review, builds disclosure schedules and closing checklists, drafts board consents and minutes in house format, an
- More detail: Codex-local India adaptation of the Claude for Legal Corporate Legal plugin. It preserves the upstream skills, agents, references, guardrails, and setup interview, while using Codex-local practice profile paths under ~/.codex and Indian jurisdiction defaults unless the matter profile says otherwise.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write, Research
  - Skills: 13 (ai-tool-handoff, board-minutes, closing-checklist, cold-start-interview, customize, deal-team-summary, diligence-issue-extraction, entity-compliance, +5 more)
  - Agents: 1 (dataroom-watcher)
  - Keywords: legal, law, india, codex, attorney-review, corporate-legal
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/agent-repos/claude-for-legal-india/corporate-legal`
- Metadata files used: plugin manifest: `/Users/raghav/agent-repos/claude-for-legal-india/corporate-legal/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/agent-repos/claude-for-legal-india/corporate-legal/.mcp.json`; README/CODEX: `/Users/raghav/agent-repos/claude-for-legal-india/corporate-legal/README.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-for-legal; repository: https://github.com/anthropics/claude-for-legal; author/developer: Anthropic base; India adaptation by Raghav Badhwar

### `employment-legal@claude-for-legal-india`

- Display name: Employment Legal
- Marketplace: `claude-for-legal-india`
- Status: installed, enabled
- Version: `1.0.2`
- Category: Productivity
- What it does: Reviews hires and terminations for jurisdiction-specific risk flags, classifies workers against the controlling state test, tracks leave deadlines before they'r
- More detail: Codex-local India adaptation of the Claude for Legal Employment Legal plugin. It preserves the upstream skills, agents, references, guardrails, and setup interview, while using Codex-local practice profile paths under ~/.codex and Indian jurisdiction defaults unless the matter profile says otherwise.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write, Research
  - Skills: 20 (cold-start-interview, customize, expansion-kickoff, expansion-update, handbook-updates, hiring-review, internal-investigation, international-expansion, +12 more)
  - Agents: 1 (leave-tracker)
  - Keywords: legal, law, india, codex, attorney-review, employment-legal
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/agent-repos/claude-for-legal-india/employment-legal`
- Metadata files used: plugin manifest: `/Users/raghav/agent-repos/claude-for-legal-india/employment-legal/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/agent-repos/claude-for-legal-india/employment-legal/.mcp.json`; README/CODEX: `/Users/raghav/agent-repos/claude-for-legal-india/employment-legal/README.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-for-legal; repository: https://github.com/anthropics/claude-for-legal; author/developer: Anthropic base; India adaptation by Raghav Badhwar

### `ip-legal@claude-for-legal-india`

- Display name: IP Legal
- Marketplace: `claude-for-legal-india`
- Status: installed, enabled
- Version: `1.0.2`
- Category: Productivity
- What it does: Runs first-pass trademark clearance and freedom-to-operate triage, screens invention disclosures for initial patentability, drafts and triages cease-and-desist
- More detail: Codex-local India adaptation of the Claude for Legal IP Legal plugin. It preserves the upstream skills, agents, references, guardrails, and setup interview, while using Codex-local practice profile paths under ~/.codex and Indian jurisdiction defaults unless the matter profile says otherwise. Active Codex skills are compact router/wrapper surfaces; preserved upstream Claude skill text remains under...
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write, Research
  - Skills: 13 (cease-desist, clearance, cold-start-interview, customize, fto-triage, infringement-triage, invention-intake, ip-clause-review, +5 more)
  - Keywords: legal, law, india, codex, attorney-review, ip-legal
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/agent-repos/claude-for-legal-india/ip-legal`
- Metadata files used: plugin manifest: `/Users/raghav/agent-repos/claude-for-legal-india/ip-legal/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/agent-repos/claude-for-legal-india/ip-legal/.mcp.json`; README/CODEX: `/Users/raghav/agent-repos/claude-for-legal-india/ip-legal/README.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-for-legal; repository: https://github.com/anthropics/claude-for-legal; author/developer: Anthropic base; India adaptation by Raghav Badhwar

### `law-student@claude-for-legal-india`

- Display name: Law Student
- Marketplace: `claude-for-legal-india`
- Status: installed, enabled
- Version: `1.0.2`
- Category: Productivity
- What it does: Drills Socratically, briefs cases, builds outlines, runs bar prep sessions tuned to your jurisdiction, grades IRAC practice, and plans the study schedule - with
- More detail: Codex-local India adaptation of the Claude for Legal Law Student plugin. It preserves the upstream skills, agents, references, guardrails, and setup interview, while using Codex-local practice profile paths under ~/.codex and Indian jurisdiction defaults unless the matter profile says otherwise.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write, Research
  - Skills: 13 (bar-prep-questions, case-brief, cold-call-prep, cold-start-interview, customize, exam-forecast, flashcards, irac-practice, +5 more)
  - Keywords: legal, law, india, codex, attorney-review, law-student
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/agent-repos/claude-for-legal-india/law-student`
- Metadata files used: plugin manifest: `/Users/raghav/agent-repos/claude-for-legal-india/law-student/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/agent-repos/claude-for-legal-india/law-student/.mcp.json`; README/CODEX: `/Users/raghav/agent-repos/claude-for-legal-india/law-student/README.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-for-legal; repository: https://github.com/anthropics/claude-for-legal; author/developer: Anthropic base; India adaptation by Raghav Badhwar

### `legal-builder-hub@claude-for-legal-india`

- Display name: Legal Builder Hub
- Marketplace: `claude-for-legal-india`
- Status: installed, enabled
- Version: `1.0.2`
- Category: Productivity
- What it does: Finds, evaluates, and installs community legal skills - with a security review gate before anything lands in your environment. India-localized default posture;
- More detail: Codex-local India adaptation of the Claude for Legal Legal Builder Hub plugin. It preserves the upstream skills, agents, references, guardrails, and setup interview, while using Codex-local practice profile paths under ~/.codex and Indian jurisdiction defaults unless the matter profile says otherwise.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write, Research
  - Skills: 10 (auto-updater, cold-start-interview, customize, disable, registry-browser, related-skills-surfacer, skill-installer, skill-manager, +2 more)
  - Agents: 1 (registry-sync)
  - References: 1 (allowlist-default)
  - Keywords: legal, law, india, codex, attorney-review, legal-builder-hub
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/agent-repos/claude-for-legal-india/legal-builder-hub`
- Metadata files used: plugin manifest: `/Users/raghav/agent-repos/claude-for-legal-india/legal-builder-hub/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/agent-repos/claude-for-legal-india/legal-builder-hub/.mcp.json`; README/CODEX: `/Users/raghav/agent-repos/claude-for-legal-india/legal-builder-hub/README.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-for-legal; repository: https://github.com/anthropics/claude-for-legal; author/developer: Anthropic base; India adaptation by Raghav Badhwar

### `legal-clinic@claude-for-legal-india`

- Display name: Legal Clinic
- Marketplace: `claude-for-legal-india`
- Status: installed, enabled
- Version: `1.0.2`
- Category: Productivity
- What it does: Sets up the clinic, onboards students, runs structured intake, tracks deadlines with malpractice-aware caution, and hands off cases at semester end - built with
- More detail: Codex-local India adaptation of the Claude for Legal Legal Clinic plugin. It preserves the upstream skills, agents, references, guardrails, and setup interview, while using Codex-local practice profile paths under ~/.codex and Indian jurisdiction defaults unless the matter profile says otherwise.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write, Research
  - Skills: 16 (build-guide, client-comms-log, client-intake, client-letter, cold-start-interview, customize, deadlines, draft, +8 more)
  - Keywords: legal, law, india, codex, attorney-review, legal-clinic
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/agent-repos/claude-for-legal-india/legal-clinic`
- Metadata files used: plugin manifest: `/Users/raghav/agent-repos/claude-for-legal-india/legal-clinic/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/agent-repos/claude-for-legal-india/legal-clinic/.mcp.json`; README/CODEX: `/Users/raghav/agent-repos/claude-for-legal-india/legal-clinic/README.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-for-legal; repository: https://github.com/anthropics/claude-for-legal; author/developer: Anthropic base; India adaptation by Raghav Badhwar

### `litigation-legal@claude-for-legal-india`

- Display name: Litigation Legal
- Marketplace: `claude-for-legal-india`
- Status: installed, enabled
- Version: `1.0.2`
- Category: Productivity
- What it does: Manages the litigation portfolio - matters, deadlines, holds, demands, outside counsel - and does the work: claim charts (patent and civil), chronologies, depo
- More detail: Codex-local India adaptation of the Claude for Legal Litigation Legal plugin. It preserves the upstream skills, agents, references, guardrails, and setup interview, while using Codex-local practice profile paths under ~/.codex and Indian jurisdiction defaults unless the matter profile says otherwise.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write, Research
  - Skills: 19 (brief-section-drafter, chronology, claim-chart, cold-start-interview, customize, demand-draft, demand-intake, demand-received, +11 more)
  - Agents: 1 (docket-watcher)
  - Keywords: legal, law, india, codex, attorney-review, litigation-legal
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/agent-repos/claude-for-legal-india/litigation-legal`
- Metadata files used: plugin manifest: `/Users/raghav/agent-repos/claude-for-legal-india/litigation-legal/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/agent-repos/claude-for-legal-india/litigation-legal/.mcp.json`; README/CODEX: `/Users/raghav/agent-repos/claude-for-legal-india/litigation-legal/README.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-for-legal; repository: https://github.com/anthropics/claude-for-legal; author/developer: Anthropic base; India adaptation by Raghav Badhwar

### `privacy-legal@claude-for-legal-india`

- Display name: Privacy Legal
- Marketplace: `claude-for-legal-india`
- Status: installed, enabled
- Version: `1.0.2`
- Category: Productivity
- What it does: Triages processing activities, generates PIAs, reviews DPAs as controller or processor, drafts DSAR responses within statutory timelines, and monitors policy dr
- More detail: Codex-local India adaptation of the Claude for Legal Privacy Legal plugin. It preserves the upstream skills, agents, references, guardrails, and setup interview, while using Codex-local practice profile paths under ~/.codex and Indian jurisdiction defaults unless the matter profile says otherwise. Active Codex skills are compact router/wrapper surfaces; preserved upstream Claude skill text remains under...
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write, Research
  - Skills: 10 (cold-start-interview, customize, dpa-review, dsar-response, matter-workspace, pia-generation, policy-monitor, privacy-legal-router, +2 more)
  - Keywords: legal, law, india, codex, attorney-review, privacy-legal
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/agent-repos/claude-for-legal-india/privacy-legal`
- Metadata files used: plugin manifest: `/Users/raghav/agent-repos/claude-for-legal-india/privacy-legal/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/agent-repos/claude-for-legal-india/privacy-legal/.mcp.json`; README/CODEX: `/Users/raghav/agent-repos/claude-for-legal-india/privacy-legal/README.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-for-legal; repository: https://github.com/anthropics/claude-for-legal; author/developer: Anthropic base; India adaptation by Raghav Badhwar

### `product-legal@claude-for-legal-india`

- Display name: Product Legal
- Marketplace: `claude-for-legal-india`
- Status: installed, enabled
- Version: `1.0.2`
- Category: Productivity
- What it does: Reviews product launches against your risk calibration, answers 'is this a problem?' questions in minutes, checks marketing copy for claims that need substantia
- More detail: Codex-local India adaptation of the Claude for Legal Product Legal plugin. It preserves the upstream skills, agents, references, guardrails, and setup interview, while using Codex-local practice profile paths under ~/.codex and Indian jurisdiction defaults unless the matter profile says otherwise. Active Codex skills are compact router/wrapper surfaces; preserved upstream Claude skill text remains under...
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write, Research
  - Skills: 8 (cold-start-interview, customize, feature-risk-assessment, is-this-a-problem, launch-review, marketing-claims-review, matter-workspace, product-legal-router)
  - Keywords: legal, law, india, codex, attorney-review, product-legal
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/agent-repos/claude-for-legal-india/product-legal`
- Metadata files used: plugin manifest: `/Users/raghav/agent-repos/claude-for-legal-india/product-legal/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/agent-repos/claude-for-legal-india/product-legal/.mcp.json`; README/CODEX: `/Users/raghav/agent-repos/claude-for-legal-india/product-legal/README.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-for-legal; repository: https://github.com/anthropics/claude-for-legal; author/developer: Anthropic base; India adaptation by Raghav Badhwar

### `regulatory-legal@claude-for-legal-india`

- Display name: Regulatory Legal
- Marketplace: `claude-for-legal-india`
- Status: installed, enabled
- Version: `1.0.2`
- Category: Productivity
- What it does: Watches regulatory feeds, diffs new rules against your policy library, tracks comment deadlines and open gaps, and writes the digest your team reads Monday morn
- More detail: Codex-local India adaptation of the Claude for Legal Regulatory Legal plugin. It preserves the upstream skills, agents, references, guardrails, and setup interview, while using Codex-local practice profile paths under ~/.codex and Indian jurisdiction defaults unless the matter profile says otherwise.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write, Research
  - Skills: 9 (cold-start-interview, comments, customize, gap-surfacer, gaps, matter-workspace, policy-diff, policy-redraft, +1 more)
  - Agents: 1 (reg-change-monitor)
  - Keywords: legal, law, india, codex, attorney-review, regulatory-legal
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/agent-repos/claude-for-legal-india/regulatory-legal`
- Metadata files used: plugin manifest: `/Users/raghav/agent-repos/claude-for-legal-india/regulatory-legal/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/agent-repos/claude-for-legal-india/regulatory-legal/.mcp.json`; README/CODEX: `/Users/raghav/agent-repos/claude-for-legal-india/regulatory-legal/README.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-for-legal; repository: https://github.com/anthropics/claude-for-legal; author/developer: Anthropic base; India adaptation by Raghav Badhwar

### `ai-elements@local-codex-plugins`

- Display name: AI Elements
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `0.1.0`
- Category: Developer Tools
- What it does: Install and compose Vercel AI Elements UI.
- More detail: Adds a Codex skill and helper script for auditing projects, selecting AI Elements components, and using npx ai-elements@latest safely in React and Next.js apps.
- Features and capabilities:
  - Interface capabilities: Read, Write, CLI
  - Skills: 1 (ai-elements)
  - Scripts: 1 (ai-elements)
  - Keywords: ai-elements, vercel-ai-sdk, shadcn, react, nextjs, chat-ui
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/ai-elements`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/ai-elements/.codex-plugin/plugin.json`
- External links/attribution: homepage: https://elements.ai-sdk.dev/; author/developer: Local developer

### `ai-governance-legal@local-codex-plugins`

- Display name: AI Governance Legal
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.0.2`
- Category: Productivity
- What it does: Triages proposed AI use cases against your registry, runs impact assessments across the regimes in scope, reviews vendor AI terms for training-on-data and liabi
- More detail: Codex-local India adaptation of the Claude for Legal AI Governance Legal plugin. It preserves the upstream skills, agents, references, guardrails, and setup interview, while using Codex-local practice profile paths under ~/.codex and Indian jurisdiction defaults unless the matter profile says otherwise. Active Codex skills are compact router/wrapper surfaces; preserved upstream Claude skill text remains under...
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write, Research
  - MCP servers: Slack (http), Google Drive (http)
  - Skills: 11 (ai-governance-legal-router, ai-inventory, aia-generation, cold-start-interview, customize, matter-workspace, policy-monitor, policy-starter, +3 more)
  - Keywords: legal, law, india, codex, attorney-review, ai-governance-legal
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/claude-for-legal/ai-governance-legal`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/claude-for-legal/ai-governance-legal/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/claude-for-legal/ai-governance-legal/.mcp.json`; README/CODEX: `/Users/raghav/plugins/claude-for-legal/ai-governance-legal/README.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-for-legal; repository: https://github.com/anthropics/claude-for-legal; author/developer: Anthropic base; India adaptation by Raghav Badhwar

### `brand-design-studio@local-codex-plugins`

- Display name: Brand Design Studio
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.0.0`
- Category: Design
- What it does: Packaging and brand identity design studio.
- More detail: A Codex-local packaging and brand identity design studio skill. It guides product packaging work through discovery, archetypes, color systems, typography, visual language, mockup direction, and a final brand design bible.
- Features and capabilities:
  - Interface capabilities: Interactive, Design, Write
  - Skills: 1 (packaging-design)
  - Keywords: brand-design, packaging, identity, visual-design, codex
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/brand-design-studio`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/brand-design-studio/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/plugins/brand-design-studio/README.md`
- External links/attribution: homepage: https://claude.com/plugins; author/developer: Brand Design Studio - Antigravity x Raghav

### `claude-code-setup@local-codex-plugins`

- Display name: Claude Code Setup
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.0.0+codex.20260531105234`
- Category: Developer Tools
- What it does: Audit and upgrade repos with Codex/Claude automation, safe hooks, templates, runtime checks, and evidence scoring.
- More detail: Codex-native upgrade of the Claude Code Setup plugin. It preserves the original Claude automation recommender source while adding focused active skills, runnable audit/install scripts, a local MCP server, safe Claude hook templates, Codex plugin runtime verification, candidate scoring, parity mapping, risk controls, and implementation-ready recommendations for MCP servers, skills, plugins, hooks, agents, and...
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - MCP servers: claude-code-setup (node)
  - Skills: 5 (claude-automation-recommender, claude-hook-installer, codex-plugin-runtime-verifier, repo-automation-auditor, workflow-gap-mapper)
  - Scripts: 4 (automation-audit, install-automation-assets, mcp_server, test_mcp_server)
  - Keywords: agents, automation-audit, automation-installer, claude-code-plugin, codex, codex-setup, hooks, mcp, skills, local-adaptation
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/claude-code-setup`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/claude-code-setup/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/claude-code-setup/.mcp.json`; README/CODEX: `/Users/raghav/plugins/claude-code-setup/README.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-plugins-official; repository: https://github.com/anthropics/claude-plugins-official; author/developer: Anthropic

### `claude-for-legal@local-codex-plugins`

- Display name: Claude for Legal India (Codex Port)
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.0.2-codex.1`
- Category: Productivity
- What it does: Routes legal workflows to the installed India-adapted Codex practice plugins.
- More detail: A Codex-local India adaptation of Anthropic's Claude for Legal suite. The root skill helps choose the right practice plugin and enforces attorney-review, citation-verification, Codex-local profile storage, and Indian-law default guardrails.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write, Research
  - Skills: 1 (claude-for-legal)
  - References: 2 (company-profile-template, dashboard-template)
  - Scripts: 6 (lint-tool-scope, orchestrate, port_to_codex, validate, deploy-managed-agent, test-cookbooks)
  - Keywords: legal, law, plugins, codex, india, attorney-review
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/claude-for-legal`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/claude-for-legal/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/plugins/claude-for-legal/README.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-for-legal; repository: https://github.com/anthropics/claude-for-legal; author/developer: Anthropic base; India adaptation by Raghav Badhwar

### `claude-md-management@local-codex-plugins`

- Display name: Claude Md Management
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.0.0`
- Category: Developer Tools
- What it does: Tools to maintain and improve CLAUDE.md files - audit quality, capture session learnings, and keep project memory current.
- More detail: Codex-local adaptation of the Claude Code plugin `claude-md-management` copied from `/Users/raghav/.claude/plugins/cache/claude-plugins-official/claude-md-management/1.0.0`. Original files are preserved; Claude commands, agents, hooks, and MCP config are exposed through Codex plugin surfaces where possible.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - Skills: 2 (claude-md-improver, command-revise-claude-md)
  - Keywords: claude-code-plugin, codex, local-adaptation
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/claude-md-management`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/claude-md-management/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/plugins/claude-md-management/README.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-plugins-official; repository: https://github.com/anthropics/claude-plugins-official; author/developer: Anthropic

### `cli-printing-press-factory@local-codex-plugins`

- Display name: CLI Printing Press Factory
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `0.1.0+codex.20260611002017`
- Category: Developer Tools
- What it does: Create production-grade CLIs from APIs, docs, HAR captures, and plans.
- More detail: A local Codex plugin that turns an API, app, docs page, OpenAPI spec, HAR capture, or plan into a disciplined cli-printing-press workflow. It gives agents source-selection rules, generation commands, quality gates, verification scripts, and MCP tools for status, planning, pipeline creation, direct generation, and generated-CLI checks.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write, MCP
  - MCP servers: cli-printing-press-factory (python3)
  - Skills: 4 (cli-printing-press-factory, printing-press-agent-tooling, printing-press-create-cli, printing-press-quality-review)
  - Scripts: 3 (mcp_server, printing_press_factory, test_mcp_server)
  - Keywords: cli, printing-press, openapi, mcp, api-tools, codegen
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/cli-printing-press-factory`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/cli-printing-press-factory/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/cli-printing-press-factory/.mcp.json`
- External links/attribution: homepage: https://openai.com; repository: https://openai.com; author/developer: OpenAI Codex

### `cocounsel-legal@local-codex-plugins`

- Display name: Cocounsel Legal
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `0.1.0`
- Category: Productivity
- What it does: CoCounsel Legal delivers comprehensive Westlaw Deep Research reports with inline, linked citations to Westlaw and Practical Law sources. India-localized default
- More detail: Codex-local India adaptation of the Claude for Legal Cocounsel Legal plugin. It preserves the upstream skills, agents, references, guardrails, and setup interview, while using Codex-local practice profile paths under ~/.codex and Indian jurisdiction defaults unless the matter profile says otherwise.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write, Research
  - MCP servers: cocounsel-legal (http)
  - Skills: 2 (cocounsel-legal, deep-research)
  - Keywords: legal, law, india, codex, attorney-review, cocounsel-legal
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/claude-for-legal/external_plugins/cocounsel-legal`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/claude-for-legal/external_plugins/cocounsel-legal/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/claude-for-legal/external_plugins/cocounsel-legal/.mcp.json`; README/CODEX: `/Users/raghav/plugins/claude-for-legal/external_plugins/cocounsel-legal/README.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-for-legal; repository: https://github.com/anthropics/claude-for-legal; author/developer: Thomson Reuters

### `code-review@local-codex-plugins`

- Display name: Code Review
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `0.0.0-claude-unknown`
- Category: Developer Tools
- What it does: Automated code review for pull requests using multiple specialized agents with confidence-based scoring
- More detail: Codex-local adaptation of the Claude Code plugin `code-review` copied from `/Users/raghav/.claude/plugins/cache/claude-plugins-official/code-review/unknown`. Original files are preserved; Claude commands, agents, hooks, and MCP config are exposed through Codex plugin surfaces where possible.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - Skills: 1 (command-code-review)
  - Keywords: claude-code-plugin, codex, local-adaptation
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/code-review`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/code-review/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/plugins/code-review/README.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-plugins-official; repository: https://github.com/anthropics/claude-plugins-official; author/developer: Anthropic

### `code-simplifier@local-codex-plugins`

- Display name: Code Simplifier
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.0.0`
- Category: Developer Tools
- What it does: Agent that simplifies and refines code for clarity, consistency, and maintainability while preserving functionality
- More detail: Codex-local adaptation of the Claude Code plugin `code-simplifier` copied from `/Users/raghav/.claude/plugins/cache/claude-plugins-official/code-simplifier/1.0.0`. Original files are preserved; Claude commands, agents, hooks, and MCP config are exposed through Codex plugin surfaces where possible.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - Skills: 1 (agent-code-simplifier)
  - Keywords: claude-code-plugin, codex, local-adaptation
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/code-simplifier`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/code-simplifier/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/plugins/code-simplifier/README.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-plugins-official; repository: https://github.com/anthropics/claude-plugins-official; author/developer: Anthropic

### `commercial-legal@local-codex-plugins`

- Display name: Commercial Legal
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.0.2`
- Category: Productivity
- What it does: Reviews vendor agreements, NDAs, and SaaS subscriptions against your sales-side or purchasing-side playbook, tracks renewals and cancel-by deadlines before they
- More detail: Codex-local India adaptation of the Claude for Legal Commercial Legal plugin. It preserves the upstream skills, agents, references, guardrails, and setup interview, while using Codex-local practice profile paths under ~/.codex and Indian jurisdiction defaults unless the matter profile says otherwise. Active Codex skills are compact router/wrapper surfaces; preserved upstream Claude skill text remains under...
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write, Research
  - MCP servers: Ironclad (http), DocuSign (http), iManage (http), TopCounsel (http), Definely (http), Slack (http), Google Drive (http)
  - Skills: 13 (amendment-history, cold-start-interview, commercial-legal-router, customize, escalation-flagger, matter-workspace, nda-review, renewal-tracker, +5 more)
  - Keywords: legal, law, india, codex, attorney-review, commercial-legal
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/claude-for-legal/commercial-legal`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/claude-for-legal/commercial-legal/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/claude-for-legal/commercial-legal/.mcp.json`; README/CODEX: `/Users/raghav/plugins/claude-for-legal/commercial-legal/README.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-for-legal; repository: https://github.com/anthropics/claude-for-legal; author/developer: Anthropic base; India adaptation by Raghav Badhwar

### `commit-commands@local-codex-plugins`

- Display name: Commit Commands
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `0.0.0-claude-unknown`
- Category: Developer Tools
- What it does: Streamline your git workflow with simple commands for committing, pushing, and creating pull requests
- More detail: Codex-local adaptation of the Claude Code plugin `commit-commands` copied from `/Users/raghav/.claude/plugins/cache/claude-plugins-official/commit-commands/unknown`. Original files are preserved; Claude commands, agents, hooks, and MCP config are exposed through Codex plugin surfaces where possible.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - Skills: 3 (command-clean-gone, command-commit, command-commit-push-pr)
  - Keywords: claude-code-plugin, codex, local-adaptation
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/commit-commands`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/commit-commands/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/plugins/commit-commands/README.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-plugins-official; repository: https://github.com/anthropics/claude-plugins-official; author/developer: Anthropic

### `context7@local-codex-plugins`

- Display name: Context7
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `0.0.0-claude-unknown`
- Category: Developer Tools
- What it does: Upstash Context7 MCP server for up-to-date documentation lookup. Pull version-specific documentation and code examples directly from source repositories into your LLM context.
- More detail: Codex-local adaptation of the Claude Code plugin `context7` copied from `/Users/raghav/.claude/plugins/cache/claude-plugins-official/context7/unknown`. Original files are preserved; Claude commands, agents, hooks, and MCP config are exposed through Codex plugin surfaces where possible.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write, MCP
  - MCP servers: context7 (npx)
  - Skills: 1 (context7-mcp)
  - Keywords: claude-code-plugin, codex, local-adaptation
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/context7`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/context7/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/context7/.mcp.json`; README/CODEX: `/Users/raghav/plugins/context7/README.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-plugins-official; repository: https://github.com/anthropics/claude-plugins-official; author/developer: Upstash

### `copilot-sdk@local-codex-plugins`

- Display name: Copilot Sdk
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.0.0`
- Category: Developer Tools
- What it does: Build applications with the GitHub Copilot SDK across multiple programming languages. Includes comprehensive instructions for C#, Go, Node.js/TypeScript, and Python to help you create AI-powered applications.
- More detail: Local Codex import of the Awesome Copilot plugin "copilot-sdk". Build applications with the GitHub Copilot SDK across multiple programming languages. Includes comprehensive instructions for C#, Go, Node.js/TypeScript, and Python to help you create AI-powered applications. Includes 1 plugin-local skill bundle(s).
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - Skills: 1 (copilot-sdk)
  - Keywords: copilot-sdk, sdk, csharp, go, nodejs, typescript, python, ai, github-copilot
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/copilot-sdk`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/copilot-sdk/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/plugins/copilot-sdk/README.md`
- External links/attribution: homepage: https://github.com/github/awesome-copilot; repository: https://github.com/github/awesome-copilot; author/developer: Awesome Copilot Community

### `corporate-legal@local-codex-plugins`

- Display name: Corporate Legal
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.0.2`
- Category: Productivity
- What it does: Runs M&A diligence at scale with cited tabular review, builds disclosure schedules and closing checklists, drafts board consents and minutes in house format, an
- More detail: Codex-local India adaptation of the Claude for Legal Corporate Legal plugin. It preserves the upstream skills, agents, references, guardrails, and setup interview, while using Codex-local practice profile paths under ~/.codex and Indian jurisdiction defaults unless the matter profile says otherwise.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write, Research
  - MCP servers: Slack (http), Google Drive (http), Box (http), iManage (http), TopCounsel (http), Definely (http), Solve Intelligence (http)
  - Skills: 13 (ai-tool-handoff, board-minutes, closing-checklist, cold-start-interview, customize, deal-team-summary, diligence-issue-extraction, entity-compliance, +5 more)
  - Agents: 1 (dataroom-watcher)
  - Keywords: legal, law, india, codex, attorney-review, corporate-legal
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/claude-for-legal/corporate-legal`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/claude-for-legal/corporate-legal/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/claude-for-legal/corporate-legal/.mcp.json`; README/CODEX: `/Users/raghav/plugins/claude-for-legal/corporate-legal/README.md`; Codex usage: `/Users/raghav/plugins/claude-for-legal/corporate-legal/CODEX.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-for-legal; repository: https://github.com/anthropics/claude-for-legal; author/developer: Anthropic base; India adaptation by Raghav Badhwar

### `data@local-codex-plugins`

- Display name: Data Analyst India
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.2.0`
- Category: Data & Analytics
- What it does: India-aware data analysis workflows for SQL, exploration, validation, dashboards, visualizations, and stakeholder insigh
- More detail: India-aware data analysis workflows for SQL, exploration, validation, dashboards, visualizations, and stakeholder insights. Uses compact router-first skills, India context checks, connector/export fallbacks, and explicit approval gates. Includes compact source-schemas and domain-specific India playbooks.
- Features and capabilities:
  - Interface capabilities: Analyze, Query, Visualize
  - MCP servers: bigquery (http), hex (http), amplitude (http), amplitude-eu (http), atlassian (http), definite (http)
  - Skills: 11 (analyze, build-dashboard, create-viz, data, data-context-extractor, data-visualization, explore-data, sql-queries, +3 more)
  - References: 4 (india-context, quality-gates, source-schemas, tooling-and-connectors)
  - Keywords: data, codex, plugin, india, approval-gated
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/data`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/data/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/data/.mcp.json`; README/CODEX: `/Users/raghav/plugins/data/README.md`; Codex usage: `/Users/raghav/plugins/data/CODEX_USAGE.md`
- External links/attribution: homepage: https://claude.com/plugins; author/developer: Anthropic

### `database-data-management@local-codex-plugins`

- Display name: Database Data Management
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.0.0`
- Category: Developer Tools
- What it does: Database administration, SQL optimization, and data management tools for PostgreSQL, SQL Server, and general database development best practices.
- More detail: Local Codex import of the Awesome Copilot plugin "database-data-management". Database administration, SQL optimization, and data management tools for PostgreSQL, SQL Server, and general database development best practices. Includes 4 plugin-local skill bundle(s). Includes 2 plugin-local agent definition file(s).
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - Skills: 4 (postgresql-code-review, postgresql-optimization, sql-code-review, sql-optimization)
  - Agents: 2 (ms-sql-dba, postgresql-dba)
  - Keywords: database, sql, postgresql, sql-server, dba, optimization, queries, data-management
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/database-data-management`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/database-data-management/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/plugins/database-data-management/README.md`
- External links/attribution: homepage: https://github.com/github/awesome-copilot; repository: https://github.com/github/awesome-copilot; author/developer: Awesome Copilot Community

### `design@local-codex-plugins`

- Display name: Design Productivity India
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.3.0`
- Category: Design
- What it does: India-aware design workflows for critique, accessibility, UX copy, design systems, research synthesis, and developer han
- More detail: India-aware design workflows for critique, accessibility, UX copy, design systems, research synthesis, and developer handoff. Uses compact router-first skills, India context checks, connector/export fallbacks, and explicit approval gates. Includes compact source-schemas and domain-specific India playbooks.
- Features and capabilities:
  - Interface capabilities: Review, Write, Handoff
  - MCP servers: slack (http), figma (http), linear (http), asana (http), atlassian (http), notion (http), intercom (http)
  - Skills: 8 (accessibility-review, design, design-critique, design-handoff, design-system, research-synthesis, user-research, ux-copy)
  - References: 4 (india-context, quality-gates, source-schemas, tooling-and-connectors)
  - Keywords: design, codex, plugin, india, approval-gated
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/design`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/design/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/design/.mcp.json`; README/CODEX: `/Users/raghav/plugins/design/README.md`; Codex usage: `/Users/raghav/plugins/design/CODEX_USAGE.md`
- External links/attribution: homepage: https://claude.com/plugins; author/developer: Anthropic

### `employment-legal@local-codex-plugins`

- Display name: Employment Legal
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.0.2`
- Category: Productivity
- What it does: Reviews hires and terminations for jurisdiction-specific risk flags, classifies workers against the controlling state test, tracks leave deadlines before they'r
- More detail: Codex-local India adaptation of the Claude for Legal Employment Legal plugin. It preserves the upstream skills, agents, references, guardrails, and setup interview, while using Codex-local practice profile paths under ~/.codex and Indian jurisdiction defaults unless the matter profile says otherwise.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write, Research
  - MCP servers: Slack (http), Google Drive (http)
  - Skills: 20 (cold-start-interview, customize, expansion-kickoff, expansion-update, handbook-updates, hiring-review, internal-investigation, international-expansion, +12 more)
  - Agents: 1 (leave-tracker)
  - Keywords: legal, law, india, codex, attorney-review, employment-legal
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/claude-for-legal/employment-legal`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/claude-for-legal/employment-legal/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/claude-for-legal/employment-legal/.mcp.json`; README/CODEX: `/Users/raghav/plugins/claude-for-legal/employment-legal/README.md`; Codex usage: `/Users/raghav/plugins/claude-for-legal/employment-legal/CODEX.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-for-legal; repository: https://github.com/anthropics/claude-for-legal; author/developer: Anthropic base; India adaptation by Raghav Badhwar

### `enterprise-search@local-codex-plugins`

- Display name: Enterprise Search India
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.3.0`
- Category: Productivity
- What it does: India-aware enterprise search across email, files, chat, tasks, and internal knowledge with privacy and privilege safegu
- More detail: India-aware enterprise search across email, files, chat, tasks, and internal knowledge with privacy and privilege safeguards. Uses compact router-first skills, India context checks, connector/export fallbacks, and explicit approval gates. Includes compact source-schemas and domain-specific India playbooks.
- Features and capabilities:
  - Interface capabilities: Search, Summarize, Research
  - MCP servers: slack (http), notion (http), guru (http), atlassian (http), asana (http), ms365 (http)
  - Skills: 6 (digest, enterprise-search, knowledge-synthesis, search, search-strategy, source-management)
  - References: 4 (india-context, quality-gates, source-schemas, tooling-and-connectors)
  - Keywords: enterprise, search, codex, plugin, india, approval-gated
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/enterprise-search`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/enterprise-search/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/enterprise-search/.mcp.json`; README/CODEX: `/Users/raghav/plugins/enterprise-search/README.md`; Codex usage: `/Users/raghav/plugins/enterprise-search/CODEX_USAGE.md`
- External links/attribution: homepage: https://claude.com/plugins; author/developer: Anthropic

### `feature-dev@local-codex-plugins`

- Display name: Feature Dev
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `0.0.0-claude-unknown`
- Category: Developer Tools
- What it does: Comprehensive feature development workflow with specialized agents for codebase exploration, architecture design, and quality review
- More detail: Codex-local adaptation of the Claude Code plugin `feature-dev` copied from `/Users/raghav/.claude/plugins/cache/claude-plugins-official/feature-dev/unknown`. Original files are preserved; Claude commands, agents, hooks, and MCP config are exposed through Codex plugin surfaces where possible.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - Skills: 4 (agent-code-architect, agent-code-explorer, agent-code-reviewer, command-feature-dev)
  - Keywords: claude-code-plugin, codex, local-adaptation
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/feature-dev`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/feature-dev/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/plugins/feature-dev/README.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-plugins-official; repository: https://github.com/anthropics/claude-plugins-official; author/developer: Anthropic

### `finance@local-codex-plugins`

- Display name: Finance & Accounting India
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.3.0`
- Category: Productivity
- What it does: India-aware finance workflows for journal entries, reconciliation, close, statements, variance analysis, audit support,
- More detail: India-aware finance workflows for journal entries, reconciliation, close, statements, variance analysis, audit support, and controls. Uses compact router-first skills, India context checks, connector/export fallbacks, and explicit approval gates. Includes compact source-schemas and domain-specific India playbooks.
- Features and capabilities:
  - Interface capabilities: Analyze, Reconcile, Report, Interactive, Read, Write, Research, MCP
  - MCP servers: bigquery (http), slack (http), ms365 (http)
  - Skills: 9 (audit-support, close-management, finance, financial-statements, journal-entry, journal-entry-prep, reconciliation, sox-testing, +1 more)
  - References: 4 (india-context, quality-gates, source-schemas, tooling-and-connectors)
  - Keywords: finance, codex, plugin, india, local-first, approval-gated
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/finance`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/finance/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/finance/.mcp.json`; README/CODEX: `/Users/raghav/plugins/finance/README.md`; Codex usage: `/Users/raghav/plugins/finance/CODEX_USAGE.md`
- External links/attribution: homepage: https://claude.com/plugins; repository: https://claude.com; author/developer: Anthropic base; India/Codex adaptation by Raghav Badhwar

### `frontend-design@local-codex-plugins`

- Display name: Frontend Design
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `0.0.0-claude-unknown`
- Category: Developer Tools
- What it does: Frontend design skill for UI/UX implementation
- More detail: Codex-local adaptation of the Claude Code plugin `frontend-design` copied from `/Users/raghav/.claude/plugins/cache/claude-plugins-official/frontend-design/unknown`. Original files are preserved; Claude commands, agents, hooks, and MCP config are exposed through Codex plugin surfaces where possible.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - Skills: 1 (frontend-design)
  - Keywords: claude-code-plugin, codex, local-adaptation
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/frontend-design`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/frontend-design/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/plugins/frontend-design/README.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-plugins-official; repository: https://github.com/anthropics/claude-plugins-official; author/developer: Anthropic

### `frontend-web-dev@local-codex-plugins`

- Display name: Frontend Web Dev
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.0.0`
- Category: Developer Tools
- What it does: Essential prompts, instructions, and chat modes for modern frontend web development including React, Angular, Vue, TypeScript, and CSS frameworks.
- More detail: Local Codex import of the Awesome Copilot plugin "frontend-web-dev". Essential prompts, instructions, and chat modes for modern frontend web development including React, Angular, Vue, TypeScript, and CSS frameworks. Includes 2 plugin-local skill bundle(s). Includes 2 plugin-local agent definition file(s).
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - Skills: 2 (playwright-explore-website, playwright-generate-test)
  - Agents: 2 (electron-angular-native, expert-react-frontend-engineer)
  - Keywords: frontend, web, react, typescript, javascript, css, html, angular, vue
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/frontend-web-dev`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/frontend-web-dev/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/plugins/frontend-web-dev/README.md`
- External links/attribution: homepage: https://github.com/github/awesome-copilot; repository: https://github.com/github/awesome-copilot; author/developer: Awesome Copilot Community

### `gem-team@local-codex-plugins`

- Display name: Gem Team
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.6.6`
- Category: Developer Tools
- What it does: Multi-agent orchestration framework for spec-driven development and automated verification.
- More detail: Local Codex import of the Awesome Copilot plugin "gem-team". Multi-agent orchestration framework for spec-driven development and automated verification. Includes 15 plugin-local agent definition file(s).
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - Agents: 15 (gem-browser-tester, gem-code-simplifier, gem-critic, gem-debugger, gem-designer-mobile, gem-designer, gem-devops, gem-documentation-writer, +7 more)
  - Keywords: multi-agent, orchestration, tdd, testing, e2e, devops, security-audit, code-review, prd, mobile
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/gem-team`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/gem-team/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/plugins/gem-team/README.md`
- External links/attribution: homepage: https://github.com/github/awesome-copilot; repository: https://github.com/github/awesome-copilot; author/developer: Awesome Copilot Community

### `human-resources@local-codex-plugins`

- Display name: Human Resources India
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.3.0`
- Category: Productivity
- What it does: India-aware HR workflows for recruiting, offers, onboarding, compensation, policies, people reports, and performance rev
- More detail: India-aware HR workflows for recruiting, offers, onboarding, compensation, policies, people reports, and performance reviews. Uses compact router-first skills, India context checks, connector/export fallbacks, and explicit approval gates. Includes compact source-schemas and domain-specific India playbooks.
- Features and capabilities:
  - Interface capabilities: Draft, Review, Plan, Interactive, Read, Write, Research, MCP
  - MCP servers: slack (http), notion (http), atlassian (http), ms365 (http)
  - Skills: 10 (comp-analysis, draft-offer, human-resources, interview-prep, onboarding, org-planning, people-report, performance-review, +2 more)
  - References: 4 (india-context, quality-gates, source-schemas, tooling-and-connectors)
  - Keywords: human, resources, codex, plugin, india, local-first, human-resources, approval-gated
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/human-resources`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/human-resources/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/human-resources/.mcp.json`; README/CODEX: `/Users/raghav/plugins/human-resources/README.md`; Codex usage: `/Users/raghav/plugins/human-resources/CODEX_USAGE.md`
- External links/attribution: homepage: https://claude.com/plugins; repository: https://claude.com; author/developer: Anthropic base; India/Codex adaptation by Raghav Badhwar

### `inventor-intelligence@local-codex-plugins`

- Display name: Inventor Intelligence
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `0.3.0`
- Category: Productivity
- What it does: Invent and stress-test breakthrough concepts.
- More detail: Inventor Intelligence packages the supplied inventor-intelligence-v3 skill bundle as a Codex plugin. It activates cross-domain synthesis, first-principles constraint analysis, Provocateur Mode, novelty checks, feasibility tiers, and validation planning for invention-heavy work.
- Features and capabilities:
  - Interface capabilities: Skill, Research, Ideation, Analysis
  - Skills: 1 (inventor-intelligence)
  - Keywords: invention, first-principles, ideation, research, validation
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/inventor-intelligence`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/inventor-intelligence/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/plugins/inventor-intelligence/README.md`
- External links/attribution: author/developer: Local developer

### `ip-legal@local-codex-plugins`

- Display name: IP Legal
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.0.2`
- Category: Productivity
- What it does: Runs first-pass trademark clearance and freedom-to-operate triage, screens invention disclosures for initial patentability, drafts and triages cease-and-desist
- More detail: Codex-local India adaptation of the Claude for Legal IP Legal plugin. It preserves the upstream skills, agents, references, guardrails, and setup interview, while using Codex-local practice profile paths under ~/.codex and Indian jurisdiction defaults unless the matter profile says otherwise. Active Codex skills are compact router/wrapper surfaces; preserved upstream Claude skill text remains under...
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write, Research
  - MCP servers: Solve Intelligence (http), CourtListener (http), Descrybe (http), Slack (http), Google Drive (http)
  - Skills: 13 (cease-desist, clearance, cold-start-interview, customize, fto-triage, infringement-triage, invention-intake, ip-clause-review, +5 more)
  - Keywords: legal, law, india, codex, attorney-review, ip-legal
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/claude-for-legal/ip-legal`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/claude-for-legal/ip-legal/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/claude-for-legal/ip-legal/.mcp.json`; README/CODEX: `/Users/raghav/plugins/claude-for-legal/ip-legal/README.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-for-legal; repository: https://github.com/anthropics/claude-for-legal; author/developer: Anthropic base; India adaptation by Raghav Badhwar

### `karimo@local-codex-plugins`

- Display name: KARIMO
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `9.9.1`
- Category: Developer Tools
- What it does: PRD-driven autonomous agent orchestration
- More detail: Codex-local adaptation of opensesh/KARIMO. It preserves the upstream Claude plugin agents, slash commands, templates, installer, and KARIMO rules, and adds Codex skill bundles so the workflow can be used from Codex with research, planning, worktree execution, review, and feedback loops.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write, Automation, Research
  - Skills: 9 (bash-utilities, code-standards, doc-standards, external-research, firecrawl-web-tools, karimo, orchestration-inference, research-methods, +1 more)
  - Commands: 11 (configure, dashboard, doctor, feedback, greptile-review, help, merge, plan, +3 more)
  - Agents: 22 (brief-corrector, brief-reviewer, brief-writer, coverage-reviewer, documenter-opus, documenter, feedback-auditor, greptile-remediator, +14 more)
  - Keywords: karimo, prd, orchestration, agents, worktrees, review, research, planning
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/karimo`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/karimo/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/plugins/karimo/README.md`
- External links/attribution: homepage: https://github.com/opensesh/KARIMO; repository: https://github.com/opensesh/KARIMO; author/developer: Open Session

### `law-student@local-codex-plugins`

- Display name: Law Student
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.0.2`
- Category: Productivity
- What it does: Drills Socratically, briefs cases, builds outlines, runs bar prep sessions tuned to your jurisdiction, grades IRAC practice, and plans the study schedule - with
- More detail: Codex-local India adaptation of the Claude for Legal Law Student plugin. It preserves the upstream skills, agents, references, guardrails, and setup interview, while using Codex-local practice profile paths under ~/.codex and Indian jurisdiction defaults unless the matter profile says otherwise.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write, Research
  - MCP servers: Slack (http), Google Drive (http), CourtListener (http), Descrybe (http)
  - Skills: 13 (bar-prep-questions, case-brief, cold-call-prep, cold-start-interview, customize, exam-forecast, flashcards, irac-practice, +5 more)
  - Keywords: legal, law, india, codex, attorney-review, law-student
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/claude-for-legal/law-student`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/claude-for-legal/law-student/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/claude-for-legal/law-student/.mcp.json`; README/CODEX: `/Users/raghav/plugins/claude-for-legal/law-student/README.md`; Codex usage: `/Users/raghav/plugins/claude-for-legal/law-student/CODEX.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-for-legal; repository: https://github.com/anthropics/claude-for-legal; author/developer: Anthropic base; India adaptation by Raghav Badhwar

### `legal@local-codex-plugins`

- Display name: Legal Productivity India
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.3.0`
- Category: Productivity
- What it does: India-aware legal productivity workflows for contract review, privacy, compliance, vendor checks, legal briefs, and appr
- More detail: India-aware legal productivity workflows for contract review, privacy, compliance, vendor checks, legal briefs, and approvals. Uses compact router-first skills, India context checks, connector/export fallbacks, and explicit approval gates. Includes compact source-schemas and domain-specific India playbooks.
- Features and capabilities:
  - Interface capabilities: Review, Draft, Research
  - MCP servers: slack (http), box (http), egnyte (http), atlassian (http), ms365 (http), docusign (http)
  - Skills: 10 (brief, compliance-check, legal, legal-response, legal-risk-assessment, meeting-briefing, review-contract, signature-request, +2 more)
  - References: 4 (india-context, quality-gates, source-schemas, tooling-and-connectors)
  - Keywords: legal, codex, plugin, india, approval-gated
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/legal`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/legal/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/legal/.mcp.json`; README/CODEX: `/Users/raghav/plugins/legal/README.md`; Codex usage: `/Users/raghav/plugins/legal/CODEX_USAGE.md`
- External links/attribution: homepage: https://claude.com/plugins; author/developer: Anthropic

### `legal-builder-hub@local-codex-plugins`

- Display name: Legal Builder Hub
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.0.2`
- Category: Productivity
- What it does: Finds, evaluates, and installs community legal skills - with a security review gate before anything lands in your environment. India-localized default posture;
- More detail: Codex-local India adaptation of the Claude for Legal Legal Builder Hub plugin. It preserves the upstream skills, agents, references, guardrails, and setup interview, while using Codex-local practice profile paths under ~/.codex and Indian jurisdiction defaults unless the matter profile says otherwise.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write, Research
  - MCP servers: Slack (http), Google Drive (http), Lawve AI (http)
  - Skills: 10 (auto-updater, cold-start-interview, customize, disable, registry-browser, related-skills-surfacer, skill-installer, skill-manager, +2 more)
  - Agents: 1 (registry-sync)
  - References: 1 (allowlist-default)
  - Keywords: legal, law, india, codex, attorney-review, legal-builder-hub
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/claude-for-legal/legal-builder-hub`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/claude-for-legal/legal-builder-hub/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/claude-for-legal/legal-builder-hub/.mcp.json`; README/CODEX: `/Users/raghav/plugins/claude-for-legal/legal-builder-hub/README.md`; Codex usage: `/Users/raghav/plugins/claude-for-legal/legal-builder-hub/CODEX.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-for-legal; repository: https://github.com/anthropics/claude-for-legal; author/developer: Anthropic base; India adaptation by Raghav Badhwar

### `legal-clinic@local-codex-plugins`

- Display name: Legal Clinic
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.0.2`
- Category: Productivity
- What it does: Sets up the clinic, onboards students, runs structured intake, tracks deadlines with malpractice-aware caution, and hands off cases at semester end - built with
- More detail: Codex-local India adaptation of the Claude for Legal Legal Clinic plugin. It preserves the upstream skills, agents, references, guardrails, and setup interview, while using Codex-local practice profile paths under ~/.codex and Indian jurisdiction defaults unless the matter profile says otherwise.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write, Research
  - MCP servers: Slack (http), Google Drive (http), CourtListener (http), Courtroom5 (http), Descrybe (http)
  - Skills: 16 (build-guide, client-comms-log, client-intake, client-letter, cold-start-interview, customize, deadlines, draft, +8 more)
  - Keywords: legal, law, india, codex, attorney-review, legal-clinic
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/claude-for-legal/legal-clinic`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/claude-for-legal/legal-clinic/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/claude-for-legal/legal-clinic/.mcp.json`; README/CODEX: `/Users/raghav/plugins/claude-for-legal/legal-clinic/README.md`; Codex usage: `/Users/raghav/plugins/claude-for-legal/legal-clinic/CODEX.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-for-legal; repository: https://github.com/anthropics/claude-for-legal; author/developer: Anthropic base; India adaptation by Raghav Badhwar

### `litigation-legal@local-codex-plugins`

- Display name: Litigation Legal
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.0.2`
- Category: Productivity
- What it does: Manages the litigation portfolio - matters, deadlines, holds, demands, outside counsel - and does the work: claim charts (patent and civil), chronologies, depo
- More detail: Codex-local India adaptation of the Claude for Legal Litigation Legal plugin. It preserves the upstream skills, agents, references, guardrails, and setup interview, while using Codex-local practice profile paths under ~/.codex and Indian jurisdiction defaults unless the matter profile says otherwise.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write, Research
  - MCP servers: Slack (http), Google Drive (http), Everlaw (http), TopCounsel (http), CourtListener (http), Aurora (http), Trellis (http)
  - Skills: 19 (brief-section-drafter, chronology, claim-chart, cold-start-interview, customize, demand-draft, demand-intake, demand-received, +11 more)
  - Agents: 1 (docket-watcher)
  - Keywords: legal, law, india, codex, attorney-review, litigation-legal
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/claude-for-legal/litigation-legal`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/claude-for-legal/litigation-legal/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/claude-for-legal/litigation-legal/.mcp.json`; README/CODEX: `/Users/raghav/plugins/claude-for-legal/litigation-legal/README.md`; Codex usage: `/Users/raghav/plugins/claude-for-legal/litigation-legal/CODEX.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-for-legal; repository: https://github.com/anthropics/claude-for-legal; author/developer: Anthropic base; India adaptation by Raghav Badhwar

### `marketing@local-codex-plugins`

- Display name: Marketing India
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.3.0`
- Category: Marketing
- What it does: India-aware marketing workflows for campaigns, content, brand review, SEO, email, competitor analysis, and performance r
- More detail: India-aware marketing workflows for campaigns, content, brand review, SEO, email, competitor analysis, and performance reporting. Uses compact router-first skills, India context checks, connector/export fallbacks, and explicit approval gates. Includes compact source-schemas and domain-specific India playbooks.
- Features and capabilities:
  - Interface capabilities: Draft, Plan, Analyze
  - MCP servers: slack (http), canva (http), figma (http), hubspot (http), amplitude (http), amplitude-eu (http), notion (http), ahrefs (http), similarweb (http), klaviyo (http), supermetrics (http)
  - Skills: 9 (brand-review, campaign-plan, competitive-brief, content-creation, draft-content, email-sequence, marketing, performance-report, +1 more)
  - References: 4 (india-context, quality-gates, source-schemas, tooling-and-connectors)
  - Keywords: marketing, codex, plugin, india, approval-gated
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/marketing`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/marketing/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/marketing/.mcp.json`; README/CODEX: `/Users/raghav/plugins/marketing/README.md`; Codex usage: `/Users/raghav/plugins/marketing/CODEX_USAGE.md`
- External links/attribution: homepage: https://claude.com/plugins; author/developer: Anthropic

### `medconsumables-analyst@local-codex-plugins`

- Display name: MedConsumables Analyst
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `0.1.0`
- Category: Business
- What it does: India medical consumables analyst for market, product, sourcing, sales, finance, and compliance workflows.
- More detail: India-focused medical consumables and disposables business analyst adapted from the supplied JSX artifact. Provides structured workflows for product category analysis, starter SKU strategy, domestic and import sourcing, hospital and tender sales, working-capital modelling, and CDSCO/BIS/drug-license risk checks. Uses evidence-first, current-source checks for market, regulatory, and supplier claims.
- Features and capabilities:
  - Interface capabilities: Analyze, Research, Plan, Report, Interactive
  - Skills: 1 (medconsumables-analyst)
  - References: 1 (domain-map)
  - Keywords: medical-consumables, healthcare, india, business-analysis, sourcing, cdsco, hospital-procurement
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/medconsumables-analyst`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/medconsumables-analyst/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/plugins/medconsumables-analyst/README.md`; Codex usage: `/Users/raghav/plugins/medconsumables-analyst/CODEX_USAGE.md`
- External links/attribution: homepage: https://local.codex/plugins/medconsumables-analyst; repository: https://local.codex/plugins/medconsumables-analyst; author/developer: Raghav Badhwar; Codex adaptation

### `operations@local-codex-plugins`

- Display name: Operations India
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.3.0`
- Category: Productivity
- What it does: India-aware operations workflows for vendor review, process docs, compliance tracking, capacity planning, runbooks, risk
- More detail: India-aware operations workflows for vendor review, process docs, compliance tracking, capacity planning, runbooks, risk, and status reports. Uses compact router-first skills, India context checks, connector/export fallbacks, and explicit approval gates. Includes compact source-schemas and domain-specific India playbooks.
- Features and capabilities:
  - Interface capabilities: Document, Plan, Review, Interactive, Read, Write, Research, MCP
  - MCP servers: slack (http), notion (http), atlassian (http), asana (http), ms365 (http)
  - Skills: 10 (capacity-plan, change-request, compliance-tracking, operations, process-doc, process-optimization, risk-assessment, runbook, +2 more)
  - References: 4 (india-context, quality-gates, source-schemas, tooling-and-connectors)
  - Keywords: operations, codex, plugin, india, local-first, approval-gated
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/operations`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/operations/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/operations/.mcp.json`; README/CODEX: `/Users/raghav/plugins/operations/README.md`; Codex usage: `/Users/raghav/plugins/operations/CODEX_USAGE.md`
- External links/attribution: homepage: https://claude.com/plugins; repository: https://claude.com; author/developer: Anthropic base; India/Codex adaptation by Raghav Badhwar

### `polyglot-test-agent@local-codex-plugins`

- Display name: Polyglot Test Agent
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.0.0`
- Category: Developer Tools
- What it does: Multi-agent pipeline for generating comprehensive unit tests across any programming language. Orchestrates research, planning, and implementation phases using specialized agents to produce tests that compile, pass, and follow project conventions.
- More detail: Local Codex import of the Awesome Copilot plugin "polyglot-test-agent". Multi-agent pipeline for generating comprehensive unit tests across any programming language. Orchestrates research, planning, and implementation phases using specialized agents to produce tests that compile, pass, and follow project conventions. Includes 1 plugin-local skill bundle(s). Includes 8 plugin-local agent definition file(s).
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - Skills: 1 (polyglot-test-agent)
  - Agents: 8 (polyglot-test-builder, polyglot-test-fixer, polyglot-test-generator, polyglot-test-implementer, polyglot-test-linter, polyglot-test-planner, polyglot-test-researcher, polyglot-test-tester)
  - Keywords: testing, unit-tests, polyglot, test-generation, multi-agent, tdd, csharp, typescript, python, go
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/polyglot-test-agent`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/polyglot-test-agent/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/plugins/polyglot-test-agent/README.md`
- External links/attribution: homepage: https://github.com/github/awesome-copilot; repository: https://github.com/github/awesome-copilot; author/developer: Awesome Copilot Community

### `privacy-legal@local-codex-plugins`

- Display name: Privacy Legal
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.0.2`
- Category: Productivity
- What it does: Triages processing activities, generates PIAs, reviews DPAs as controller or processor, drafts DSAR responses within statutory timelines, and monitors policy dr
- More detail: Codex-local India adaptation of the Claude for Legal Privacy Legal plugin. It preserves the upstream skills, agents, references, guardrails, and setup interview, while using Codex-local practice profile paths under ~/.codex and Indian jurisdiction defaults unless the matter profile says otherwise. Active Codex skills are compact router/wrapper surfaces; preserved upstream Claude skill text remains under...
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write, Research
  - MCP servers: Slack (http), Google Drive (http)
  - Skills: 10 (cold-start-interview, customize, dpa-review, dsar-response, matter-workspace, pia-generation, policy-monitor, privacy-legal-router, +2 more)
  - Keywords: legal, law, india, codex, attorney-review, privacy-legal
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/claude-for-legal/privacy-legal`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/claude-for-legal/privacy-legal/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/claude-for-legal/privacy-legal/.mcp.json`; README/CODEX: `/Users/raghav/plugins/claude-for-legal/privacy-legal/README.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-for-legal; repository: https://github.com/anthropics/claude-for-legal; author/developer: Anthropic base; India adaptation by Raghav Badhwar

### `product-legal@local-codex-plugins`

- Display name: Product Legal
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.0.2`
- Category: Productivity
- What it does: Reviews product launches against your risk calibration, answers 'is this a problem?' questions in minutes, checks marketing copy for claims that need substantia
- More detail: Codex-local India adaptation of the Claude for Legal Product Legal plugin. It preserves the upstream skills, agents, references, guardrails, and setup interview, while using Codex-local practice profile paths under ~/.codex and Indian jurisdiction defaults unless the matter profile says otherwise. Active Codex skills are compact router/wrapper surfaces; preserved upstream Claude skill text remains under...
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write, Research
  - MCP servers: Slack (http), Google Drive (http), Linear (http), Atlassian (http), Asana (http)
  - Skills: 8 (cold-start-interview, customize, feature-risk-assessment, is-this-a-problem, launch-review, marketing-claims-review, matter-workspace, product-legal-router)
  - Keywords: legal, law, india, codex, attorney-review, product-legal
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/claude-for-legal/product-legal`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/claude-for-legal/product-legal/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/claude-for-legal/product-legal/.mcp.json`; README/CODEX: `/Users/raghav/plugins/claude-for-legal/product-legal/README.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-for-legal; repository: https://github.com/anthropics/claude-for-legal; author/developer: Anthropic base; India adaptation by Raghav Badhwar

### `product-management@local-codex-plugins`

- Display name: Product Management India
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.3.0`
- Category: Product Management
- What it does: India-aware product workflows for PRDs, roadmaps, user research, metrics, competitive analysis, launch checks, and updat
- More detail: India-aware product workflows for PRDs, roadmaps, user research, metrics, competitive analysis, launch checks, and updates. Uses compact router-first skills, India context checks, connector/export fallbacks, and explicit approval gates. Includes compact source-schemas and domain-specific India playbooks.
- Features and capabilities:
  - Interface capabilities: Plan, Write, Analyze
  - MCP servers: slack (http), linear (http), asana (http), monday (http), clickup (http), atlassian (http), notion (http), figma (http), amplitude (http), amplitude-eu (http), pendo (http), intercom (http), +2 more
  - Skills: 10 (brainstorm, competitive-brief, metrics-review, product-brainstorming, product-management, roadmap-update, sprint-planning, stakeholder-update, +2 more)
  - References: 4 (india-context, quality-gates, source-schemas, tooling-and-connectors)
  - Keywords: product, management, codex, plugin, india, approval-gated
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/product-management`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/product-management/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/product-management/.mcp.json`; README/CODEX: `/Users/raghav/plugins/product-management/README.md`; Codex usage: `/Users/raghav/plugins/product-management/CODEX_USAGE.md`
- External links/attribution: homepage: https://claude.com/plugins; author/developer: Anthropic

### `productivity@local-codex-plugins`

- Display name: Productivity India
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.3.0`
- Category: Productivity
- What it does: India-aware productivity workflows for tasks, memory, daily planning, and work context with privacy safeguards.
- More detail: India-aware productivity workflows for tasks, memory, daily planning, and work context with privacy safeguards. Uses compact router-first skills, India context checks, connector/export fallbacks, and explicit approval gates. Includes compact source-schemas and domain-specific India playbooks.
- Features and capabilities:
  - Interface capabilities: Plan, Track, Summarize
  - MCP servers: slack (http), notion (http), asana (http), linear (http), atlassian (http), ms365 (http), monday (http), clickup (http)
  - Skills: 5 (memory-management, productivity, start, task-management, update)
  - References: 4 (india-context, quality-gates, source-schemas, tooling-and-connectors)
  - Keywords: productivity, codex, plugin, india, approval-gated
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/productivity`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/productivity/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/productivity/.mcp.json`; README/CODEX: `/Users/raghav/plugins/productivity/README.md`; Codex usage: `/Users/raghav/plugins/productivity/CODEX_USAGE.md`
- External links/attribution: homepage: https://claude.com/plugins; author/developer: Anthropic

### `project-planning@local-codex-plugins`

- Display name: Project Planning
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.0.0`
- Category: Developer Tools
- What it does: Tools and guidance for software project planning, feature breakdown, epic management, implementation planning, and task organization for development teams.
- More detail: Local Codex import of the Awesome Copilot plugin "project-planning". Tools and guidance for software project planning, feature breakdown, epic management, implementation planning, and task organization for development teams. Includes 8 plugin-local skill bundle(s). Includes 7 plugin-local agent definition file(s).
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - Skills: 8 (breakdown-epic-arch, breakdown-epic-pm, breakdown-feature-implementation, breakdown-feature-prd, create-github-issues-feature-from-implementation-plan, create-implementation-plan, create-technical-spike, update-implementation-plan)
  - Agents: 7 (implementation-plan, plan, planner, prd, research-technical-spike, task-planner, task-researcher)
  - Keywords: planning, project-management, epic, feature, implementation, task, architecture, technical-spike
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/project-planning`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/project-planning/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/plugins/project-planning/README.md`
- External links/attribution: homepage: https://github.com/github/awesome-copilot; repository: https://github.com/github/awesome-copilot; author/developer: Awesome Copilot Community

### `ralph-loop@local-codex-plugins`

- Display name: Ralph Loop
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.0.0`
- Category: Developer Tools
- What it does: Continuous self-referential AI loops for interactive iterative development, implementing the Ralph Wiggum technique. Run Claude in a while-true loop with the same prompt until task
- More detail: Codex-local adaptation of the Claude Code plugin `ralph-loop` copied from `/Users/raghav/.claude/plugins/cache/claude-plugins-official/ralph-loop/1.0.0`. Original files are preserved; Claude commands, agents, hooks, and MCP config are exposed through Codex plugin surfaces where possible.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - Skills: 4 (command-cancel-ralph, command-help, command-ralph-loop, ralph-loop-hooks)
  - Keywords: claude-code-plugin, codex, local-adaptation
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/ralph-loop`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/ralph-loop/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/plugins/ralph-loop/README.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-plugins-official; repository: https://github.com/anthropics/claude-plugins-official; author/developer: Anthropic

### `regulatory-legal@local-codex-plugins`

- Display name: Regulatory Legal
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.0.2`
- Category: Productivity
- What it does: Watches regulatory feeds, diffs new rules against your policy library, tracks comment deadlines and open gaps, and writes the digest your team reads Monday morn
- More detail: Codex-local India adaptation of the Claude for Legal Regulatory Legal plugin. It preserves the upstream skills, agents, references, guardrails, and setup interview, while using Codex-local practice profile paths under ~/.codex and Indian jurisdiction defaults unless the matter profile says otherwise.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write, Research
  - MCP servers: Slack (http), Google Drive (http)
  - Skills: 9 (cold-start-interview, comments, customize, gap-surfacer, gaps, matter-workspace, policy-diff, policy-redraft, +1 more)
  - Agents: 1 (reg-change-monitor)
  - Keywords: legal, law, india, codex, attorney-review, regulatory-legal
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/claude-for-legal/regulatory-legal`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/claude-for-legal/regulatory-legal/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/claude-for-legal/regulatory-legal/.mcp.json`; README/CODEX: `/Users/raghav/plugins/claude-for-legal/regulatory-legal/README.md`; Codex usage: `/Users/raghav/plugins/claude-for-legal/regulatory-legal/CODEX.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-for-legal; repository: https://github.com/anthropics/claude-for-legal; author/developer: Anthropic base; India adaptation by Raghav Badhwar

### `sales@local-codex-plugins`

- Display name: Sales India
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.3.0`
- Category: Productivity
- What it does: India-aware sales workflows for account research, outreach drafts, call prep, pipeline review, forecasting, and sales as
- More detail: India-aware sales workflows for account research, outreach drafts, call prep, pipeline review, forecasting, and sales assets. Uses compact router-first skills, India context checks, connector/export fallbacks, and explicit approval gates. Includes compact source-schemas and domain-specific India playbooks.
- Features and capabilities:
  - Interface capabilities: Research, Draft, Analyze, Interactive, Read, Write, MCP
  - MCP servers: slack (http), hubspot (http), close (http), clay (http), zoominfo (http), notion (http), atlassian (http), fireflies (http), ms365 (http), apollo (http), outreach (http), similarweb (http)
  - Skills: 10 (account-research, call-prep, call-summary, competitive-intelligence, create-an-asset, daily-briefing, draft-outreach, forecast, +2 more)
  - References: 4 (india-context, quality-gates, source-schemas, tooling-and-connectors)
  - Keywords: sales, codex, plugin, india, local-first, approval-gated
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/sales`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/sales/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/sales/.mcp.json`; README/CODEX: `/Users/raghav/plugins/sales/README.md`; Codex usage: `/Users/raghav/plugins/sales/CODEX_USAGE.md`
- External links/attribution: homepage: https://claude.com/plugins; repository: https://claude.com; author/developer: Anthropic base; India/Codex adaptation by Raghav Badhwar

### `security-best-practices@local-codex-plugins`

- Display name: Security Best Practices
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.0.0`
- Category: Developer Tools
- What it does: Security frameworks, accessibility guidelines, performance optimization, and code quality best practices for building secure, maintainable, and high-performance applications.
- More detail: Local Codex import of the Awesome Copilot plugin "security-best-practices". Security frameworks, accessibility guidelines, performance optimization, and code quality best practices for building secure, maintainable, and high-performance applications. Includes 1 plugin-local skill bundle(s).
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - Skills: 1 (ai-prompt-engineering-safety-review)
  - Keywords: security, accessibility, performance, code-quality, owasp, a11y, optimization, best-practices
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/security-best-practices`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/security-best-practices/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/plugins/security-best-practices/README.md`
- External links/attribution: homepage: https://github.com/github/awesome-copilot; repository: https://github.com/github/awesome-copilot; author/developer: Awesome Copilot Community

### `security-guidance@local-codex-plugins`

- Display name: Security Guidance
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `2.0.0`
- Category: Developer Tools
- What it does: Security review for Claude-generated code. Pattern-based warnings on edits, LLM-powered diff review on Stop, and an agentic commit reviewer that catches injection, XSS, SSRF, hardc
- More detail: Codex-local adaptation of the Claude Code plugin `security-guidance` copied from `/Users/raghav/.claude/plugins/cache/claude-plugins-official/security-guidance/2.0.0`. Original files are preserved; Claude commands, agents, hooks, and MCP config are exposed through Codex plugin surfaces where possible.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - Skills: 1 (security-guidance-hooks)
  - Keywords: claude-code-plugin, codex, local-adaptation
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/security-guidance`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/security-guidance/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/plugins/security-guidance/README.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-plugins-official/tree/main/plugins/security-guidance; repository: https://github.com/anthropics/claude-plugins-official; author/developer: David Dworken

### `small-business@local-codex-plugins`

- Display name: Small Business India
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `0.3.0`
- Category: Productivity
- What it does: India-aware small-business workflows for cash flow, invoices, GST/TDS, payroll planning, customer support, campaigns, an
- More detail: India-aware small-business workflows for cash flow, invoices, GST/TDS, payroll planning, customer support, campaigns, and accountant handoff. Uses compact router-first skills, India context checks, connector/export fallbacks, and explicit approval gates. Includes compact source-schemas and domain-specific India playbooks.
- Features and capabilities:
  - Interface capabilities: Plan, Automate, Review, Interactive, Read, Write, Research, MCP
  - MCP servers: quickbooks (http), paypal (sse), hubspot (http), canva (http), docusign (http), slack (http), stripe (http), square (http), ms365 (http), gmail (http), google-calendar (http), google-drive (http)
  - Skills: 7 (cash-flow-snapshot, close-month, handle-complaint, invoice-chase, plan-payroll, small-business, tax-prep)
  - References: 4 (india-context, quality-gates, source-schemas, tooling-and-connectors)
  - Keywords: small, business, codex, plugin, india, local-first, small-business, approval-gated
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/small-business`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/small-business/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/small-business/.mcp.json`; README/CODEX: `/Users/raghav/plugins/small-business/README.md`; Codex usage: `/Users/raghav/plugins/small-business/CODEX_USAGE.md`
- External links/attribution: homepage: https://claude.com/plugins; repository: https://claude.com; author/developer: Anthropic base; India/Codex adaptation by Raghav Badhwar

### `software-engineering-team@local-codex-plugins`

- Display name: Software Engineering Team
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.0.0`
- Category: Developer Tools
- What it does: 7 specialized agents covering the full software development lifecycle from UX design and architecture to security and DevOps.
- More detail: Local Codex import of the Awesome Copilot plugin "software-engineering-team". 7 specialized agents covering the full software development lifecycle from UX design and architecture to security and DevOps. Includes 7 plugin-local agent definition file(s).
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - Agents: 7 (se-gitops-ci-specialist, se-product-manager-advisor, se-responsible-ai-code, se-security-reviewer, se-system-architecture-reviewer, se-technical-writer, se-ux-ui-designer)
  - Keywords: team, enterprise, security, devops, ux, architecture, product, ai-ethics
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/software-engineering-team`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/software-engineering-team/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/plugins/software-engineering-team/README.md`
- External links/attribution: homepage: https://github.com/github/awesome-copilot; repository: https://github.com/github/awesome-copilot; author/developer: Awesome Copilot Community

### `sprecial-agent-loop@local-codex-plugins`

- Display name: sprecial agent loop
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.1.0`
- Category: Productivity
- What it does: Build and package reliable agent loops.
- More detail: Interviews the user, creates requirements, selects architecture, generates prompts/tools/state/guardrails/evals, simulates tests, critiques the loop, revises it, and packages a final handoff.
- Features and capabilities:
  - Interface capabilities: Read, Write
  - Skills: 1 (agent-loop-builder)
  - Scripts: 2 (loop_builder_core, package_validate)
  - Keywords: agents, loops, workflow, skills, codex, evaluation, guardrails
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/sprecial-agent-loop`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/sprecial-agent-loop/.codex-plugin/plugin.json`
- External links/attribution: author/developer: Manya Jain / ChatGPT

### `structured-autonomy@local-codex-plugins`

- Display name: Structured Autonomy
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.0.0`
- Category: Developer Tools
- What it does: Premium planning, thrifty implementation
- More detail: Local Codex import of the Awesome Copilot plugin "structured-autonomy". Premium planning, thrifty implementation Includes 3 plugin-local skill bundle(s).
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - Skills: 3 (structured-autonomy-generate, structured-autonomy-implement, structured-autonomy-plan)
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/structured-autonomy`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/structured-autonomy/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/plugins/structured-autonomy/README.md`
- External links/attribution: homepage: https://github.com/github/awesome-copilot; repository: https://github.com/github/awesome-copilot; author/developer: Awesome Copilot Community

### `technical-spike@local-codex-plugins`

- Display name: Technical Spike
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.0.0`
- Category: Developer Tools
- What it does: Tools for creation, management and research of technical spikes to reduce unknowns and assumptions before proceeding to specification and implementation of solutions.
- More detail: Local Codex import of the Awesome Copilot plugin "technical-spike". Tools for creation, management and research of technical spikes to reduce unknowns and assumptions before proceeding to specification and implementation of solutions. Includes 1 plugin-local skill bundle(s). Includes 1 plugin-local agent definition file(s).
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - Skills: 1 (create-technical-spike)
  - Agents: 1 (research-technical-spike)
  - Keywords: technical-spike, assumption-testing, validation, research
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/technical-spike`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/technical-spike/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/plugins/technical-spike/README.md`
- External links/attribution: homepage: https://github.com/github/awesome-copilot; repository: https://github.com/github/awesome-copilot; author/developer: Awesome Copilot Community

### `telegram@local-codex-plugins`

- Display name: Telegram
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `0.0.6`
- Category: Developer Tools
- What it does: Telegram channel for Claude Code - messaging bridge with built-in access control. Manage pairing, allowlists, and policy via /telegram:access.
- More detail: Codex-local adaptation of the Claude Code plugin `telegram` copied from `/Users/raghav/.claude/plugins/cache/claude-plugins-official/telegram/0.0.6`. Original files are preserved; Claude commands, agents, hooks, and MCP config are exposed through Codex plugin surfaces where possible.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write, MCP
  - MCP servers: telegram (bun)
  - Skills: 3 (access, configure, telegram-mcp)
  - Keywords: channel, claude-code-plugin, codex, local-adaptation, mcp, messaging, telegram
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/telegram`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/telegram/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/telegram/.mcp.json`; README/CODEX: `/Users/raghav/plugins/telegram/README.md`
- External links/attribution: homepage: https://github.com/anthropics/claude-plugins-official; repository: https://github.com/anthropics/claude-plugins-official; author/developer: Anthropic

### `testing-automation@local-codex-plugins`

- Display name: Testing Automation
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `1.0.0`
- Category: Developer Tools
- What it does: Comprehensive collection for writing tests, test automation, and test-driven development including unit tests, integration tests, and end-to-end testing strategies.
- More detail: Local Codex import of the Awesome Copilot plugin "testing-automation". Comprehensive collection for writing tests, test automation, and test-driven development including unit tests, integration tests, and end-to-end testing strategies. Includes 5 plugin-local skill bundle(s). Includes 4 plugin-local agent definition file(s).
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - Skills: 5 (ai-prompt-engineering-safety-review, csharp-nunit, java-junit, playwright-explore-website, playwright-generate-test)
  - Agents: 4 (playwright-tester, tdd-green, tdd-red, tdd-refactor)
  - Keywords: testing, tdd, automation, unit-tests, integration, playwright, jest, nunit
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/testing-automation`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/testing-automation/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/plugins/testing-automation/README.md`
- External links/attribution: homepage: https://github.com/github/awesome-copilot; repository: https://github.com/github/awesome-copilot; author/developer: Awesome Copilot Community

### `trading-desk@local-codex-plugins`

- Display name: Trading Desk
- Marketplace: `local-codex-plugins`
- Status: installed, enabled
- Version: `0.1.0`
- Category: Business
- What it does: Invoke a multi-asset analyst team for source-backed paper-trading research.
- More detail: Trading Desk coordinates specialist Codex skills for technical analysis, chart pattern review, fundamentals, news reaction, sentiment and propaganda checks, cycle history, contrarian review, risk management, investment committee synthesis, and workspace-local paper-trade tracking. V1 is research and paper trading only. It never places live orders.
- Features and capabilities:
  - Interface capabilities: Analyze, Research, Interactive, Read, Write
  - Skills: 11 (chart-pattern-analyst, contrarian-analyst, cycle-history-analyst, fundamental-analyst, investment-committee, news-reaction-analyst, paper-trading, risk-manager, +3 more)
  - References: 4 (analysis-framework, paper-ledger-schema, quality-gates, risk-policy)
  - Scripts: 1 (trading_ledger)
  - Keywords: trading, paper-trading, market-research, technical-analysis, fundamental-analysis, risk-management, codex
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/trading-desk`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/trading-desk/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/plugins/trading-desk/README.md`; Codex usage: `/Users/raghav/plugins/trading-desk/CODEX_USAGE.md`
- External links/attribution: author/developer: Raghav Badhwar

### `browser@openai-bundled`

- Display name: Browser
- Marketplace: `openai-bundled`
- Status: installed, enabled
- Version: `26.623.70822`
- Category: Engineering
- What it does: Control the in-app browser with Codex
- More detail: Browser lets Codex open and control the in-app browser, mainly for local development pages and files. Use it to navigate, inspect, click, type, and take screenshots while testing pages inside Codex.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - Skills: 1 (control-in-app-browser)
  - Scripts: 6 (check-extension-installed, check-native-host-manifest, chrome-is-running, installed-browsers, open-chrome-window, browser-client)
  - Keywords: browser, automation, chrome, iab, node-repl, browser-client
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/bundled-marketplaces/openai-bundled/plugins/browser`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/bundled-marketplaces/openai-bundled/plugins/browser/.codex-plugin/plugin.json`
- External links/attribution: homepage: https://github.com/openai/openai/tree/master/lib/browser_use/plugin; repository: https://github.com/openai/openai/tree/master/lib/browser_use/plugin; author/developer: OpenAI

### `chrome@openai-bundled`

- Display name: Chrome
- Marketplace: `openai-bundled`
- Status: installed, enabled
- Version: `26.623.70822`
- Category: Productivity
- What it does: Control Chrome with Codex
- More detail: Chrome lets Codex use your Chrome browser for tasks that need your existing browser state, including open tabs, page content, and websites you're already signed into. It can navigate, view, click, type, and take screenshots while working. You stay in control: Codex asks before interacting with new sites, you can stop actions at any time, and you can manage or remove Chrome access in settings. Browser content may...
- Features and capabilities:
  - Interface capabilities: Interactive, Read
  - Skills: 1 (control-chrome)
  - Scripts: 7 (check-extension-installed, check-native-host-manifest, chrome-is-running, installed-browsers, open-chrome-window, browser-client, installManifest)
  - Keywords: browser, chrome
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/bundled-marketplaces/openai-bundled/plugins/chrome`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/bundled-marketplaces/openai-bundled/plugins/chrome/.codex-plugin/plugin.json`
- External links/attribution: homepage: https://github.com/openai/openai/tree/master/lib/browser_use/plugin; repository: https://github.com/openai/openai/tree/master/lib/browser_use/plugin; author/developer: OpenAI

### `computer-use@openai-bundled`

- Display name: Computer Use
- Marketplace: `openai-bundled`
- Status: installed, enabled
- Version: `1.0.857`
- Category: Productivity
- What it does: Control Mac apps from Codex
- More detail: Mac Computer Use lets Codex use any app on your computer, including your web browsers and files you allow it to access. It may take screenshots or page content while working. You stay in control: you choose which apps to allow Codex to access, you can stop actions at any time, and control whether we use screenshots for training.
- Features and capabilities:
  - MCP servers: computer-use (./Codex Computer Use.app/Contents/SharedSupport/SkyComputerUseClient.app/Contents/MacOS/SkyComputerUseClient)
  - Skills: 1 (computer-use)
  - Keywords: computer-use, desktop-control, macos, automation, accessibility
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/bundled-marketplaces/openai-bundled/plugins/computer-use`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/bundled-marketplaces/openai-bundled/plugins/computer-use/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/.codex/.tmp/bundled-marketplaces/openai-bundled/plugins/computer-use/.mcp.json`
- External links/attribution: homepage: https://openai.com/; author/developer: OpenAI

### `record-and-replay@openai-bundled`

- Display name: Record & Replay
- Marketplace: `openai-bundled`
- Status: installed, enabled
- Version: `1.0.857`
- Category: Productivity
- What it does: Record what I'm doing on my Mac and turn it into a Skill
- More detail: Record & Replay lets Codex record your actions on your Mac to create skills for more automated workflows. When you choose to start a recording, Codex will record your mouse clicks, text you type, and the content in windows you interact with until you stop it (up to 30 minutes). You can stop or cancel recording at any time, and cancelling will discard any existing recording. Avoid recording sensitive workflows.
- Features and capabilities:
  - MCP servers: event-stream (./Codex Computer Use.app/Contents/SharedSupport/SkyComputerUseClient.app/Contents/MacOS/SkyComputerUseClient)
  - Skills: 1 (record-and-replay)
  - Keywords: record-and-replay, macos, accessibility, recording, replay, skills, automation, record
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/bundled-marketplaces/openai-bundled/plugins/record-and-replay`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/bundled-marketplaces/openai-bundled/plugins/record-and-replay/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/.codex/.tmp/bundled-marketplaces/openai-bundled/plugins/record-and-replay/.mcp.json`
- External links/attribution: homepage: https://openai.com/; author/developer: OpenAI

### `alpaca@openai-curated`

- Display name: Alpaca
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Finance
- What it does: Stop watching the markets.
- More detail: Stop watching the markets. Turn your words into insights with Alpaca. Ask Codex real market questions and get live answers you can act on, including historical data, snapshots, quotes, and option chain information. Stock, options, and crypto market data embedded right into your conversation so you can turn analysis into automated actions. "How has AAPL's stock performed this quarter vs GOOG?" "Show me the SPY option...
- Features and capabilities:
  - App connectors: alpaca
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/alpaca`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/alpaca/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/alpaca/.app.json`
- External links/attribution: homepage: https://alpaca.markets/; repository: https://github.com/openai/plugins; author/developer: Alpaca

### `apollo@openai-curated`

- Display name: Apollo
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Business & Operations
- What it does: Prospecting and outbound execution in Apollo
- More detail: Apollo's MCP connector lets ChatGPT safely work inside your Apollo workspace to accelerate prospecting and outbound execution. Search and qualify accounts and contacts using Apollo's data, enrich records, summarize key context, and take action (e.g., create lists, log notes, generate tasks, and draft or assemble outbound using sequences) using your team's rules and permissions. Designed for speed and control...
- Features and capabilities:
  - App connectors: apollo
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/apollo`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/apollo/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/apollo/.app.json`
- External links/attribution: homepage: https://www.apollo.io; repository: https://github.com/openai/plugins; author/developer: Apollo

### `binance@openai-curated`

- Display name: Binance
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Finance
- What it does: Binance for Codex lets you access and explore Binance public, read-only market data using natural language.
- More detail: Binance for Codex lets you access and explore Binance public, read-only market data using natural language. Retrieve current and historical prices, order books, recent trades, candlesticks (klines), and exchange metadata across Spot, Futures, and Options. No authentication is required. This app does not access user accounts and does not support trading or transactions. Market data is provided "as is" from Binance's...
- Features and capabilities:
  - App connectors: binance
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/binance`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/binance/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/binance/.app.json`
- External links/attribution: homepage: https://www.binance.com; repository: https://github.com/openai/plugins; author/developer: Binance

### `biorender@openai-curated`

- Display name: BioRender
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Creativity
- What it does: BioRender helps scientists create professional figures in minutes.
- More detail: BioRender helps scientists create professional figures in minutes. Access thousands of scientifically accurate templates and icons directly in Codex to visualize protocols, pathways, molecular structures, and more. Brainstorm with your team, communicate research concepts, or build publication-ready figures for presentations, manuscripts, grant proposals, and posters.
- Features and capabilities:
  - App connectors: biorender
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/biorender`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/biorender/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/biorender/.app.json`
- External links/attribution: homepage: https://biorender.com/; repository: https://github.com/openai/plugins; author/developer: BioRender

### `build-ios-apps@openai-curated`

- Display name: Build iOS Apps
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Developer Tools
- What it does: Build, refine, and debug iOS apps with App Intents, SwiftUI, and Xcode workflows
- More detail: Use Build iOS Apps to design App Intents and App Shortcuts, build or refactor SwiftUI UI, render SwiftUI previews in the Codex in-app browser, adopt modern iOS patterns such as Liquid Glass, audit runtime performance, capture ETTrace profiles, investigate memory leaks, and debug apps on simulators with XcodeBuildMCP-backed workflows.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - MCP servers: xcodebuildmcp (npx)
  - Skills: 9 (ios-app-intents, ios-debugger-agent, ios-ettrace-performance, ios-memgraph-leaks, ios-simulator-browser, swiftui-liquid-glass, swiftui-performance-audit, swiftui-ui-patterns, +1 more)
  - Agents: 1 (openai)
  - Keywords: ios, swift, swiftui, app-intents, shortcuts, siri, spotlight, xcode, performance, debugging
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/build-ios-apps`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/build-ios-apps/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/.codex/.tmp/plugins/plugins/build-ios-apps/.mcp.json`; README/CODEX: `/Users/raghav/.codex/.tmp/plugins/plugins/build-ios-apps/README.md`
- External links/attribution: homepage: https://openai.com/; repository: https://github.com/openai/plugins; author/developer: OpenAI

### `build-macos-apps@openai-curated`

- Display name: Build macOS Apps
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Developer Tools
- What it does: Build, debug, instrument, and implement macOS apps with SwiftUI and AppKit guidance
- More detail: macOS development workflows for discovering local projects, building and running desktop apps, implementing native SwiftUI scenes, bridging into AppKit when necessary, adding lightweight Logger telemetry, triaging test failures, inspecting signing and entitlements, and debugging desktop-specific build or runtime errors.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - Skills: 11 (appkit-interop, build-run-debug, liquid-glass, packaging-notarization, signing-entitlements, swiftpm-macos, swiftui-patterns, telemetry, +3 more)
  - Commands: 3 (build-and-run-macos-app, fix-codesign-error, test-macos-app)
  - Agents: 1 (openai)
  - Keywords: macos, swift, swiftui, appkit, xcode, swiftpm, debugging, codesign, logging, telemetry
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/build-macos-apps`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/build-macos-apps/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/.codex/.tmp/plugins/plugins/build-macos-apps/README.md`
- External links/attribution: homepage: https://openai.com/; repository: https://github.com/openai/plugins; author/developer: OpenAI

### `build-web-apps@openai-curated`

- Display name: Build Web Apps
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Developer Tools
- What it does: Build frontend-focused web apps with generated assets, browser testing, payments, and databases
- More detail: Use Build Web Apps to create frontend application surfaces with Codex-generated visual assets, verify them with the Browser plugin and built-in app browser, compose shadcn/ui, wire Stripe payments, and design or tune Supabase/Postgres data flows.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - Skills: 6 (frontend-app-builder, frontend-testing-debugging, react-best-practices, shadcn-best-practices, stripe-best-practices, supabase-best-practices)
  - Agents: 1 (openai)
  - Keywords: build-web-apps, build, product-apps, frontend, image-generation, browser-testing, frontend-debugging, stripe, supabase, shadcn
- Install policy: `AVAILABLE`
- Auth policy: `ON_USE`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/build-web-apps`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/build-web-apps/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/.codex/.tmp/plugins/plugins/build-web-apps/README.md`
- External links/attribution: homepage: https://openai.com/; repository: https://github.com/openai/plugins; author/developer: OpenAI

### `build-web-data-visualization@openai-curated`

- Display name: Build Web Data Visualization
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Developer Tools
- What it does: Design, build, test, and export web data visualizations
- More detail: Use Build Web Data Visualization to choose, design, implement, test, and export browser charts, dashboards, maps, WebGL/Three.js scenes, Canvas/D3 visuals, Gantt charts, UML/software diagrams, scrollytelling, reports, PDFs, and slide decks. It emphasizes source-backed data, accessible responsive layouts, URL-shareable analysis state, and concept-first design for advanced visual stories.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - Skills: 18 (accessibility-and-inclusive-visualization, canvas2d-data-visualization, d3-data-visualization, dashboards-and-real-time-visualization, data-visualization, gantt-chart-visualization, geospatial-and-cartographic-visualization, grammar-of-graphics-and-declarative-visualization, +10 more)
  - Agents: 1 (openai)
  - Keywords: build-web-data-visualization, web-data-visualization, data-visualization, charts, dashboards, maps, geospatial, vega-lite, observable-plot, d3
- Install policy: `AVAILABLE`
- Auth policy: `ON_USE`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/build-web-data-visualization`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/build-web-data-visualization/.codex-plugin/plugin.json`
- External links/attribution: homepage: https://openai.com/; author/developer: OpenAI

### `canva@openai-curated`

- Display name: Canva
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Creativity
- What it does: Search, create, edit designs
- Features and capabilities:
  - App connectors: canva
  - Skills: 3 (canva-branded-presentation, canva-resize-for-all-social-media, canva-translate-design)
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/canva`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/canva/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/canva/.app.json`
- External links/attribution: homepage: https://www.canva.com; repository: https://github.com/openai/plugins; author/developer: Canva

### `circleci@openai-curated`

- Display name: CircleCI
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Developer Tools
- What it does: Build, test, and deploy any application
- More detail: Bring testing, deployment, and CI best practices into Codex
- Features and capabilities:
  - Interface capabilities: Interactive, Write
  - Skills: 4 (builds, chunk, cli, config)
  - Keywords: circleci, ci/cd, ci
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/circleci`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/circleci/.codex-plugin/plugin.json`
- External links/attribution: homepage: https://circleci.com; repository: https://github.com/circleci-public/skills; author/developer: CircleCI

### `coderabbit@openai-curated`

- Display name: CodeRabbit
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Developer Tools
- What it does: Run AI-powered code review for your current changes
- More detail: Run CodeRabbit review workflows in Codex to inspect diffs, surface actionable findings, and turn review output into follow-up fixes.
- Features and capabilities:
  - Interface capabilities: Interactive, Write
  - Skills: 1 (coderabbit-review)
  - Keywords: code-review, ai, coderabbit, codex
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/coderabbit`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/coderabbit/.codex-plugin/plugin.json`
- External links/attribution: homepage: https://docs.coderabbit.ai/cli/overview; repository: https://github.com/coderabbitai/codex-plugin; author/developer: CodeRabbit AI

### `codex-security@openai-curated`

- Display name: Codex Security
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Security
- What it does: Security scanning for your codebase
- More detail: Codex Security packages reusable workflows for security scans, analysis, validation, and investigation across code, diffs, and related artifacts.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - App connectors: linear, github, atlassian
  - MCP servers: codex-security (node)
  - Skills: 10 (attack-path-analysis, deep-security-scan, finding-discovery, fix-finding, security-diff-scan, security-scan, threat-model, track-findings, +2 more)
  - References: 8 (config-preflight, final-report, finding-detail-fields, sarif-adapter, scan-artifacts, scan-contract, shared-hard-rules, static-finding-assessment)
  - Scripts: 18 (config_preflight, filesystem_identity, finalize_scan_contract, finding_preview, generate_rank_input, report_projection, snapshot_sqlite, validate_report_format, +10 more)
  - Keywords: security, code-review, diff-review, appsec, threat-modeling
- Install policy: `AVAILABLE`
- Auth policy: `ON_USE`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/codex-security`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/codex-security/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/codex-security/.app.json`; MCP config: `/Users/raghav/.codex/.tmp/plugins/plugins/codex-security/.mcp.json`
- External links/attribution: homepage: https://developers.openai.com/codex/security; repository: https://github.com/openai/plugins; author/developer: OpenAI

### `daloopa@openai-curated`

- Display name: Daloopa
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Finance
- What it does: Institutional-grade financial analysis workflows.
- More detail: Use Daloopa MCP data to create cited company tearsheets, earnings reviews, valuation work, comp sheets, research notes, and banking-style analysis outputs.
- Features and capabilities:
  - Interface capabilities: Analysis, Research, File generation
  - App connectors: daloopa
  - Skills: 23 (build-model, bull-bear, capital-allocation, comp-sheet, comps, dcf, earnings-flash, earnings-prep, +15 more)
  - Scripts: 1 (package_chatgpt_skills)
  - Keywords: finance, equity-research, earnings, valuation, daloopa
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/daloopa`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/daloopa/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/daloopa/.app.json`; README/CODEX: `/Users/raghav/.codex/.tmp/plugins/plugins/daloopa/README.md`
- External links/attribution: homepage: https://daloopa.com; repository: https://github.com/daloopa/daloopa-plugin-codex; author/developer: Daloopa

### `dow-jones-factiva@openai-curated`

- Display name: Dow Jones Factiva
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Education & Research
- What it does: The Factiva Connector, enables authorized users to search Factiva's global news archive, including premium...
- More detail: The Factiva Connector, enables authorized users to search Factiva's global news archive, including premium Dow Jones sources, and incorporate insights from that content into their Codex responses. Users can research companies, industries, and markets and ground their answers in licensed content, complete with citations and direct links to original articles. A subscription to Factiva is required. Factiva content may...
- Features and capabilities:
  - App connectors: dow-jones-factiva
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/dow-jones-factiva`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/dow-jones-factiva/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/dow-jones-factiva/.app.json`
- External links/attribution: homepage: https://www.dowjones.com/business-intelligence/factiva/; repository: https://github.com/openai/plugins; author/developer: Factiva, Inc.

### `expo@openai-curated`

- Display name: Expo
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Developer Tools
- What it does: Build, deploy, upgrade, and debug Expo and React Native apps
- More detail: Official Expo-authored skills for building Expo Router UI, authoring API routes, configuring data fetching and styling, writing Expo native modules, creating dev clients, upgrading Expo SDKs, wiring Codex app Run actions, and deploying Expo apps with EAS workflows, builds, hosting, TestFlight, App Store, and Play Store guidance.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - Skills: 13 (building-native-ui, codex-expo-run-actions, expo-api-routes, expo-cicd-workflows, expo-deployment, expo-dev-client, expo-module, expo-tailwind-setup, +5 more)
  - Commands: 1 (setup-codex-run-actions)
  - Agents: 1 (openai)
  - Keywords: expo, react-native, expo-router, codex-run-actions, eas, mobile, ios, android, deployment, upgrades
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/expo`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/expo/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/.codex/.tmp/plugins/plugins/expo/README.md`
- External links/attribution: homepage: https://docs.expo.dev/skills/; repository: https://github.com/expo/skills/tree/main/plugins/expo; author/developer: Expo Team

### `figma@openai-curated`

- Display name: Figma
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Creativity
- What it does: Design-to-code workflows powered by the Figma integration
- More detail: Figma workflows for implementing designs in code, creating Code Connect templates for published Figma components, and generating project-specific design system rules for repeatable Figma-to-code work.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - App connectors: figma
  - MCP servers: figma (http)
  - Skills: 11 (figma-code-connect, figma-create-new-file, figma-generate-design, figma-generate-diagram, figma-generate-library, figma-implement-motion, figma-swiftui, figma-use, +3 more)
  - Commands: 4 (connect-figma-components, create-design-system-rules, implement-from-figma, review-design-parity)
  - Agents: 5 (design-parity-review-agent, design-system-rules-agent, figma-code-connect-agent, figma-implementation-agent, openai)
  - Scripts: 1 (post_write_figma_parity_check)
  - Keywords: figma, design-to-code, ui-implementation, code-connect, design-system
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/figma`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/figma/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/figma/.app.json`; MCP config: `/Users/raghav/.codex/.tmp/plugins/plugins/figma/.mcp.json`; README/CODEX: `/Users/raghav/.codex/.tmp/plugins/plugins/figma/README.md`
- External links/attribution: homepage: https://www.figma.com; repository: https://github.com/openai/plugins; author/developer: Figma

### `game-studio@openai-curated`

- Display name: Game Studio
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Developer Tools
- What it does: Design, prototype, and ship browser games
- More detail: Plan, prototype, and build browser games with guided workflows for gameplay systems, UI, asset pipelines, and playtesting across 2D and 3D projects.
- Features and capabilities:
  - Interface capabilities: Interactive, Write
  - Skills: 9 (game-playtest, game-studio, game-ui-frontend, phaser-2d-game, react-three-fiber-game, sprite-pipeline, three-webgl-game, web-3d-asset-pipeline, +1 more)
  - References: 16 (alternative-3d-engines, engine-selection, frontend-prompts, gltf-loading-starter, phaser-architecture, playtest-checklist, rapier-integration-starter, react-three-fiber-stack, +8 more)
  - Scripts: 3 (build_sprite_edit_canvas, normalize_sprite_strip, render_sprite_preview_sheet)
  - Keywords: games, phaser, threejs, react-three-fiber, gltf, rapier, webgl, sprites, playtest
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/game-studio`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/game-studio/.codex-plugin/plugin.json`
- External links/attribution: homepage: https://openai.com/; repository: https://github.com/openai/plugins; author/developer: OpenAI

### `gmail@openai-curated`

- Display name: Gmail
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Communication
- What it does: Read and manage Gmail
- More detail: Use Gmail to summarize inbox activity, draft replies, and organize email threads through the connected Gmail app.
- Features and capabilities:
  - Interface capabilities: Interactive, Write
  - App connectors: gmail
  - Skills: 2 (gmail, gmail-inbox-triage)
  - Keywords: gmail, email, google
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/gmail`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/gmail/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/gmail/.app.json`
- External links/attribution: homepage: https://workspace.google.com/products/gmail/; repository: https://github.com/openai/plugins; author/developer: OpenAI

### `google-calendar@openai-curated`

- Display name: Google Calendar
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Productivity
- What it does: Manage Google Calendar events and schedules
- More detail: Use Google Calendar to summarize a day, check availability, list calendars, and create, update, or delete events directly from task prompts.
- Features and capabilities:
  - Interface capabilities: Interactive, Write
  - App connectors: google-calendar
  - Skills: 5 (google-calendar, google-calendar-daily-brief, google-calendar-free-up-time, google-calendar-group-scheduler, google-calendar-meeting-prep)
  - Keywords: google-calendar, calendar, agenda, daily-brief, scheduling, productivity
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/google-calendar`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/google-calendar/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/google-calendar/.app.json`
- External links/attribution: homepage: https://workspace.google.com/products/calendar/; repository: https://github.com/openai/plugins; author/developer: OpenAI

### `google-drive@openai-curated`

- Display name: Google Drive
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Productivity
- What it does: Work across Drive, Docs, Sheets, and Slides
- More detail: Use Google Drive as one unified Google file plugin for search, file organization, sharing, and Google Docs, Google Sheets, and Google Slides workflows.
- Features and capabilities:
  - Interface capabilities: Interactive, Write
  - App connectors: google-drive
  - Skills: 5 (google-docs, google-drive, google-drive-comments, google-sheets, google-slides)
  - Keywords: google-drive, google-docs, google-sheets, google-slides, productivity
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/google-drive`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/google-drive/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/google-drive/.app.json`
- External links/attribution: homepage: https://workspace.google.com/products/drive/; repository: https://github.com/openai/plugins; author/developer: OpenAI

### `govtribe@openai-curated`

- Display name: GovTribe
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Education & Research
- What it does: Search government contracts, awards, and vendors directly from Codex.
- More detail: Search government contracts, awards, and vendors directly from Codex. GovTribe brings U.S. procurement intelligence into your AI workflow-find relevant opportunities across federal agencies; analyze vendor competition; explore teaming partners; and track agency spending patterns. Whether you're researching new markets, conducting competitive analysis, or preparing a proposal, get instant access to billions in public...
- Features and capabilities:
  - App connectors: govtribe
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/govtribe`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/govtribe/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/govtribe/.app.json`
- External links/attribution: homepage: https://govtribe.com/; repository: https://github.com/openai/plugins; author/developer: Government Executive Media Group LLC

### `hugging-face@openai-curated`

- Display name: Hugging Face
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Developer Tools
- What it does: Inspect models, datasets, Spaces, and research
- More detail: Connect to the Hugging Face Hub to explore Models and Datasets, access SDK Documentation and more. Manage Machine Learning Jobs and connect to thousands of AI applications via Spaces.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - App connectors: hugging-face
  - Skills: 11 (cli, community-evals, datasets, gradio, jobs, llm-trainer, paper-publisher, papers, +3 more)
  - Keywords: hugging-face, models, datasets, spaces, machine-learning
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/hugging-face`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/hugging-face/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/hugging-face/.app.json`
- External links/attribution: homepage: https://huggingface.co; repository: https://github.com/openai/plugins; author/developer: Hugging Face

### `hyperframes@openai-curated`

- Display name: HyperFrames by HeyGen
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Creativity
- What it does: Write HTML, render video
- More detail: Build videos from HTML with HyperFrames. Author compositions with HTML + CSS + GSAP, use the CLI for init/preview/render/transcribe/tts, install reusable registry blocks and components, follow the GSAP animation reference, and turn any website into a video with the 7-step capture-to-video pipeline.
- Features and capabilities:
  - Interface capabilities: Read, Write
  - Skills: 5 (gsap, hyperframes, hyperframes-cli, hyperframes-registry, website-to-hyperframes)
  - Keywords: hyperframes, video, html, gsap, animation, composition, rendering, captions, tts, audio-reactive
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/hyperframes`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/hyperframes/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/.codex/.tmp/plugins/plugins/hyperframes/README.md`
- External links/attribution: homepage: https://hyperframes.heygen.com; repository: https://github.com/heygen-com/hyperframes; author/developer: HeyGen

### `jam@openai-curated`

- Display name: Jam
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Productivity
- What it does: Screen record with context
- Features and capabilities:
  - App connectors: jam
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/jam`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/jam/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/jam/.app.json`
- External links/attribution: homepage: https://jam.dev; repository: https://github.com/openai/plugins; author/developer: Jam

### `life-science-research@openai-curated`

- Display name: Life Science Research
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Education & Research
- What it does: General life-sciences research with routing, evidence synthesis, and optional parallel subagent analysis
- More detail: Internal life-science research workflows that help Codex interpret a user's research question, normalize the relevant entities, choose the right skills, and synthesize evidence-backed answers across public resources. The plugin spans human genetics, functional genomics, expression, pathways, protein structure, chemistry, pharmacology, literature, clinical evidence, and public study discovery, with a research-router...
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - Skills: 50 (alphafold-skill, bgee-skill, bindingdb-skill, biobankjapan-phewas-skill, biorxiv-skill, biostudies-arrayexpress-skill, cbioportal-skill, cellxgene-skill, +42 more)
  - Keywords: life-science, research, bioinformatics, human-genetics, functional-genomics, transcriptomics, proteomics, metabolomics, clinical-research, drug-discovery
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/life-science-research`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/life-science-research/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/.codex/.tmp/plugins/plugins/life-science-research/README.md`
- External links/attribution: homepage: https://github.com/openai/openai/tree/master/plugins/life-science-research; repository: https://github.com/openai/openai/tree/master/plugins/life-science-research; author/developer: OpenAI

### `moody-s@openai-curated`

- Display name: Moody's
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Finance
- What it does: Credit ratings, research, entity intelligence, ownership, financials, and filings.
- More detail: Connect to Moody's GenAI-Ready Data through the enterprise MCP integration. Resolve covered entities, retrieve ratings and outlooks, analyze credit opinions, scorecards, upgrade/downgrade drivers, ESG considerations, ownership structures, subsidiaries, company profiles, financial statements, filings, earnings-call transcripts, news, peer sets, sector outlooks, and country-risk context, all within your workflow.
- Features and capabilities:
  - Interface capabilities: Entity resolution and firmographics, Credit ratings and rating history, Credit opinions, outlooks, and rating drivers, Upgrade and downgrade trigger analysis, Rating methodology and scorecard factors, ESG credit considerations, Ownership, beneficial owners, ultimate owners, and subsidiaries, Financial statements, key indicators, and ratios, Company filings search and summarization, Research document search, +5 more
  - App connectors: moody-s
  - Skills: 7 (moody-s-company-analysis, moody-s-earnings-brief, moody-s-explore-mcp, moody-s-issuer-brief, moody-s-peer-analysis, moody-s-rating-analysis, moody-s-sector-brief)
  - Keywords: moodys, credit, ratings, research, risk, entity-intelligence, ownership, beneficial-ownership, corporate-structure, subsidiaries
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/moody-s`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/moody-s/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/moody-s/.app.json`
- External links/attribution: homepage: https://www.moodys.com/web/en/us/genai/model-context-protocol.html; repository: https://github.com/openai/plugins; author/developer: Moody's

### `mt-newswires@openai-curated`

- Display name: MT Newswires
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Finance
- What it does: MT Newswires brings real-time global financial news directly into Codex - providing original, unbiased an...
- More detail: MT Newswires brings real-time global financial news directly into Codex - providing original, unbiased and comprehensive multi-asset class coverage of capital markets and economies in over 180 topics. Powered by a global newsroom trusted by the largest banks, brokerages, professional trading, wealth management and research applications globally, every story is built for AI - so you get answers grounded in live...
- Features and capabilities:
  - App connectors: mt-newswires
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/mt-newswires`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/mt-newswires/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/mt-newswires/.app.json`
- External links/attribution: homepage: https://www.mtnewswires.com; repository: https://github.com/openai/plugins; author/developer: MT Newswires

### `neon-postgres@openai-curated`

- Display name: Neon Postgres
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Developer Tools
- What it does: Manage Neon Serverless Postgres projects and databases
- More detail: Use the Neon Postgres plugin to create and manage Neon Serverless Postgres projects and databases. Includes the Neon MCP Server for project and database management, and the neon-postgres skill with guides on connection methods, branching, autoscaling, Neon Auth, and more.
- Features and capabilities:
  - Interface capabilities: Interactive, Write
  - App connectors: neon-postgres
  - Skills: 2 (neon-postgres, neon-postgres-egress-optimizer)
  - Keywords: neon, postgres, serverless, database, mcp, sql
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/neon-postgres`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/neon-postgres/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/neon-postgres/.app.json`
- External links/attribution: homepage: https://neon.com/docs/ai/neon-mcp-server; repository: https://github.com/openai/plugins; author/developer: Neon

### `netlify@openai-curated`

- Display name: Netlify
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Developer Tools
- What it does: Deploy projects and manage releases
- More detail: Use Netlify to inspect deployment state, manage sites, and pair the Netlify app with the curated deployment skill for preview and production workflows.
- Features and capabilities:
  - Interface capabilities: Interactive, Write
  - App connectors: netlify
  - Skills: 12 (netlify-ai-gateway, netlify-blobs, netlify-caching, netlify-cli-and-deploy, netlify-config, netlify-deploy, netlify-edge-functions, netlify-forms, +4 more)
  - Keywords: netlify, deployment, hosting, preview, static-sites
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/netlify`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/netlify/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/netlify/.app.json`
- External links/attribution: homepage: https://www.netlify.com; repository: https://github.com/openai/plugins; author/developer: Netlify

### `ngs-analysis@openai-curated`

- Display name: Life Sciences NGS Analysis
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Education & Research
- What it does: Guided NGS routing and local execution for sequencing analysis
- More detail: A guided intake, routing, and execution plugin for next-generation sequencing workflows. It helps Codex inspect local sequencing inputs, ask only the missing assay-specific questions, choose public or freely accessible runtime-installable packages where possible, check existing tool availability before any install, and execute supported local workflows with validation, logs, manifests, QC reports, and artifact...
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - Skills: 18 (ngs-amplicon-microbiome, ngs-analysis-router, ngs-atacseq-peaks-qc, ngs-bcl-to-fastq, ngs-bulk-rnaseq, ngs-bulk-rnaseq-counts-qc, ngs-bulk-rnaseq-differential-expression, ngs-chip-cutrun-peaks-qc, +10 more)
  - References: 6 (runtime-install-guidance, database-registry, intake-schema, pipeline-registry, reference-registry, run-envelope-schema)
  - Scripts: 23 (ngs_epigenomics_utils, ngs_planner_utils, ngs_preflight, ngs_reference_manager, ngs_resource_gate, ngs_run_utils, ngs_visualization_utils, run_amplicon_microbiome, +15 more)
  - Keywords: ngs, sequencing, bioinformatics, fastq, bcl, rnaseq, scrnaseq, variant-calling, atacseq, chipseq
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/ngs-analysis`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/ngs-analysis/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/.codex/.tmp/plugins/plugins/ngs-analysis/README.md`
- External links/attribution: homepage: https://openai.com/; repository: https://github.com/openai/openai; author/developer: OpenAI

### `notion@openai-curated`

- Display name: Notion
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Productivity
- What it does: Notion workflows for specs, research, meetings, and knowledge capture
- More detail: Notion workflows for turning specs into implementation plans, synthesizing research into structured documentation, preparing meeting materials with workspace context, and capturing decisions or conversations into durable knowledge pages.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - App connectors: notion
  - MCP servers: notion (http)
  - Skills: 4 (notion-knowledge-capture, notion-meeting-intelligence, notion-research-documentation, notion-spec-to-implementation)
  - Agents: 1 (openai)
  - Keywords: notion, documentation, research, meeting-prep, knowledge-management, planning
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/notion`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/notion/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/notion/.app.json`; MCP config: `/Users/raghav/.codex/.tmp/plugins/plugins/notion/.mcp.json`; README/CODEX: `/Users/raghav/.codex/.tmp/plugins/plugins/notion/README.md`
- External links/attribution: homepage: https://www.notion.so/; repository: https://github.com/openai/plugins; author/developer: OpenAI

### `openai-developers@openai-curated`

- Display name: OpenAI Developers
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Developer Tools
- What it does: Develop AI apps, agents, and ChatGPT Apps with OpenAI best practices
- More detail: Use OpenAI Developers in Codex to build AI applications, agents, and ChatGPT Apps with OpenAI docs, the OpenAI API, Apps SDK, and Agents SDK. Connect to the OpenAI Platform (platform.openai.com) and see your Codex-built apps work right out of the box with real OpenAI API keys. Run and locally deploy Agents SDK projects through the Deployment Manager, scaffold ChatGPT Apps, and prepare ChatGPT Apps submission...
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - App connectors: openai-platform
  - MCP servers: openai-api-key-local-confirmation (node)
  - Skills: 5 (agents-sdk, build-chatgpt-app, chatgpt-app-submission, openai-api-troubleshooting, openai-platform-api-key)
  - Scripts: 1 (openai-platform-api-key)
  - Keywords: openai-platform, api-key, agents-sdk, agents, chatgpt-apps, apps-sdk, mcp, submissions, codex
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/openai-developers`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/openai-developers/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/openai-developers/.app.json`; MCP config: `/Users/raghav/.codex/.tmp/plugins/plugins/openai-developers/.mcp.json`; README/CODEX: `/Users/raghav/.codex/.tmp/plugins/plugins/openai-developers/README.md`
- External links/attribution: homepage: https://platform.openai.com/; repository: https://github.com/openai/plugins/tree/main/plugins/openai-developers; author/developer: OpenAI

### `particl-market-research@openai-curated`

- Display name: Particl Market Research
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Education & Research
- What it does: Particl Market Research helps teams answer ecommerce research questions directly in Codex.
- More detail: Particl Market Research helps teams answer ecommerce research questions directly in Codex. It supports company discovery, product catalog research, product detail and variant analysis, market leader discovery, market trend analysis, marketing asset discovery, retail event tracking, sales timeseries, and product mix breakdowns. The app uses your authenticated Particl account and returns structured market intelligence...
- Features and capabilities:
  - App connectors: particl-market-research
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/particl-market-research`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/particl-market-research/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/particl-market-research/.app.json`
- External links/attribution: homepage: https://www.particl.com; repository: https://github.com/openai/plugins; author/developer: Particl

### `pitchbook@openai-curated`

- Display name: PitchBook
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Finance
- What it does: PitchBook provides structured access to private capital market data across companies, investors, funds, de...
- More detail: PitchBook provides structured access to private capital market data across companies, investors, funds, deals, limited partners, and people. It returns normalized fields such as firmographics, financing rounds, deal terms, ownership information, financials, fund performance metrics when available, LP commitments, investor portfolios, and team details with associated source metadata. Use this connector when a query...
- Features and capabilities:
  - App connectors: pitchbook
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/pitchbook`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/pitchbook/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/pitchbook/.app.json`
- External links/attribution: homepage: https://www.pitchbook.com; repository: https://github.com/openai/plugins; author/developer: PitchBook

### `plugin-eval@openai-curated`

- Display name: Plugin Eval
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Developer Tools
- What it does: Start from chat, then evaluate or benchmark locally
- More detail: Ask Codex to evaluate a plugin or skill, give you a full analysis of a named plugin such as game-studio, explain why it scored that way, show what to fix first, explain its token budget, measure real token usage, benchmark a plugin, or tell you what to run next. Plugin Eval keeps the path engineer-friendly: start with a natural chat request, then use the local `plugin-eval start` entrypoint or the routed workflow...
- Features and capabilities:
  - Interface capabilities: Interactive, Write
  - Skills: 5 (evaluate-plugin, evaluate-skill, improve-skill, metric-pack-designer, plugin-eval)
  - References: 6 (benchmark-harness, chat-first-workflows, evaluation-result-schema, metric-pack-manifest, observed-usage, technical-design)
  - Scripts: 1 (plugin-eval)
  - Keywords: codex, plugin, skill, evaluation, quality, budget
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/plugin-eval`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/plugin-eval/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/.codex/.tmp/plugins/plugins/plugin-eval/README.md`
- External links/attribution: homepage: https://openai.com/; repository: https://github.com/openai/plugins; author/developer: OpenAI Codex

### `ranked-ai@openai-curated`

- Display name: Ranked AI
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Productivity
- What it does: Ranked AI provides industry leading AI SEO & PPC software, with a fully managed service integrated into it.
- More detail: Ranked AI provides industry leading AI SEO & PPC software, with a fully managed service integrated into it. We combine AI with industry veterans that know how to help you rank your website on traditional & AI search. Manage your traditional & AI search keywords, audits, backlinks, reports and more with our integrated app.
- Features and capabilities:
  - App connectors: ranked-ai
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/ranked-ai`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/ranked-ai/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/ranked-ai/.app.json`
- External links/attribution: homepage: https://www.ranked.ai; repository: https://github.com/openai/plugins; author/developer: Ranked AI, LLC

### `razorpay@openai-curated`

- Display name: Razorpay
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Finance
- What it does: Connect your Razorpay account to access your payment data through conversation.
- More detail: Connect your Razorpay account to access your payment data through conversation. Ask Codex about your payments, orders, refunds, settlements, QR codes, payment links etc. Get instant answers to questions like "Show me today's payments," "What's the status of my recent settlements," or "Find refunds from last week." Perfect for merchants who want quick insights without navigating dashboards. View transaction details...
- Features and capabilities:
  - App connectors: razorpay
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/razorpay`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/razorpay/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/razorpay/.app.json`
- External links/attribution: homepage: https://razorpay.com/; repository: https://github.com/openai/plugins; author/developer: Razorpay Software Private Limited

### `remotion@openai-curated`

- Display name: Remotion
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Creativity
- What it does: Create motion graphics from prompts
- More detail: Build videos programmatically with Remotion and React. Covers animations, timing, audio, captions, 3D, transitions, charts, text effects, and more.
- Features and capabilities:
  - Interface capabilities: Read, Write
  - Skills: 1 (remotion)
  - Keywords: remotion, video, react, animation, composition, rendering, ffmpeg, captions, audio
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/remotion`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/remotion/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/.codex/.tmp/plugins/plugins/remotion/README.md`
- External links/attribution: homepage: https://remotion.dev; repository: https://github.com/remotion-dev/remotion; author/developer: Remotion

### `render@openai-curated`

- Display name: Render
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Developer Tools
- What it does: Deploy, debug, monitor, and migrate apps on Render.
- More detail: Provides skills for deploying apps with Blueprints, debugging failed deploys, monitoring service health and metrics, building Render Workflows, and migrating from Heroku.
- Features and capabilities:
  - Interface capabilities: Interactive, Write
  - Skills: 21 (render-background-workers, render-blueprints, render-cli, render-cron-jobs, render-debug, render-deploy, render-disks, render-docker, +13 more)
  - Agents: 1 (openai)
  - Scripts: 2 (sync-skills, validate-render-yaml)
  - Keywords: render, deploy, cloud, blueprint, monitoring, debugging
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/render`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/render/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/.codex/.tmp/plugins/plugins/render/README.md`
- External links/attribution: homepage: https://github.com/renderinc/render-codex-plugin; repository: https://github.com/renderinc/render-codex-plugin; author/developer: Render

### `scite@openai-curated`

- Display name: Scite
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Education & Research
- What it does: Scite delivers answers grounded in peer-reviewed research you can verify.
- More detail: Scite delivers answers grounded in peer-reviewed research you can verify. Each response is backed by real scientific sources, with citations that show how studies have been supported, disputed, or contextualized by other researchers. Behind the scenes, Scite's proprietary citation-based ranking model prioritizes trustworthy, validated research, helping users move beyond claims to evidence.
- Features and capabilities:
  - App connectors: scite
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/scite`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/scite/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/scite/.app.json`
- External links/attribution: homepage: https://www.scite.ai; repository: https://github.com/openai/plugins; author/developer: Scite

### `slack@openai-curated`

- Display name: Slack
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Communication
- What it does: Read and manage Slack
- More detail: Use Slack to summarize channels, draft messages, and organize team conversations through the connected Slack integration.
- Features and capabilities:
  - Interface capabilities: Interactive, Write
  - App connectors: slack
  - Skills: 6 (slack, slack-channel-summarization, slack-daily-digest, slack-notification-triage, slack-outgoing-message, slack-reply-drafting)
  - Keywords: slack, chat, collaboration
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/slack`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/slack/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/slack/.app.json`
- External links/attribution: homepage: https://slack.com/; repository: https://github.com/openai/plugins; author/developer: OpenAI

### `supabase@openai-curated`

- Display name: Supabase
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Developer Tools
- What it does: Supabase skills and MCP tools for Codex
- More detail: Official Supabase plugin for Codex. Includes agent skills for Supabase development and Postgres best practices, plus MCP server integration for managing your Supabase projects directly from Codex.
- Features and capabilities:
  - Interface capabilities: Read, Write
  - App connectors: supabase
  - Skills: 2 (supabase, supabase-postgres-best-practices)
  - Keywords: supabase, postgres, database, backend, mcp
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/supabase`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/supabase/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/supabase/.app.json`; README/CODEX: `/Users/raghav/.codex/.tmp/plugins/plugins/supabase/README.md`
- External links/attribution: homepage: https://supabase.com; repository: https://github.com/supabase-community/supabase-plugin; author/developer: Supabase

### `superpowers@openai-curated`

- Display name: Superpowers
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Developer Tools
- What it does: Planning, TDD, debugging, and delivery workflows for coding agents
- More detail: Use Superpowers to guide agent work through brainstorming, implementation planning, test-driven development, systematic debugging, parallel execution, code review, and finish-the-branch workflows.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - Skills: 14 (brainstorming, dispatching-parallel-agents, executing-plans, finishing-a-development-branch, receiving-code-review, requesting-code-review, subagent-driven-development, systematic-debugging, +6 more)
  - Keywords: brainstorming, subagent-driven-development, skills, planning, tdd, debugging, code-review, workflow
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/superpowers`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/superpowers/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/.codex/.tmp/plugins/plugins/superpowers/README.md`
- External links/attribution: homepage: https://github.com/obra/superpowers; repository: https://github.com/obra/superpowers; author/developer: Jesse Vincent

### `taxdown@openai-curated`

- Display name: Taxdown
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Finance
- What it does: TaxDown te ayuda a resolver dudas fiscales en Espana, tanto para particulares como autonomos: deducciones,...
- More detail: TaxDown te ayuda a resolver dudas fiscales en Espana, tanto para particulares como autonomos: deducciones, IRPF, renta y obligaciones fiscales, con respuestas claras y orientadas a tu caso.
- Features and capabilities:
  - App connectors: taxdown
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/taxdown`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/taxdown/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/taxdown/.app.json`
- External links/attribution: homepage: https://taxdown.es/; repository: https://github.com/openai/plugins; author/developer: TAXDOWN S.L.

### `test-android-apps@openai-curated`

- Display name: Test Android Apps
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Developer Tools
- What it does: Reproduce issues, inspect UI, and capture performance evidence from Android emulators
- More detail: Use Test Android Apps to build and install app variants, drive a booted Android emulator with adb input events, inspect UI trees, capture screenshots, collect logcat output, and gather Simpleperf, Perfetto, gfxinfo, or memory/leak evidence while reproducing issues.
- Features and capabilities:
  - Interface capabilities: Interactive, Read
  - Skills: 2 (android-emulator-qa, android-performance)
  - Agents: 1 (openai)
  - Keywords: android, adb, emulator, qa, logcat, uiautomator, performance, simpleperf, perfetto, memory
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/test-android-apps`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/test-android-apps/.codex-plugin/plugin.json`
- External links/attribution: homepage: https://openai.com/; repository: https://github.com/openai/plugins; author/developer: OpenAI

### `vercel@openai-curated`

- Display name: Vercel
- Marketplace: `openai-curated`
- Status: installed, enabled
- Version: `3fdeeb49`
- Category: Developer Tools
- What it does: Build and deploy web apps and agents
- More detail: Bring Vercel ecosystem guidance into Codex with curated skills and the connected Vercel app. Packages the upstream vercel/vercel-plugin skills, agents, and commands under the local `vercel` plugin identity for the Codex plugin marketplace.
- Features and capabilities:
  - Interface capabilities: Interactive, Write
  - App connectors: vercel
  - Skills: 48 (agent-browser, agent-browser-verify, ai-elements, ai-gateway, ai-generation-persistence, ai-sdk, auth, bootstrap, +40 more)
  - Commands: 6 (_conventions, bootstrap, deploy, env, marketplace, status)
  - Agents: 3 (ai-architect, deployment-expert, performance-optimizer)
  - Keywords: vercel, nextjs, ai-sdk, turborepo, turbopack, workflow, deployment, edge-functions, serverless, ai-gateway
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/vercel`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/vercel/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/vercel/.app.json`; README/CODEX: `/Users/raghav/.codex/.tmp/plugins/plugins/vercel/README.md`
- External links/attribution: homepage: https://vercel.com/; repository: https://github.com/vercel/vercel-plugin; author/developer: Vercel Labs

### `documents@openai-primary-runtime`

- Display name: Documents
- Marketplace: `openai-primary-runtime`
- Status: installed, enabled
- Version: `26.614.11602`
- Category: Productivity
- What it does: Create and edit document artifacts
- More detail: Create, edit, inspect, render, verify, and export DOCX document artifacts locally. Use Documents when the durable output or target is a document, doc, docs, Word file, Google Doc, Google Docs document, memo, report, or writing artifact.
- Features and capabilities:
  - Interface capabilities: Interactive, Write
  - Skills: 1 (documents)
  - Keywords: doc, docs, document, documents, word, google docs, google doc, memo, write, writing
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.cache/codex-runtimes/codex-primary-runtime/plugins/openai-primary-runtime/plugins/documents`
- Metadata files used: plugin manifest: `/Users/raghav/.cache/codex-runtimes/codex-primary-runtime/plugins/openai-primary-runtime/plugins/documents/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/.cache/codex-runtimes/codex-primary-runtime/plugins/openai-primary-runtime/plugins/documents/README.md`
- External links/attribution: homepage: https://openai.com/; repository: https://github.com/openai/openai; author/developer: OpenAI

### `pdf@openai-primary-runtime`

- Display name: PDF
- Marketplace: `openai-primary-runtime`
- Status: installed, enabled
- Version: `26.614.11602`
- Category: Productivity
- What it does: Read, create, and verify PDF files
- More detail: Read, create, inspect, render, verify, and extract content from PDF files locally. Use PDF when the durable output or target is a PDF file and visual layout fidelity matters.
- Features and capabilities:
  - Interface capabilities: Interactive, Write
  - Skills: 1 (pdf)
  - Keywords: pdf, pdfs, document, documents, report, render, review, extract, extraction, pypdf
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.cache/codex-runtimes/codex-primary-runtime/plugins/openai-primary-runtime/plugins/pdf`
- Metadata files used: plugin manifest: `/Users/raghav/.cache/codex-runtimes/codex-primary-runtime/plugins/openai-primary-runtime/plugins/pdf/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/.cache/codex-runtimes/codex-primary-runtime/plugins/openai-primary-runtime/plugins/pdf/README.md`
- External links/attribution: homepage: https://openai.com/; repository: https://github.com/openai/openai; author/developer: OpenAI

### `presentations@openai-primary-runtime`

- Display name: Presentations
- Marketplace: `openai-primary-runtime`
- Status: installed, enabled
- Version: `26.614.11602`
- Category: Productivity
- What it does: Create and edit presentations
- More detail: Create, edit, inspect, render, verify, and export presentation slide decks locally, including PPTX authoring and native Google Slides handoff guidance. Use Presentations when the durable output or target is a deck, slidedeck, presentation deck, slide deck, slides, PowerPoint, Google Slides, presentation, speaker notes, or visual deck repair.
- Features and capabilities:
  - Interface capabilities: Interactive, Write
  - Skills: 1 (presentations)
  - Keywords: slides, slide, deck, slidedeck, presentation, presentations, google slides, powerpoint, ppt, pptx
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.cache/codex-runtimes/codex-primary-runtime/plugins/openai-primary-runtime/plugins/presentations`
- Metadata files used: plugin manifest: `/Users/raghav/.cache/codex-runtimes/codex-primary-runtime/plugins/openai-primary-runtime/plugins/presentations/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/.cache/codex-runtimes/codex-primary-runtime/plugins/openai-primary-runtime/plugins/presentations/README.md`
- External links/attribution: homepage: https://openai.com/; repository: https://github.com/openai/openai; author/developer: OpenAI

### `spreadsheets@openai-primary-runtime`

- Display name: Spreadsheets
- Marketplace: `openai-primary-runtime`
- Status: installed, enabled
- Version: `26.614.11602`
- Category: Productivity
- What it does: Create and edit spreadsheet files
- More detail: Create, edit, inspect, render, verify, and export XLSX, CSV, and TSV spreadsheets locally, including local XLSX authoring for native Google Sheets handoff. Use Spreadsheets when the durable output or target is a spreadsheet, workbook, sheet, Google Sheet, or CSV file.
- Features and capabilities:
  - Interface capabilities: Interactive, Write
  - Skills: 1 (spreadsheets)
  - Keywords: sheet, sheets, google sheet, google sheets, spreadsheet, spreadsheets, excel, csv, xlsx, xls
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.cache/codex-runtimes/codex-primary-runtime/plugins/openai-primary-runtime/plugins/spreadsheets`
- Metadata files used: plugin manifest: `/Users/raghav/.cache/codex-runtimes/codex-primary-runtime/plugins/openai-primary-runtime/plugins/spreadsheets/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/.cache/codex-runtimes/codex-primary-runtime/plugins/openai-primary-runtime/plugins/spreadsheets/README.md`
- External links/attribution: homepage: https://openai.com/; repository: https://github.com/openai/openai; author/developer: OpenAI

### `template-creator@openai-primary-runtime`

- Display name: Template Creator
- Marketplace: `openai-primary-runtime`
- Status: installed, enabled
- Version: `26.623.12021`
- Category: Productivity
- What it does: Create or update personal artifact templates
- More detail: Turn DOCX, PPTX, and XLSX references into reusable personal template skills, or update an existing personal artifact template.
- Features and capabilities:
  - Interface capabilities: Interactive, Write
  - Skills: 1 (template-creator)
  - Keywords: artifact, template, document, presentation, spreadsheet
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.cache/codex-runtimes/codex-primary-runtime/plugins/openai-primary-runtime/plugins/template-creator`
- Metadata files used: plugin manifest: `/Users/raghav/.cache/codex-runtimes/codex-primary-runtime/plugins/openai-primary-runtime/plugins/template-creator/.codex-plugin/plugin.json`
- External links/attribution: homepage: https://openai.com/; repository: https://github.com/openai/openai; author/developer: OpenAI

## Installed But Disabled Plugins

### `claude-desktop-apify@local-codex-plugins`

- Display name: Codex Desktop Apify
- Marketplace: `local-codex-plugins`
- Status: installed, disabled
- Version: `0.9.17`
- Category: Productivity
- What it does: Extract data from any website with thousands of scrapers, crawlers, and automations on Apify Store.
- More detail: Extract data from any website with thousands of scrapers, crawlers, and automations on Apify Store. Codex uses this as a local MCP-backed plugin; authorize filesystem, browser, app, or account access only when the workflow needs it.
- Features and capabilities:
  - Interface capabilities: MCP, Desktop Extension
  - MCP servers: claude-desktop-apify (node)
  - Keywords: codex, mcp, desktop-extension, apify
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/claude-desktop-apify`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/claude-desktop-apify/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/claude-desktop-apify/.mcp.json`; README/CODEX: `/Users/raghav/plugins/claude-desktop-apify/README.md`
- External links/attribution: homepage: https://apify.com/; repository: https://github.com/apify/apify-mcp-server; author/developer: Apify Technologies s.r.o.

### `claude-desktop-commander@local-codex-plugins`

- Display name: Codex Desktop Commander
- Marketplace: `local-codex-plugins`
- Status: installed, disabled
- Version: `0.2.41`
- Category: Productivity
- What it does: Build, explore, and automate on your local machine with access to files and terminal.
- More detail: Build, explore, and automate on your local machine with access to files and terminal. Codex uses this as a local MCP-backed plugin; authorize filesystem, browser, app, or account access only when the workflow needs it.
- Features and capabilities:
  - Interface capabilities: MCP, Desktop Extension
  - MCP servers: claude-desktop-commander (node)
  - Keywords: codex, mcp, desktop-extension, commander
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/claude-desktop-commander`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/claude-desktop-commander/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/claude-desktop-commander/.mcp.json`; README/CODEX: `/Users/raghav/plugins/claude-desktop-commander/README.md`
- External links/attribution: homepage: https://github.com/wonderwhy-er/DesktopCommanderMCP; repository: https://github.com/wonderwhy-er/DesktopCommanderMCP.git; author/developer: Desktop Commander Team

### `claude-desktop-figma@local-codex-plugins`

- Display name: Codex Desktop Figma
- Marketplace: `local-codex-plugins`
- Status: installed, disabled
- Version: `1.0.8`
- Category: Productivity
- What it does: The Figma MCP server helps you pull in Figma context and generate high-quality code that aligns with your codebase and design intent.
- More detail: The Figma MCP server helps you pull in Figma context and generate high-quality code that aligns with your codebase and design intent. Codex uses this as a local MCP-backed plugin; authorize filesystem, browser, app, or account access only when the workflow needs it.
- Features and capabilities:
  - Interface capabilities: MCP, Desktop Extension
  - MCP servers: claude-desktop-figma (node)
  - Keywords: codex, mcp, desktop-extension, figma
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/claude-desktop-figma`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/claude-desktop-figma/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/claude-desktop-figma/.mcp.json`; README/CODEX: `/Users/raghav/plugins/claude-desktop-figma/README.md`
- External links/attribution: homepage: https://www.figma.com; repository: https://github.com/figma/dev-mode-mcp-server-dxt; author/developer: Figma

### `claude-desktop-filesystem@local-codex-plugins`

- Display name: Codex Desktop Filesystem
- Marketplace: `local-codex-plugins`
- Status: installed, disabled
- Version: `0.2.2`
- Category: Productivity
- What it does: Let Codex access your filesystem to read and write files.
- More detail: Let Codex access your filesystem to read and write files. Codex uses this as a local MCP-backed plugin; authorize filesystem, browser, app, or account access only when the workflow needs it.
- Features and capabilities:
  - Interface capabilities: MCP, Desktop Extension
  - MCP servers: claude-desktop-filesystem (node)
  - Keywords: codex, mcp, desktop-extension, filesystem
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/claude-desktop-filesystem`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/claude-desktop-filesystem/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/claude-desktop-filesystem/.mcp.json`; README/CODEX: `/Users/raghav/plugins/claude-desktop-filesystem/README.md`
- External links/attribution: homepage: https://www.claude.ai; repository: https://github.com/modelcontextprotocol/servers; author/developer: Anthropic

### `claude-desktop-osascript@local-codex-plugins`

- Display name: Codex Desktop AppleScript
- Marketplace: `local-codex-plugins`
- Status: installed, disabled
- Version: `0.0.1`
- Category: Productivity
- What it does: Execute AppleScript to automate tasks on macOS.
- More detail: Execute AppleScript to automate tasks on macOS. Codex uses this as a local MCP-backed plugin; authorize filesystem, browser, app, or account access only when the workflow needs it.
- Features and capabilities:
  - Interface capabilities: MCP, Desktop Extension
  - MCP servers: claude-desktop-osascript (node)
  - Keywords: codex, mcp, desktop-extension, osascript
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/claude-desktop-osascript`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/claude-desktop-osascript/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/claude-desktop-osascript/.mcp.json`; README/CODEX: `/Users/raghav/plugins/claude-desktop-osascript/README.md`
- External links/attribution: homepage: https://github.com/k6l3/osascript-dxt; repository: https://github.com/k6l3/osascript-dxt; author/developer: Kenneth Lien

### `claude-desktop-pdf-toolkit@local-codex-plugins`

- Display name: Codex Desktop PDF Toolkit
- Marketplace: `local-codex-plugins`
- Status: installed, disabled
- Version: `0.8.6`
- Category: Productivity
- What it does: A local PDF workflow for Codex: fill forms, sign/date PDFs, fetch PDF URLs, merge/split files, extract data, and analyze documents.
- More detail: A local PDF workflow for Codex: fill forms, sign/date PDFs, fetch PDF URLs, merge/split files, extract data, and analyze documents. Codex uses this as a local MCP-backed plugin; authorize filesystem, browser, app, or account access only when the workflow needs it.
- Features and capabilities:
  - Interface capabilities: MCP, Desktop Extension
  - MCP servers: claude-desktop-pdf-toolkit (node)
  - Keywords: codex, mcp, desktop-extension, pdf-toolkit
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/claude-desktop-pdf-toolkit`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/claude-desktop-pdf-toolkit/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/claude-desktop-pdf-toolkit/.mcp.json`; README/CODEX: `/Users/raghav/plugins/claude-desktop-pdf-toolkit/README.md`
- External links/attribution: homepage: https://github.com/Open-Document-Alliance/PDF-Tools; repository: https://github.com/Open-Document-Alliance/PDF-Tools; author/developer: Open Document Alliance

### `claude-desktop-pdf-viewer@local-codex-plugins`

- Display name: Codex Desktop PDF Viewer
- Marketplace: `local-codex-plugins`
- Status: installed, disabled
- Version: `1.7.0`
- Category: Productivity
- What it does: Read, annotate, and interact with PDF files - interactive viewer with search, navigation, annotations, form filling, and text extraction
- More detail: Read, annotate, and interact with PDF files - interactive viewer with search, navigation, annotations, form filling, and text extraction Codex uses this as a local MCP-backed plugin; authorize filesystem, browser, app, or account access only when the workflow needs it.
- Features and capabilities:
  - Interface capabilities: MCP, Desktop Extension
  - MCP servers: claude-desktop-pdf-viewer (node)
  - Keywords: codex, mcp, desktop-extension, pdf-viewer
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/claude-desktop-pdf-viewer`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/claude-desktop-pdf-viewer/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/claude-desktop-pdf-viewer/.mcp.json`; README/CODEX: `/Users/raghav/plugins/claude-desktop-pdf-viewer/README.md`
- External links/attribution: homepage: https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/pdf-server; repository: https://github.com/modelcontextprotocol/ext-apps; author/developer: Anthropic

### `claude-desktop-powerpoint@local-codex-plugins`

- Display name: Codex Desktop PowerPoint
- Marketplace: `local-codex-plugins`
- Status: installed, disabled
- Version: `0.4.2`
- Category: Productivity
- What it does: Control Microsoft PowerPoint with AppleScript automation
- More detail: Control Microsoft PowerPoint with AppleScript automation Codex uses this as a local MCP-backed plugin; authorize filesystem, browser, app, or account access only when the workflow needs it.
- Features and capabilities:
  - Interface capabilities: MCP, Desktop Extension
  - MCP servers: claude-desktop-powerpoint (node)
  - Keywords: codex, mcp, desktop-extension, powerpoint
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/claude-desktop-powerpoint`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/claude-desktop-powerpoint/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/claude-desktop-powerpoint/.mcp.json`; README/CODEX: `/Users/raghav/plugins/claude-desktop-powerpoint/README.md`
- External links/attribution: homepage: https://www.anthropic.com; repository: https://www.anthropic.com; author/developer: Anthropic

### `claude-desktop-word@local-codex-plugins`

- Display name: Codex Desktop Word
- Marketplace: `local-codex-plugins`
- Status: installed, disabled
- Version: `0.4.2`
- Category: Productivity
- What it does: Control Microsoft Word with AppleScript automation
- More detail: Control Microsoft Word with AppleScript automation Codex uses this as a local MCP-backed plugin; authorize filesystem, browser, app, or account access only when the workflow needs it.
- Features and capabilities:
  - Interface capabilities: MCP, Desktop Extension
  - MCP servers: claude-desktop-word (node)
  - Keywords: codex, mcp, desktop-extension, word
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/claude-desktop-word`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/claude-desktop-word/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/claude-desktop-word/.mcp.json`; README/CODEX: `/Users/raghav/plugins/claude-desktop-word/README.md`
- External links/attribution: homepage: https://www.anthropic.com; repository: https://www.anthropic.com; author/developer: Anthropic

### `fitness-hub-autopilot@local-codex-plugins`

- Display name: Fitness Hub Autopilot
- Marketplace: `local-codex-plugins`
- Status: installed, disabled
- Version: `0.1.0`
- Category: Developer Tools
- What it does: Repo-native plan/build/test/fix loops for Fitness Hub AI.
- More detail: A repo-local Codex plugin that adapts the strongest parts of Replit Agent's workflow to this Fitness Hub AI workspace: plan-first execution, incremental checkpoints, deterministic verification, real browser smoke plans, and repo-aware self-correction across the API, admin panel, and gym app artifacts.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - MCP servers: fitness-hub-autopilot (python3)
  - Skills: 3 (app-testing, verification-loop, skills)
  - Scripts: 3 (install_local_plugin, mcp_server, test_mcp_server)
  - Keywords: fitness-hub, autonomous, verification, replit-inspired, mcp, playwright
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/fitness-hub-autopilot`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/fitness-hub-autopilot/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/fitness-hub-autopilot/.mcp.json`; README/CODEX: `/Users/raghav/plugins/fitness-hub-autopilot/README.md`
- External links/attribution: homepage: https://openai.com; repository: https://openai.com; author/developer: Codex

### `internship-outreach-automation@local-codex-plugins`

- Display name: Internship Outreach Automation
- Marketplace: `local-codex-plugins`
- Status: installed, disabled
- Version: `0.2.0`
- Category: Productivity
- What it does: People-only, tracker-safe internship outreach
- More detail: Discovers or imports relevant companies and decision-makers, dedupes against the internship outreach tracker, blocks generic inboxes for named-person outreach, builds person-level research dossiers, scores ethical persuasion models, drafts high-quality outreach, attaches the canonical resume, and sends only checkpoint-approved emails through gws.
- Features and capabilities:
  - Interface capabilities: Write, Automation, Research
  - MCP servers: internship-outreach-automation (python3)
  - Skills: 1 (skills)
  - Scripts: 3 (mcp_server, outreach_engine, test_mcp_server)
  - Keywords: internship, outreach, gmail, research, automation, psychology, tracker, resume-attachment
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/internship-outreach-automation`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/internship-outreach-automation/.codex-plugin/plugin.json`; app connector: `/Users/raghav/plugins/internship-outreach-automation/.app.json`; MCP config: `/Users/raghav/plugins/internship-outreach-automation/.mcp.json`; README/CODEX: `/Users/raghav/plugins/internship-outreach-automation/README.md`
- External links/attribution: homepage: https://github.com/raghavbadhwar; repository: https://github.com/raghavbadhwar/internship-outreach-automation; author/developer: Raghav

### `pateintautomation@local-codex-plugins`

- Display name: Pateintautomation
- Marketplace: `local-codex-plugins`
- Status: installed, disabled
- Version: `0.1.0`
- Category: Productivity
- What it does: Google Form intake and appointment workflow plugin
- More detail: Packages a patient intake workflow with Google Apps Script templates, setup guidance, booking-state design, and Codex instructions for extending the automation safely.
- Features and capabilities:
  - Interface capabilities: Write, Automation
  - Skills: 1 (pateintautomation)
  - Keywords: google-forms, google-calendar, google-sheets, gmail, patient-intake, workflow
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/pateintautomation`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/pateintautomation/.codex-plugin/plugin.json`; app connector: `/Users/raghav/plugins/pateintautomation/.app.json`; MCP config: `/Users/raghav/plugins/pateintautomation/.mcp.json`; README/CODEX: `/Users/raghav/plugins/pateintautomation/README.md`
- External links/attribution: homepage: [TODO: https://example.com/pateintautomation]; repository: [TODO: https://example.com/pateintautomation]; author/developer: Raghav

### `cloudflare@openai-curated`

- Display name: Cloudflare
- Marketplace: `openai-curated`
- Status: installed, disabled
- Version: `3fdeeb49`
- Category: Developer Tools
- What it does: Cloudflare platform guidance with official MCP
- More detail: Bring Cloudflare platform guidance into Codex with curated skills for the broader platform, Wrangler CLI, and the Agents SDK, plus the official Cloudflare API MCP server for authenticated access to live account data and workflows across Workers, Pages, storage, AI, networking, security, and analytics services.
- Features and capabilities:
  - Interface capabilities: Interactive, Write
  - MCP servers: cloudflare-api (http)
  - Skills: 9 (agents-sdk, building-ai-agent-on-cloudflare, building-mcp-server-on-cloudflare, cloudflare, durable-objects, sandbox-sdk, web-perf, workers-best-practices, +1 more)
  - Commands: 2 (build-agent, build-mcp)
  - Keywords: cloudflare, workflow, deployment, edge-functions, edge, analytics, wrangler, agents-sdk, serverless, ai-gateway
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/cloudflare`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/cloudflare/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/.codex/.tmp/plugins/plugins/cloudflare/.mcp.json`; README/CODEX: `/Users/raghav/.codex/.tmp/plugins/plugins/cloudflare/README.md`
- External links/attribution: homepage: https://workers.cloudflare.com/; repository: https://github.com/openai/plugins; author/developer: Cloudflare

### `github@openai-curated`

- Display name: GitHub
- Marketplace: `openai-curated`
- Status: installed, disabled
- Version: `3fdeeb49`
- Category: Developer Tools
- What it does: Triage PRs, issues, CI, and publish flows
- More detail: Use GitHub to inspect repositories, review pull requests, address feedback, debug failing Actions checks, and prepare code changes for review through a connector-first workflow with targeted CLI fallbacks.
- Features and capabilities:
  - Interface capabilities: Interactive, Write
  - App connectors: github
  - MCP servers: github (http)
  - Skills: 4 (gh-address-comments, gh-fix-ci, github, yeet)
  - Keywords: github, pull-request, code-review, issues, ci, actions
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/github`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/github/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/github/.app.json`; MCP config: `/Users/raghav/.codex/.tmp/plugins/plugins/github/.mcp.json`; README/CODEX: `/Users/raghav/.codex/.tmp/plugins/plugins/github/README.md`
- External links/attribution: homepage: https://github.com/; repository: https://github.com/openai/plugins; author/developer: OpenAI

### `midpage@openai-curated`

- Display name: Midpage
- Marketplace: `openai-curated`
- Status: installed, disabled
- Version: `3fdeeb49`
- Category: Education & Research
- What it does: Legal research with cited case law
- More detail: Connect ChatGPT to a database of case law. With the Midpage App, ChatGPT can conduct complex legal research, review opinions, and craft high quality work product. Everything is hyperlinked to real sources for easy verification.
- Features and capabilities:
  - App connectors: midpage
  - Skills: 4 (cite-check, draft-brief, draft-long-form-memo, litigation-update-post)
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/midpage`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/midpage/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/midpage/.app.json`
- External links/attribution: homepage: https://www.midpage.ai; repository: https://github.com/openai/plugins; author/developer: Midpage

### `morningstar@openai-curated`

- Display name: Morningstar
- Marketplace: `openai-curated`
- Status: installed, disabled
- Version: `3fdeeb49`
- Category: Finance
- What it does: Screen, summarize, and compare funds with the Morningstar app.
- More detail: Bundled Morningstar fund workflows for Codex: production screening with normalization, fund returns screening, single-fund deep summaries, and side-by-side comparison for 2 to 4 funds. The plugin links to the reviewed Morningstar ChatGPT app for authenticated data access and includes explicit data-availability disclosures.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - App connectors: morningstar
  - Skills: 3 (fund-comparison, fund-screener, fund-summarizer)
  - Keywords: morningstar, funds, etf, research, screening
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/morningstar`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/morningstar/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/morningstar/.app.json`; README/CODEX: `/Users/raghav/.codex/.tmp/plugins/plugins/morningstar/README.md`
- External links/attribution: homepage: https://www.morningstar.com; repository: https://github.com/Morningstar/morningstar-plugins; author/developer: Morningstar

### `readwise@openai-curated`

- Display name: Readwise
- Marketplace: `openai-curated`
- Status: installed, disabled
- Version: `3fdeeb49`
- Category: Education & Research
- What it does: The official app for Readwise and Reader.
- More detail: The official app for Readwise and Reader. This app allows you to have Codex semantically search through all of your highlights, and any content saved to your Reader library. More than that, it can do basically anything you can do in Reader! Triage your inbox, organize your library, catch up on your feed, and much more -- just ask :)
- Features and capabilities:
  - App connectors: readwise
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/readwise`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/readwise/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/readwise/.app.json`
- External links/attribution: homepage: https://readwise.io; repository: https://github.com/openai/plugins; author/developer: Readwise Inc.

### `temporal@openai-curated`

- Display name: Temporal
- Marketplace: `openai-curated`
- Status: installed, disabled
- Version: `3fdeeb49`
- Category: Developer Tools
- What it does: Develop, run, and manage Temporal applications across the entire platform lifecycle
- More detail: Comprehensive guidance for working with Temporal - developing workflows, activities, and workers across Python, TypeScript, Go, and Java SDKs; using the Temporal CLI for local development and operations; running and managing self-hosted Temporal Server; and working with Temporal Cloud for production deployments.
- Features and capabilities:
  - Interface capabilities: Read, Write
  - Skills: 1 (temporal-developer)
  - Keywords: temporal, workflow, durable-execution, python, typescript, go, java, microservices, distributed-systems
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/temporal`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/temporal/.codex-plugin/plugin.json`
- External links/attribution: homepage: https://temporal.io/; repository: https://github.com/temporalio/codex-temporal-plugin; author/developer: Temporal

### `third-bridge@openai-curated`

- Display name: Third Bridge
- Marketplace: `openai-curated`
- Status: installed, disabled
- Version: `3fdeeb49`
- Category: Finance
- What it does: Seamlessly incorporate critical context and trusted insights from industry experts as part of your financia...
- More detail: Seamlessly incorporate critical context and trusted insights from industry experts as part of your financial and business analysis. Refocus on extracting high-quality, reliable information by querying Third Bridge's best-in-class substantial Library of expert content and data. Our MCP systematically and securely instructs Large Language Models (LLMs) to query insights from our database into their systems...
- Features and capabilities:
  - App connectors: third-bridge
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/third-bridge`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/third-bridge/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/third-bridge/.app.json`
- External links/attribution: homepage: https://www.thirdbridge.com; repository: https://github.com/openai/plugins; author/developer: Third Bridge Group

## Available But Not Installed Plugins

### `claude-desktop-chrome-control@local-codex-plugins`

- Display name: Codex Desktop Chrome Control
- Marketplace: `local-codex-plugins`
- Status: available, not installed
- Version: `0.1.6`
- Category: Productivity
- What it does: Control Google Chrome browser tabs, windows, and navigation
- More detail: Control Google Chrome browser tabs, windows, and navigation Codex uses this as a local MCP-backed plugin; authorize filesystem, browser, app, or account access only when the workflow needs it.
- Features and capabilities:
  - Interface capabilities: MCP, Desktop Extension
  - MCP servers: claude-desktop-chrome-control (node)
  - Keywords: codex, mcp, desktop-extension, chrome-control
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/plugins/claude-desktop-chrome-control`
- Metadata files used: plugin manifest: `/Users/raghav/plugins/claude-desktop-chrome-control/.codex-plugin/plugin.json`; MCP config: `/Users/raghav/plugins/claude-desktop-chrome-control/.mcp.json`; README/CODEX: `/Users/raghav/plugins/claude-desktop-chrome-control/README.md`
- External links/attribution: homepage: https://www.claude.ai; repository: https://www.claude.ai; author/developer: Anthropic

### `latex@openai-bundled`

- Display name: LaTeX
- Marketplace: `openai-bundled`
- Status: available, not installed
- Version: `0.2.4`
- Category: Education & Research
- What it does: Compile LaTeX with Tectonic or TeX Live
- More detail: LaTeX workflows for Codex that use bundled Tectonic first for simple projects, fall back to detected TeX Live or MacTeX for fuller projects, validate local LaTeX readiness, and optionally install a Codex-managed full TeX Live runtime only when no usable system installation is present.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - Skills: 3 (latex-compile, latex-doctor, texlive-runtime-installer)
  - Scripts: 7 (compile_latex, detect_tectonic, detect_texlive, install_texlive, latex_doctor, tectonic-path, build_private_bundle)
  - Keywords: latex, tectonic, texlive, mactex, latexmk, pdf, typesetting
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/bundled-marketplaces/openai-bundled/plugins/latex`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/bundled-marketplaces/openai-bundled/plugins/latex/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/.codex/.tmp/bundled-marketplaces/openai-bundled/plugins/latex/README.md`
- External links/attribution: homepage: https://github.com/openai/openai/tree/master/plugins/latex; repository: https://github.com/openai/openai/tree/master/plugins/latex; author/developer: OpenAI

### `actively@openai-curated`

- Display name: Actively
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Business & Operations
- What it does: Account agents for GTM intelligence
- More detail: Win more deals with Actively by directly accessing your always-on per account agents that help you drive the next best action. Actively's per-account agents are synthesizing across all of your internal context (ex. CRM data, call transcripts, emails) and external signals to drive actionable intelligence. Designed for SDRs, AEs, AMs, and revenue leaders who need deep, contextual account knowledge, from meeting prep...
- Features and capabilities:
  - App connectors: actively
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/actively`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/actively/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/actively/.app.json`
- External links/attribution: homepage: https://www.actively.ai; repository: https://github.com/openai/plugins; author/developer: Actively

### `aiera@openai-curated`

- Display name: Aiera
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.2`
- Category: Finance
- What it does: Institutional financial data and events
- More detail: Access institutional-grade financial data from Aiera, including live corporate events, filings, company publications, broker research, and much more.
- Features and capabilities:
  - App connectors: aiera
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/aiera`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/aiera/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/aiera/.app.json`
- External links/attribution: homepage: https://www.aiera.com; repository: https://github.com/openai/plugins; author/developer: Aiera

### `airtable@openai-curated`

- Display name: Airtable
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `0.1.3`
- Category: Productivity
- What it does: Database and operations layer for your agents.
- More detail: Airtable is the database and operations layer for your agents - whether running product, marketing, sales, ops, HR, or a custom business app. It combines structured data with multiplayer visual surfaces (grid, kanban, calendar, gallery, timeline) humans and agents share - plus sync integrations to Jira, Salesforce, Zendesk, Google Drive, Databricks, and the rest of your stack, all backed by enterprise governance...
- Features and capabilities:
  - Interface capabilities: Read, Write
  - App connectors: airtable
  - Skills: 3 (airtable-cli, airtable-filters, airtable-overview)
  - Agents: 1 (openai)
  - Keywords: airtable, database, relational-database, application-database, data-store, persistence, crud, product, product-ops, crm
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/airtable`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/airtable/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/airtable/.app.json`
- External links/attribution: homepage: https://www.airtable.com; repository: https://github.com/airtable/skills; author/developer: Airtable

### `alation@openai-curated`

- Display name: Alation
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Data & Analytics
- What it does: Trusted enterprise data context and governance
- More detail: Alation brings trusted enterprise data context into ChatGPT. Connect ChatGPT to Alation's enterprise data catalog, governance, and trusted business context so users can discover, understand, and use data with confidence. The Alation Intelligence Operating System (AIOS) helps AI ground responses in trusted enterprise context, including catalog metadata, governance policies, semantic definitions, lineage, data...
- Features and capabilities:
  - App connectors: alation
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/alation`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/alation/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/alation/.app.json`
- External links/attribution: homepage: https://www.alation.com; repository: https://github.com/openai/plugins; author/developer: Alation

### `amplitude@openai-curated`

- Display name: Amplitude
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.2`
- Category: Data & Analytics
- What it does: Product analytics and funnels
- Features and capabilities:
  - App connectors: amplitude
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/amplitude`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/amplitude/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/amplitude/.app.json`
- External links/attribution: repository: https://github.com/openai/plugins; author/developer: Amplitude

### `asana@openai-curated`

- Display name: Asana
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `0.1.4`
- Category: Productivity
- What it does: Read and manage Asana
- More detail: Work with your Asana tasks, subtasks, comments, due dates, and project details to create summaries, understand priorities, and prepare clear status updates.
- Features and capabilities:
  - Interface capabilities: Interactive, Write
  - App connectors: asana
  - Keywords: asana, tasks, project-management, productivity, collaboration, work-management
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/asana`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/asana/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/asana/.app.json`
- External links/attribution: homepage: https://asana.com; repository: https://github.com/openai/plugins; author/developer: Asana, Inc.

### `atlassian-rovo@openai-curated`

- Display name: Atlassian Rovo
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Productivity
- What it does: Manage Jira and Confluence fast
- Features and capabilities:
  - Interface capabilities: Interactive, Write
  - App connectors: atlassian-rovo
  - Skills: 5 (capture-tasks-from-meeting-notes, generate-status-report, search-company-knowledge, spec-to-backlog, triage-issue)
  - Agents: 1 (openai)
  - Keywords: atlassian
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/atlassian-rovo`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/atlassian-rovo/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/atlassian-rovo/.app.json`
- External links/attribution: homepage: https://www.atlassian.com; repository: https://github.com/openai/plugins; author/developer: Atlassian

### `attio@openai-curated`

- Display name: Attio
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Business & Operations
- What it does: Attio connects Codex directly to your CRM workspace, letting you manage customer relationships through na...
- More detail: Attio connects Codex directly to your CRM workspace, letting you manage customer relationships through natural conversation. Search and filter contacts, companies, and deals with flexible queries. Create, update, and organize records without switching between screens. Add notes, manage tasks, and track your sales pipeline-all through simple requests. Key capabilities: - Search records using powerful filters (find...
- Features and capabilities:
  - App connectors: attio
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/attio`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/attio/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/attio/.app.json`
- External links/attribution: homepage: https://attio.com; repository: https://github.com/openai/plugins; author/developer: Attio Ltd

### `base44@openai-curated`

- Display name: Base44
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3-beta.1`
- Category: Developer Tools
- What it does: Build and deploy Base44 full-stack apps from Codex
- More detail: Build and deploy Base44 full-stack apps with Codex. Includes CLI project management, JavaScript/TypeScript SDK development, and production troubleshooting skills.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - App connectors: base44
  - Skills: 3 (base44-cli, base44-sdk, base44-troubleshooter)
  - Keywords: base44, full-stack, sdk, cli, deployment, entities, backend-functions, javascript, typescript
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/base44`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/base44/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/base44/.app.json`
- External links/attribution: homepage: https://docs.base44.com; repository: https://github.com/base44/skills; author/developer: base44

### `boltz-api-cli@openai-curated`

- Display name: Boltz
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `0.1.1`
- Category: Education & Research
- What it does: Predict structures, screen molecules and proteins, and design binders
- More detail: Use Boltz from Codex for biomolecular modeling workflows: predict structure and binding for protein, RNA, DNA, and ligand complexes; rank small-molecule or protein libraries against targets; and design novel small molecules, peptides, antibodies, nanobodies, or custom protein binders with structures and confidence metrics.
- Features and capabilities:
  - Interface capabilities: Interactive, Write
  - Skills: 8 (boltz-check-status, boltz-cli-setup, boltz-protein-design, boltz-protein-screen, boltz-small-molecule-adme, boltz-small-molecule-design, boltz-small-molecule-screen, boltz-structure-and-binding)
  - Keywords: boltz, boltz-api, go-cli, computational-biology, protein-design, protein-screening, small-molecule-design, virtual-screening, structure-prediction, molecular-modeling
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/boltz-api-cli`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/boltz-api-cli/.codex-plugin/plugin.json`
- External links/attribution: homepage: https://boltz.bio; repository: https://github.com/boltz-bio/boltz-api-skills; author/developer: Boltz

### `box@openai-curated`

- Display name: Box
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `0.0.3`
- Category: Productivity
- What it does: Search and reference your documents
- More detail: Search and reference your documents in Box and work safely with Box content flows from Codex.
- Features and capabilities:
  - App connectors: box
  - Skills: 1 (box)
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/box`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/box/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/box/.app.json`
- External links/attribution: homepage: https://www.box.com/home; repository: https://github.com/openai/plugins; author/developer: OpenAI

### `brand24@openai-curated`

- Display name: Brand24
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Productivity
- What it does: The Brand24 app in Codex lets marketing and PR teams instantly explore brand mentions, sentiment, and med...
- More detail: The Brand24 app in Codex lets marketing and PR teams instantly explore brand mentions, sentiment, and media coverage using simple prompts. Summarize conversations, track brand reputation, analyze trends over time, and uncover key discussion sources across social media, news, blogs, and forums without leaving Codex. From spotting emerging issues to understanding audience perception and campaign impact, Codex...
- Features and capabilities:
  - App connectors: brand24
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/brand24`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/brand24/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/brand24/.app.json`
- External links/attribution: homepage: https://brand24.com; repository: https://github.com/openai/plugins; author/developer: Brand24 Global Inc.

### `brex@openai-curated`

- Display name: Brex
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Finance
- What it does: Connect Brex to Codex and review your company finances through natural conversation - at Codex speed.
- More detail: Connect Brex to Codex and review your company finances through natural conversation - at Codex speed. For finance teams: Analyze spend, detect anomalies, and run custom queries and reports instantly to accelerate decisions and do more with less. For employees: See how much you can spend, ask policy questions, check reimbursement status, manage travel, and more right in Codex. Access is role-aware by default...
- Features and capabilities:
  - App connectors: brex
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/brex`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/brex/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/brex/.app.json`
- External links/attribution: homepage: https://brex.com; repository: https://github.com/openai/plugins; author/developer: Brex Inc.

### `brighthire@openai-curated`

- Display name: BrightHire
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `0.1.1`
- Category: Productivity
- What it does: Search and analyze BrightHire interviews, candidates, calls, and hiring data.
- More detail: Use BrightHire from Codex to retrieve interview intelligence context, inspect calls and candidates, and support hiring workflows with governed access to BrightHire data.
- Features and capabilities:
  - Interface capabilities: Interactive, Read
  - App connectors: brighthire
  - Skills: 1 (brighthire)
  - Keywords: brighthire, interviews, hiring, recruiting, codex
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/brighthire`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/brighthire/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/brighthire/.app.json`
- External links/attribution: homepage: https://www.brighthire.com; repository: https://github.com/brighthire/brighthire-codex-plugin; author/developer: BrightHire

### `calendly@openai-curated`

- Display name: Calendly
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.2`
- Category: Productivity
- What it does: Scheduling links, availability, and bookings
- More detail: Bring Calendly into ChatGPT to take scheduling actions through simple prompts. Create and update event types, generate scheduling links, adjust availability, book or cancel meetings, and more - right in ChatGPT.
- Features and capabilities:
  - App connectors: calendly
  - Keywords: calendly, calendar, scheduling, meetings, availability, events
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/calendly`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/calendly/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/calendly/.app.json`
- External links/attribution: homepage: https://calendly.com; repository: https://github.com/openai/plugins; author/developer: Calendly

### `carta-crm@openai-curated`

- Display name: Carta CRM
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Business & Operations
- What it does: Carta CRM helps investment teams stay on top of deal flow by keeping deals, companies, and relationships in...
- More detail: Carta CRM helps investment teams stay on top of deal flow by keeping deals, companies, and relationships in one place. Track opportunities through each stage, capture meeting notes and key takeaways alongside the right deal or contact, and quickly find past context when you need it.
- Features and capabilities:
  - App connectors: carta-crm
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/carta-crm`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/carta-crm/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/carta-crm/.app.json`
- External links/attribution: homepage: https://carta.com; repository: https://github.com/openai/plugins; author/developer: Carta Inc.

### `catalyst-by-zoho@openai-curated`

- Display name: Catalyst by Zoho
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.1`
- Category: Developer Tools
- What it does: Use Catalyst by Zoho capabilities in Codex.
- More detail: Catalyst by Zoho plugin extends Codex with MCP-backed workflows and skills for building, managing, and operating Catalyst projects.
- Features and capabilities:
  - Interface capabilities: MCP, Read, Write
  - App connectors: catalyst-by-zoho
  - Skills: 1 (catalyst-by-zoho)
  - Keywords: zoho, catalyst, serverless, mcp, cloud
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/catalyst-by-zoho`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/catalyst-by-zoho/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/catalyst-by-zoho/.app.json`
- External links/attribution: homepage: https://catalyst.zoho.com/; repository: https://github.com/catalystbyzoho; author/developer: Catalyst by Zoho

### `cb-insights@openai-curated`

- Display name: CB Insights
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Finance
- What it does: Unleash Codex as your private markets research agent.
- More detail: Unleash Codex as your private markets research agent. Source companies, build market maps, draft investment memos, and monitor competitors - all powered by CB Insights' predictive intelligence. Tap into 11M+ double-validated company profiles, leading coverage of recent equity deals, proprietary taxonomies, unique scores, hidden signals, and over 20 years of bleeding edge technology research to identify and analyze...
- Features and capabilities:
  - App connectors: cb-insights
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/cb-insights`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/cb-insights/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/cb-insights/.app.json`
- External links/attribution: homepage: https://cbinsights.com; repository: https://github.com/openai/plugins; author/developer: CB Insights

### `channel99@openai-curated`

- Display name: Channel99
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Productivity
- What it does: Channel99 real time go to market intelligence connects Codex directly to Channel99's performance marketin...
- More detail: Channel99 real time go to market intelligence connects Codex directly to Channel99's performance marketing intelligence. giving AI assistants real-time access to unified B2B marketing data and insights.. Powered by Channel99's advanced attribution, account identification, and AI-driven analytics. The Channel99 connection enables natural-language queries that deliver accurate campaign performance, spend efficiency...
- Features and capabilities:
  - App connectors: channel99
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/channel99`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/channel99/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/channel99/.app.json`
- External links/attribution: homepage: https://www.channel99.com/; repository: https://github.com/openai/plugins; author/developer: Channel99 Inc.

### `chronograph-gp@openai-curated`

- Display name: Chronograph GP
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.0`
- Category: Finance
- What it does: Trusted portfolio data for private capital GP teams
- More detail: Chronograph GP provides portfolio monitoring, valuations, and analytics for private capital General Partner users. Query trusted portfolio data, analyze investments, surface company-level metrics, and access private markets portfolio data using natural language.
- Features and capabilities:
  - App connectors: chronograph-gp
  - Skills: 1 (chronograph-portfolio-company-one-pager)
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/chronograph-gp`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/chronograph-gp/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/chronograph-gp/.app.json`
- External links/attribution: homepage: https://www.chronograph.pe/; repository: https://github.com/openai/plugins; author/developer: Chronograph

### `chronograph-lp@openai-curated`

- Display name: Chronograph LP
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Finance
- What it does: Trusted portfolio data for private capital LP teams
- More detail: Chronograph LP provides portfolio monitoring and analytics for private capital Limited Partner users. Access trusted private markets portfolio data, from underlying portfolio companies and assets to funds, vehicles, commitments, and more.
- Features and capabilities:
  - App connectors: chronograph-lp
  - Skills: 3 (chronograph-cashflow-forecast, chronograph-gp-meeting-prep, chronograph-portfolio-company-one-pager)
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/chronograph-lp`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/chronograph-lp/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/chronograph-lp/.app.json`
- External links/attribution: homepage: https://www.chronograph.pe/; repository: https://github.com/openai/plugins; author/developer: Chronograph

### `circleback@openai-curated`

- Display name: Circleback
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.2`
- Category: Communication
- What it does: Circleback helps teams get the most out of every conversation with AI-powered meeting notes, action items,...
- More detail: Circleback helps teams get the most out of every conversation with AI-powered meeting notes, action items, automations, and search. Search and access data from in-person and online meetings you've recorded in Circleback, including meeting notes, action items, transcripts, people, and companies as well as your calendar and email.
- Features and capabilities:
  - App connectors: circleback
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/circleback`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/circleback/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/circleback/.app.json`
- External links/attribution: homepage: https://circleback.ai; repository: https://github.com/openai/plugins; author/developer: Circleback AI, Inc.

### `clay@openai-curated`

- Display name: Clay
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.2`
- Category: Business & Operations
- What it does: Find and engage prospects
- Features and capabilities:
  - App connectors: clay
  - Keywords: clay, gtm, sales, prospecting, lead-enrichment, contacts, accounts
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/clay`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/clay/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/clay/.app.json`
- External links/attribution: homepage: https://www.clay.com; repository: https://github.com/openai/plugins; author/developer: Clay

### `clickup@openai-curated`

- Display name: ClickUp
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Productivity
- What it does: Turn Codex into your ClickUp command center.
- More detail: Turn Codex into your ClickUp command center. Ask anything, find everything, take action - without breaking your flow. Deep workspace search: Ask questions naturally, get precise answers from across all your work Action in the same breath: Find, create, update, and manage work in Codex Zero context switching: Go from question to answer to action without leaving the conversation
- Features and capabilities:
  - App connectors: clickup
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/clickup`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/clickup/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/clickup/.app.json`
- External links/attribution: repository: https://github.com/openai/plugins; author/developer: ClickUp

### `close@openai-curated`

- Display name: Close
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Business & Operations
- What it does: Reference and update Close CRM
- More detail: With Close's ChatGPT app, ChatGPT will be able to reference and update Close for any task you can dream up. Whether you need to generate a custom report, research and create a new lead list, get a summary of recent interactions with a customer, or create new Workflows - all you have to do is ask ChatGPT to take care of it for you.
- Features and capabilities:
  - App connectors: close
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/close`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/close/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/close/.app.json`
- External links/attribution: homepage: https://www.close.com; repository: https://github.com/openai/plugins; author/developer: Close

### `cloudinary@openai-curated`

- Display name: Cloudinary
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.2`
- Category: Developer Tools
- What it does: Manage, search, and transform your Cloudinary media library - directly from Codex.
- More detail: Manage, search, and transform your Cloudinary media library - directly from Codex. The Cloudinary app connects your Cloudinary account to Codex, giving you full control over your visual assets through natural language. Upload, organize, tag, transform, and analyze images or videos without leaving the chat. What You Can Do - Upload assets from URLs, local files, or base64 data - automatically analyze, tag, or...
- Features and capabilities:
  - App connectors: cloudinary
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/cloudinary`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/cloudinary/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/cloudinary/.app.json`
- External links/attribution: homepage: https://cloudinary.com/; repository: https://github.com/openai/plugins; author/developer: Cloudinary

### `cogedim@openai-curated`

- Display name: Cogedim
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Other
- What it does: Cogedim is one of France's leading real estate developers.
- More detail: Cogedim is one of France's leading real estate developers. A specialist in off-plan sales (VEFA) for over 60 years, Cogedim guides you every step of the way, from defining your needs to handing over the keys.
- Features and capabilities:
  - App connectors: cogedim
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/cogedim`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/cogedim/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/cogedim/.app.json`
- External links/attribution: homepage: https://www.cogedim.com; repository: https://github.com/openai/plugins; author/developer: ALTAREA PROMOTION MANAGEMENT

### `common-room@openai-curated`

- Display name: Common Room
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Productivity
- What it does: Embed complete buyer intelligence directly within Codex.
- More detail: Embed complete buyer intelligence directly within Codex. Research accounts and contacts, surface buying signals, and browse activity history - all through natural language. Build prospect lists of net-new companies by industry, size, tech stack, or location. Filter and sort contacts by segment, role, lead score, or website visits. Every result is grounded in real context, real prioritization, and real revenue...
- Features and capabilities:
  - App connectors: common-room
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/common-room`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/common-room/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/common-room/.app.json`
- External links/attribution: homepage: https://commonroom.io; repository: https://github.com/openai/plugins; author/developer: Common Room

### `conductor@openai-curated`

- Display name: Conductor
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Productivity
- What it does: The Conductor MCP server retrieves proprietary performance metrics regarding a brand's visibility, sentimen...
- More detail: The Conductor MCP server retrieves proprietary performance metrics regarding a brand's visibility, sentiment, and rankings on both traditional search engines (e.g., Google) and Generative AI platforms (e.g., Codex, Gemini, Copilot, Perplexity or Google AI Overview). Invoke this tool when users request share of voice, competitive benchmarking, or AI search insights, specifically looking for citations, brand mentions...
- Features and capabilities:
  - App connectors: conductor
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/conductor`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/conductor/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/conductor/.app.json`
- External links/attribution: homepage: https://www.conductor.com/; repository: https://github.com/openai/plugins; author/developer: Conductor Inc.

### `convex@openai-curated`

- Display name: Convex
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `0.1.2`
- Category: Developer Tools
- What it does: Add a backend to JS/TS apps.
- More detail: Use the reviewed Convex ChatGPT app from Codex whenever a project needs a backend: database schema, reactive queries, mutations, server functions, auth-aware data access, real-time features, file storage, scheduled jobs, mobile/web app backends, or production scaling guidance. Convex helps coding agents choose backend primitives that are type-safe, reactive, and suitable for full-stack JavaScript and TypeScript apps.
- Features and capabilities:
  - Interface capabilities: Backend setup, Database schema, Reactive queries, Server functions, Auth-aware data access, Realtime apps, Scheduled jobs, File storage, Mobile backends, Scaling guidance
  - App connectors: convex
  - Keywords: convex, backend, database, realtime, reactive, websocket, auth, storage, scheduler, cron
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/convex`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/convex/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/convex/.app.json`; README/CODEX: `/Users/raghav/.codex/.tmp/plugins/plugins/convex/README.md`
- External links/attribution: homepage: https://chatgpt.com/apps/convex/asdk_app_6a0faef988b48191b843bac5cd170a9e; repository: https://github.com/get-convex/convex-codex-plugin; author/developer: Convex, Inc.

### `coupler-io@openai-curated`

- Display name: Coupler.io
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.2`
- Category: Data & Analytics
- What it does: Analyze multi-channel marketing, financial, sales, e-commerce, and other business data within Codex by co...
- More detail: Analyze multi-channel marketing, financial, sales, e-commerce, and other business data within Codex by connecting to your Coupler.io data flows. Fetch and transform raw data from platforms like Google Ads, Facebook, HubSpot, and Salesforce into actionable intelligence for smarter, faster decision-making with accurate, up-to-date business information. You can use the Coupler.io connector to: 1. Analyze customer...
- Features and capabilities:
  - App connectors: coupler-io
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/coupler-io`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/coupler-io/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/coupler-io/.app.json`
- External links/attribution: homepage: https://www.coupler.io/; repository: https://github.com/openai/plugins; author/developer: Coupler.io

### `coveo@openai-curated`

- Display name: Coveo
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.2`
- Category: Productivity
- What it does: Search your enterprise content
- Features and capabilities:
  - App connectors: coveo
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/coveo`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/coveo/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/coveo/.app.json`
- External links/attribution: homepage: https://www.coveo.com; repository: https://github.com/openai/plugins; author/developer: Coveo

### `cube@openai-curated`

- Display name: Cube
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Finance
- What it does: With the Cube MCP Server, you can: - Query live Cube data from actuals, budgets, forecasts, variances, and...
- More detail: With the Cube MCP Server, you can: - Query live Cube data from actuals, budgets, forecasts, variances, and more - Ask an AI to generate board decks, run variance analysis, or build financial summaries using your real Cube data - Drill into transaction-level detail and dimension breakdowns directly from an AI chat - Maintain full security: Cube's role-based access control (RBAC) security model enforces your user...
- Features and capabilities:
  - App connectors: cube
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/cube`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/cube/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/cube/.app.json`
- External links/attribution: homepage: https://www.cubesoftware.com/; repository: https://github.com/openai/plugins; author/developer: Cube

### `datadog@openai-curated`

- Display name: Datadog (Preview)
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `0.1.2`
- Category: Developer Tools
- What it does: Investigate logs, metrics, traces, and incidents
- More detail: Analyze, investigate, and act on your Datadog telemetry directly from Codex using natural language. Ask questions about your production applications, identify, visualize, and remediate issues in your critical services. Run agentic loops to ensure you continue to maintain good observability and service management posture.
- Features and capabilities:
  - Interface capabilities: Interactive, Writes
  - App connectors: datadog
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/datadog`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/datadog/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/datadog/.app.json`
- External links/attribution: homepage: https://www.datadoghq.com/; repository: https://github.com/openai/plugins; author/developer: Datadog

### `datasite@openai-curated`

- Display name: Datasite
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Productivity
- What it does: Manage secure M&A data rooms
- More detail: Connect ChatGPT to your Datasite virtual data room - the secure workspace where thousands of M&A deals are facilitated annually. Set up folder structures, invite users, search documents, track buyer Q&A, and audit data room readiness, all through natural language. No workflow interruptions. No security trade-offs. Built for advisors, bankers, and corporate development teams - backed by the enterprise security and...
- Features and capabilities:
  - App connectors: datasite
  - Skills: 8 (bulk-qa-answers, document-quality-check, gap-analysis, irl-tracker, launch-readiness-orchestrator, risk-analysis-audit, smart-file-renaming, vdr-index-setup)
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/datasite`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/datasite/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/datasite/.app.json`
- External links/attribution: homepage: https://www.datasite.com; repository: https://github.com/openai/plugins; author/developer: Datasite

### `deepnote@openai-curated`

- Display name: Deepnote
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `0.1.5`
- Category: Data & Analytics
- What it does: Explore data and automate analysis in Deepnote
- More detail: Deepnote gives teams a collaborative workspace for notebooks, SQL, apps, and data workflows. This plugin helps OpenAI work with connected Deepnote projects, inspect and run notebooks, and turn workspace context into useful analysis and shareable results.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - App connectors: deepnote
  - Skills: 5 (deepnote, deepnote-data-execution, deepnote-links, deepnote-notebook-editing, deepnote-notebooks)
  - Keywords: deepnote, chatgpt-app, openai, notebooks, data, analytics
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/deepnote`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/deepnote/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/deepnote/.app.json`; README/CODEX: `/Users/raghav/.codex/.tmp/plugins/plugins/deepnote/README.md`
- External links/attribution: homepage: https://deepnote.com; repository: https://github.com/openai/plugins/tree/main/plugins/deepnote; author/developer: Deepnote

### `demandbase@openai-curated`

- Display name: Demandbase
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Business & Operations
- What it does: Demandbase integration with Codex gives sales, marketing, and GTM teams seamless access to rich B2B data...
- More detail: Demandbase integration with Codex gives sales, marketing, and GTM teams seamless access to rich B2B data directly inside Codex for easier account targeting and engagement. This app connects Codex to Demandbase via a secure MCP connection, letting you access both first and third party data: Third-Party Data (3P): Search and retrieve industry-leading company and contact data from Demandbase, including firmographics...
- Features and capabilities:
  - App connectors: demandbase
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/demandbase`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/demandbase/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/demandbase/.app.json`
- External links/attribution: homepage: https://www.demandbase.com; repository: https://github.com/openai/plugins; author/developer: Demandbase Inc

### `digitalocean@openai-curated`

- Display name: DigitalOcean
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `0.2.2`
- Category: Developer Tools
- What it does: Provision a droplet as a Codex workspace
- More detail: Provision and configure a DigitalOcean droplet as a remote Codex SSH workspace using the connected DigitalOcean app.
- Features and capabilities:
  - Interface capabilities: Interactive, Write
  - App connectors: digitalocean
  - Skills: 1 (provision-droplet)
  - Keywords: digitalocean, droplet, virtual-machine, remote-session
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/digitalocean`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/digitalocean/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/digitalocean/.app.json`; README/CODEX: `/Users/raghav/.codex/.tmp/plugins/plugins/digitalocean/README.md`
- External links/attribution: homepage: https://www.digitalocean.com/; repository: https://github.com/digitalocean/CodexPlugin; author/developer: DigitalOcean

### `dnb-finance-analytics@openai-curated`

- Display name: D&B Finance Analytics
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.2`
- Category: Finance
- What it does: Commercial credit origination and risk workflows
- More detail: Power commercial credit origination and portfolio management workflows with D&B Finance Analytics embedded AI decisioning layer. Dun & Bradstreet connects the D&B Commercial Graph with proprietary customer data and credit policies to help evaluate applications, set credit limits, and uncover portfolio risk and opportunity.
- Features and capabilities:
  - Interface capabilities: Portfolio search, filtering, aggregation, and sorting, Company search by name or D-U-N-S number, Detailed company credit-risk reports, Company ownership and linkage trees, Credit application decisioning, Portfolio folder creation, movement, and organization, Server-provided Finance Analytics skill discovery
  - App connectors: dnb-finance-analytics
  - Skills: 1 (fa-jobs-to-be-done)
  - Keywords: dnb, dun-bradstreet, finance-analytics, business-identity, company-data, firmographics, credit-risk, corporate-linkage, portfolio-management, credit-origination
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/dnb-finance-analytics`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/dnb-finance-analytics/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/dnb-finance-analytics/.app.json`
- External links/attribution: homepage: https://www.dnb.com/; repository: https://github.com/openai/plugins; author/developer: Dun & Bradstreet

### `docket@openai-curated`

- Display name: Docket
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Productivity
- What it does: Docket AI makes your sales knowledge your instant superpower.
- More detail: Docket AI makes your sales knowledge your instant superpower. Sales reps get accurate, on-demand answers to product, competitive, technical, and customer questions-pulled directly from your unified Sales Knowledge Lake(TM). Guided by verified company intel, reps handle objections confidently, uncover prospect details, and craft personalised responses on the spot.
- Features and capabilities:
  - App connectors: docket
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/docket`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/docket/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/docket/.app.json`
- External links/attribution: homepage: https://www.docket.io/; repository: https://github.com/openai/plugins; author/developer: Docket AI

### `docusign@openai-curated`

- Display name: Docusign
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Productivity
- What it does: Automate contract creation and insights
- More detail: Simplify contract management with intelligent automation powered by Docusign. Go beyond simple execution to make complex agreement workflows effortless. Use natural language to create and send a contract, instantly surface insights like renewal dates and key obligations, and automate workflows that keep your business moving faster and with less friction.
- Features and capabilities:
  - App connectors: docusign
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/docusign`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/docusign/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/docusign/.app.json`
- External links/attribution: homepage: https://www.docusign.com; repository: https://github.com/openai/plugins; author/developer: Docusign

### `domotz-preview@openai-curated`

- Display name: Domotz (Preview)
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Productivity
- What it does: Monitor and manage your network infrastructure through natural language.
- More detail: Monitor and manage your network infrastructure through natural language. Query devices, check alerts, inspect metrics, manage configurations, and control power across all your sites. Requires a Domotz account enabled to the MCP Preview program.
- Features and capabilities:
  - App connectors: domotz-preview
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/domotz-preview`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/domotz-preview/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/domotz-preview/.app.json`
- External links/attribution: homepage: https://www.domotz.com; repository: https://github.com/openai/plugins; author/developer: Domotz

### `dovetail@openai-curated`

- Display name: Dovetail
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Productivity
- What it does: Connect Dovetail inside Codex to turn customer feedback into decisions without leaving your conversation.
- More detail: Connect Dovetail inside Codex to turn customer feedback into decisions without leaving your conversation. Search your Dovetail workspace for relevant projects, notes, docs, and themes, and get results back instantly. Ask things like "Summarize top friction points impacting enterprise renewal conversations" to surface evidence in seconds.
- Features and capabilities:
  - App connectors: dovetail
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/dovetail`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/dovetail/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/dovetail/.app.json`
- External links/attribution: homepage: https://dovetail.com; repository: https://github.com/openai/plugins; author/developer: Dovetail

### `egnyte@openai-curated`

- Display name: Egnyte
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Productivity
- What it does: Work with documents and files stored in Egnyte directly from Codex.
- More detail: Work with documents and files stored in Egnyte directly from Codex. Search across folders, retrieve relevant files, and extract key information to answer questions or generate summaries. Quickly surface insights from contracts, reports, and internal documents. Combine information from multiple files to create concise summaries, stakeholder updates, or draft written content grounded in your team's internal materials.
- Features and capabilities:
  - App connectors: egnyte
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/egnyte`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/egnyte/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/egnyte/.app.json`
- External links/attribution: homepage: https://www.egnyte.com; repository: https://github.com/openai/plugins; author/developer: Egnyte Inc

### `factset@openai-curated`

- Display name: FactSet
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.2`
- Category: Finance
- What it does: Connect financial data, analytics, and workflows
- More detail: FactSet Model Context Protocol (MCP) is an open, API-based standard designed to seamlessly connect financial data, analytics models, and applications across different platforms. By enabling smooth interoperability, MCP empowers investment teams to easily share insights, streamline workflows, and enhance collaboration regardless of their tools or technology stacks. With MCP, firms can integrate new solutions...
- Features and capabilities:
  - App connectors: factset
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/factset`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/factset/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/factset/.app.json`
- External links/attribution: homepage: https://www.factset.com; repository: https://github.com/openai/plugins; author/developer: FactSet

### `fal@openai-curated`

- Display name: Fal
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Creativity
- What it does: Generate and manage media with Fal models
- More detail: Fal brings image, video, audio, 3D, training, and editing workflows into Codex through an OpenAI app connector plus focused production skills for model recommendation, schema inspection, pricing, async jobs, file uploads, and media generation.
- Features and capabilities:
  - App connectors: fal
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/fal`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/fal/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/fal/.app.json`
- External links/attribution: homepage: https://fal.ai; repository: https://github.com/openai/plugins; author/developer: Fal

### `finn@openai-curated`

- Display name: FINN
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.4`
- Category: Travel
- What it does: A FINN car subscription is a flexible way to stay mobile anytime - without long-term commitments like buyin...
- More detail: A FINN car subscription is a flexible way to stay mobile anytime - without long-term commitments like buying or leasing a car. With a fixed monthly rate that already includes insurance, maintenance, registration, and even CO2 offsetting, the car subscription offers full transparency and convenience. Best of all, you can book online in just a few minutes, and your new car will be delivered straight to your doorstep...
- Features and capabilities:
  - App connectors: finn
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/finn`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/finn/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/finn/.app.json`
- External links/attribution: homepage: https://www.finn.com/de-DE; repository: https://github.com/openai/plugins; author/developer: FINN GmbH

### `fireflies@openai-curated`

- Display name: Fireflies
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.2`
- Category: Communication
- What it does: The Fireflies app brings your meetings and knowledge directly into Codex.
- More detail: The Fireflies app brings your meetings and knowledge directly into Codex. Analyze any conversation-sales, customer success, product, recruiting-for insights, action items, and sentiment. Track feature requests and pain points, update CRMs or systems of record, and instantly retrieve context from your organization's meetings. With Fireflies and Codex, centralize your company knowledge and turn every conversation into...
- Features and capabilities:
  - App connectors: fireflies
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/fireflies`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/fireflies/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/fireflies/.app.json`
- External links/attribution: homepage: https://fireflies.ai; repository: https://github.com/openai/plugins; author/developer: Fireflies

### `fiscal-ai@openai-curated`

- Display name: Fiscal AI
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Finance
- What it does: Audit-ready financial data and equity research
- More detail: Access institutional-grade financial data directly within ChatGPT. Fiscal.ai delivers fundamental metrics and ratios minutes after earnings are reported, with every figure verifiable via direct links to the source filing. Beyond core financials, Fiscal.ai provides company-specific KPIs, revenue segments, and adjusted metrics. Combined with historical and current market quotes, it enables grounded, audit-ready equity...
- Features and capabilities:
  - App connectors: fiscal-ai
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/fiscal-ai`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/fiscal-ai/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/fiscal-ai/.app.json`
- External links/attribution: homepage: https://fiscal.ai; repository: https://github.com/openai/plugins; author/developer: Fiscal AI

### `fyxer@openai-curated`

- Display name: Fyxer
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.2`
- Category: Communication
- What it does: Fyxer for Codex lets you write emails that sound like you, right from the chat.
- More detail: Fyxer for Codex lets you write emails that sound like you, right from the chat. Fyxer learns your writing style from past emails and uses context from your calendar and meeting notes to create personalized email drafts. Just describe what you want to say and get a polished email ready to review and send.
- Features and capabilities:
  - App connectors: fyxer
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/fyxer`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/fyxer/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/fyxer/.app.json`
- External links/attribution: homepage: https://www.fyxer.com; repository: https://github.com/openai/plugins; author/developer: Fyxer

### `glean@openai-curated`

- Display name: Glean
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.0`
- Category: Productivity
- What it does: Access enterprise knowledge with Glean
- More detail: Bring enterprise context to ChatGPT and your AI tools with Glean's Remote MCP server. Search across all your organization's connected data sources-documents, wikis, code repositories, and more. Find employees by name, role, or expertise. Read specific documents, access Gmail and Outlook emails, and lookup meeting details. Custom agent workflows enable powerful automation tailored to your organization. Make Glean...
- Features and capabilities:
  - Interface capabilities: Read
  - App connectors: glean
  - Keywords: glean, enterprise-search, knowledge-management, mcp
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/glean`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/glean/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/glean/.app.json`
- External links/attribution: homepage: https://glean.com; repository: https://github.com/openai/plugins; author/developer: Glean Technologies, Inc.

### `granola@openai-curated`

- Display name: Granola
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Communication
- What it does: Granola MCP connects your meeting history to Codex so your assistant can pull real context from past conv...
- More detail: Granola MCP connects your meeting history to Codex so your assistant can pull real context from past conversations while you work. Use MCP when you're already working on something bigger: - Writing PRDs or proposals: Pull customer feedback, stakeholder input, and decisions from relevant meetings directly into your draft - Building presentations or reports: Combine insights from multiple conversations with your other...
- Features and capabilities:
  - App connectors: granola
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/granola`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/granola/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/granola/.app.json`
- External links/attribution: homepage: https://www.granola.ai; repository: https://github.com/openai/plugins; author/developer: Granola

### `happenstance@openai-curated`

- Display name: Happenstance
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Productivity
- What it does: Happenstance searches your professional network using natural language to find the right people.
- More detail: Happenstance searches your professional network using natural language to find the right people. Results surface mutual connections and rank by relationship strength, helping you find the warmest intro path. Deep research anyone to get comprehensive profiles with career history and expertise. Ideal for sales, recruiting, venture capital, and business development.
- Features and capabilities:
  - App connectors: happenstance
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/happenstance`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/happenstance/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/happenstance/.app.json`
- External links/attribution: homepage: https://happenstance.ai; repository: https://github.com/openai/plugins; author/developer: Happenstance, Inc.

### `hebbia@openai-curated`

- Display name: Hebbia
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Business & Operations
- What it does: Institutional research and financial workflows
- More detail: Bring Hebbia's institutional intelligence into ChatGPT and Codex. The Hebbia MCP server lets you tap into your firm's knowledge and premium public to make better decisions on deals and investments and run financial workflows from research to reports, slides, and financial models.
- Features and capabilities:
  - App connectors: hebbia
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/hebbia`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/hebbia/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/hebbia/.app.json`
- External links/attribution: homepage: https://www.hebbia.ai; repository: https://github.com/openai/plugins; author/developer: Hebbia

### `help-scout@openai-curated`

- Display name: Help Scout
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Productivity
- What it does: Connect to sync Help Scout mailboxes and conversations for use in Codex.
- Features and capabilities:
  - App connectors: help-scout
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/help-scout`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/help-scout/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/help-scout/.app.json`
- External links/attribution: homepage: https://www.helpscout.com/; repository: https://github.com/openai/plugins; author/developer: OpenAI

### `hex@openai-curated`

- Display name: Hex
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `0.1.0`
- Category: Data & Analytics
- What it does: Search Hex projects and ask Hex Threads questions
- More detail: Hex helps users find existing Hex projects, dashboards, and data apps, then ask Hex Threads questions when the user explicitly wants to work in Hex.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - App connectors: hex
  - Skills: 1 (hex)
  - Keywords: hex, data-analysis, analytics, threads, dashboards, notebooks
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/hex`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/hex/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/hex/.app.json`; README/CODEX: `/Users/raghav/.codex/.tmp/plugins/plugins/hex/README.md`
- External links/attribution: homepage: https://hex.tech/; repository: https://github.com/openai/plugins/tree/main/plugins/hex; author/developer: OpenAI

### `heygen@openai-curated`

- Display name: HeyGen
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `2.2.4`
- Category: Creativity
- What it does: Avatar videos and personalized video messages
- More detail: HeyGen Skills give your agent a face, a voice, and the ability to send video like a message. Use heygen-avatar to build a persistent digital identity from a written description or hosted photo URL and pick a voice, then heygen-video to generate identity-first presenter videos via the HeyGen v3 Video Agent pipeline (avatar resolution, aspect ratio correction, prompt engineering, and voice selection are handled...
- Features and capabilities:
  - Interface capabilities: Read, Write
  - App connectors: heygen
  - Skills: 2 (heygen-avatar, heygen-video)
  - Agents: 1 (openai)
  - Keywords: heygen, avatar, identity, video, digital-twin, video-message, presenter, talking-head, ai-avatar, avatar-video
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/heygen`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/heygen/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/heygen/.app.json`; README/CODEX: `/Users/raghav/.codex/.tmp/plugins/plugins/heygen/README.md`
- External links/attribution: homepage: https://heygen.com; repository: https://github.com/heygen-com/skills; author/developer: HeyGen

### `hg-insights@openai-curated`

- Display name: HG Insights
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Productivity
- What it does: Prospect data and revenue intelligence
- More detail: HG Insights - Revenue Growth Intelligence gives sales teams instant access to comprehensive prospect data. Get technology stacks, company firmographics, decision-maker contacts, IT spending insights, and contract intelligence for any company. Simply ask about a company by name or domain to uncover actionable sales intelligence powered by HG Insights data. Requires a RGI Developers or RGI Agents account from HG...
- Features and capabilities:
  - App connectors: hg-insights
  - Keywords: hg-insights, revenue-growth-intelligence, gtm, technographics, buyer-intent, account-intelligence
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/hg-insights`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/hg-insights/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/hg-insights/.app.json`
- External links/attribution: homepage: https://hginsights.com; repository: https://github.com/openai/plugins; author/developer: HG Insights

### `highlevel@openai-curated`

- Display name: HighLevel
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.2`
- Category: Productivity
- What it does: HighLevel gives agencies a unified CRM, automation, and client communication platform.
- More detail: HighLevel gives agencies a unified CRM, automation, and client communication platform. This connector lets you securely bring HighLevel data-contacts, opportunities, appointments, conversations and more-into GPT, turning raw records into clear summaries, next-step recommendations, and ready-to-use content. Analyze pipelines, qualify leads, and prepare follow-ups in seconds without leaving the chat.
- Features and capabilities:
  - App connectors: highlevel
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/highlevel`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/highlevel/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/highlevel/.app.json`
- External links/attribution: homepage: https://www.gohighlevel.com; repository: https://github.com/openai/plugins; author/developer: HighLevel

### `hostinger@openai-curated`

- Display name: Hostinger
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Developer Tools
- What it does: Hostinger Horizons lets you build real websites and apps just by describing what you want.
- More detail: Hostinger Horizons lets you build real websites and apps just by describing what you want. Designed for people with no technical background, it turns ideas into working products in minutes. When you're happy with the result, launch instantly with one click.
- Features and capabilities:
  - App connectors: hostinger
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/hostinger`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/hostinger/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/hostinger/.app.json`
- External links/attribution: homepage: https://hostinger.com; repository: https://github.com/openai/plugins; author/developer: Hostinger

### `hubspot@openai-curated`

- Display name: HubSpot
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `2.0.3`
- Category: Business & Operations
- What it does: Work with your HubSpot data to analyze patterns, create and update records, and manage your CRM operations.
- More detail: Work with your HubSpot data to analyze patterns, create and update records, and manage your CRM operations. Read from and write to deals, contacts, companies, tickets, engagements, and other objects you have permission to access. Prepare reports, update deal stages, log calls and emails, create tasks, or review pipeline details before meetings. Use it for quick updates in chat or comprehensive CRM management, all...
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - App connectors: hubspot
  - Skills: 4 (hubspot, hubspot-crm-data-hygiene, hubspot-customer-prep, hubspot-pipeline-health)
  - Keywords: hubspot, crm, sales, pipeline, customer-support
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/hubspot`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/hubspot/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/hubspot/.app.json`
- External links/attribution: homepage: https://www.hubspot.com/; repository: https://github.com/openai/plugins; author/developer: HubSpot

### `intercom@openai-curated`

- Display name: Intercom
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Business & Operations
- What it does: Customer conversations, contacts, tickets, and support workflows from Intercom
- Features and capabilities:
  - App connectors: intercom
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/intercom`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/intercom/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/intercom/.app.json`
- External links/attribution: homepage: https://www.intercom.com; repository: https://github.com/openai/plugins; author/developer: Intercom

### `keybid-puls@openai-curated`

- Display name: KeyBid Puls
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Finance
- What it does: Unlock the profitability of short-term rental investments with our ROI Calculator app, tailored for platfor...
- More detail: Unlock the profitability of short-term rental investments with our ROI Calculator app, tailored for platforms like Airbnb, Booking.com, and VRBO. Users can paste property URLs from sites such as idealista.com, imobiliare.ro, storia.ro, and spitogatos.gr (with more integrations on the way), or upload screenshots from other real estate platforms. The app analyzes the data to deliver instant revenue projections...
- Features and capabilities:
  - App connectors: keybid-puls
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/keybid-puls`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/keybid-puls/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/keybid-puls/.app.json`
- External links/attribution: homepage: https://keybid.eu; repository: https://github.com/openai/plugins; author/developer: KeyBid

### `linear@openai-curated`

- Display name: Linear
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `0.0.3`
- Category: Productivity
- What it does: Find and reference issues and projects.
- More detail: Manage issues, projects, and team workflows in Linear from Codex.
- Features and capabilities:
  - App connectors: linear
  - MCP servers: linear (http)
  - Skills: 1 (linear)
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/linear`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/linear/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/linear/.app.json`; MCP config: `/Users/raghav/.codex/.tmp/plugins/plugins/linear/.mcp.json`
- External links/attribution: homepage: https://linear.app/; repository: https://github.com/openai/plugins; author/developer: OpenAI

### `lovable@openai-curated`

- Display name: Lovable
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.2`
- Category: Developer Tools
- What it does: Create full-stack web apps from prompts
- More detail: Creates full-stack web applications and websites from natural language prompts, handling build, backend, database, and authentication setup, and returning build status, URLs, and screenshots. Use to initiate or check website builds and to provide users with links to further modify or extend their sites in an external web interface.
- Features and capabilities:
  - App connectors: lovable
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/lovable`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/lovable/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/lovable/.app.json`
- External links/attribution: homepage: https://lovable.dev; repository: https://github.com/openai/plugins; author/developer: Lovable

### `lseg@openai-curated`

- Display name: LSEG
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.2`
- Category: Finance
- What it does: Financial market data and analytics
- More detail: The LSEG connector provides real-time access to LSEG's comprehensive financial market data ecosystem, spanning across asset classes and domains. It enables seamless integration of institutional-grade market data, analytics and valuation tools directly into conversational AI workflows, allowing users to access deep market insights, perform complex calculations and analyse financial instruments through natural...
- Features and capabilities:
  - App connectors: lseg
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/lseg`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/lseg/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/lseg/.app.json`
- External links/attribution: homepage: https://www.lseg.com; repository: https://github.com/openai/plugins; author/developer: LSEG

### `magicpath@openai-curated`

- Display name: MagicPath
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `0.1.1`
- Category: Developer Tools
- What it does: Find, install, and author MagicPath UI components from Codex
- More detail: Use MagicPath through the magicpath-ai CLI to search UI components, inspect source, install React and TypeScript components into applications, work with team projects and themes, and create or edit canvas components from local code.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - Skills: 1 (magicpath)
  - Keywords: magicpath, codex, ui-components, design, react, tailwind
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/magicpath`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/magicpath/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/.codex/.tmp/plugins/plugins/magicpath/README.md`
- External links/attribution: homepage: https://github.com/MagicPathAI/agent-skills; repository: https://github.com/MagicPathAI/agent-skills; author/developer: MagicPathAI

### `marcopolo@openai-curated`

- Display name: MarcoPolo
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Developer Tools
- What it does: MarcoPolo spins up a secure container where Codex can work with your actual data.
- More detail: MarcoPolo spins up a secure container where Codex can work with your actual data. Connect to your databases, APIs, S3, lakehouses, CRMs, Jira, logs and much more-using scoped credentials that are never exposed to the model. Codex gets DuckDB, Python, a shell, and a set of tools to explore, query, transform, and analyze data across systems. The workspace persists over time, so that you can build on your work. Prep a...
- Features and capabilities:
  - App connectors: marcopolo
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/marcopolo`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/marcopolo/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/marcopolo/.app.json`
- External links/attribution: homepage: https://marcopolo.dev; repository: https://github.com/openai/plugins; author/developer: Immersa, Inc.

### `mem@openai-curated`

- Display name: Mem
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.2`
- Category: Productivity
- What it does: Give Codex the full context of your second brain by connecting your Mem knowledge base.
- More detail: Give Codex the full context of your second brain by connecting your Mem knowledge base. Search your AI notebook for context, capture and recall ideas, save chats into new notes, edit and update living docs, and organize your AI workspace - simply by asking Codex. Use for: synthesizing and pulling actions items from meeting notes, deep research, personal knowledge management (PKM), knowledge repository building, task...
- Features and capabilities:
  - App connectors: mem
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/mem`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/mem/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/mem/.app.json`
- External links/attribution: homepage: https://mem.ai; repository: https://github.com/openai/plugins; author/developer: Mem Labs, Inc.

### `meticulate@openai-curated`

- Display name: Meticulate
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.2`
- Category: Productivity
- What it does: Research companies and similar targets
- More detail: Meticulate helps sales and go-to-market teams research companies directly in ChatGPT. Upload a company list or describe the accounts you care about, then identify companies, find similar targets, pull key business details, and answer structured research questions across accounts.
- Features and capabilities:
  - App connectors: meticulate
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/meticulate`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/meticulate/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/meticulate/.app.json`
- External links/attribution: repository: https://github.com/openai/plugins; author/developer: Meticulate

### `mixpanel@openai-curated`

- Display name: Mixpanel
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `2.0.3`
- Category: Data & Analytics
- What it does: Query and analyze Mixpanel
- More detail: Query and analyze your Mixpanel data directly in ChatGPT. Run segmentation, funnel, and retention analyses, explore your event taxonomy, manage Lexicon metadata, and resolve data quality issues - all without leaving your conversation. With the Mixpanel MCP server connected, ChatGPT can reason about your product analytics alongside your code, documents, and decisions. Ask questions in plain language, drill into user...
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - App connectors: mixpanel
  - Keywords: mixpanel, analytics, segmentation, funnels, retention, events
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/mixpanel`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/mixpanel/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/mixpanel/.app.json`
- External links/attribution: homepage: https://mixpanel.com/home; repository: https://github.com/openai/plugins; author/developer: Mixpanel

### `mixpanel-headless@openai-curated`

- Display name: Mixpanel Headless
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `0.1.2`
- Category: Data & Analytics
- What it does: Analyze Mixpanel data with Python
- More detail: Use Mixpanel Headless skills to install and authenticate the mixpanel_headless Python SDK, discover Mixpanel schemas, run segmentation, funnel, retention, flow, and user-profile analyses, and build or inspect Mixpanel dashboards from Codex.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - Skills: 4 (dashboard-expert, mixpanel-auth, mixpanelyst, setup)
  - Keywords: mixpanel, analytics, product-analytics, python, data-science, funnels, retention, flows, dashboards
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/mixpanel-headless`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/mixpanel-headless/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/.codex/.tmp/plugins/plugins/mixpanel-headless/README.md`
- External links/attribution: homepage: https://mixpanel.github.io/mixpanel-headless/; repository: https://github.com/mixpanel/mixpanel-headless; author/developer: Mixpanel

### `monday-com@openai-curated`

- Display name: Monday.com
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.2`
- Category: Productivity
- What it does: A powerful MCP connector enabling AI agents to seamlessly interact with monday.com.
- More detail: A powerful MCP connector enabling AI agents to seamlessly interact with monday.com. This connector provides comprehensive access to monday.com features including board management, item operations, dashboards, and more, allowing AI assistants to help manage projects, gain insights, and automate workflows within monday.com.
- Features and capabilities:
  - App connectors: monday-com
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/monday-com`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/monday-com/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/monday-com/.app.json`
- External links/attribution: homepage: https://monday.com; repository: https://github.com/openai/plugins; author/developer: Monday.com

### `motherduck@openai-curated`

- Display name: MotherDuck
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.2`
- Category: Data & Analytics
- What it does: Connect AI assistants to your MotherDuck data warehouse.
- More detail: Connect AI assistants to your MotherDuck data warehouse. Explore, visualize, and manage data using natural language-no SQL skills required. Create Dives: interactive visualizations that let you save and share answers with your team, staying up-to-date with your latest data. Works with real-world data without requiring semantic models or pre-configuration. Your AI assistant acts like a data analyst, exploring...
- Features and capabilities:
  - App connectors: motherduck
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/motherduck`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/motherduck/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/motherduck/.app.json`
- External links/attribution: homepage: https://motherduck.com/; repository: https://github.com/openai/plugins; author/developer: MotherDuck Corporation

### `myregistry-com@openai-curated`

- Display name: MyRegistry.com
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Other
- What it does: MyRegistry.com helps make gift-giving easy for friends & family to get you the gifts you really want!
- More detail: MyRegistry.com helps make gift-giving easy for friends & family to get you the gifts you really want! Create a universal gift list for weddings, baby showers, birthdays, or any celebration and add gifts from any store.
- Features and capabilities:
  - App connectors: myregistry-com
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/myregistry-com`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/myregistry-com/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/myregistry-com/.app.json`
- External links/attribution: homepage: https://www.myregistry.com/; repository: https://github.com/openai/plugins; author/developer: MyRegistry.com

### `network-solutions@openai-curated`

- Display name: Network Solutions
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Productivity
- What it does: The Network Solutions Domain Search Assistant makes finding an available domain fast, simple, and conversat...
- More detail: The Network Solutions Domain Search Assistant makes finding an available domain fast, simple, and conversational. Instead of searching one name at a time, users can describe their idea in plain language and instantly check domain availability across relevant extensions. The assistant helps refine names, suggest alternatives, and quickly identify options that are ready to register. Built to remove friction and...
- Features and capabilities:
  - App connectors: network-solutions
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/network-solutions`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/network-solutions/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/network-solutions/.app.json`
- External links/attribution: homepage: https://www.networksolutions.com/; repository: https://github.com/openai/plugins; author/developer: Network Solutions

### `nvidia@openai-curated`

- Display name: NVIDIA
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.2`
- Category: Developer Tools
- What it does: Guided help for NVIDIA AI, GPU, robotics, simulation, and 3D workflows.
- More detail: NVIDIAs ecosystem spans GPU acceleration, CUDA, AI agents, inference, robotics, Physical AI, Omniverse, and simulation. This plugin helps you understand the pieces, choose a path, validate your setup, and build practical NVIDIA-powered workflows.
- Features and capabilities:
  - Interface capabilities: Interactive, Write
  - Skills: 11 (aiq-deploy, aiq-research, cuopt-user-rules, dynamo-interconnect-check, dynamo-router-starter, nemoclaw-user-get-started, omniverse-cad-to-simready, omniverse-realtime-viewer, +3 more)
  - Keywords: nvidia, gpu, cuda, ai-agents, inference, llm-serving, robotics, simulation, omniverse, openusd
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/nvidia`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/nvidia/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/.codex/.tmp/plugins/plugins/nvidia/README.md`
- External links/attribution: homepage: https://build.nvidia.com/skills/; repository: https://github.com/NVIDIA/skills; author/developer: NVIDIA

### `omni-analytics@openai-curated`

- Display name: Omni Analytics
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.4`
- Category: Data & Analytics
- What it does: Query Omni using the same semantic model, permissions, and logic defined by your data team directly from Codex.
- More detail: Query Omni using the same semantic model, permissions, and logic defined by your data team directly from Codex. Allow internal teams to ask data questions in their AI workflows without logging into Omni directly, while still enforcing row-level security and business definitions.
- Features and capabilities:
  - App connectors: omni-analytics
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/omni-analytics`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/omni-analytics/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/omni-analytics/.app.json`
- External links/attribution: homepage: https://www.omni.co; repository: https://github.com/openai/plugins; author/developer: Omni Analytics

### `openai-ads-conversions@openai-curated`

- Display name: OpenAI Ads Conversions
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `0.1.0`
- Category: Developer Tools
- What it does: Set up OpenAI Ads Pixel and CAPI tracking
- More detail: Use OpenAI Ads Conversions to guide Codex through adding or extending Measurement Pixel and optional Conversions API instrumentation in a repository, with local verification helpers and guidance for safe secret handling, deduplication, attribution context, and setup reporting.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - Skills: 1 (openai-ads-conversions-setup)
  - Keywords: openai-ads, ads, conversions, measurement-pixel, capi
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/openai-ads-conversions`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/openai-ads-conversions/.codex-plugin/plugin.json`; README/CODEX: `/Users/raghav/.codex/.tmp/plugins/plugins/openai-ads-conversions/README.md`
- External links/attribution: homepage: https://developers.openai.com/ads/; repository: https://github.com/openai/plugins/tree/main/plugins/openai-ads-conversions; author/developer: OpenAI

### `otter-ai@openai-curated`

- Display name: Otter.ai
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Communication
- What it does: The Otter.ai MCP server connects Codex to your meeting intelligence, enabling search and retrieval of tra...
- More detail: The Otter.ai MCP server connects Codex to your meeting intelligence, enabling search and retrieval of transcripts, summaries, action items, and meeting metadata directly within your workflow. Search meetings by keyword, date range, attendee, folder, or channel, then fetch full transcripts with speaker attribution. Use it to prepare for meetings by reviewing past discussions, extract decisions from historical...
- Features and capabilities:
  - App connectors: otter-ai
  - Keywords: otter, meetings, transcripts, summaries, action-items, productivity
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/otter-ai`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/otter-ai/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/otter-ai/.app.json`
- External links/attribution: homepage: https://otter.ai; repository: https://github.com/openai/plugins; author/developer: Otter.ai

### `outlook-calendar@openai-curated`

- Display name: Outlook Calendar
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `0.1.3`
- Category: Productivity
- What it does: Manage Outlook schedules and meeting changes
- More detail: Use Outlook Calendar to summarize a day, compare availability, prepare for meetings, explain Outlook status semantics, and schedule, reschedule, or cancel events through the connected Microsoft Outlook app.
- Features and capabilities:
  - Interface capabilities: Interactive, Write
  - App connectors: outlook-calendar
  - Skills: 6 (outlook-calendar, outlook-calendar-daily-brief, outlook-calendar-free-up-time, outlook-calendar-group-scheduler, outlook-calendar-meeting-prep, outlook-calendar-shared-calendars)
  - Keywords: outlook-calendar, calendar, microsoft, scheduling, teams, daily-brief, meeting-prep
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/outlook-calendar`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/outlook-calendar/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/outlook-calendar/.app.json`
- External links/attribution: homepage: https://www.microsoft.com/en-us/microsoft-365/outlook/calendar-app; repository: https://github.com/openai/plugins; author/developer: OpenAI

### `outlook-email@openai-curated`

- Display name: Outlook Email
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `0.1.3`
- Category: Communication
- What it does: Triage Outlook inboxes and draft replies
- More detail: Use Outlook Email to triage inboxes, summarize threads, extract actions, and draft replies or forwards through the connected Microsoft Outlook app.
- Features and capabilities:
  - Interface capabilities: Interactive, Write
  - App connectors: outlook-email
  - Skills: 6 (outlook-email, outlook-email-inbox-triage, outlook-email-reply-drafting, outlook-email-shared-mailboxes, outlook-email-subscription-cleanup, outlook-email-task-extraction)
  - Keywords: outlook-email, email, microsoft
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/outlook-email`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/outlook-email/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/outlook-email/.app.json`
- External links/attribution: homepage: https://www.microsoft.com/en-us/microsoft-365/outlook/email-and-calendar-software-microsoft-outlook; repository: https://github.com/openai/plugins; author/developer: OpenAI

### `outreach@openai-curated`

- Display name: Outreach
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.2`
- Category: Business & Operations
- What it does: Revenue workflow automation with Outreach
- More detail: Bring Outreach knowledge and actions into ChatGPT so your teams can move faster, combine insights across systems, and complete advanced revenue tasks without switching tools. Outreach is an end-to-end AI Revenue Platform for all go-to-market teams. By embedding agentic AI across every revenue workflow, Outreach increases sales productivity, boosts pipeline, and gives leaders the visibility and predictability they...
- Features and capabilities:
  - App connectors: outreach
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/outreach`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/outreach/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/outreach/.app.json`
- External links/attribution: homepage: https://www.outreach.io; repository: https://github.com/openai/plugins; author/developer: Outreach

### `picsart@openai-curated`

- Display name: Picsart
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Creativity
- What it does: Generate videos, images, and audio
- More detail: Generate high-quality video, images, and audio from 140+ AI models - all with one Picsart account. Try prompts like this: @Picsart , create a cinematic 10-second video ad for our product launch Turn this product photo into a 6-second vertical video, @Picsart @Picsart generate three photoreal hero images for a new launch @Picsart , create a 15-second instrumental music bed for a product demo
- Features and capabilities:
  - App connectors: picsart
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/picsart`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/picsart/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/picsart/.app.json`
- External links/attribution: homepage: https://picsart.com; repository: https://github.com/openai/plugins; author/developer: Picsart

### `pipedrive@openai-curated`

- Display name: Pipedrive
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Business & Operations
- What it does: Connect to sync Pipedrive deals and contacts for use in Codex.
- Features and capabilities:
  - App connectors: pipedrive
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/pipedrive`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/pipedrive/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/pipedrive/.app.json`
- External links/attribution: homepage: https://www.pipedrive.com/; repository: https://github.com/openai/plugins; author/developer: OpenAI

### `policynote@openai-curated`

- Display name: PolicyNote
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Education & Research
- What it does: Use the PolicyNote app to access structured policy and regulatory intelligence from around the world.
- More detail: Use the PolicyNote app to access structured policy and regulatory intelligence from around the world. Search legislation, regulatory actions, policy updates, and government activity across jurisdictions. The app enables developers, analysts, and policy professionals to retrieve policy data programmatically and integrate it into internal tools, research workflows, dashboards, or monitoring systems. Queries return...
- Features and capabilities:
  - App connectors: policynote
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/policynote`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/policynote/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/policynote/.app.json`
- External links/attribution: homepage: https://fiscalnote.com/products/policynote-api; repository: https://github.com/openai/plugins; author/developer: FiscalNote

### `posthog@openai-curated`

- Display name: PostHog
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `0.1.2`
- Category: Data & Analytics
- What it does: Analyze product data and manage experiments
- More detail: PostHog gives your AI agent direct access to your product analytics, feature flags, experiments, error tracking, surveys, logs, and LLM analytics. Ask questions about your data, create insights, toggle feature flags, analyze errors, search docs, and more - all from chat.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - App connectors: posthog
  - Skills: 1 (posthog)
  - Keywords: posthog, analytics, product-analytics, feature-flags, experiments, error-tracking, session-replay, surveys, llm-analytics, hogql
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/posthog`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/posthog/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/posthog/.app.json`
- External links/attribution: homepage: https://posthog.com/docs; repository: https://github.com/openai/plugins; author/developer: PostHog

### `pylon@openai-curated`

- Display name: Pylon
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Productivity
- What it does: Access Pylon's customer support platform directly from Codex to search, manage, and resolve customer issues.
- More detail: Access Pylon's customer support platform directly from Codex to search, manage, and resolve customer issues. Stay on top of your support queue while connecting Codex's insights to real customer conversations. You can use the Pylon app to: Check your queue: "What Pylon issues are assigned to me that need a response?" Research customers: "Summarize recent issues from Acme Corp and flag any escalations." Update issues...
- Features and capabilities:
  - App connectors: pylon
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/pylon`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/pylon/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/pylon/.app.json`
- External links/attribution: homepage: https://www.usepylon.com/; repository: https://github.com/openai/plugins; author/developer: Pylon Labs Inc.

### `quartr@openai-curated`

- Display name: Quartr
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Finance
- What it does: Public company IR data and earnings research
- More detail: Access structured first-party IR data from over 14,500+ public companies across 65 markets Quartr delivers live and recorded earnings calls, real-time and historical transcripts with speaker identification, slide presentations, filings, reports, and event summaries. Best-in-class reliability and timeliness. Ideal for financial research, investment analysis, and building data-driven workflows on top of...
- Features and capabilities:
  - App connectors: quartr
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/quartr`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/quartr/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/quartr/.app.json`
- External links/attribution: homepage: https://quartr.com; repository: https://github.com/openai/plugins; author/developer: Quartr

### `quickbooks@openai-curated`

- Display name: QuickBooks
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Finance
- What it does: Analyze finances and manage QuickBooks records
- More detail: Turn your business's raw financial data into clear financial insights. Analyze profitability, cash flow, accounts receivable and payable, and compare your performance against similar businesses in your industry and region. Generate accounting-compliant profit & loss, cash flow statements, balance sheets, and AR/AP aging reports in minutes. Manage invoices, estimates, payments, customers, products, and payroll...
- Features and capabilities:
  - App connectors: quickbooks
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/quickbooks`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/quickbooks/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/quickbooks/.app.json`
- External links/attribution: homepage: https://quickbooks.intuit.com; repository: https://github.com/openai/plugins; author/developer: QuickBooks

### `quicknode@openai-curated`

- Display name: Quicknode
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Developer Tools
- What it does: Manage your Quicknode infrastructure directly in OpenAI.
- More detail: Manage your Quicknode infrastructure directly in OpenAI. Create and manage endpoints, monitor logs and usage, configure security and rate limits, and review billing from one conversation.
- Features and capabilities:
  - App connectors: quicknode
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/quicknode`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/quicknode/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/quicknode/.app.json`
- External links/attribution: homepage: https://www.quicknode.com/; repository: https://github.com/openai/plugins; author/developer: Quicknode

### `read-ai@openai-curated`

- Display name: Read AI
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Communication
- What it does: Read AI brings your meeting intelligence directly into your AI workflows.
- More detail: Read AI brings your meeting intelligence directly into your AI workflows. Connect your Read AI account to access meeting summaries, transcripts, action items, key questions, and more - all retrievable through natural conversation. Read AI can look up recent meetings, pull the full transcript from a specific call, surface action items from last week's syncs, or find what key questions came up in a discussion. What...
- Features and capabilities:
  - App connectors: read-ai
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/read-ai`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/read-ai/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/read-ai/.app.json`
- External links/attribution: homepage: https://read.ai; repository: https://github.com/openai/plugins; author/developer: Read AI, Inc

### `replayio@openai-curated`

- Display name: Replay.io
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `0.1.0`
- Category: Developer Tools
- What it does: Record browser sessions and inspect Replay recordings or Replay QA results
- More detail: Drive the host agent browser with Replay Chromium selected by AGENT_BROWSER_EXECUTABLE_PATH to capture time-travel debuggable recordings, upload pending recordings after the run, analyze uploaded recordings through Replay MCP tools, and create Replay QA projects for recording analysis or live-app exploration. In MCP Apps-aware hosts, Replay tool results can render rich debugging widgets for logpoints, console...
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - App connectors: replayio
  - Skills: 2 (replay-qa-api, replayio)
  - Scripts: 2 (post_bash_upload, stop_close_and_upload)
  - Keywords: replay, agent-browser, playwright, browser-automation, time-travel-debugging, recording, replay-qa, chatgpt-app
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/replayio`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/replayio/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/replayio/.app.json`
- External links/attribution: homepage: https://replay.io; repository: https://github.com/replayio/plugins; author/developer: Replay

### `replit@openai-curated`

- Display name: Replit
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.2`
- Category: Developer Tools
- What it does: Create and iterate Replit web apps
- More detail: Enables creating a brand-new web application in the user's Replit account from a natural-language description, without exposing code directly in the chat. Also supports inspecting and explaining the current app's behavior and applying natural-language change requests to that same app over iterative development.
- Features and capabilities:
  - App connectors: replit
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/replit`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/replit/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/replit/.app.json`
- External links/attribution: homepage: https://replit.com; repository: https://github.com/openai/plugins; author/developer: Replit

### `responsive@openai-curated`

- Display name: Responsive
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Productivity
- What it does: The Responsive App makes it easy to work with your organization's data inside Codex.
- More detail: The Responsive App makes it easy to work with your organization's data inside Codex. Search your Content Library and generate responses so you can move faster with trusted information and without switching tools.
- Features and capabilities:
  - App connectors: responsive
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/responsive`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/responsive/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/responsive/.app.json`
- External links/attribution: homepage: https://www.responsive.io; repository: https://github.com/openai/plugins; author/developer: RFPIO Inc. (d/b/a Responsive)

### `rox@openai-curated`

- Display name: Rox
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Productivity
- What it does: Analyze sales data from Rox workspaces
- More detail: Rox helps users find and analyze authenticated sales data from their Rox workspace, including accounts, deals, contacts, notes, emails, meetings, documents, org charts, and Slack activity. The app exposes a guided data interface: users can discover available data functions, inspect each function's schema and workflow guidance, then invoke read-only functions to answer sales and account intelligence questions.
- Features and capabilities:
  - App connectors: rox
  - Keywords: rox, sales, revenue, gtm, crm, account-intelligence, prospecting
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/rox`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/rox/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/rox/.app.json`
- External links/attribution: homepage: https://www.rox.com; repository: https://github.com/openai/plugins; author/developer: Rox Data Corp

### `s-p@openai-curated`

- Display name: S&P Global
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Finance
- What it does: Query S&P Global financial datasets
- More detail: Use natural language to query a range of S&P Global datasets, including S&P Capital IQ Financials, transcripts, and more. Designed to save time and resources for engineering, product, and business teams in financial services, this server streamlines access to company information, financial statements, historical market data, and global securities.
- Features and capabilities:
  - App connectors: s-p
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/s-p`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/s-p/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/s-p/.app.json`
- External links/attribution: homepage: https://www.spglobal.com; repository: https://github.com/openai/plugins; author/developer: S&P Global

### `semrush@openai-curated`

- Display name: Semrush
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Productivity
- What it does: The Semrush MCP provides structured, quantitative SEO and traffic data for domains, keywords, backlinks, an...
- More detail: The Semrush MCP provides structured, quantitative SEO and traffic data for domains, keywords, backlinks, and market-level audience insights. It returns factual datasets including domain analytics, keyword metrics, backlink profiles, traffic data across time periods and channels, geographic and demographic distributions, and competitive or industry-level indicators. The model should invoke this MCP whenever a user...
- Features and capabilities:
  - App connectors: semrush
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/semrush`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/semrush/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/semrush/.app.json`
- External links/attribution: homepage: https://www.semrush.com/; repository: https://github.com/openai/plugins; author/developer: Semrush Holdings, Inc.

### `sendgrid@openai-curated`

- Display name: SendGrid
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `0.1.2`
- Category: Developer Tools
- What it does: Connector for interacting with the SendGrid email API.
- Features and capabilities:
  - App connectors: sendgrid
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/sendgrid`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/sendgrid/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/sendgrid/.app.json`
- External links/attribution: homepage: https://sendgrid.com/; repository: https://github.com/openai/plugins; author/developer: OpenAI

### `sentry@openai-curated`

- Display name: Sentry
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `0.1.2`
- Category: Developer Tools
- What it does: Inspect recent Sentry issues and events
- More detail: Use Sentry skills to inspect recent issues, review events, and summarize production errors with a read-only workflow.
- Features and capabilities:
  - Interface capabilities: Interactive, Write
  - Skills: 1 (sentry)
  - Keywords: sentry, observability, triage
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/sentry`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/sentry/.codex-plugin/plugin.json`
- External links/attribution: homepage: https://sentry.io/; repository: https://github.com/openai/plugins; author/developer: OpenAI

### `setu-bharat-connect-billpay@openai-curated`

- Display name: Setu Bharat Connect BillPay
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.2`
- Category: Finance
- What it does: This app helps you pay your utility bills through simple conversation.
- More detail: This app helps you pay your utility bills through simple conversation. Instead of navigating apps or filling forms, you can just tell the assistant what you want to do-like paying your electricity, broadband, or other utility bills. The app finds the right biller, fetches the exact bill amount, and guides you through payment step by step. You can check pending bills, view bill amounts before paying, confirm whether...
- Features and capabilities:
  - App connectors: setu-bharat-connect-billpay
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/setu-bharat-connect-billpay`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/setu-bharat-connect-billpay/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/setu-bharat-connect-billpay/.app.json`
- External links/attribution: homepage: https://setu.co/; repository: https://github.com/openai/plugins; author/developer: Setu

### `sharepoint@openai-curated`

- Display name: SharePoint
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `0.1.3`
- Category: Productivity
- What it does: Summarize SharePoint sites and files
- More detail: Use SharePoint to summarize sites, pages, and files, extract owners and status, and plan safe content updates through the connected Microsoft SharePoint app.
- Features and capabilities:
  - Interface capabilities: Interactive, Write
  - App connectors: sharepoint
  - Skills: 7 (sharepoint, sharepoint-powerpoint, sharepoint-shared-doc-maintenance, sharepoint-site-discovery, sharepoint-spreadsheet-formula-builder, sharepoint-spreadsheets, sharepoint-word-docs)
  - Keywords: sharepoint, documents, microsoft
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/sharepoint`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/sharepoint/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/sharepoint/.app.json`
- External links/attribution: homepage: https://www.microsoft.com/en-us/microsoft-365/sharepoint/collaboration; repository: https://github.com/openai/plugins; author/developer: OpenAI

### `shopify@openai-curated`

- Display name: Shopify
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.3.3`
- Category: Developer Tools
- What it does: Build Shopify apps, themes, storefronts, and APIs
- More detail: Shopify developer tools for searching Shopify documentation, generating and validating GraphQL, Liquid, Hydrogen, Functions, UI extension, and CLI workflows. Skill scripts send usage telemetry to shopify.dev by default; set OPT_OUT_INSTRUMENTATION=true to disable.
- Features and capabilities:
  - Interface capabilities: Read, Write
  - App connectors: shopify
  - Skills: 20 (shopify-admin, shopify-app-store-review, shopify-custom-data, shopify-customer, shopify-dev, shopify-functions, shopify-hydrogen, shopify-liquid, +12 more)
  - Keywords: shopify, mcp, graphql, liquid, storefront, admin-api
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/shopify`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/shopify/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/shopify/.app.json`
- External links/attribution: homepage: https://github.com/Shopify/Shopify-AI-Toolkit; repository: https://github.com/Shopify/Shopify-AI-Toolkit; author/developer: Shopify

### `shutterstock@openai-curated`

- Display name: Shutterstock
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Creativity
- What it does: Search stock media libraries
- More detail: Searches stock libraries to find candidate images, videos, music, and sound effects that match user-specified subjects, styles, moods, or settings, returning watermarked preview URLs with basic metadata for selection. Use when users want to browse or choose existing stock media (including multiple grouped image searches), not to generate, edit, license, or download files.
- Features and capabilities:
  - App connectors: shutterstock
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/shutterstock`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/shutterstock/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/shutterstock/.app.json`
- External links/attribution: homepage: https://www.shutterstock.com; repository: https://github.com/openai/plugins; author/developer: Shutterstock

### `signnow@openai-curated`

- Display name: SignNow
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Productivity
- What it does: Get documents signed faster without switching between tools.
- More detail: Get documents signed faster without switching between tools. The SignNow MCP server connects Codex directly to your SignNow account, letting you manage the entire eSignature workflow through conversation. Send signature requests, create documents from templates and pre-fill them, track invite statuses, and retrieve signed files - all by describing what you need in plain language. Whether you're handling contracts...
- Features and capabilities:
  - App connectors: signnow
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/signnow`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/signnow/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/signnow/.app.json`
- External links/attribution: homepage: https://www.signnow.com; repository: https://github.com/openai/plugins; author/developer: airSlate Inc

### `similarweb@openai-curated`

- Display name: Similarweb
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.2`
- Category: Data & Analytics
- What it does: Research web and app market intelligence
- More detail: Research any website or app inside ChatGPT using Similarweb's market intelligence data. Analyze competitor traffic, uncover top keywords, explore audience demographics, and benchmark performance across industries-all through simple prompts. Ask things like "Show me Nike's traffic sources breakdown" or "What keywords is Adidas ranking for?" and get real-time insights without switching tools. Whether you're a...
- Features and capabilities:
  - App connectors: similarweb
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/similarweb`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/similarweb/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/similarweb/.app.json`
- External links/attribution: homepage: https://www.similarweb.com; repository: https://github.com/openai/plugins; author/developer: Similarweb

### `skywatch@openai-curated`

- Display name: SkyWatch
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Productivity
- What it does: Search and explore satellite imagery from top providers including Vantor, Planet, Airbus, and more, all in...
- More detail: Search and explore satellite imagery from top providers including Vantor, Planet, Airbus, and more, all in one place. SkyWatch lets you find archive imagery by location, date, resolution, and cloud cover, compare pricing across providers, and browse available satellites and product offerings. Results include direct links to view and order imagery on SkyWatch Explore.
- Features and capabilities:
  - App connectors: skywatch
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/skywatch`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/skywatch/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/skywatch/.app.json`
- External links/attribution: homepage: https://skywatch.com; repository: https://github.com/openai/plugins; author/developer: SkyWatch Space Applications Inc.

### `statsig@openai-curated`

- Display name: Statsig
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `2.0.3`
- Category: Developer Tools
- What it does: Bring your Statsig workspace into Codex.
- More detail: Bring your Statsig workspace into Codex. Product builders can now explore, manage, and create Statsig experiments, feature gates, dynamic configs, and more directly in Codex conversations. Ask things like: "Move this experiment to 50% rollout." "Turn on this feature gate for all users." "Show me which dynamic configs changed this week." "Explain how the DAU metric is defined." You can both read and write to Statsig...
- Features and capabilities:
  - App connectors: statsig
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/statsig`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/statsig/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/statsig/.app.json`
- External links/attribution: homepage: https://statsig.com; repository: https://github.com/openai/plugins; author/developer: Statsig, LLC

### `streak@openai-curated`

- Display name: Streak
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.2`
- Category: Business & Operations
- What it does: Streak is a CRM built directly into Gmail, so you can track deals, contacts, and workflows from your inbox.
- More detail: Streak is a CRM built directly into Gmail, so you can track deals, contacts, and workflows from your inbox. Emails are logged automatically, pipelines update as conversations move forward, and notes and tasks stay attached to the work they belong to-without copying data into another tool. Designed for teams and individuals who manage sales, partnerships, or customer relationships primarily over email and want a...
- Features and capabilities:
  - App connectors: streak
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/streak`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/streak/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/streak/.app.json`
- External links/attribution: homepage: https://www.streak.com; repository: https://github.com/openai/plugins; author/developer: Rewardly, Inc.

### `stripe@openai-curated`

- Display name: Stripe
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.2`
- Category: Finance
- What it does: Payments and business tools
- Features and capabilities:
  - App connectors: stripe
  - Skills: 2 (stripe-best-practices, upgrade-stripe)
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/stripe`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/stripe/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/stripe/.app.json`
- External links/attribution: homepage: https://stripe.com; repository: https://github.com/openai/plugins; author/developer: Stripe

### `superhuman@openai-curated`

- Display name: Superhuman Mail
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `0.1.2`
- Category: Communication
- What it does: The most productive email app ever, for Gmail & Outlook
- More detail: Build powerful workflows and automations for email and calendar. Find anything in your inbox, draft replies that sound like you for every recipient, check read statuses, schedule meetings, and send - all without leaving Codex.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - App connectors: superhuman
  - Skills: 6 (batch-draft-writer, deal-tracker, eod-wrapup, meeting-scheduler, morning-briefing, superhuman-mail)
  - Keywords: superhuman, mail, email, calendar, mcp
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/superhuman`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/superhuman/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/superhuman/.app.json`
- External links/attribution: homepage: https://help.superhuman.com/hc/en-us/articles/49810745762067-Superhuman-Mail-MCP-Server; repository: https://github.com/superhuman/mcp-mail; author/developer: Superhuman

### `teams@openai-curated`

- Display name: Teams
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `0.1.3`
- Category: Communication
- What it does: Summarize Teams and draft follow-ups
- More detail: Use Teams to summarize chats, extract actions, and draft channel or meeting follow-ups through the connected Microsoft Teams app.
- Features and capabilities:
  - Interface capabilities: Interactive, Write
  - App connectors: teams
  - Skills: 7 (teams, teams-channel-summarization, teams-daily-digest, teams-messages, teams-notification-triage, teams-planner-task-management, teams-reply-drafting)
  - Keywords: teams, chat, microsoft
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/teams`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/teams/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/teams/.app.json`
- External links/attribution: homepage: https://www.microsoft.com/en-us/microsoft-teams/group-chat-software; repository: https://github.com/openai/plugins; author/developer: OpenAI

### `teamwork-com@openai-curated`

- Display name: Teamwork.com
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Productivity
- What it does: Connect to sync Teamwork projects and tasks for use in Codex.
- Features and capabilities:
  - App connectors: teamwork-com
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/teamwork-com`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/teamwork-com/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/teamwork-com/.app.json`
- External links/attribution: homepage: https://www.teamwork.com/; repository: https://github.com/openai/plugins; author/developer: OpenAI

### `thoughtspot@openai-curated`

- Display name: ThoughtSpot
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Data & Analytics
- What it does: Trusted business data answers
- More detail: From everyday data questions to high-level strategic analyses, Spotter by ThoughtSpot helps business and data teams get answers and insights they can trust, validate, and act on, enabling everyone to use data to drive the business forward.
- Features and capabilities:
  - App connectors: thoughtspot
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/thoughtspot`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/thoughtspot/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/thoughtspot/.app.json`
- External links/attribution: homepage: https://www.thoughtspot.com; repository: https://github.com/openai/plugins; author/developer: ThoughtSpot

### `tinman-ai@openai-curated`

- Display name: Tinman AI
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Finance
- What it does: Tinman AI helps loan officers and underwriters quickly underwrite home financing scenarios and answer compl...
- More detail: Tinman AI helps loan officers and underwriters quickly underwrite home financing scenarios and answer complex eligibility questions using trusted credit decision data and underwriting logic. Instead of navigating fragmented systems, scattered guidelines, or manual spreadsheets, users can evaluate eligibility, DTI restructuring, and income calculations across a broad set of lenders and investors, instantly...
- Features and capabilities:
  - App connectors: tinman-ai
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/tinman-ai`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/tinman-ai/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/tinman-ai/.app.json`
- External links/attribution: homepage: https://better.com; repository: https://github.com/openai/plugins; author/developer: Better

### `twilio-developer-kit@openai-curated`

- Display name: Twilio Developer Kit
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `0.2.2`
- Category: Developer Tools
- What it does: Twilio Skills for building, debugging, and shipping on Twilio
- More detail: Procedural knowledge that guides AI coding agents to the right Twilio APIs for any use case. Covers channel selection, production best practices, compliance requirements, and common pitfalls across Messaging, Voice, Verify, SendGrid, and 30+ products. Skills follow a progressive disclosure architecture - your agent sees lightweight metadata at startup and loads full guidance only when a task matches.
- Features and capabilities:
  - Interface capabilities: Read, Write
  - Skills: 56 (twilio-account-setup, twilio-agent-augmentation-architect, twilio-agent-connect, twilio-ai-agent-architect, twilio-call-recordings, twilio-cli-reference, twilio-compliance-onboarding, twilio-compliance-traffic, +48 more)
  - Keywords: twilio, sms, voice, whatsapp, rcs, messaging, verify, sendgrid, email, compliance
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/twilio-developer-kit`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/twilio-developer-kit/.codex-plugin/plugin.json`
- External links/attribution: homepage: https://www.twilio.com/docs; repository: https://github.com/twilio/ai; author/developer: Twilio

### `united-rentals@openai-curated`

- Display name: United Rentals
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Productivity
- What it does: Get the right equipment for the job without guesswork.
- More detail: Get the right equipment for the job without guesswork. Share your project details and receive tailored equipment recommendations, along with specifications to support confident selection.
- Features and capabilities:
  - App connectors: united-rentals
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/united-rentals`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/united-rentals/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/united-rentals/.app.json`
- External links/attribution: homepage: https://www.unitedrentals.com; repository: https://github.com/openai/plugins; author/developer: United Rentals

### `vantage@openai-curated`

- Display name: Vantage
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.2`
- Category: Developer Tools
- What it does: Vantage is a cloud observability and optimization platform that aggregates cloud infrastructure costs acros...
- More detail: Vantage is a cloud observability and optimization platform that aggregates cloud infrastructure costs across providers to deliver a centralized view into total cloud spend. Vantage has multiple tools for optimizing cloud spend and provides organizations with advanced FinOps workflows and cost governance.
- Features and capabilities:
  - App connectors: vantage
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/vantage`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/vantage/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/vantage/.app.json`
- External links/attribution: homepage: https://www.vantage.sh; repository: https://github.com/openai/plugins; author/developer: Vantage

### `waldo@openai-curated`

- Display name: Waldo
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Productivity
- What it does: Waldo is an AI-powered strategy platform for agencies and brands.
- More detail: Waldo is an AI-powered strategy platform for agencies and brands. Run strategy agent, explore collected signals - paid ads, brand mentions, audience conversations, trending topics, and more - and retrieve data across your team's brand spaces.
- Features and capabilities:
  - App connectors: waldo
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/waldo`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/waldo/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/waldo/.app.json`
- External links/attribution: homepage: https://www.waldo.fyi; repository: https://github.com/openai/plugins; author/developer: Curiosities, Inc.

### `weatherpromise@openai-curated`

- Display name: WeatherPromise
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.2`
- Category: Travel
- What it does: Protect your trip with WeatherPromise and get back the full cost if it rains more than promised during your...
- More detail: Protect your trip with WeatherPromise and get back the full cost if it rains more than promised during your vacation, automatically. Tell us your destination, travel dates and trip cost and we'll show you an offer, personalized to your trip. Once you purchase the offer, your trip is protected. You will get a link to your personal dashboard where you can monitor the weather during your trip. Rain is measured using...
- Features and capabilities:
  - App connectors: weatherpromise
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/weatherpromise`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/weatherpromise/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/weatherpromise/.app.json`
- External links/attribution: homepage: https://www.weatherpromise.com/; repository: https://github.com/openai/plugins; author/developer: WeatherPromise, Inc.

### `windsor-ai@openai-curated`

- Display name: Windsor.ai
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Data & Analytics
- What it does: Windsor.ai connects your marketing and business data sources to Codex so you can ask questions in natural...
- More detail: Windsor.ai connects your marketing and business data sources to Codex so you can ask questions in natural language and get answers from your connected accounts. Common data sources customers connect include: Google Ads, Meta (Facebook) Ads, Instagram, LinkedIn Ads, LinkedIn Company Pages, TikTok Ads, GA4, Google Search Console, YouTube Analytics, Google Business Profile, HubSpot, Salesforce, Shopify, Klaviyo, Amazon...
- Features and capabilities:
  - App connectors: windsor-ai
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/windsor-ai`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/windsor-ai/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/windsor-ai/.app.json`
- External links/attribution: homepage: https://windsor.ai; repository: https://github.com/openai/plugins; author/developer: Windsor.ai

### `wix@openai-curated`

- Display name: Wix
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.1.2`
- Category: Developer Tools
- What it does: Build Wix apps, headless websites, and manage your Wix business from Codex
- More detail: Build and deploy Wix apps and headless websites, and manage your Wix business with Codex. Includes Wix CLI development skills for dashboard extensions, backend APIs, site widgets, service plugins, and data collections. Build headless websites with Wix Headless - from fully-hosted Astro apps to self-hosted in any framework - powered by Wix's backend for eCommerce, bookings, CMS, events, and members. Also includes...
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - App connectors: wix
  - Skills: 4 (wix-app, wix-design-system, wix-headless, wix-manage)
  - Keywords: wix, wix-cli, wix-mcp, ecommerce, cms, wix-apps, wix-headless, headless
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/wix`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/wix/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/wix/.app.json`
- External links/attribution: homepage: https://dev.wix.com/docs/api-reference/articles/ai-tools/about-wix-skills; repository: https://github.com/wix/skills; author/developer: Wix

### `yepcode@openai-curated`

- Display name: YepCode
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Developer Tools
- What it does: YepCode lets you build custom AI tools using your own code with JSON Schema-defined inputs, executed in an...
- More detail: YepCode lets you build custom AI tools using your own code with JSON Schema-defined inputs, executed in an isolated sandbox with access to any npm or PyPI package and secure environment variables. Define reusable processes in Node.js or Python, expose them as callable AI tools, and execute them on demand or on a schedule. Every run is logged and auditable, enabling traceable, production-grade AI integrations. Built...
- Features and capabilities:
  - App connectors: yepcode
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/yepcode`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/yepcode/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/yepcode/.app.json`
- External links/attribution: homepage: https://yepcode.io/; repository: https://github.com/openai/plugins; author/developer: YepCode S.L.

### `zoho@openai-curated`

- Display name: Zoho
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.3`
- Category: Business & Operations
- What it does: Manage Zoho CRM sales workflows
- More detail: Zoho CRM is an AI-powered sales software that helps businesses of all sizes manage their sales better. With SFA features, advanced automation, easy-to-use UI, advanced analytics, and deep customization capabilities, Zoho CRM truly understands your business. With Codex, you can extend the functionalities of Zoho CRM by simply prompting. Your business, your Zoho CRM-powered by Codex.
- Features and capabilities:
  - App connectors: zoho
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/zoho`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/zoho/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/zoho/.app.json`
- External links/attribution: homepage: https://www.zoho.com; repository: https://github.com/openai/plugins; author/developer: Zoho

### `zoom@openai-curated`

- Display name: Zoom
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.2`
- Category: Communication
- What it does: Use Zoom meeting context and build Zoom integrations.
- More detail: Zoom connects Codex to Zoom meeting context through the Zoom app connector and provides developer workflows for planning, building, debugging, and reviewing Zoom integrations across APIs, SDKs, webhooks, WebSockets, bots, and automation use cases.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - App connectors: zoom
  - Skills: 27 (build-zoom-bot, build-zoom-meeting-app, choose-zoom-approach, cobrowse-sdk, contact-center, debug-zoom, debug-zoom-integration, general, +19 more)
  - Commands: 26 (_conventions, build-zoom-apps-sdk-app, build-zoom-bot, build-zoom-cobrowse-app, build-zoom-contact-center-app, build-zoom-meeting-app, build-zoom-meeting-sdk-app, build-zoom-phone-integration, +18 more)
  - Agents: 3 (zoom-integration-reviewer, zoom-oauth-scope-auditor, openai)
  - Keywords: zoom, codex-plugin, connector, meetings, transcripts, recordings, docs, developers, rest-api, meeting-sdk
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/zoom`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/zoom/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/zoom/.app.json`; README/CODEX: `/Users/raghav/.codex/.tmp/plugins/plugins/zoom/README.md`
- External links/attribution: homepage: https://developers.zoom.us/; repository: https://github.com/zoom/zoom-plugin-codex; author/developer: Zoom

### `zoominfo@openai-curated`

- Display name: ZoomInfo
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `1.0.2`
- Category: Business & Operations
- What it does: Prospecting and account research with ZoomInfo
- More detail: Access ZoomInfo's data and AI context within ChatGPT. Prospecting, Account Research, Verified Contacts, buying signals, and more are now available directly in your conversations.
- Features and capabilities:
  - App connectors: zoominfo
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/zoominfo`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/zoominfo/.codex-plugin/plugin.json`; app connector: `/Users/raghav/.codex/.tmp/plugins/plugins/zoominfo/.app.json`
- External links/attribution: homepage: https://www.zoominfo.com; repository: https://github.com/openai/plugins; author/developer: ZoomInfo

### `zotero@openai-curated`

- Display name: Zotero
- Marketplace: `openai-curated`
- Status: available, not installed
- Version: `0.1.2`
- Category: Education & Research
- What it does: Find papers and add citations from Zotero
- More detail: Connect Codex to your Zotero desktop library so it can find saved papers, export BibTeX, add citation keys to drafts, read indexed attachment text when you ask, and import new reference records into Zotero with your approval.
- Features and capabilities:
  - Interface capabilities: Interactive, Read, Write
  - Skills: 1 (zotero)
  - Keywords: zotero, citations, bibliography, bibtex, references, research, papers, latex
- Install policy: `AVAILABLE`
- Auth policy: `ON_INSTALL`
- Source path: `/Users/raghav/.codex/.tmp/plugins/plugins/zotero`
- Metadata files used: plugin manifest: `/Users/raghav/.codex/.tmp/plugins/plugins/zotero/.codex-plugin/plugin.json`
- External links/attribution: homepage: https://openai.com/; repository: https://github.com/openai/plugins; author/developer: OpenAI

## Source Commands And Files

- Primary inventory command: `codex plugin list --available --json`
- Local plugin marketplace examples: `/Users/raghav/.agents/plugins/marketplace.json`, `/Users/raghav/.codex/.tmp/plugins/.agents/plugins/marketplace.json`, `/Users/raghav/agent-repos/claude-for-legal-india/.claude-plugin/marketplace.json`
- Local plugin cache root: `/Users/raghav/.codex/plugins/cache/`
- OpenAI curated plugin source snapshot root: `/Users/raghav/.codex/.tmp/plugins/plugins/`
- Workspace generated file: `/Users/raghav/Downloads/tender_export_os_v3_1_runtime_system/CODEX_PLUGINS_REFERENCE.md`

## Maintenance Notes

- Regenerate this file after installing, disabling, or removing plugins.
- For runtime debugging, inspect both plugin install state and active MCP/app connector health; the inventory file alone does not prove tools are currently callable.
- For Gmail, Drive, Calendar, Supabase, Vercel, and similar app connectors, verify the connected account and required permissions before making read/write calls.

