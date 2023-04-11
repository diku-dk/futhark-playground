define("ace/mode/futhark_highlight_rules",["require","exports","module","ace/lib/oop","ace/mode/text_highlight_rules"], function(require, exports, module) {
    "use strict";
    
    var oop = require("../lib/oop");
    var TextHighlightRules = require("./text_highlight_rules").TextHighlightRules;
    
    var FutharkHighlightRules = function() {
        var keywordMapper = this.createKeywordMapper({
           "keyword": "if|then|else|let|loop|in|with|type|val|entry|for|while|do|case|match|include|import|module|open|local|assert|def"
        }, "identifier");
        
        var functionKeywords = "map|map1|map2|map3|map4|map5|stream_map|stream_map_per|reduce|reduce_comm|scan|filter|partition|stream_red|stream_red_per|stream_seq|iota|replicate|scatter|drop|rotate|split|flatten|unflatten|curry|uncurry|id|const"
        var typeKeywords = "i8|i16|i32|i64|u8|u16|u32|u64|int|real|bool|char|f16|f32|f64"
        
        var escapeRe = /\\(\d+|['"\\&trnbvf])/;
        
        var smallRe = /[a-z_]/.source;
        var largeRe = /[A-Z]/.source;
        var idRe = /[a-z_A-Z0-9']/.source;
    
        this.$rules = {
            start: [{
                token: "string.start",
                regex: '"',
                next: "string"
            }, {
                token: "string.character",
                regex: "'(?:" + escapeRe.source + "|.)'?"
            }, {
                token: "comment",
                regex: "--.*"
            }, {
                token : "constant.numeric", // binary
                regex : "\\b0[bB][01][01_]*(i8|i16|i32|i64|u8|u16|u32|u64|f16|f32|f64)?\\b"
            }, {
                token : "constant.numeric", // decimal
                regex : "\\b[0-9][0-9_]*(\\.[0-9]+)?(i8|i16|i32|i64|u8|u16|u32|u64|f16|f32|f64)?\\b"
            }, {
                token : "constant.numeric", // hex
                regex : "\\b0[xX][0-9a-fA-F][0-9a-fA-F_]*(\\.[0-9a-fA-F]+)(i8|i16|i32|i64|u8|u16|u32|u64|f16|f32|f64)?\\b"
            }, {
                token : "constant.numeric", // hexfloat
                regex : "\\b0[xX][0-9a-fA-F][0-9a-fA-F_]*\\.[0-9a-fA-F][0-9a-fA-F_]*([pP][\\+\\-]?[0-9_]+)(i8|i16|i32|i64|u8|u16|u32|u64|f16|f32|f64)?\\b"
            }, {
               token : "support.type",
               regex : typeKeywords
            }, {
                token : "support.function",
                regex : functionKeywords
            }, {
                token : "keyword",
                regex : /\.\.|\||:|=|\\|"|->|<-|\u2192/
            }, {
                token : "keyword.operator",
                regex : /[-!#$%&*+.\/<=>?@\\^|~:\u03BB\u2192]+/
            }, {
                token : "operator.punctuation",
                regex : /[,;`]/
            }, {
                regex : largeRe + idRe + "+\\.?",
                token : function(value) {
                    if (value[value.length - 1] == ".")
                        return "entity.name.function"; 
                    return "constant.language"; 
                }
            }, {
                regex : "^" + smallRe  + idRe + "+",
                token : function(value) {
                    return "constant.language"; 
                }
            }, {
                token : keywordMapper,
                regex : "[\\w\\xff-\\u218e\\u2455-\\uffff]+\\b"
            }, {
                regex: "{-#?",
                token: "comment.start",
                onMatch: function(value, currentState, stack) {
                    this.next = value.length == 2 ? "blockComment" : "docComment";
                    return this.token;
                }
            }, {
                token: "variable.language",
                regex: /\[markdown\|/,
                next: "markdown"
            }, {
                token: "paren.lparen",
                regex: /[\[({]/ 
            }, {
                token: "paren.rparen",
                regex: /[\])}]/
            } ],
            markdown: [{
                regex: /\|\]/,
                next: "start"
            }, {
                defaultToken : "string"
            }],
            blockComment: [{
                regex: "{-",
                token: "comment.start",
                push: "blockComment"
            }, {
                regex: "-}",
                token: "comment.end",
                next: "pop"
            }, {
                defaultToken: "comment"
            }],
            docComment: [{
                regex: "{-",
                token: "comment.start",
                push: "docComment"
            }, {
                regex: "-}",
                token: "comment.end",
                next: "pop" 
            }, {
                defaultToken: "doc.comment"
            }],
            string: [{
                token: "constant.language.escape",
                regex: escapeRe
            }, {
                token: "text",
                regex: /\\(\s|$)/,
                next: "stringGap"
            }, {
                token: "string.end",
                regex: '"',
                next: "start"
            }, {
                defaultToken: "string"
            }],
            stringGap: [{
                token: "text",
                regex: /\\/,
                next: "string"
            }, {
                token: "error",
                regex: "",
                next: "start"
            }]
        };
        
        this.normalizeRules();
    };
    oop.inherits(FutharkHighlightRules, TextHighlightRules);
    
    exports.FutharkHighlightRules = FutharkHighlightRules;
    });
    
    define("ace/mode/folding/cstyle",["require","exports","module","ace/lib/oop","ace/range","ace/mode/folding/fold_mode"], function(require, exports, module) {
    "use strict";
    
    var oop = require("../../lib/oop");
    var Range = require("../../range").Range;
    var BaseFoldMode = require("./fold_mode").FoldMode;
    
    var FoldMode = exports.FoldMode = function(commentRegex) {
        if (commentRegex) {
            this.foldingStartMarker = new RegExp(
                this.foldingStartMarker.source.replace(/\|[^|]*?$/, "|" + commentRegex.start)
            );
            this.foldingStopMarker = new RegExp(
                this.foldingStopMarker.source.replace(/\|[^|]*?$/, "|" + commentRegex.end)
            );
        }
    };
    oop.inherits(FoldMode, BaseFoldMode);
    
    (function() {
        
        this.foldingStartMarker = /([\{\[\(])[^\}\]\)]*$|^\s*(\/\*)/;
        this.foldingStopMarker = /^[^\[\{\(]*([\}\]\)])|^[\s\*]*(\*\/)/;
        this.singleLineBlockCommentRe= /^\s*(\/\*).*\*\/\s*$/;
        this.tripleStarBlockCommentRe = /^\s*(\/\*\*\*).*\*\/\s*$/;
        this.startRegionRe = /^\s*(\/\*|\/\/)#?region\b/;
        this._getFoldWidgetBase = this.getFoldWidget;
        this.getFoldWidget = function(session, foldStyle, row) {
            var line = session.getLine(row);
        
            if (this.singleLineBlockCommentRe.test(line)) {
                if (!this.startRegionRe.test(line) && !this.tripleStarBlockCommentRe.test(line))
                    return "";
            }
        
            var fw = this._getFoldWidgetBase(session, foldStyle, row);
        
            if (!fw && this.startRegionRe.test(line))
                return "start"; // lineCommentRegionStart
        
            return fw;
        };
    
        this.getFoldWidgetRange = function(session, foldStyle, row, forceMultiline) {
            var line = session.getLine(row);
            
            if (this.startRegionRe.test(line))
                return this.getCommentRegionBlock(session, line, row);
            
            var match = line.match(this.foldingStartMarker);
            if (match) {
                var i = match.index;
    
                if (match[1])
                    return this.openingBracketBlock(session, match[1], row, i);
                    
                var range = session.getCommentFoldRange(row, i + match[0].length, 1);
                
                if (range && !range.isMultiLine()) {
                    if (forceMultiline) {
                        range = this.getSectionRange(session, row);
                    } else if (foldStyle != "all")
                        range = null;
                }
                
                return range;
            }
    
            if (foldStyle === "markbegin")
                return;
    
            var match = line.match(this.foldingStopMarker);
            if (match) {
                var i = match.index + match[0].length;
    
                if (match[1])
                    return this.closingBracketBlock(session, match[1], row, i);
    
                return session.getCommentFoldRange(row, i, -1);
            }
        };
        
        this.getSectionRange = function(session, row) {
            var line = session.getLine(row);
            var startIndent = line.search(/\S/);
            var startRow = row;
            var startColumn = line.length;
            row = row + 1;
            var endRow = row;
            var maxRow = session.getLength();
            while (++row < maxRow) {
                line = session.getLine(row);
                var indent = line.search(/\S/);
                if (indent === -1)
                    continue;
                if  (startIndent > indent)
                    break;
                var subRange = this.getFoldWidgetRange(session, "all", row);
                
                if (subRange) {
                    if (subRange.start.row <= startRow) {
                        break;
                    } else if (subRange.isMultiLine()) {
                        row = subRange.end.row;
                    } else if (startIndent == indent) {
                        break;
                    }
                }
                endRow = row;
            }
            
            return new Range(startRow, startColumn, endRow, session.getLine(endRow).length);
        };
        this.getCommentRegionBlock = function(session, line, row) {
            var startColumn = line.search(/\s*$/);
            var maxRow = session.getLength();
            var startRow = row;
            
            var re = /^\s*(?:\/\*|\/\/|--)#?(end)?region\b/;
            var depth = 1;
            while (++row < maxRow) {
                line = session.getLine(row);
                var m = re.exec(line);
                if (!m) continue;
                if (m[1]) depth--;
                else depth++;
    
                if (!depth) break;
            }
    
            var endRow = row;
            if (endRow > startRow) {
                return new Range(startRow, startColumn, endRow, line.length);
            }
        };
    
    }).call(FoldMode.prototype);
    
    });
    
    define("ace/mode/futhark",["require","exports","module","ace/lib/oop","ace/mode/text","ace/mode/futhark_highlight_rules","ace/mode/folding/cstyle"], function(require, exports, module) {
    "use strict";
    
    var oop = require("../lib/oop");
    var TextMode = require("./text").Mode;
    var HighlightRules = require("./futhark_highlight_rules").FutharkHighlightRules;
    var FoldMode = require("./folding/cstyle").FoldMode;
    
    var Mode = function() {
        this.HighlightRules = HighlightRules;
        this.foldingRules = new FoldMode();
        this.$behaviour = this.$defaultBehaviour;
    };
    oop.inherits(Mode, TextMode);
    
    (function() {
        this.lineCommentStart = "--";
        this.blockComment = {start: "{-", end: "-}", nestable: true};
        this.$id = "ace/mode/futhark";
    }).call(Mode.prototype);
    
    exports.Mode = Mode;
    });                (function() {
                        window.require(["ace/mode/futhark"], function(m) {
                            if (typeof module == "object" && typeof exports == "object" && module) {
                                module.exports = m;
                            }
                        });
                    })();
                