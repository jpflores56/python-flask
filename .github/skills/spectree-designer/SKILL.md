---
name: SpecTree Designer
description: "Design-to-code fidelity skill. Extracts Figma designs via MCP tools (stdio transport), generates or fixes pixel-perfect code across any framework, and iterates to <1% visual diff using Playwright + pixelmatch. Supports Build mode (create from scratch) and Fix mode (match existing code to design)."
---

# SpecTree Designer Skill

Convert Figma designs into pixel-perfect code with **<1% visual diff**. Works with React, Angular, Vue, Svelte, Next.js, Nuxt, or static HTML.

> **How it works:** Extract the design → scout your codebase for reusable tokens/components → generate or fix code → screenshot → compare pixel-by-pixel → iterate until ≤1% diff → show you the proof.

---

## Phase 0: Prerequisites Check

Before anything else, verify the environment is ready.

### Step 0.1: Check Figma MCP Connectivity

Test that the Figma MCP server is available by calling:

```
figma_get_file_data({ depth: 0 })
```

- If this **succeeds** → Figma MCP is connected. Continue.
- If this **fails** → show the setup guide below and STOP.

### Step 0.2: Check Playwright

```bash
node -e "require('playwright')" 2>/dev/null
```

- If exit code 0 → installed as a project dependency. Continue.
- If not found → add to setup checklist. Playwright must be a project dev dependency (`pnpm add -D playwright`), not just available via `npx`.

### Step 0.3: Check pixelmatch + pngjs

```bash
node -e "require('pixelmatch'); require('pngjs')" 2>/dev/null
```

- If exit code 0 → installed. Continue.
- If not found → add to setup checklist.

### Step 0.4: Setup Guide (show only if anything is missing)

If ANY prerequisite is missing, show this guide and STOP:

```
╔══════════════════════════════════════════════════════════════╗
║  SPECTREE-DESIGNER SETUP                                     ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  1. FIGMA MCP SERVER                                         ║
║     Add to your Copilot MCP config:                          ║
║                                                              ║
║     VS Code: Settings → Copilot → MCP → Edit in settings.json║
║     Add under "mcp.servers":                                 ║
║                                                              ║
║     "figma": {                                               ║
║       "type": "stdio",                                       ║
║       "command": "npx",                                      ║
║       "args": ["-y", "@anthropic/figma-mcp-server"],         ║
║       "env": {                                               ║
║         "FIGMA_PERSONAL_ACCESS_TOKEN": "<your-token>"        ║
║       }                                                      ║
║     }                                                        ║
║                                                              ║
║     Get your token:                                          ║
║     Figma → Settings → Personal Access Tokens → Generate    ║
║                                                              ║
║  2. PLAYWRIGHT                                               ║
║     pnpm:  pnpm add -D playwright                            ║
║     npm:   npm install -D playwright                         ║
║     yarn:  yarn add -D playwright                            ║
║     Then install the browser:                                ║
║     npx playwright install chromium                          ║
║                                                              ║
║  3. PIXELMATCH (detect package manager first)                ║
║     pnpm:  pnpm add -D pixelmatch pngjs                     ║
║     npm:   npm install -D pixelmatch pngjs                   ║
║     yarn:  yarn add -D pixelmatch pngjs                      ║
║                                                              ║
║  4. HOW TO GET A FIGMA FRAME LINK                            ║
║     • Open your Figma file                                   ║
║     • Select the frame/component you want to implement       ║
║     • Right-click → "Copy link to selection"                 ║
║     • Paste the URL when invoking this skill                 ║
║     • URL format: https://figma.com/design/{fileKey}/...     ║
║       ?node-id={nodeId}                                      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

After the user installs prerequisites, re-run Phase 0 checks.

---

## Phase 1: Input & Context Gathering

### Step 1.1: Parse Figma URL

Extract `fileKey` and `nodeId` from the user-provided Figma URL.

Supported formats:
- `https://www.figma.com/design/{fileKey}/{name}?node-id={nodeId}`
- `https://www.figma.com/file/{fileKey}/{name}?node-id={nodeId}`
- `https://figma.com/design/{fileKey}?node-id={nodeId}`
- Node IDs may use `%3A` encoding for `:` — decode it.

If the user provides only a file URL without `node-id`, ask them to select a specific frame and paste the link with the node selected.

### Step 1.2: Extract Figma Frame Dimensions (CRITICAL)

Call `figma_get_file_data` to get the frame's exact dimensions:

```
figma_get_file_data({ nodeIds: ["{nodeId}"], verbosity: "standard", depth: 0 })
```

Extract from the response:
- `absoluteBoundingBox.width` → **viewportWidth**
- `absoluteBoundingBox.height` → **viewportHeight**

🔴 **These dimensions are the source of truth for Playwright viewport size.** If the viewport doesn't match the Figma frame, pixel comparison is meaningless.

Store: `viewport = { width: viewportWidth, height: viewportHeight }`

### Step 1.3: Auto-Detect Framework

Read `package.json` in the project root and check `dependencies` + `devDependencies`:

| Dependency | Framework |
|------------|-----------|
| `react` or `react-dom` | React |
| `next` | Next.js |
| `@angular/core` | Angular |
| `vue` | Vue |
| `nuxt` | Nuxt |
| `svelte` | Svelte |
| `@sveltejs/kit` | SvelteKit |
| None of the above | Static HTML/CSS |

**Monorepo note:** If the root `package.json` doesn't have framework deps (common in monorepos), scan the package that contains the target component. Use the workspace structure detected in Step 1.7 to find the right `package.json` (e.g., `packages/web/package.json` or the package containing the target route).

### Step 1.4: Auto-Detect Styling Approach

Scan for styling patterns:

| Signal | Styling Approach |
|--------|------------------|
| `tailwindcss` in deps + `tailwind.config.*` exists | Tailwind CSS |
| `*.module.css` or `*.module.scss` files exist | CSS Modules |
| `*.scss` files + no modules | SCSS (global) |
| `styled-components` or `@emotion/styled` in deps | CSS-in-JS |
| `*.vue` files with `<style scoped>` | Vue Scoped Styles |
| `*.svelte` files with `<style>` | Svelte Scoped Styles |
| None of the above | Vanilla CSS |

### Step 1.5: Detect Mode (Build vs Fix)

Determine whether to CREATE a new component or FIX an existing one:

- If the user specifies a target file/component and it **exists** → **Fix mode**
- If the user specifies a target file/component and it **does NOT exist** → **Build mode**
- If ambiguous → ask the user: "Should I create a new component or fix an existing one?"

### Step 1.5b: Determine Page Route

Determine the URL path where the component is rendered:

1. **User specified a URL/route** → use it directly (e.g., `/dashboard`, `/login`)
2. **Fix mode** → scan the framework's router config to find the component's route:
   - React Router: search `src/` for `<Route` elements referencing the component
   - Next.js: derive from file path in `app/` or `pages/` directory
   - Angular: search `*-routing.module.ts` for the component's path
   - Vue Router: search `router/` config for the component reference
