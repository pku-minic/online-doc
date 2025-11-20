Prism.languages.koopa = {
  'comment': [
    {
      pattern: /\/\/!.*|\/\*![\s\S]*?!\*\//,
      alias: 'doc-comment'
    },
    {
      pattern: /\/\/.*|\/\*[\s\S]*?\*\//,
      greedy: true
    }
  ],
  'string': {
    pattern: /"[^"]*"/,
    greedy: true
  },
  'label': {
    pattern: /((?:^|[^\w@%]))(?:@|%)(?:[a-zA-Z_][a-zA-Z0-9_]*|\d+)(?=.*:)/,
    lookbehind: true,
    alias: 'function'
  },
  'keyword': /\b(?:alloc|load|store|getptr|getelemptr|br|jump|ret|call|fun|decl|global|zeroinit|undef)\b/,
  'builtin': /\b(?:ne|eq|gt|lt|ge|le|add|sub|mul|div|mod|and|or|xor|shl|shr|sar)\b/,
  'type': {
    pattern: /\bi32\b/,
    alias: 'class-name'
  },
  'variable': {
    pattern: /(?:@|%)(?:[a-zA-Z_][a-zA-Z0-9_]*|\d+)/
  },
  'number': /\b\d+\b/,
  'punctuation': /[{}[\](),:*=]/
};
