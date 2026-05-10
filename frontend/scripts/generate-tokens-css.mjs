import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const inputPath = path.join(root, "figma", "design-tokens.tokens.json");
const outputPath = path.join(root, "app", "tokens.css");

const raw = fs.readFileSync(inputPath, "utf8");
const json = JSON.parse(raw);

const rootVars = new Map();
const themeVars = new Map();
const seenRoot = new Set();
const typoFontFamilies = new Map();
const typoLetterSpacings = new Map();

function toKebab(value) {
  return String(value)
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function formatCssValue(type, value) {
  if (type === "dimension") return Number(value) === 0 ? "0" : `${value}px`;
  if (type === "number") return String(value);
  if (type === "string" || type === "color") return String(value);
  return null;
}

function collectTypographyMeta(group, prop, rawValue) {
  if (prop === "fontsize") {
    return;
  }
  if (prop === "fontfamily") {
    if (!typoFontFamilies.has(group)) typoFontFamilies.set(group, new Set());
    typoFontFamilies.get(group).add(rawValue);
  } else if (prop === "letterspacing") {
    const num = Number(rawValue);
    if (num !== 0) {
      if (!typoLetterSpacings.has(group)) typoLetterSpacings.set(group, new Set());
      typoLetterSpacings.get(group).add(num);
    }
  }
}

function applyColorTheme(p0, p1, cleanPath, type, cssValue) {
  if (type !== "color") return;
  if (p0 === "color") {
    themeVars.set(`--color-${cleanPath.slice(1).join("-")}`, cssValue);
  } else if (p0 === "variable-collection" && p1 === "color") {
    themeVars.set(`--color-${cleanPath.slice(2).join("-")}`, cssValue);
  }
}

function applyTypographyTheme(p1, p2, p3, rawValue, cssValue) {
  const key = `${p1}-${p2}`;
  if (p3 === "fontsize") {
    themeVars.set(`--text-${key}`, cssValue);
  } else if (p3 === "lineheight") {
    themeVars.set(`--text-${key}--line-height`, cssValue);
  } else {
    collectTypographyMeta(p1, p3, rawValue);
  }
}

function applyThemeMapping(cleanPath, node, cssValue) {
  const [p0, p1, p2, p3] = cleanPath;
  applyColorTheme(p0, p1, cleanPath, node.type, cssValue);
  if (p0 === "typography" && p1 && p2 && p3) {
    applyTypographyTheme(p1, p2, p3, node.value, cssValue);
  }
}

function walk(node, pathParts = []) {
  if (!node || typeof node !== "object") return;

  const isLeafToken =
    Object.hasOwn(node, "type") &&
    Object.hasOwn(node, "value");

  if (isLeafToken) {
    if (node.type === "custom-fontStyle") return;
    const cleanPath = pathParts.map(toKebab).filter(Boolean);
    const varName = cleanPath.join("-");
    const cssValue = formatCssValue(node.type, node.value);
    if (cssValue !== null && !seenRoot.has(varName)) {
      seenRoot.add(varName);
      rootVars.set(varName, cssValue);
    }
    if (cssValue !== null) applyThemeMapping(cleanPath, node, cssValue);
    return;
  }

  for (const [key, value] of Object.entries(node)) {
    walk(value, [...pathParts, key]);
  }
}

walk(json);

for (const [group, families] of typoFontFamilies) {
  if (families.size === 1) themeVars.set(`--font-${group}`, [...families][0]);
}

for (const [group, values] of typoLetterSpacings) {
  if (values.size === 1) themeVars.set(`--tracking-${group}`, `${[...values][0]}px`);
}

const rootLines = [...rootVars.entries()]
  .sort(([a], [b]) => a.localeCompare(b))
  .map(([name, val]) => `  --${name}: ${val};`);

const themeLines = [...themeVars.entries()]
  .sort(([a], [b]) => a.localeCompare(b))
  .map(([name, val]) => `  ${name}: ${val};`);

const out = [
  "/* Auto-generated from figma/design-tokens.tokens.json — do not edit by hand */",
  "",
  ":root {",
  ...rootLines,
  "}",
  "",
  "@theme inline {",
  ...themeLines,
  "}",
  "",
].join("\n");

fs.writeFileSync(outputPath, out, "utf8");
console.log(
  `Generated ${path.relative(root, outputPath)} — ${rootLines.length} :root vars, ${themeLines.length} @theme vars`
);