3. **Build mode** → ask the user: "What route should this component be accessible at?"
4. **Fallback** → default to `/` if no route can be determined

Store: `pageRoute = "/dashboard"` (or whatever is determined)

### Step 1.6: Read Existing Project Config

Check if `pd-config.json` exists in the project root (backward compat with Pixel Developer):
```bash
cat pd-config.json 2>/dev/null
```
If it exists, merge its values (devServer, colorTokens, radiusTokens, iconComponent, etc.) into the context. Otherwise, infer from the codebase.

### Step 1.7: Detect Dev Server Command

First, detect the package manager (use an if/elif chain — stop at first match to avoid ambiguity from leftover lockfiles):

```bash
# Prefer packageManager field in package.json (most authoritative)
node -e "const pm = require('./package.json').packageManager; if (pm) console.log(pm.split('@')[0])" 2>/dev/null

# Fallback: check lockfiles in priority order (stop at first match)
if [ -f "pnpm-lock.yaml" ]; then echo "pnpm"
elif [ -f "yarn.lock" ]; then echo "yarn"
elif [ -f "package-lock.json" ]; then echo "npm"
fi
```

Store: `pkgManager = "pnpm" | "yarn" | "npm"`

Then scan `package.json` scripts for the dev server command, using the detected package manager:

| Script name | pnpm | npm | yarn |
|-------------|------|-----|------|
| `dev` | `pnpm dev` | `npm run dev` | `yarn dev` |
| `start` | `pnpm start` | `npm start` | `yarn start` |
| `serve` | `pnpm serve` | `npm run serve` | `yarn serve` |
| Angular `ng serve` | `pnpm ng serve` | `npx ng serve` | `yarn ng serve` |

For monorepos (detected by `pnpm-workspace.yaml`, `workspaces` in package.json, or Turborepo `turbo.json`):
- Determine which package contains the target component
- Use filtered commands: `pnpm --filter <pkg> dev`, `yarn workspace <pkg> dev`, etc.

Also detect the expected port from the script or default:
- Next.js: 3000
- Angular: 4200
- Vite (React/Vue/Svelte): 5173
- Nuxt: 3000
- Custom: read from script args (`--port XXXX`)

Store: `devServer = { command, url: "http://localhost:{port}" }`

### Step 1.8: Discover Project Coding Standards

🔴 **This step is critical.** All code generated or modified by this skill MUST conform to the project's existing standards. Do NOT invent patterns — learn them from the codebase.

#### 1.8a: Read Linter & Formatter Configs

Check for and read these configuration files:

```bash
# Linting
ls .eslintrc.* eslint.config.* .stylelintrc.* biome.json 2>/dev/null

# Formatting
ls .prettierrc* .editorconfig 2>/dev/null

# TypeScript
ls tsconfig.json tsconfig.app.json 2>/dev/null
```

Extract key settings:
- **Quotes**: single vs double (`singleQuote: true`)
- **Semicolons**: with or without
- **Indent**: tabs vs spaces, indent size
- **Trailing commas**: always, never, ES5
- **Import ordering**: grouped? sorted? plugin used?
- **CSS/SCSS rules**: any Stylelint rules about property order, naming, nesting depth

#### 1.8b: Learn Import Patterns from Existing Code

Read 2-3 existing component files and note:

| Pattern | Example | How to detect |
|---------|---------|---------------|
| **Path aliases** | `import { Button } from '@/components/ui/button'` | Check `tsconfig.json` paths or `vite.config.*` resolve.alias |
| **Barrel exports** | `import { Button, Card } from '@/components'` | Check for `index.ts` files in component dirs |
| **Relative imports** | `import { utils } from '../../lib/utils'` | No alias config found |
| **Import grouping** | External → internal → relative → styles | Read ESLint import plugin config or observe pattern in files |

Store the detected import style so ALL generated imports follow it.

#### 1.8c: Learn File Naming & Location Conventions

Scan the existing project structure:

```bash
# What does the component directory structure look like?
find src/ -maxdepth 4 -type d | head -30

# How are component files named?
git ls-files 'src/**/*.tsx' 'src/**/*.vue' 'src/**/*.component.ts' | head -15
```

Detect:
- **File naming**: PascalCase (`Button.tsx`), kebab-case (`button.tsx`), or dot-notation (`button.component.ts`)
- **Co-location**: Are styles next to components? Tests next to components? Or in separate dirs?
- **Feature organization**: By feature (`features/auth/`) or by type (`components/`, `pages/`, `hooks/`)?
- **Where new components go**: `src/components/`, `src/app/`, `src/features/`, `app/components/`

🔴 **New files MUST go in the correct directory following the project's convention.**

#### 1.8d: Learn Component Patterns from Real Code

Read 2-3 of the project's **best** existing components (pick ones that are well-structured and similar to the target). For each, note:

- **How props/inputs are defined** — interfaces? types? decorators? inline?
- **How styles are applied** — className? class? Tailwind utilities? CSS Modules? styled()? 
- **How state is managed** — useState? signals? @Input/@Output? Pinia? Zustand?
- **How events are handled** — onClick? (click)? @click? on:click?
- **Export style** — default export? named export? both?
- **Component structure** — hooks at top? render helpers? sub-components in same file?

Store these patterns as the **component blueprint** — all generated code must follow this exact structure.

#### 1.8e: Detect CSS Methodology in Practice

Beyond the config files, scan actual CSS/SCSS to confirm the methodology:

```bash
# Check for Tailwind usage in templates
grep -r "className=" src/ --include="*.tsx" --include="*.jsx" | head -5
grep -r "class=" src/ --include="*.vue" --include="*.svelte" --include="*.html" | head -5

# Check for CSS Modules
git ls-files 'src/**/*.module.css' 'src/**/*.module.scss' | head -5

# Check for BEM patterns
grep -rE '\.[a-z]+__[a-z]' src/ --include="*.scss" --include="*.css" | head -5

# Check for styled-components
grep -r "styled\." src/ --include="*.tsx" --include="*.ts" | head -5
```

The detected methodology is the ONLY one to use. If the project uses Tailwind, NEVER generate raw CSS. If it uses BEM SCSS, NEVER use Tailwind classes.

Store as `codingStandards` (in-memory):
```
codingStandards:
  quotes: "single" | "double"
  semicolons: true | false
  indent: { type: "spaces" | "tabs", size: 2 | 4 }
  imports: { style: "aliases" | "barrel" | "relative", alias: "@/" | "~/" | null, groupOrder: [...] }
  fileNaming: "PascalCase" | "kebab-case" | "dot-notation"
  componentDir: "src/components/" | "src/app/" | ...
  coLocation: { styles: true | false, tests: true | false }
  exportStyle: "default" | "named" | "both"
  cssMethods: "tailwind" | "css-modules" | "scss-bem" | "css-in-js" | "scoped" | "vanilla"
  propsPattern: "interface" | "type" | "inline" | "decorator"
  componentBlueprint: { ... } // structure learned from reading real components
```

