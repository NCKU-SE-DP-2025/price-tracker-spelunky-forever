module.exports = {
  root: true,
  env: {
    node: true,
    browser: true,
    es2021: true,
  },
  parserOptions: {
    ecmaVersion: 2021,
    sourceType: 'module',
  },
  extends: [
    'plugin:vue/essential',   // Vue 3 用這個就好
    'eslint:recommended',
    'prettier',               // 或保留 @vue/eslint-config-prettier 二擇一
  ],
  rules: {
    'no-unused-vars': 'warn',
    'no-undef': 'off',
    // 'vue/script-setup-uses-vars': 'error' 
  },
  globals: {
    defineProps: 'readonly',
    defineEmits: 'readonly',
    defineExpose: 'readonly',
    withDefaults: 'readonly',
  },
};
