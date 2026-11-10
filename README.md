# Agent Skills

[![skills.sh](https://skills.sh/b/stewartmoreland/skills)](https://skills.sh/stewartmoreland/skills)

A collection of reusable AI coding agent skills structured for the [skills.sh](https://www.skills.sh) ecosystem and the [Vercel `skills` CLI](https://github.com/vercel-labs/skills).

Compatible with **Claude Code**, **Cursor**, **Codex**, **Antigravity**, **GitHub Copilot**, **Windsurf**, **OpenCode**, and [75+ other coding agents](https://www.skills.sh/docs).

---

## Quick Start

Requires Node.js 22.20+. Run from your project directory:

```bash
# Interactively choose skills and target agents from this repository
npx skills add stewartmoreland/skills

# List all available skills in this repository
npx skills add stewartmoreland/skills --list

# Install a specific skill
npx skills add stewartmoreland/skills --skill fastapi-service-architecture

# Install globally across all projects for a specific agent
npx skills add stewartmoreland/skills --skill framer-motion -g -a claude-code

# Use a skill on-the-fly without installing
npx skills use stewartmoreland/skills@lighthouse-audit --agent claude-code
```

---

## Included Skills

### Animation & Creative Direction

| Skill | Description | Install Command |
| :--- | :--- | :--- |
| [`framer-motion`](skills/framer-motion/SKILL.md) | Build, refine, and debug animations in React (`motion/react`) and React Native with spring physics, layout transitions, gestures, and scroll choreography. | `npx skills add stewartmoreland/skills --skill framer-motion` |
| [`reanimated-v4`](skills/reanimated-v4/SKILL.md) | Production animations in React Native with `react-native-reanimated` v4 (worklets, CSS animations/transitions, layout animations, and gesture-driven motion). | `npx skills add stewartmoreland/skills --skill reanimated-v4` |
| [`react-native-skia`](skills/react-native-skia/SKILL.md) | Custom 2D graphics, interactive financial/price charts, shaders (SKSL), glassmorphism, and offline rendering with `@shopify/react-native-skia`. | `npx skills add stewartmoreland/skills --skill react-native-skia` |
| [`lottie-animation`](skills/lottie-animation/SKILL.md) | Create, refine, debug, validate, and package Lottie JSON animations and dotLottie v2.0 bundles (themes, state machines, and multi-platform renderers). | `npx skills add stewartmoreland/skills --skill lottie-animation` |
| [`story-craft`](skills/story-craft/SKILL.md) | Creative direction, scripting, storyboarding, beat sheets, learning design, and pacing critique for explainer videos, motion graphics, and animated media. | `npx skills add stewartmoreland/skills --skill story-craft` |
| [`visual-craft`](skills/visual-craft/SKILL.md) | Art-direction and frame-driven visual execution layer for Remotion video scenes, compositions, camera choreography, and shaders/effects. | `npx skills add stewartmoreland/skills --skill visual-craft` |

### Mobile & App Store

| Skill | Description | Install Command |
| :--- | :--- | :--- |
| [`expo-ar`](skills/expo-ar/SKILL.md) | Build custom Expo native modules bridging Apple ARKit (Swift) and Google ARCore (Kotlin) with plane detection, raycasting, LiDAR/Depth API, and 3D anchors. | `npx skills add stewartmoreland/skills --skill expo-ar` |
| [`koubou`](skills/koubou/SKILL.md) | Generate localized App Store screenshots for iPhone, iPad, Mac, and Apple Watch using HTML/CSS templates and device frames. | `npx skills add stewartmoreland/skills --skill koubou` |

### Web, Frontend & APIs

| Skill | Description | Install Command |
| :--- | :--- | :--- |
| [`tiptap-blog-editor`](skills/tiptap-blog-editor/SKILL.md) | Build rich-text WYSIWYG blog/article editors with TipTap v3 (ProseMirror), SSR-safe React/Next.js setup, toolbars, bubble menus, and persistence. | `npx skills add stewartmoreland/skills --skill tiptap-blog-editor` |
| [`hey-api-openapi-ts`](skills/hey-api-openapi-ts/SKILL.md) | Generate type-safe TypeScript SDKs, HTTP clients, Zod/Valibot validators, and TanStack Query/SWR hooks from OpenAPI specifications using `@hey-api/openapi-ts`. | `npx skills add stewartmoreland/skills --skill hey-api-openapi-ts` |
| [`lighthouse-audit`](skills/lighthouse-audit/SKILL.md) | Drive web performance (Core Web Vitals), SEO, accessibility, Lighthouse CI, and Agentic Browsing readiness (WebMCP, `llms.txt`) with Lighthouse v13+. | `npx skills add stewartmoreland/skills --skill lighthouse-audit` |

### Backend, Data & AI

| Skill | Description | Install Command |
| :--- | :--- | :--- |
| [`fastapi-service-architecture`](skills/fastapi-service-architecture/SKILL.md) | Layered async FastAPI service architecture with SQLAlchemy 2.0 repositories, cursor/offset pagination, request-scoped sessions, Postgres RLS multi-tenancy, and uv workspaces. | `npx skills add stewartmoreland/skills --skill fastapi-service-architecture` |
| [`geospatial`](skills/geospatial/SKILL.md) | Ingest, reproject, tile, query, and model geospatial & hydrologic data with PostGIS, GDAL, Rasterio, rio-tiler, PySheds, TauDEM, GeoPandas, PMTiles, and Mapbox. | `npx skills add stewartmoreland/skills --skill geospatial` |
| [`ultralytics-yolo`](skills/ultralytics-yolo/SKILL.md) | Build, train, evaluate, track, and export computer-vision models (detection, segmentation, pose, OBB) with Ultralytics YOLO for cloud and edge deployment. | `npx skills add stewartmoreland/skills --skill ultralytics-yolo` |
| [`drawpyo`](skills/drawpyo/SKILL.md) | Programmatically generate editable Draw.io / diagrams.net (`.drawio`) architecture, tree, and flowchart diagrams in Python using `drawpyo`. | `npx skills add stewartmoreland/skills --skill drawpyo` |

---

## Repository Structure

```text
.
├── README.md
├── skills.sh.json              # skills.sh repo page groupings & display configuration
└── skills/                     # Standard multi-skill discovery directory
    ├── drawpyo/
    ├── expo-ar/
    ├── fastapi-service-architecture/
    ├── framer-motion/
    ├── geospatial/
    ├── hey-api-openapi-ts/
    ├── koubou/
    ├── lighthouse-audit/
    ├── lottie-animation/
    ├── react-native-skia/
    ├── reanimated-v4/
    ├── story-craft/
    ├── tiptap-blog-editor/
    ├── ultralytics-yolo/
    └── visual-craft/
```

Each skill directory contains a `SKILL.md` file with YAML frontmatter (`name` and `description`) along with supporting `references/`, `assets/`, or `scripts/`.

## Adding or Updating Skills

To scaffold a new skill in this collection:

```bash
npx skills init skills/<new-skill-name>
```

To verify local discovery with the Vercel Skills CLI:

```bash
npx skills add . --list
```