---

## Phase 2: Design Extraction (Ground Truth)

### Step 2.1: Capture Reference Screenshot

```
figma_take_screenshot({ nodeId: "{nodeId}", scale: 2, format: "png" })
```

This returns an image URL. Download it and save to `.pixel-perfect/reference.png`:

```bash
mkdir -p .pixel-perfect
curl -sL "{imageUrl}" -o .pixel-perfect/reference.png
```

🔴 **Record the exact pixel dimensions** of this image. At scale=2, a 1440×900 frame produces a 2880×1800 PNG. Store: `referenceDimensions = { width, height }`

### Step 2.2: Extract Component Specs

```
figma_get_component_for_development({ nodeId: "{nodeId}" })
```

This returns layout specs (dimensions, padding, spacing, auto-layout) plus a rendered image. Use this as the primary source for element-level specs.

### Step 2.3: Extract Design Tokens

```
figma_get_variables({ resolveAliases: true, format: "full" })
```

This resolves all variable aliases to their final values (hex colors, numbers). Store the resolved tokens for matching against code later.

### Step 2.4: Extract Styles

```
figma_get_styles({ verbosity: "standard" })
```

Captures text styles (font family, size, weight, line-height, letter-spacing) and color styles.

### Step 2.5: Extract Node Tree

```
figma_get_file_data({ nodeIds: ["{nodeId}"], verbosity: "standard", depth: 3 })
```

Walk the node tree to build the **design-spec** — a structured mental model of every element:

```
design-spec (in-memory):
  viewport: { width, height }
  referencePath: ".pixel-perfect/reference.png"
  referenceDimensions: { width, height }
  elements: [
    {
      name: "Header Bar",
      type: "frame",
      bounds: { x, y, width, height },
      layout: { type: "auto-layout", direction: "horizontal", gap, padding },
      fills: [{ color: "#080D12", opacity: 1 }],
      strokes: [...],
      effects: [...],
      borderRadius: { topLeft, topRight, bottomLeft, bottomRight },
      typography: { fontFamily, fontSize, fontWeight, lineHeight, letterSpacing, color },
      textContent: "...",
      children: [...]
    }
  ]
  tokens: { colors: {}, spacing: {}, typography: {}, radii: {}, shadows: {} }
  assets: [{ nodeId, name, type: "svg"|"png" }]
```

### Step 2.6: Export Assets (icons, images)

For each image or icon node identified in the tree:

```
figma_take_screenshot({ nodeId: "{assetNodeId}", format: "svg", scale: 1 })
```

Save to the project's assets directory (detect location from existing assets or use `src/assets/`).

---

## Phase 3: Codebase Scout

### Step 3.1: Scan Component Library

Search for existing UI component library in the project:

```bash
# React: shadcn/ui, MUI, Mantine, Chakra, Radix
ls node_modules/@radix-ui node_modules/@mui node_modules/@mantine node_modules/@chakra-ui 2>/dev/null
# Check for shadcn components
ls src/components/ui/ 2>/dev/null

# Angular: Angular Material, PrimeNG, NgZorro
ls node_modules/@angular/material node_modules/primeng 2>/dev/null

# Vue: Vuetify, PrimeVue, Quasar, Element Plus
ls node_modules/vuetify node_modules/primevue node_modules/quasar 2>/dev/null
```

For each library found, note its component naming patterns and available components.

🔴 **COMPONENT REUSE RULE:** Before creating ANY custom UI element, you MUST check if an existing component can do the job. Creating a custom `<div class="button">` when the project has a `<Button>` component is a violation. The order of preference is:

1. **Use existing shared component as-is** (e.g., `<Button variant="primary">`)
2. **Use existing component with style overrides** (e.g., `<Button className="custom-width">`)
3. **Use the component library's primitive** (e.g., `<Card>` from shadcn instead of custom div)
4. **Create custom HTML only as last resort** — when NO existing component matches

### Step 3.2: Scan Design Token Files

Based on the styling approach detected in Phase 1:

| Approach | Token file patterns |
|----------|-------------------|
| Tailwind | `tailwind.config.*`, `theme.ts`, `tokens.ts` |
| SCSS | `_variables.scss`, `_colors.scss`, `_tokens.scss` |
| CSS Vars | Search for `:root { --` in `*.css` files |
| CSS-in-JS | `theme.ts`, `theme.js`, `tokens.ts` |

Read token files and build a token catalog mapping hex values → token names.

### Step 3.3: Scan Existing Similar Components

Use the agent's search tools to find component files in the project:

```bash
# Find component files matching the detected framework
find src/ -type f \( -name "*.tsx" -o -name "*.jsx" -o -name "*.vue" -o -name "*.svelte" -o -name "*.component.ts" \) | head -20
```

Or with git (faster, respects .gitignore):
```bash
git ls-files 'src/**/*.tsx' 'src/**/*.jsx' 'src/**/*.vue' 'src/**/*.svelte' 'src/**/*.component.ts' | head -20
```

Read 2-3 existing components similar to the target (by name or purpose) to understand:
- Naming conventions used
- Layout patterns (flex vs grid)
- How design tokens are consumed
- Import patterns

### Step 3.4: Build Reuse Map

🔴 **Every design element MUST be mapped** before any code is written. For each element in the design-spec, explicitly record whether it maps to an existing component or requires custom code.

Produce a **reuse-map** (in-memory) that maps design-spec elements to existing code:

```
reuse-map (in-memory):
  sharedComponents: [
    { name, selector/import, props, matchesDesignElements: [...] }
  ]
  designTokens: {
    colors: { "#hex": "var(--token-name)" | "$scss-var" | "tailwind-class" },
    spacing: { "8": "gap-2" | "$spacing-sm" | "var(--space-2)" },
    radii: { "8": "rounded-lg" | "$radius-sm" },
    shadows: { ... }
  }
  elementMapping: [
    { designElement: "Primary Button", strategy: "reuse", component: "Button", import: "@/components/ui/button" },
    { designElement: "User Avatar", strategy: "reuse", component: "Avatar", import: "@/components/ui/avatar" },
    { designElement: "Stats Grid", strategy: "custom", reason: "no matching component exists" }
  ]
  conventions: {
    naming: "BEM" | "PascalCase" | "kebab-case",
    layoutPreference: "flexbox" | "grid" | "mixed",
    tokenUsage: "css-vars" | "scss-vars" | "tailwind" | "css-in-js"
  }
```

If more than 30% of design elements are mapped as "custom" when the project has a component library, **re-examine** — you're likely missing reusable components.

---

## Phase 3.5: Build Mode (ONLY if component doesn't exist — skip in Fix mode)

### Step 3.5.1: Generate Component Skeleton

Using the framework adaptation table (see appendix) **AND the coding standards discovered in Phase 1.8**, generate the correct file structure. The file MUST be:
- Named following the project's naming convention (`codingStandards.fileNaming`)
- Placed in the project's standard component directory (`codingStandards.componentDir`)
- Structured to match the component blueprint from Phase 1.8d

