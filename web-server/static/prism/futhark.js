Prism.languages.futhark = {
	'function': /(?<=\bdef\s+)\w+/,
	'builtin': /\b(?:map|map1|map2|map3|map4|map5|stream_map|stream_map_per|reduce|reduce_comm|scan|filter|partition|stream_red|stream_red_per|stream_seq|iota|replicate|scatter|drop|rotate|split|flatten|unflatten|curry|uncurry|id|const)\b/,
	'comment': /--*/,
	'boolean': /\b(?:false|true)\b/,
	'keyword': /\b(?:if|then|else|let|loop|in|with|type|val|entry|for|while|do|case|match|include|import|module|open|local|assert|def|\.\.|\||:|=|\\|"|->|<-|\u2192|i8|i16|i32|i64|u8|u16|u32|u64|int|real|bool|char|f16|f32|f64)\b/,
	'operator': /[-!#$%&*+.\/<=>?@\\^|~:\u03BB\u2192]+/,
	'string': {
		pattern: /(?:"""[\s\S]*?"""|@"(?:""|[^"])*"|"(?:\\[\s\S]|[^\\"])*"|'''[\s\S]*?'''|@'(?:''|[^'])*'|'(?:\\[\s\S]|[^\\'])*')B?/,
		greedy: true
	},
	'char': {
		pattern: /'(?:[^\\']|\\(?:.|\d{3}|x[a-fA-F\d]{2}|u[a-fA-F\d]{4}|U[a-fA-F\d]{8}))'B?/,
		greedy: true
	},
	'punctuation': /[,;`]/,
	'number': [
		/0[bB][01][01_]*(i8|i16|i32|i64|u8|u16|u32|u64|f16|f32|f64)?/,
		/(?<![^\W_0-9])[0-9][0-9_]*(\\.[0-9]+)?(i8|i16|i32|i64|u8|u16|u32|u64|f16|f32|f64)?(?![^\W_0-9])/,
		/0[xX][0-9a-fA-F][0-9a-fA-F_]*(\\.[0-9a-fA-F]+)?(i8|i16|i32|i64|u8|u16|u32|u64|f16|f32|f64)?/,
		/0[xX][0-9a-fA-F][0-9a-fA-F_]*\\.[0-9a-fA-F][0-9a-fA-F_]*([pP][\\+\\-]?[0-9_]+)?(i8|i16|i32|i64|u8|u16|u32|u64|f16|f32|f64)?/,
	]	
	
};