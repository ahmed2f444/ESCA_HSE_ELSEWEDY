module.exports = {
  root: true,
  env: {
    browser: true,
    es2022: true,
  },
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
    ecmaFeatures: {
      jsx: true,
    },
  },
  plugins: ['react-hooks'],
  ignorePatterns: ['dist/', 'node_modules/', 'src/api/mock/seed.generated.js'],
  rules: {
    'react-hooks/rules-of-hooks': 'error',
    'react-hooks/exhaustive-deps': 'warn',
    'no-constant-binary-expression': 'error',
    'no-dupe-keys': 'error',
    'no-undef': 'error',
    'no-unreachable': 'error',
  },
}