| Framework | Files to create |
|-----------|----------------|
| React | `ComponentName.tsx` + `ComponentName.module.css` (or Tailwind inline) |
| Angular | `component-name.component.ts` + `.html` + `.scss` |
| Vue | `ComponentName.vue` (SFC with `<template>`, `<script>`, `<style>`) |
| Svelte | `ComponentName.svelte` |
| Next.js | `page.tsx` or `ComponentName.tsx` + styles |
| Static | `index.html` + `styles.css` |

### Step 3.5.2: Apply Design Spec

Walk the design-spec elements and generate:
1. **HTML/Template structure** — match the element hierarchy from Figma, using **existing shared components** from the reuse-map wherever possible (not custom HTML)
2. **Styles** — apply dimensions, colors, typography, spacing from design-spec, using **only tokens and the project's CSS methodology** (never hardcode values, never use a different styling approach)
3. **Assets** — reference exported SVGs/PNGs
4. **Imports** — follow the project's import pattern from `codingStandards.imports`
5. **Props/Types** — follow the project's props pattern from `codingStandards.propsPattern`

### Step 3.5.3: Verify Build

Run the framework's build/type-check command:
```bash
# Detect from framework table
{buildCheckCommand} 2>&1 | tail -20
```

If build fails → fix compilation errors before continuing.

### Step 3.5.4: Take Baseline Screenshot

Start the dev server, take the first screenshot, and establish the initial diff % baseline. This feeds into Phase 4.

---

## Phase 4: Comparison & Fix Loop

This is the core engine. Iterate up to **5 rounds** to reach ≤1% diff.

### Step 4.0: Ensure Dev Server Is Running

```bash
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" {devServer.url}/ 2>/dev/null)
CURL_EXIT=$?
```

- If `CURL_EXIT` is 0 (any HTTP response received, including `404`, `302`) → server is running. Continue.
- If `CURL_EXIT` is non-zero (connection refused, DNS failure) OR `HTTP_CODE` is `000` → server is NOT running. Start it:
  ```bash
  {devServer.command} &
  DEV_SERVER_PID=$!
  # Wait for server to be ready (poll every 2s, max 30s — accept any HTTP response)
  for i in $(seq 1 15); do
    curl -s -o /dev/null {devServer.url}/ 2>/dev/null && break
    sleep 2
  done
  ```
  Store `DEV_SERVER_PID` — the skill will print cleanup instructions at the end (Phase 5.3).
- If server won't start after 30s → check for port conflict: `lsof -i :{port}`. Report to user.

### Step 4.1: Capture Implementation Screenshot

Write and execute an inline Node.js script:

```bash
mkdir -p .pixel-perfect
cat > .pixel-perfect/capture.mjs << 'CAPTURE_EOF'
import { chromium } from 'playwright';
import * as fs from 'fs';

const DETERMINISTIC_CSS = `
  *, *::before, *::after {
    animation-duration: 0s !important;
    animation-delay: 0s !important;
    transition-duration: 0s !important;
    transition-delay: 0s !important;
    caret-color: transparent !important;
    scroll-behavior: auto !important;
  }
  ::-webkit-scrollbar { display: none !important; }
  * { scrollbar-width: none !important; }
  * { -webkit-font-smoothing: antialiased !important; }
  * { cursor: none !important; }
`;

const url = process.argv[2];
const outPath = process.argv[3] || '.pixel-perfect/actual.png';
const vpWidth = parseInt(process.argv[4]) || 1440;
const vpHeight = parseInt(process.argv[5]) || 900;

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: vpWidth, height: vpHeight },
  deviceScaleFactor: 2,
});
const page = await context.newPage();

await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
await page.addStyleTag({ content: DETERMINISTIC_CSS });

// Wait for fonts and rendering to settle
await page.evaluate(() => document.fonts.ready);
// Wait for lazy-loaded content (images, async components)
await page.waitForLoadState('networkidle').catch(() => {});
// Extra settle time for animations/transitions being disabled
await page.waitForTimeout(1000);

await page.screenshot({ path: outPath, fullPage: false });
await browser.close();

console.log(JSON.stringify({ path: outPath, viewport: { width: vpWidth, height: vpHeight }, scale: 2 }));
CAPTURE_EOF
node .pixel-perfect/capture.mjs "{devServer.url}{pageRoute}" ".pixel-perfect/actual.png" {viewport.width} {viewport.height}
```

🔴 **Critical:** The viewport width/height MUST match the Figma frame dimensions from Step 1.2. `deviceScaleFactor: 2` must match the Figma export `scale: 2`.

**Hot-reload awareness (iterations 2+):** After code changes, wait before capturing:
```bash
sleep 2  # HMR debounce
curl -s -o /dev/null -w "%{http_code}" {devServer.url}/ 2>/dev/null  # verify server alive
```

### Step 4.2: Run Pixel Comparison

Write and execute an inline comparison script:

