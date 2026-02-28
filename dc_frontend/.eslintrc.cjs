module.exports = {
  root: true,
  env: {
    browser: true,
    node: true,
    es2022: true,
  },
  parser: "vue-eslint-parser",
  parserOptions: {
    parser: "@typescript-eslint/parser",
    ecmaVersion: "latest",
    sourceType: "module",
  },
  extends: [
    "plugin:vue/vue3-recommended",
    "@vue/eslint-config-typescript",
    "@vue/eslint-config-prettier",
  ],
  rules: {
    "vue/multi-word-component-names": "off",
    "vue/no-side-effects-in-computed-properties": "off",
    "vue/no-mutating-props": "off",
    "vue/no-unused-vars": "off",
    "@typescript-eslint/no-unused-vars": "warn",
  },
};
