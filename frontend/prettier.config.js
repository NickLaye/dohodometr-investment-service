/** @type {import('prettier').Config} */
module.exports = {
  // Basic formatting
  printWidth: 80,
  tabWidth: 2,
  useTabs: false,
  semi: true,
  singleQuote: true,
  quoteProps: 'as-needed',
  trailingComma: 'es5',
  bracketSpacing: true,
  bracketSameLine: false,
  arrowParens: 'avoid',
  endOfLine: 'lf',

  // JSX specific
  jsxSingleQuote: true,

  // Plugin configurations
  plugins: ['prettier-plugin-tailwindcss'],

  // File specific overrides
  overrides: [
    {
      files: '*.md',
      options: {
        printWidth: 100,
        proseWrap: 'always',
      },
    },
    {
      files: '*.{json,yml,yaml}',
      options: {
        printWidth: 120,
      },
    },
    {
      files: '*.{ts,tsx}',
      options: {
        parser: 'typescript',
      },
    },
    {
      files: '*.css',
      options: {
        printWidth: 120,
      },
    },
  ],
};