```bash
cat > .pixel-perfect/compare.mjs << 'COMPARE_EOF'
import { PNG } from 'pngjs';
import pixelmatch from 'pixelmatch';
import * as fs from 'fs';

const refPath = process.argv[2] || '.pixel-perfect/reference.png';
const actPath = process.argv[3] || '.pixel-perfect/actual.png';
const diffPath = process.argv[4] || '.pixel-perfect/diff.png';

const refImg = PNG.sync.read(fs.readFileSync(refPath));
const actImg = PNG.sync.read(fs.readFileSync(actPath));

// If dimensions differ by ≤10px, crop both to the smaller size
let { width, height } = refImg;
if (Math.abs(refImg.width - actImg.width) > 10 || Math.abs(refImg.height - actImg.height) > 10) {
  console.error(JSON.stringify({
    error: 'dimension_mismatch',
    reference: { width: refImg.width, height: refImg.height },
    actual: { width: actImg.width, height: actImg.height },
    message: 'Screenshots have significantly different dimensions. Check viewport/DPI settings.'
  }));
  process.exit(1);
}

// Crop both images to the same dimensions (smallest common size)
width = Math.min(refImg.width, actImg.width);
height = Math.min(refImg.height, actImg.height);

function cropImageData(img, targetW, targetH) {
  const cropped = new PNG({ width: targetW, height: targetH });
  for (let y = 0; y < targetH; y++) {
    for (let x = 0; x < targetW; x++) {
      const srcIdx = (y * img.width + x) * 4;
      const dstIdx = (y * targetW + x) * 4;
      cropped.data[dstIdx] = img.data[srcIdx];
      cropped.data[dstIdx + 1] = img.data[srcIdx + 1];
      cropped.data[dstIdx + 2] = img.data[srcIdx + 2];
      cropped.data[dstIdx + 3] = img.data[srcIdx + 3];
    }
  }
  return cropped;
}

const refCropped = (refImg.width !== width || refImg.height !== height) ? cropImageData(refImg, width, height) : refImg;
const actCropped = (actImg.width !== width || actImg.height !== height) ? cropImageData(actImg, width, height) : actImg;

const diff = new PNG({ width, height });
const DIFF_COLOR = [255, 0, 255]; // magenta — explicitly configured
const numDiffPixels = pixelmatch(
  refCropped.data, actCropped.data, diff.data,
  width, height,
  { threshold: 0.15, includeAA: false, diffColor: DIFF_COLOR }
);

const totalPixels = width * height;
const diffPercent = ((numDiffPixels / totalPixels) * 100).toFixed(2);

// Quadrant analysis — count pixels matching the configured DIFF_COLOR
function quadrantDiff(diffData, fullW, fullH, x0, y0, qw, qh) {
  let count = 0;
  for (let y = y0; y < y0 + qh && y < fullH; y++) {
    for (let x = x0; x < x0 + qw && x < fullW; x++) {
      const idx = (y * fullW + x) * 4;
      if (diffData[idx] === DIFF_COLOR[0] && diffData[idx + 1] === DIFF_COLOR[1] && diffData[idx + 2] === DIFF_COLOR[2]) count++;
    }
  }
  return ((count / (qw * qh)) * 100).toFixed(2);
}

const halfW = Math.floor(width / 2);
const halfH = Math.floor(height / 2);
const rightW = width - halfW;   // handles odd widths
const bottomH = height - halfH; // handles odd heights
const quadrants = {
  topLeft: quadrantDiff(diff.data, width, height, 0, 0, halfW, halfH),
  topRight: quadrantDiff(diff.data, width, height, halfW, 0, rightW, halfH),
  bottomLeft: quadrantDiff(diff.data, width, height, 0, halfH, halfW, bottomH),
  bottomRight: quadrantDiff(diff.data, width, height, halfW, halfH, rightW, bottomH),
};

fs.writeFileSync(diffPath, PNG.sync.write(diff));

// Generate composite (reference | actual | diff side by side) using cropped images
const composite = new PNG({ width: width * 3, height });
for (let y = 0; y < height; y++) {
  for (let x = 0; x < width; x++) {
    const srcIdx = (y * width + x) * 4;
    // Reference
    const dst1 = (y * width * 3 + x) * 4;
    composite.data[dst1] = refCropped.data[srcIdx];
    composite.data[dst1+1] = refCropped.data[srcIdx+1];
    composite.data[dst1+2] = refCropped.data[srcIdx+2];
    composite.data[dst1+3] = refCropped.data[srcIdx+3];
    // Actual
    const dst2 = (y * width * 3 + (x + width)) * 4;
    composite.data[dst2] = actCropped.data[srcIdx];
    composite.data[dst2+1] = actCropped.data[srcIdx+1];
    composite.data[dst2+2] = actCropped.data[srcIdx+2];
    composite.data[dst2+3] = actCropped.data[srcIdx+3];
    // Diff
    const dst3 = (y * width * 3 + (x + width * 2)) * 4;
    composite.data[dst3] = diff.data[srcIdx];
    composite.data[dst3+1] = diff.data[srcIdx+1];
    composite.data[dst3+2] = diff.data[srcIdx+2];
    composite.data[dst3+3] = diff.data[srcIdx+3];
  }
}
fs.writeFileSync('.pixel-perfect/composite.png', PNG.sync.write(composite));

console.log(JSON.stringify({
  diffPercent: parseFloat(diffPercent),
  numDiffPixels,
  totalPixels,
  dimensions: { width, height },
  quadrants,
  paths: { reference: refPath, actual: actPath, diff: diffPath, composite: '.pixel-perfect/composite.png' }
}));
COMPARE_EOF
node .pixel-perfect/compare.mjs
```

Read the JSON output. If `diffPercent ≤ 1.0` → **PASS** → skip to Phase 5.

### Step 4.3: Analyze Diff Regions

Using the quadrant analysis and the diff image:

1. **Identify hotspot quadrant(s)** — which quadrant(s) have the highest diff %?
2. **Map hotspots to design-spec elements** — based on element positions in the design-spec, which elements fall in the hot quadrant?
3. **Cross-reference** — for each hot element, compare the design-spec value (expected) against the actual code value.
4. **Produce a prioritized fix-list** ordered by **cascading category**:

```
Priority 1: LAYOUT (width, height, display, flex-direction, grid, position)
  → Layout fixes cascade — fixing a container often fixes child positions
Priority 2: STRUCTURE (missing/extra DOM elements, wrong nesting)
  → Structural fixes change the element tree and can resolve multiple diffs
Priority 3: COLORS (background, text color, border color, fills)
  → Independent — fixing colors doesn't affect other properties
Priority 4: TYPOGRAPHY (font-family, font-size, font-weight, line-height, letter-spacing)
  → Independent
Priority 5: SPACING (margin, padding, gap)
  → May shift elements but lower cascade impact than layout
Priority 6: EFFECTS (box-shadow, border-radius, opacity, backdrop-filter)
  → Cosmetic — lowest cascade impact
```

### Step 4.4: Apply Fixes (One Category at a Time)

For each category in priority order:

1. **Apply all fixes in this category** using framework-appropriate patterns:
   - Use tokens from the reuse-map — **NEVER hardcode a value when a token exists** (e.g., use `text-red-500` not `color: #ef4444` in a Tailwind project; use `var(--brand-red)` not `#E11837` in a CSS vars project)
   - Use shared components from the reuse-map — **NEVER recreate a component that already exists** (e.g., if the project has a `<Button>`, use it instead of styling a `<button>` manually)
   - Follow the project's naming conventions from `codingStandards` (Phase 1.8)
   - Follow the project's import patterns (path aliases, barrel exports, grouping order)
   - Follow the project's CSS methodology — if Tailwind, use utility classes; if BEM SCSS, use BEM naming; if CSS Modules, use module imports
   - Match the component blueprint structure learned in Phase 1.8d (props definition, export style, hook placement, etc.)

2. **Build gate** — after applying fixes for this category, verify compilation:
   ```bash
   {buildCheckCommand} 2>&1 | tail -20
   ```
   - ✅ Build passes → continue to next category
   - ❌ Build fails → **rollback protocol**:
     1. Revert the edit(s) that caused the failure
     2. Log the failure reason
     3. Try an alternate approach (different CSS property, wrapper element, different selector specificity)
     4. If all alternates fail → skip this fix, mark as "needs manual review"

### Step 4.5: Standards Audit (Automated + Manual)

After all fixes are applied, run a comprehensive standards check. This is **not optional** — code that doesn't follow project standards is not acceptable even at 0% visual diff.

#### 4.5a: Run Project Linters & Formatters

First, detect which linter the project uses (check config files, not trial-and-error):

