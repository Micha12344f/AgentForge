---
name: content
description: "Content Agent — public building, case studies, technical blog posts, social media content, open source releases, and LinkedIn API integration for AgentForge."
---

# CONTENT — Skill Command Sheet

> **Adopt this department to gain**: Case study writing, technical blog posts, short-form social content, open source release management, public building strategy, and full LinkedIn API access (posts, images, videos, comments, reactions, analytics).

> **Governance**: Content owns content creation material. Orchestrator alone owns cross-department DOE restructuring.

---

## Strategic Rule

Everything built should be documented publicly where possible. This is not marketing for a product — it is building a reputation as a team that ships real agentic systems. That reputation becomes distribution when the product is ready to sell.

---

## Skills

### Skill 1 — Case Studies
| Layer | Path |
|-------|------|
| Directive | `directives/case-studies.md` |
| Resources | `resources/case-study-template.md` |
| Use for | Writing structured case studies: problem → solution → architecture → results → learnings |

### Skill 2 — Technical Blog Posts
| Layer | Path |
|-------|------|
| Directive | `directives/technical-posts.md` |
| Resources | `resources/post-templates/` |
| Use for | Writing deep-dive technical posts about what was built and how |

### Skill 3 — Short-Form Social Content
| Layer | Path |
|-------|------|
| Directive | `directives/social-content.md` |
| Resources | `resources/content-calendar.md` |
| Use for | Daily/every-other-day posts on LinkedIn and X showing what was built and learned |

**Platforms**:
- **LinkedIn** — professional audience, decision-maker reach
- **X (Twitter)** — builder/developer audience, speed of feedback
- **Discord** — community updates (if applicable)

### Skill 4 — Open Source Releases
| Layer | Path |
|-------|------|
| Directive | `directives/open-source.md` |
| Resources | `resources/oss-checklist.md` |
| Use for | Releasing non-proprietary components publicly (integration clients, eval harness, approval engine) |

### Skill 5 — LinkedIn API
| Layer | Path |
|-------|------|
| Directive | `directives/linkedin-api.md` |
| Execution | `executions/linkedin_api.py` |
| Resources | Root `.env` (LINKEDIN_ACCESS_TOKEN), `shared/linkedin_oauth.py` (re-auth flow) |
| Use for | Full LinkedIn API access: create/edit/delete posts (text, image, video, article), upload media, comment, react, read engagement analytics, manage comment threads. Use this skill whenever a task involves publishing to LinkedIn or reading LinkedIn data. |

**Capabilities**:
- **Posts**: text, image, video, article, reshare, poll, multi-image — full CRUD
- **Media upload**: images (JPG/PNG/GIF) and videos (MP4, multi-part, captions, thumbnails)
- **Comments**: create, reply, edit, delete, mention, image-in-comment
- **Reactions**: LIKE, PRAISE, EMPATHY, INTEREST, APPRECIATION, ENTERTAINMENT
- **Analytics**: engagement summaries via Social Metadata API (reaction counts, comment counts)
- **Thread moderation**: enable/disable comments on any owned post

### Skill 6 — Apollo Prospecting API
| Layer | Path |
|-------|------|
| Directive | `directives/apollo-prospecting.md` |
| Execution | `executions/apollo_api.py` |
| Resources | Root `.env` (APOLLO_API_KEY) |
| Use for | Prospect research, company enrichment by domain, contact CRM management, and ICP qualification. Use this skill whenever a task involves finding company data, enriching prospects, or managing the outbound pipeline. |

**Capabilities** (Free plan — verified 2026-04-15):
- **Organization Enrichment**: full firmographic profile by domain (industry, headcount, revenue, tech stack, funding, keywords) — 1 credit/call
- **Contact CRM**: create, update, and search contacts in Apollo — free
- **Account Search**: search your saved accounts — free
- **People Search** *(paid plan required)*: search Apollo's 210M+ database by title, seniority, location, company size, tech stack
- **People Enrichment** *(paid plan required)*: get email/phone for a specific person
- **Org Search** *(paid plan required)*: search company database with advanced filters

**Auth**: `x-api-key` header. Key in root `.env` as `APOLLO_API_KEY`.

**Credit budget**: 100/month (Free plan). Never burn >10 credits in a single automated run without user confirmation.

---

## Sprint Tasks (14-Day Blitz)

### Day 13–14: Case Study, Public Artefacts, Pipeline Review

**Ship the story**:
- [ ] Write case study document: problem → solution → architecture → results → learnings
- [ ] Write 2–3 short-form posts (LinkedIn / X) showing what was built and what was learned
- [ ] Write 1 technical blog post or record demo video walking through the full stack
- [ ] Open-source at least one non-proprietary component (integration client, eval harness, or approval engine)
- [ ] Publish all artefacts

**Checkpoint**: Public proof that you built and shipped a real agentic system. Clear audience signal.

### Ongoing (All Days):
- [ ] Log at least 1 short-form content idea per day from building activity
- [ ] Capture screenshots, architecture diagrams, and demo recordings as you build
