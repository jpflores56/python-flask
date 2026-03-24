---
name: SpecTree Update
description: "Check for and install SpecTree agent, skill, and MCP server updates. Run this when you see an update notification or want to ensure you have the latest version."
tools:
  - spectree__manage_skill_packs
  - spectree__sync_local_packs
---

# SpecTree Update

Check for and install updates to SpecTree agents, skills, and MCP server.

Use this skill when:
- You see an update notification in SpecTree
- You want to ensure you have the latest agents, skills, and instructions
- You're troubleshooting issues that may be fixed in a newer version

---

## Step 1: Check Current Installed Versions

Read the local manifest to understand what's currently installed:

```
cat .spectree/manifest.json
```

Note the installed pack names and versions (e.g., `@spectree/full` at version `1.2.0`).

---

## Step 2: Check for Skill Pack Updates

Call the MCP tool to compare installed packs against the registry:

```
spectree__manage_skill_packs({
  action: "list_installed"
})
```

Review the response for each installed pack. Look for:
- **`updateAvailable: true`** — a newer version exists in the registry
- **`installedVersion`** — what you have locally
- **`latestVersion`** — what's available

---

## Step 3: Display Version Comparison

Present a clear summary to the user:

### If updates are available:

```
📦 SpecTree Skill Pack Updates Available

| Pack              | Installed | Latest | Status           |
|-------------------|-----------|--------|------------------|
| @spectree/full    | 1.2.0     | 1.3.0  | ⬆️ Update available |
```

### If no updates are available:

```
✅ All SpecTree skill packs are up to date!

| Pack              | Installed | Latest | Status     |
|-------------------|-----------|--------|------------|
| @spectree/full    | 1.3.0     | 1.3.0  | ✅ Current  |
```

If everything is already up to date, inform the user and skip to Step 5 (MCP server check).

---

## Step 4: Apply Skill Pack Updates

If updates are available, ask the user for confirmation before proceeding:

> **Updates are available for your SpecTree skill packs.** Would you like to update now? This will download new agents, skills, and instructions to your `.github/` directory.

Once the user confirms, run the CLI update command:

```bash
npx @ttc-ggi/spectree-cli update
```

After the command completes:
- Read the CLI output to determine what was updated
- Report the results: which packs were updated, how many files changed, and the new version numbers
- If the command fails, show the error output and suggest the user check their network connection or try again

---

## Step 5: Check MCP Server Version

The MCP server (`@ttc-ggi/spectree-mcp`) is installed separately via npm. Check if it needs an update:

### 5a. Get the installed MCP server version

```bash
node -e "console.log(require('@ttc-ggi/spectree-mcp/package.json').version)" 2>/dev/null || echo "not installed"
```

### 5b. Get the latest available version from the npm registry

```bash
npm view @ttc-ggi/spectree-mcp version 2>/dev/null || echo "unable to check registry"
```

### 5c. Compare versions and report

If the installed version is older than the latest:

```
🔌 MCP Server Update Available

Installed: @ttc-ggi/spectree-mcp@1.0.0
Latest:    @ttc-ggi/spectree-mcp@1.1.0

Would you like to update the MCP server? Run:
  npm update @ttc-ggi/spectree-mcp
```

If versions match:

```
✅ MCP server is up to date (@ttc-ggi/spectree-mcp@1.1.0)
```

If the MCP server is not installed locally (global install), note this:

```
ℹ️ MCP server not found in local node_modules. It may be installed globally.
Check global version with: npm list -g @ttc-ggi/spectree-mcp
```

---

## Step 6: Apply MCP Server Update (if needed)

If an MCP server update is available and the user confirms:

```bash
npm update @ttc-ggi/spectree-mcp
```

After updating, remind the user:

> **Note:** You may need to restart VS Code or reload the Copilot Chat window for MCP server changes to take effect.

---

## Step 7: Report Final Summary

After all checks and updates are complete, present a final summary:

```
🎉 SpecTree Update Complete

Skill Packs:
  @spectree/full: 1.2.0 → 1.3.0 ✅ Updated (12 files changed)

MCP Server:
  @ttc-ggi/spectree-mcp: 1.0.0 → 1.1.0 ✅ Updated

💡 Restart VS Code if you updated the MCP server.
```

Or if nothing was updated:

```
✅ Everything is up to date — no changes needed.

Skill Packs: @spectree/full@1.3.0 (current)
MCP Server:  @ttc-ggi/spectree-mcp@1.1.0 (current)
```

---

## Troubleshooting

### CLI command not found
If `npx @ttc-ggi/spectree-cli update` fails with "command not found", try:
```bash
npm exec -- @ttc-ggi/spectree-cli update
```

### Network errors
If registry checks fail, the user may be behind a firewall or offline. Suggest:
- Check internet connectivity
- Try again later
- Check npm proxy settings with `npm config get proxy`

### Manifest file missing
If `.spectree/manifest.json` doesn't exist, the skill packs may not have been installed yet. Suggest:
```bash
npx @ttc-ggi/spectree-cli install @spectree/full
```

### Drift detection
To check for discrepancies between local files and the manifest, use:
```
spectree__sync_local_packs({
  projectRoot: "."
})
```

This will report untracked files, missing files, and version mismatches.