```bash
# Detect linter by config file presence
if [ -f "eslint.config.js" ] || [ -f "eslint.config.mjs" ] || ls .eslintrc.* 2>/dev/null; then
  echo "LINTER=eslint"
elif [ -f "biome.json" ] || [ -f "biome.jsonc" ]; then
  echo "LINTER=biome"
fi

# Detect formatter
if [ -f ".prettierrc" ] || [ -f ".prettierrc.js" ] || [ -f "prettier.config.js" ]; then
  echo "FORMATTER=prettier"
fi
```

Then run ONLY the detected tools on modified/created files:

```bash
# Run the project's detected linter (auto-fix mode)
# If ESLint: npx eslint --fix {modifiedFiles}
# If Biome:  npx biome check --fix {modifiedFiles}

# Run formatter (if detected)
# npx prettier --write {modifiedFiles}

# Run CSS/SCSS linter if .stylelintrc exists
# npx stylelint --fix {modifiedStyleFiles}
```

If the project has lint/format scripts in package.json (e.g., `lint`, `lint:fix`, `format`), prefer those using the detected package manager:
```bash
# Use detected pkgManager from Step 1.7
{pkgManager} run lint:fix
{pkgManager} run format
```

🔴 **Do NOT suppress stderr.** Linter errors and warnings must be visible so they can be read and manually fixed if auto-fix doesn't resolve them.

🔴 **Do NOT use `||` between linters** (e.g., `eslint || biome`). A lint error exit code is NOT a reason to try a different tool — it means there are violations to fix.

🔴 **If linter reports errors that can't be auto-fixed**, read the errors and manually fix the code to comply. Do NOT leave linter violations.

#### 4.5b: Component Reuse Verification

Scan the generated/modified code for violations:

1. **No component recreation** — search for raw HTML patterns that match existing components:
   ```
   ❌ <div class="btn btn-primary">Click</div>   → project has <Button> component
   ✅ <Button variant="primary">Click</Button>

   ❌ <div class="avatar"><img src={url} /></div> → project has <Avatar> component
   ✅ <Avatar src={url} />

   ❌ <input type="text" class="input" />          → project has <Input> component
   ✅ <Input type="text" />
   ```

2. **If a design element was mapped to "reuse" in the reuse-map but custom code was generated**, fix it NOW.

#### 4.5c: Token Usage Verification

Scan for hardcoded values that should use tokens:

- **Colors** — No hex values (`#xxx`), `rgb()`, or `hsl()` if a token exists for that color
- **Spacing** — No pixel values (`8px`, `16px`) if the project uses a spacing scale (Tailwind `p-2`, CSS var `var(--space-2)`)
- **Border radius** — No raw `4px`, `8px` if tokens exist (`rounded-md`, `var(--radius)`)
- **Font sizes** — No raw `14px`, `16px` if a type scale exists (`text-sm`, `var(--font-size-base)`)
- **Shadows** — No raw `box-shadow` values if shadow tokens exist

#### 4.5d: Import & File Convention Verification

Check that the code follows the patterns detected in Phase 1.8:

- **Import paths** use the project's alias pattern (not relative when aliases are standard)
- **Import grouping** follows the project's convention (externals → internals → relatives)
- **File is in the correct directory** per project structure conventions
- **File is named correctly** per project naming convention
- **Exports follow the project pattern** (default vs named)

#### 4.5e: CSS Methodology Compliance

Verify the styling approach matches the project:

| Project uses | Violation check |
|-------------|-----------------|
| **Tailwind** | No raw CSS in separate files. All styling via utility classes. Use `@apply` sparingly (or per project convention). |
| **CSS Modules** | Styles in `.module.css/scss` file, imported as `styles`. No global class names. |
| **BEM SCSS** | Class names follow `block__element--modifier`. No utility classes. |
| **styled-components** | Styles in `styled()` calls, not external CSS. No `className` with raw strings. |
| **Scoped styles** | Styles in `<style scoped>` block (Vue/Svelte). No global leakage. |

#### 4.5f: Additional Quality Checks

- **No inline styles** — all styling in stylesheet files or utility classes (per project convention)
- **No `!important`** — fix specificity issues properly
- **No unused imports** — clean up any imports added during fixes that are no longer needed
- **Accessibility** — interactive elements have appropriate ARIA attributes; images have alt text
- **TypeScript** — no `any` types if the project uses strict mode; proper typing on props/state

If any violations are found, fix them in place before proceeding. These are typically quick substitutions.

### Step 4.6: Progress Report (SHOW VISUAL PROOF)

After each iteration, report progress to the user **with the composite image**:

```
Show the user the composite image at .pixel-perfect/composite.png
```

Then display the metrics:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Iteration {N}/5
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Fidelity: {prevFidelity}% → {fidelity}% ({direction}{change}%)
  Overall diff: {diffPercent}%

  Quadrant breakdown:
    ┌──────────┬──────────┐
    │ TL {q1}% │ TR {q2}% │
    ├──────────┼──────────┤
    │ BL {q3}% │ BR {q4}% │
    └──────────┴──────────┘

  Fixes applied: {count} ({breakdown by category})
  Status: {Improving|Stalled|Regressed} — {action}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Step 4.7: Stall Detection & Pivot Strategy

Between iterations, evaluate the trend:

| Trend | Condition | Action |
|-------|-----------|--------|
| **Improving** | >0.3% drop | Continue to next iteration |
| **Stalled** | <0.3% drop for 2 consecutive rounds | Trigger pivot strategy |
| **Regressed** | Diff went UP | Rollback last fix batch, re-analyze |

**Pivot Strategy (triggered on stall):**

1. **Pivot 1: Re-analyze** — Look at the diff image again. Are we fixing the WRONG elements? Focus on the hottest quadrant.
2. **Pivot 2: DOM restructuring** — Maybe the HTML structure is wrong, not just CSS values. Compare the DOM tree against the Figma element hierarchy. Restructure if they don't match.
3. **Pivot 3: Component swap** — Maybe a completely different component would match better (e.g., using a `<Card>` instead of a custom `<div>` with manual styling).
4. **Pivot 4: Ask user with evidence** — Show the composite image and ask:
   ```
   "I've reached {fidelity}% fidelity. Here's the current state:
    [composite.png: Figma ‖ Actual ‖ Diff]

    The remaining {diffPercent}% diff is concentrated in the {hotQuadrant} area.

    Options:
    a) Accept — this is close enough
    b) Give me specific guidance on what's wrong (I'll focus there)
    c) Try {N} more rounds with structural changes
    d) Stop — I'll review manually"
   ```

### Step 4.8: Text Rendering Tolerance

If remaining diff is concentrated in text regions:

1. **Validate typography METRICS** instead of pixels:
   - font-family matches design spec? ✓/✗
   - font-size matches? ✓/✗
   - font-weight matches? ✓/✗
   - line-height matches? ✓/✗
   - letter-spacing matches? ✓/✗
   - text color matches token? ✓/✗

