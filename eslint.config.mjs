import { FlatCompat } from "@eslint/eslintrc";
import path from "node:path";
import { fileURLToPath } from "node:url";

const dirname = path.dirname(fileURLToPath(import.meta.url));
const compat = new FlatCompat({ baseDirectory: dirname });

const config = [
  {
    ignores: [
      ".next/**",
      "node_modules/**",
      "coverage/**",
      "playwright-report/**",
      "test-results/**",
      "next-env.d.ts",
    ],
  },
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    files: ["frontend/**/*.{ts,tsx}"],
    rules: {
      "no-restricted-imports": [
        "error",
        {
          "patterns": [
            { "group": ["@/backend/*"], "message": "Frontend must call backend through same-origin API routes." }
          ]
        }
      ]
    }
  },
  {
    files: ["backend/**/*.ts"],
    ignores: ["backend/ai/guardedGenerate.ts"],
    rules: {
      "no-restricted-imports": ["error", { "paths": [{ "name": "openai", "message": "Only guardedGenerate.ts may import OpenAI." }] }]
    }
  }
];

export default config;