2. If ALL 6 metrics match but pixels still differ → this is a **rendering engine difference** (Figma's Skia renderer vs browser text rendering). Add to the **accepted-diffs list** with the estimated pixel count.

3. **Track accepted diffs for adjusted scoring:**
   - Maintain an in-memory `acceptedDiffPixels` counter (starts at 0)
   - For each accepted text diff, estimate the pixel area: `elementWidth × elementHeight × deviceScaleFactor²`
   - Add to `acceptedDiffPixels`
   - **Adjusted fidelity** = `((totalPixels - acceptedDiffPixels - numDiffPixels) / (totalPixels - acceptedDiffPixels)) × 100`
   - Use the adjusted fidelity in progress reports and the final score

4. Report to user: "Text in {element} matches all metrics but has a {x}% pixel diff due to font rendering differences. This is expected and has been excluded from the fidelity score."

### Step 4.9: User Checkpoint

After **5 iterations** OR when a stall is detected, ask the user:

```
"Current fidelity: {fidelity}%
 Target: ≥99% (≤1% diff)

 [Shows composite.png]

 Options:
 a) Accept — this meets my standards
 b) Keep iterating ({suggest N} more rounds)
 c) I'll point out what needs fixing (manual guidance)
 d) Stop and generate the report as-is"
```

---

## Phase 5: Completion

### Step 5.1: Final Report

```
═══════════════════════════════════════════════════════════════
  SPECTREE DESIGNER — {Component Name}
═══════════════════════════════════════════════════════════════

  Result:       {✅ PASS|❌ FAIL} ({fidelity}% fidelity)
  Mode:         {Build|Fix}
  Framework:    {React|Angular|Vue|Svelte|...}
  Iterations:   {N} of 5
  Target:       ≥99% (≤1% diff)

  Diff History:
    Initial:    {x}%
    Round 1:    {x}%  ({direction}{change}%) — {category fixes}
    Round 2:    {x}%  ({direction}{change}%) — {category fixes}
    ...
    Round N:    {x}%  ({direction}{change}%) {✅ if pass}

  Summary:
    Fixes Applied:     {total} ({layout}, {color}, {typo}, {spacing}, {effects})
    Tokens Used:       {count} / {available}
    Components Reused: {count}
    Assets Exported:   {count} ({types})
    Accepted Diffs:    {count} ({reasons — e.g., "sub-pixel text hinting"})

  Standards Compliance:
    Linter:            {✅ 0 violations | ⚠️ N violations (details)}
    Component Reuse:   {count} shared components used / {count} custom elements
    Token Coverage:    {tokensUsed} / {tokensAvailable} ({percentage}%)
    CSS Methodology:   {✅ Follows project convention | ⚠️ violations}
    Import Pattern:    {✅ Matches project style | ⚠️ violations}

  Artifacts:
    .pixel-perfect/reference.png    (Figma reference)
    .pixel-perfect/actual.png       (Final implementation)
    .pixel-perfect/diff.png         (Diff overlay)
    .pixel-perfect/composite.png    (Side-by-side comparison)

═══════════════════════════════════════════════════════════════
```

### Step 5.2: Optional CI Baseline

Ask the user: "Save baseline for CI regression testing?"

If yes:
1. Keep `.pixel-perfect/reference.png` as the baseline
2. Generate a visual regression test file appropriate for the framework:

```javascript
// .pixel-perfect/visual.spec.mjs (generic — works with any framework)
import { test, expect } from '@playwright/test';
import { PNG } from 'pngjs';
import pixelmatch from 'pixelmatch';
import * as fs from 'fs';

const DETERMINISTIC_CSS = `
  *, *::before, *::after {
    animation: none !important;
    transition: none !important;
    caret-color: transparent !important;
    scroll-behavior: auto !important;
  }
  ::-webkit-scrollbar { display: none !important; }
  * { scrollbar-width: none !important; }
`;

test.use({
  deviceScaleFactor: 2,
});

test('{ComponentName} matches Figma design', async ({ page }) => {
  await page.setViewportSize({ width: {vpWidth}, height: {vpHeight} });
  await page.goto('{url}');
  await page.addStyleTag({ content: DETERMINISTIC_CSS });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(1000);

  const actual = await page.screenshot();
  const reference = fs.readFileSync('.pixel-perfect/reference.png');

  const refPng = PNG.sync.read(reference);
  const actPng = PNG.sync.read(actual);
  const diff = new PNG({ width: refPng.width, height: refPng.height });

  const numDiff = pixelmatch(
    refPng.data, actPng.data, diff.data,
    refPng.width, refPng.height,
    { threshold: 0.15 }
  );

  const diffPercent = (numDiff / (refPng.width * refPng.height)) * 100;
  expect(diffPercent).toBeLessThan(1.0);
});
```

### Step 5.3: Clean Up & Gitignore

- Remove `.pixel-perfect/capture.mjs` and `.pixel-perfect/compare.mjs` (temporary scripts)
- Keep `.pixel-perfect/reference.png`, `actual.png`, `diff.png`, `composite.png` for the user to review
- **Dev server cleanup:** If the skill started the dev server (stored `DEV_SERVER_PID`), inform the user:
  ```
  "The dev server is still running (PID: {DEV_SERVER_PID}).
   To stop it: kill {DEV_SERVER_PID}
   Or it will stop when you close this terminal session."
  ```

**Gitignore handling:**
- If the user opted for CI baseline (Step 5.2) → `.pixel-perfect/reference.png` and `visual.spec.mjs` should be **committed**. Add other artifacts to `.gitignore`:
  ```
  # SpecTree Designer artifacts (transient)
  .pixel-perfect/actual.png
  .pixel-perfect/diff.png
  .pixel-perfect/composite.png
  .pixel-perfect/capture.mjs
  .pixel-perfect/compare.mjs
  ```
- If the user did NOT opt for CI baseline → add the entire `.pixel-perfect/` directory to `.gitignore`:
  ```
  .pixel-perfect/
  ```
- Check if `.gitignore` already exists and append (don't overwrite). If it doesn't exist, create it.

---

## Appendix A: Framework Adaptation Table

| Concern | React / Next.js | Angular | Vue / Nuxt | Svelte / SvelteKit | Static HTML |
|---------|----------------|---------|------------|-------------------|-------------|
| File extension | `.tsx` / `.jsx` | `.component.ts` + `.html` + `.scss` | `.vue` | `.svelte` | `.html` + `.css` |
| Styling | CSS Modules / Tailwind / styled-components | SCSS + BEM | Scoped `<style>` / Tailwind | Scoped `<style>` | `.css` files |
| Token files | `tailwind.config.*`, `theme.ts`, CSS vars | `_variables.scss`, CSS vars | `tailwind.config.*`, CSS vars | CSS vars | CSS vars |
| Dev server cmd | `{pkgManager} run dev` / `next dev` | `ng serve` / `{pkgManager} start` | `{pkgManager} run dev` / `nuxt dev` | `{pkgManager} run dev` | `npx serve .` |
| Default port | 3000 (Next) / 5173 (Vite) | 4200 | 3000 (Nuxt) / 5173 (Vite) | 5173 | 3000 |
| Build check | `tsc --noEmit` / `next build` | `ng build` / `npx tsc --noEmit` | `vue-tsc --noEmit` | `svelte-check` | N/A |
| Component lib | shadcn/ui, MUI, Mantine, Chakra | Angular Material, PrimeNG | Vuetify, PrimeVue, Quasar | Skeleton UI, DaisyUI | N/A |
| Icon pattern | `<IconName />` JSX | `<app-icon name="...">` | `<Icon name="..." />` | `<Icon name="..." />` | `<img>` / inline `<svg>` |
| Naming | PascalCase components | BEM CSS + kebab-case files | PascalCase + kebab-case | PascalCase | kebab-case |
| Test file | `*.spec.tsx` / `*.test.tsx` | `*.spec.ts` | `*.spec.ts` | `*.test.ts` | N/A |

---

## Appendix B: Error Recovery

| Error | Detection | Recovery |
|-------|-----------|----------|
| **Dev server won't start** | `curl` exit code non-zero or `HTTP_CODE=000` after 30s | Check port conflict: `lsof -i :{port}`. Suggest killing the conflicting process or using a different port. |
| **Dev server crashes mid-loop** | `curl` exit code non-zero or `HTTP_CODE=000` during iteration | Restart dev server. Wait for ready. Retry current iteration. |
| **Figma API rate limit (429)** | HTTP 429 response from Figma MCP tools | Wait 60 seconds. Retry. If 429 again, wait 120s. Max 3 retries. |
| **Playwright timeout** | Screenshot capture exceeds 30s | Increase timeout to 60s. Check if URL is correct. Check for redirects (auth pages). Report to user if still failing. |
| **Build failure after fix** | Build command exits non-zero | Revert the fix (restore `old_str`). Try alternate approach. If all fail, skip fix and mark for manual review. |
| **Screenshot dimension mismatch** | `compare.mjs` reports >10px difference | Warn user. Check viewport/DPI settings. Verify Figma frame dimensions match Playwright viewport. |
| **Component behind a route** | Page shows 404 or blank at root URL | Ask user for the correct route/URL. Check framework router config for the component's path. |
| **Missing font** | Text renders in fallback font | Warn user. Suggest installing the font or adding a web font import. Add text diffs to accepted-diffs list. |
| **Node.js out of memory** | Process crashes on large screenshots | Add `--max-old-space-size=4096` to Node.js invocation. |

---

## Appendix C: Accepted Diff Patterns

Some pixel differences are inherent to Figma vs browser rendering and cannot be fixed:

| Pattern | Cause | Action |
|---------|-------|--------|
| Sub-pixel text rendering | Figma uses Skia, browsers use platform renderer | Validate typography metrics instead. If all match, accept the diff. |
| Anti-aliased borders | Different anti-aliasing algorithms | Accept if border-radius, width, and color match the spec. |
| Shadow spread rendering | Figma and CSS `box-shadow` spread differently | Accept if shadow params (offset, blur, spread, color) match. |
| SVG rendering | Minor path interpolation differences | Accept if the SVG source is identical. |
| Gradient banding | Different gradient interpolation | Accept if gradient stops and colors match. |

When accepting a diff, subtract its pixel count from the total diff calculation and note it in the final report.

---

## Appendix D: Convention Detection Quick Reference

This appendix summarizes how to detect and follow common project conventions. Use this as a checklist during Phase 1.8 (Coding Standards Discovery).

### Import Pattern Detection

| Signal | Convention | Example |
|--------|-----------|---------|
| `tsconfig.json` has `paths: { "@/*": ["./src/*"] }` | **Path aliases** | `import { cn } from '@/lib/utils'` |
| `vite.config` has `resolve.alias` | **Vite aliases** | `import { Button } from '~/components/ui/button'` |
| `index.ts` barrel files exist in component dirs | **Barrel exports** | `import { Button, Card } from '@/components'` |
| None of above | **Relative imports** | `import { Button } from '../../components/Button'` |

### CSS Methodology Detection

| Signal | Convention | Code must use |
|--------|-----------|---------------|
| `tailwindcss` in `package.json` deps | **Tailwind** | Utility classes: `className="flex gap-4 p-2 bg-blue-500"` |
| `*.module.css` or `*.module.scss` files exist | **CSS Modules** | `import styles from './Component.module.css'` then `className={styles.container}` |
| `.stylelintrc` with BEM plugin or `__` in class names | **BEM** | `.block__element--modifier` naming in SCSS |
| `styled-components` or `@emotion/styled` in deps | **CSS-in-JS** | `const Wrapper = styled.div\`...\`` |
| Vue/Svelte `<style scoped>` | **Scoped styles** | Styles inside `<style scoped>` block only |

### Component Pattern Detection

| Signal | Convention | Generated code must follow |
|--------|-----------|--------------------------|
| `export default function Component()` in existing files | **Default export function** | Same pattern in new components |
| `export const Component = () =>` in existing files | **Named export arrow** | Same pattern |
| `export function Component()` (named, not default) | **Named export function** | Same pattern |
| `@Component({ ... }) export class` | **Angular decorator** | Same Angular class pattern |
| Props defined with `interface ComponentProps` | **Interface props** | Define props with interface |
| Props defined with `type ComponentProps =` | **Type props** | Define props with type alias |
| Props inlined: `({ prop1, prop2 }: { prop1: string })` | **Inline props** | Inline type in function signature |

### File Organization Detection

| Signal | Convention | New files must go to |
|--------|-----------|---------------------|
| `src/components/ui/` has primitives, `src/components/` has composites | **UI library + custom** | Primitives in `ui/`, custom in `components/` |
| `src/features/auth/`, `src/features/dashboard/` | **Feature-based** | New feature in `src/features/{name}/` |
| `src/components/`, `src/pages/`, `src/hooks/` | **Type-based** | Each file type in its category dir |
| Tests co-located: `Button.tsx` + `Button.test.tsx` | **Co-located tests** | Test file next to component |
| Tests separate: `src/components/Button.tsx`, `tests/components/Button.test.tsx` | **Separate test dir** | Test in mirror structure under `tests/` |

### Quick "Do / Don't" Summary

| ❌ DO NOT | ✅ DO INSTEAD |
|-----------|--------------|
| Write `color: #3b82f6` in a Tailwind project | Use `text-blue-500` or the project's token class |
| Create `<div class="button">` when `<Button>` exists | Use `<Button variant="primary">` |
| Use `import '../../../components/Button'` when `@/` aliases exist | Use `import { Button } from '@/components/ui/button'` |
| Name file `myComponent.tsx` when project uses PascalCase | Name file `MyComponent.tsx` |
| Put file in `src/` root when project organizes by feature | Put in `src/features/{feature}/` or `src/components/` |
| Add a new `<style>` block when project uses Tailwind | Use Tailwind utility classes inline |
| Use `React.FC<Props>` when project uses function declarations | Use `function Component(props: Props)` |
| Add raw `px` values when spacing scale exists | Use the project's spacing tokens |
