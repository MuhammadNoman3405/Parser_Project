# ============================================================
#  TOKEN / KEYWORD TABLES
# ============================================================

KEYWORDS = {
    "int": "KEYWORD_INT_DATATYPE",   "float": "KEYWORD_FLOAT_DATATYPE",
    "double": "KEYWORD_DOUBLE_DATATYPE", "char": "KEYWORD_CHAR_DATATYPE",
    "string": "KEYWORD_STRING_DATATYPE", "bool": "KEYWORD_BOOL_DATATYPE",
    "void": "KEYWORD_VOID_DATATYPE",  "long": "KEYWORD_LONG_DATATYPE",
    "if": "KEYWORD_IF",   "else": "KEYWORD_ELSE",
    "while": "KEYWORD_WHILE", "for": "KEYWORD_FOR",
    "do": "KEYWORD_DO",   "return": "KEYWORD_RETURN",
    "print": "KEYWORD_PRINT", "read": "KEYWORD_READ",
    "true": "KEYWORD_TRUE",   "false": "KEYWORD_FALSE",
    "main": "KEYWORD_MAIN",
}

DATA_TYPE_KEYWORDS = {"int", "float", "double", "char", "string", "bool", "void", "long"}

# Byte size and dimension label for each primitive type
TYPE_INFO = {
    "int":    {"size": 4,  "dimension": 0},   # 0 = scalar variable
    "float":  {"size": 4,  "dimension": 0},
    "double": {"size": 8,  "dimension": 0},
    "char":   {"size": 1,  "dimension": 0},
    "string": {"size": 8,  "dimension": 1},   # 1 = 1-D array (sequence of chars)
    "bool":   {"size": 1,  "dimension": 0},
    "void":   {"size": 0,  "dimension": 0},
    "long":   {"size": 8,  "dimension": 0},
}

OPERATOR_MAP = {
    "++": "OPERATOR_INCREMENT", "--": "OPERATOR_DECREMENT",
    "<=": "OPERATOR_LTE",       ">=": "OPERATOR_GTE",
    "==": "OPERATOR_EQ",        "!=": "OPERATOR_NEQ",
    "&&": "OPERATOR_AND",       "||": "OPERATOR_OR",
    "=":  "OPERATOR_ASSIGN",    "+":  "OPERATOR_PLUS",
    "-":  "OPERATOR_MINUS",     "*":  "OPERATOR_MULT",
    "/":  "OPERATOR_DIV",       "%":  "OPERATOR_MOD",
    "<":  "OPERATOR_LT",        ">":  "OPERATOR_GT",
    "!":  "OPERATOR_NOT",
}

SEPARATOR_MAP = {
    ";": "SEPARATOR_SEMICOLON", ",": "SEPARATOR_COMMA",
    "(": "SEPARATOR_LPAREN",    ")": "SEPARATOR_RPAREN",
    "{": "SEPARATOR_LBRACE",    "}": "SEPARATOR_RBRACE",
    "[": "SEPARATOR_LBRACKET",  "]": "SEPARATOR_RBRACKET",
}




# ============================================================
#  SYMBOL TABLE
# ============================================================

class SymbolTable:
    """
    Stores every identifier encountered during parsing.

    Columns (matching the image):
      name            – identifier text
      type            – data type ("int", "float", …) or "UNDECLARED"
      size            – byte width of the type  (0 = unknown)
      dimension       – "Scalar" / "Array" / "Unknown"
      line_declared   – source line where variable was declared
                        (None if only used, never declared)
      lines_used      – sorted list of every line where identifier appears
      address         – simulated hex memory address (stack-allocated, 4-byte aligned)
    """

    def __init__(self):
        self._table: dict[str, dict] = {}   # name → entry

    # ------------------------------------------------------------------
    def declare(self, name: str, dtype: str, line: int, array_dims: int = None):
        """
        Called when a variable declaration is parsed.
        array_dims: None = use TYPE_INFO default, 0 = scalar, 1/2/... = array depth.
        """
        info = TYPE_INFO.get(dtype, {"size": 4, "dimension": 0})
        dim  = array_dims if array_dims is not None else info["dimension"]

        if name in self._table:
            entry = self._table[name]
            if entry["type"] == "UNDECLARED":
                entry["type"]          = dtype
                entry["size"]          = info["size"]
                entry["dimension"]     = dim
                entry["line_declared"] = line
        else:
            self._table[name] = {
                "name":          name,
                "type":          dtype,
                "size":          info["size"],
                "dimension":     dim,
                "line_declared": line,
                "lines_used":    [],
            }

    def use(self, name: str, line: int):
        """
        Called whenever an identifier is *referenced* (RHS, condition,
        print target, for-update, etc.).
        If it was never declared, it is added as UNDECLARED.
        """
        if name not in self._table:
            self._table[name] = {
                "name":          name,
                "type":          "UNDECLARED",
                "size":          0,
                "dimension":     "-",
                "line_declared": None,
                "lines_used":    [line],
            }
        else:
            entry = self._table[name]
            if line not in entry["lines_used"]:
                entry["lines_used"].append(line)

    # ------------------------------------------------------------------
    def all_entries(self) -> list:
        return list(self._table.values())

    def print_table(self):
        entries = self.all_entries()
        if not entries:
            print("  (symbol table is empty)")
            return

        col_w = [14, 12, 6, 11, 19, 30]
        headers = ["Name", "Type", "Size", "Dimension",
                   "Line of Declaration", "Line(s) of Usage"]

        sep = "+" + "+".join("-" * w for w in col_w) + "+"
        def row(cells):
            return "|" + "|".join(
                str(c).center(w) for c, w in zip(cells, col_w)
            ) + "|"

        print(sep)
        print(row(headers))
        print(sep)
        for e in entries:
            used = ", ".join(str(l) for l in sorted(e["lines_used"])) or "-"
            decl = str(e["line_declared"]) if e["line_declared"] else "-"
            print(row([e["name"], e["type"], e["size"],
                       e["dimension"], decl, used]))
        print(sep)


# ============================================================
#  SCANNER
# ============================================================

class Scanner:
    """Lexical Analyzer for W++ Language"""

    def __init__(self):
        self.unrecognized_tokens = {}
        self.unrecognized_tokens_number = {}

    def is_float(self, value: str) -> bool:
        try:
            float(value)
            return True
        except ValueError:
            return False

    def load_data(self, file_path) -> str:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def load_code(self, source_code) -> str:
        return source_code

    def tokenize(self, data: str):
        tokens = []
        lines = data.split('\n')
        total = len(lines)
        for i, line in enumerate(lines, start=1):
            if line.strip():
                tokens.append((line, i))
        return tokens, total

            
    def tokenizing_operators(self, cleaned_lines):
        tokenized_operators={}
        operators_number={}
        tokenized_Separators={}
        separators_number={}
        for line, line_number in cleaned_lines:
            i=0
            while i < len(line):
                if line[i] == '"':
                    i += 1
                    while i < len(line) and line[i] != '"':
                        i += 1
                    i += 1  # skip closing quote
                    continue
                if line[i] == "'":
                    i += 1
                    while i < len(line) and line[i] != "'":
                        i += 1
                    i += 1  # skip closing quote
                    continue
                two_char_operator = line[i:i+2]
                if line[i:i+1].isdigit() or line[i:i+1].isalpha() or line[i:i+1].isspace():
                    i += 1
                elif two_char_operator in OPERATOR_MAP:
                    operator_name = OPERATOR_MAP[two_char_operator]
                    if operator_name not in tokenized_operators:
                        tokenized_operators[operator_name] = []
                    tokenized_operators[operator_name].append(line_number)
                    operators_number[operator_name] = operators_number.get(operator_name, 0) + 1
                    i += 2  # Skip the next character since it's part of the operator
                elif line[i] in OPERATOR_MAP:
                    operator_name = OPERATOR_MAP[line[i]]
                    if operator_name not in tokenized_operators:
                        tokenized_operators[operator_name] = []
                    tokenized_operators[operator_name].append(line_number)
                    operators_number[operator_name] = operators_number.get(operator_name, 0) + 1
                    i += 1
                elif line[i] in SEPARATOR_MAP:
                    separator_name = SEPARATOR_MAP[line[i]]
                    if separator_name not in tokenized_Separators:
                        tokenized_Separators[separator_name] = []
                    tokenized_Separators[separator_name].append(line_number)
                    separators_number[separator_name] = separators_number.get(separator_name, 0) + 1
                    i += 1
                elif line[i] not in OPERATOR_MAP and line[i] not in SEPARATOR_MAP and not line[i].isdigit() and not line[i].isalpha() and not line[i].isspace() and not ('.' in line[i] and line[i-1].isdigit() ):
                    if line[i] not in self.unrecognized_tokens:
                        self.unrecognized_tokens[line[i]] = []
                    self.unrecognized_tokens[line[i]].append(line_number)
                    self.unrecognized_tokens_number[line[i]] = self.unrecognized_tokens_number.get(line[i], 0) + 1
                    i += 1
                else:
                    i += 1

        return tokenized_operators , operators_number , tokenized_Separators , separators_number
            
    def tokenizing_keywords(self, cleaned_lines):
        tokenized_keywords={}
        keywords_number={}
        identifiers = {}
        identifiers_number = {}
        literal = False
        for line, line_number in cleaned_lines:
            words = line.split()  # Split by common delimiters
            for word in words: 
                
                word = word.strip(';,(){}[]<>!=+-*/%&|')
                if not word:    # skip empty strings after stripping
                    continue

                if '"' in word and word.count('"') != 2: 
                    literal = not literal  # Toggle literal state
                    continue
                if word in KEYWORDS and not literal:
                    keyword_name = KEYWORDS[word]
                    if keyword_name not in tokenized_keywords:
                        tokenized_keywords[keyword_name] = []
                    tokenized_keywords[keyword_name].append(line_number)
                    keywords_number[keyword_name] = keywords_number.get(keyword_name, 0) + 1
                    continue
                if word not in KEYWORDS and not literal and word.isidentifier():
                    if word not in identifiers:
                        identifiers[word] = []
                    identifiers[word].append(line_number)
                    identifiers_number[word] = identifiers_number.get(word, 0) + 1
                    continue
                if word not in KEYWORDS and not literal and word.count('"') !=2 and not (' ' in word) and not word.isspace() and not word.isidentifier() and not ("'" in word) and not word.isdigit() and not self.is_float(word) and word not in OPERATOR_MAP and word not in SEPARATOR_MAP:    
                    if word not in self.unrecognized_tokens:
                        self.unrecognized_tokens[word] = []
                    self.unrecognized_tokens[word].append(line_number)
                    self.unrecognized_tokens_number[word] = self.unrecognized_tokens_number.get(word, 0) + 1

        return tokenized_keywords , keywords_number , self.unrecognized_tokens , self.unrecognized_tokens_number , identifiers , identifiers_number
    
    def tokenizing_literals(self, cleaned_lines):
        literal_interger = {}
        literal_interger_number = {}
        literal_float = {}
        literal_float_number = {}
        literal_char = {}
        literal_char_number = {}
        literal = False
        for line, line_number in cleaned_lines:
            words = line.split()  # Split by common delimiters
            for word in words:  
                word = word.strip(';,){}[]')
                if '"' in word:
                    if word.count('"') != 2:  # Check if the word contains a complete literal
                        literal = not literal  # Toggle literal state
                    continue
                    
                if literal:
                    continue

                if word.startswith('-') and word[1:].isdigit():
                    if word not in literal_interger:
                        literal_interger[word] = []
                    literal_interger[word].append(line_number)
                    literal_interger_number[word] = literal_interger_number.get(word, 0) + 1
                    continue

                
                if word not in KEYWORDS and not literal and word.isdigit():
                    if word not in literal_interger:
                        literal_interger[word] = []
                    literal_interger[word].append(line_number)
                    literal_interger_number[word] = literal_interger_number.get(word, 0) + 1
                    continue
                
                if word not in KEYWORDS and not literal and self.is_float(word):
                    if word not in literal_float:
                        literal_float[word] = []
                    literal_float[word].append(line_number)
                    literal_float_number[word] = literal_float_number.get(word, 0) + 1
                    continue
                
                if word not in KEYWORDS and not literal and word.startswith("'") and word.endswith("'") and len(word) in (3, 4):
                    literal_char_value =  word[1:-1]   # Extract the character between the single quotes
                    if literal_char_value not in literal_char:
                        literal_char[literal_char_value] = []
                    literal_char[literal_char_value].append(line_number)
                    literal_char_number[literal_char_value] = literal_char_number.get(literal_char_value, 0) + 1
                    continue
                
        return  literal_interger , literal_interger_number , literal_float , literal_float_number , literal_char , literal_char_number

    def literal_words(self, cleaned_lines):
        literal_words = {}
        literal_words_number = {}

        for line, line_number in cleaned_lines:
            i = 0
            while i < len(line):

                if line[i] == '"':
                    # found opening quote, now find closing quote
                    j = i + 1
                    while j < len(line):
                        if line[j] == '\\':
                            j += 2          # skip escape sequence  \"  \\
                            continue
                        if line[j] == '"':
                            break           # found closing quote
                        j += 1

                    # extract content between the quotes
                    literal_value = line[i+1:j]     # "Hello World" → Hello World

                    if literal_value not in literal_words:
                        literal_words[literal_value] = []
                    literal_words[literal_value].append(line_number)
                    literal_words_number[literal_value] = literal_words_number.get(literal_value, 0) + 1

                    i = j + 1       # move past closing "

                else:
                    i += 1

        return literal_words, literal_words_number
  

    def line_tokenizer(self, lines):
        """
        Strip comments; return (single_comments, block_comments, cleaned_lines).
        Handles /* ... */ spanning multiple lines correctly.
        """
        single_comments = []
        block_comments  = []
        cleaned         = []
        in_block        = False
        
        current_block_comment = ""
        block_comment_start_line = None

        for line, lineno in lines:
            cleaned_line_chars = []
            i = 0
            n = len(line)
            in_string = False
            in_char = False

            while i < n:
                if in_block:
                    if line[i:i+2] == '*/':
                        current_block_comment += '*/'
                        block_comments.append((current_block_comment, block_comment_start_line))
                        current_block_comment = ""
                        block_comment_start_line = None
                        in_block = False
                        i += 2
                    else:
                        current_block_comment += line[i]
                        i += 1
                    continue

                if in_string:
                    if line[i] == '\\' and i + 1 < n:
                        cleaned_line_chars.append(line[i:i+2])
                        i += 2
                    elif line[i] == '"':
                        in_string = False
                        cleaned_line_chars.append(line[i])
                        i += 1
                    else:
                        cleaned_line_chars.append(line[i])
                        i += 1
                    continue

                if in_char:
                    if line[i] == '\\' and i + 1 < n:
                        cleaned_line_chars.append(line[i:i+2])
                        i += 2
                    elif line[i] == "'":
                        in_char = False
                        cleaned_line_chars.append(line[i])
                        i += 1
                    else:
                        cleaned_line_chars.append(line[i])
                        i += 1
                    continue

                if line[i:i+2] == '//':
                    single_comments.append((line[i:], lineno))
                    break
                elif line[i:i+2] == '/*':
                    in_block = True
                    block_comment_start_line = lineno
                    current_block_comment = '/*'
                    i += 2
                elif line[i] == '"':
                    in_string = True
                    cleaned_line_chars.append(line[i])
                    i += 1
                elif line[i] == "'":
                    in_char = True
                    cleaned_line_chars.append(line[i])
                    i += 1
                else:
                    cleaned_line_chars.append(line[i])
                    i += 1

            if in_block and current_block_comment:
                current_block_comment += '\n'
            
            cleaned_line = "".join(cleaned_line_chars).strip()
            if cleaned_line:
                cleaned.append((cleaned_line, lineno))

        if in_block and current_block_comment:
            block_comments.append((current_block_comment.rstrip('\n'), block_comment_start_line))

        return single_comments, block_comments, cleaned

    def generate_token_stream(self, cleaned_lines):
        token_stream = []

        for line, lineno in cleaned_lines:
            line_tokens = []
            i = 0

            while i < len(line):
                char = line[i]

                if char.isspace():
                    i += 1
                    continue

                # Identifier / keyword
                if char.isalpha() or char == '_':
                    word = char
                    col  = i
                    i   += 1
                    while i < len(line) and (line[i].isalnum() or line[i] == '_'):
                        word += line[i]
                        i    += 1
                    if word in KEYWORDS:
                        line_tokens.append((KEYWORDS[word], word, lineno, col))
                    elif word in DATA_TYPE_KEYWORDS:
                        line_tokens.append(("DATATYPE", word, lineno, col))
                    else:
                        line_tokens.append(("IDENTIFIER", word, lineno, col))
                    continue

                # Number
                if char.isdigit():
                    num   = char
                    col   = i
                    i    += 1
                    is_f  = False
                    has_alpha = False
                    while i < len(line):
                        if line[i].isdigit():
                            num += line[i]
                        elif line[i] == '.' and not is_f:
                            num += line[i]
                            is_f = True
                        elif line[i].isalpha() or line[i] == '_':
                            num += line[i]
                            has_alpha = True
                        else:
                            break
                        i += 1
                    if has_alpha:
                        line_tokens.append(("INVALID_IDENTIFIER", num, lineno, col))
                    else:
                        tok = "FLOAT_LITERAL" if is_f else "INTEGER_LITERAL"
                        line_tokens.append((tok, num, lineno, col))
                    continue

                # String literal
                if char == '"':
                    lit = ""
                    col = i
                    i  += 1
                    while i < len(line):
                        if line[i] == '\\' and i + 1 < len(line):
                            lit += line[i] + line[i + 1]
                            i   += 2
                            continue
                        if line[i] == '"':
                            break
                        lit += line[i]
                        i   += 1
                    if i < len(line):
                        i += 1
                        line_tokens.append(("STRING_LITERAL", lit, lineno, col))
                    else:
                        line_tokens.append(("ERROR_UNCLOSED_STRING", lit, lineno, col))
                    continue

                # Char literal
                if char == "'":
                    lit = ""
                    col = i
                    i  += 1
                    while i < len(line):
                        if line[i] == '\\' and i + 1 < len(line):
                            lit += line[i] + line[i + 1]
                            i   += 2
                            continue
                        if line[i] == "'":
                            break
                        lit += line[i]
                        i   += 1
                    if i < len(line):
                        i += 1
                        line_tokens.append(("CHAR_LITERAL", lit, lineno, col))
                    else:
                        line_tokens.append(("ERROR_UNCLOSED_CHAR", lit, lineno, col))
                    continue

                # Two-char operators
                if i + 1 < len(line):
                    two = line[i:i + 2]
                    if two in OPERATOR_MAP:
                        line_tokens.append((OPERATOR_MAP[two], two, lineno, i))
                        i += 2
                        continue

                # Single-char operators
                if char in OPERATOR_MAP:
                    line_tokens.append((OPERATOR_MAP[char], char, lineno, i))
                    i += 1
                    continue

                # Separators
                if char in SEPARATOR_MAP:
                    line_tokens.append((SEPARATOR_MAP[char], char, lineno, i))
                    i += 1
                    continue

                # Unrecognized
                line_tokens.append(("UNRECOGNIZED", char, lineno, i))
                i += 1

            token_stream.append({"line_number": lineno, "tokens": line_tokens})

        return token_stream


# ============================================================
#  PARSER  (with Symbol Table integration)
# ============================================================

class Parser:
    """Syntax Analyzer for W++ Language — builds AST and Symbol Table."""

    def __init__(self, token_stream):
        self.token_stream = token_stream
        self.all_tokens   = self._flatten(token_stream)
        self.current      = 0
        self.errors       = []
        self.warnings     = []
        self.symbol_table = SymbolTable()
        self.in_if_header = False
        self.in_while_header = False
        self.in_for_header = False

    # ── token stream helpers ────────────────────────────────────────────

    def _flatten(self, ts):
        tokens = []
        for line_data in ts:
            tokens.extend(line_data["tokens"])
        return tokens

    def peek(self, offset=0):
        idx = self.current + offset
        return self.all_tokens[idx] if idx < len(self.all_tokens) else None

    def advance(self):
        t = self.peek()
        if t:
            self.current += 1
        return t

    def match(self, ttype, tval=None):
        t = self.peek()
        if not t or t[0] != ttype:
            return False
        if tval is not None and t[1] != tval:
            return False
        return True

    def expect(self, ttype, tval=None, error_msg=None):
        if self.match(ttype, tval):
            return self.advance()
        token = self.peek()
        if ttype == "IDENTIFIER" and token and token[0] == "INVALID_IDENTIFIER":
            self.add_error(f"Invalid variable name '{token[1]}'", token)
            self.advance()
            return None
        msg   = error_msg or (f"Expected '{tval}'" if tval else f"Expected {ttype}")
        self.add_error(msg, token)
        return None

    def get_error_code_and_message(self, message, token):
        msg = message.lower()
        code = "SYNTAX_ERROR"
        
        if "main" in msg:
            code = "INVALID_MAIN"
            message = "Invalid main function"
        elif "semicolon" in msg or "expected ';'" in msg:
            code = "MISSING_SEMICOLON"
            if "print" in msg:
                message = "Print statement missing semicolon"
            elif "return" in msg:
                message = "Return statement missing semicolon"
            elif "assignment" in msg:
                message = "Assignment missing semicolon"
            else:
                message = "Missing semicolon"
        elif "variable name" in msg or "invalid variable name" in msg:
            code = "INVALID_VARIABLE_NAME"
        elif "if statement" in msg or "after 'if'" in msg:
            code = "INVALID_IF"
            message = "Invalid if statement"
        elif "while loop" in msg or "after 'while'" in msg:
            code = "INVALID_WHILE"
            message = "Invalid while loop"
        elif "for loop" in msg or "after 'for'" in msg:
            code = "INVALID_FOR"
            if "must contain 3 parts" in msg or "initialization" in msg or "condition" in msg or "header" in msg:
                message = "For loop must contain 3 parts"
            else:
                message = "Invalid for loop"
        elif "unmatched" in msg or "unexpected token '}'" in msg or "expected '}'" in msg or (token and token[1] == "}"):
            code = "UNMATCHED_BRACE"
            message = "Unmatched closing brace"
        elif "declaration" in msg or "expression" in msg or "expected value" in msg or "assign" in msg:
            code = "INVALID_DECLARATION"
            if "expression" in msg or "expected value" in msg:
                message = "Invalid expression ''"
            else:
                message = "Invalid declaration"
                
        return code, message

    def add_error(self, message, token=None):
        if self.in_for_header:
            message = f"For loop must contain 3 parts: {message}"
        elif self.in_if_header:
            message = f"Invalid if statement: {message}"
        elif self.in_while_header:
            message = f"Invalid while loop: {message}"

        code, mapped_message = self.get_error_code_and_message(message, token)

        if token and len(token) >= 3:
            self.errors.append({
                "code":    code,
                "message": mapped_message,
                "line":    token[2],
                "column":  token[3] if len(token) > 3 else 0,
                "token":   token[1],
            })
        else:
            self.errors.append({
                "code":    code,
                "message": mapped_message,
                "line":    "EOF",
                "column":  0,
                "token":   None,
            })

    def synchronize(self):
        start_idx = self.current
        error_line = self.errors[-1]["line"] if self.errors else None

        while self.peek():
            t = self.peek()
            # Stop synchronizing if we reach a new line, to report errors on subsequent lines
            if error_line is not None and error_line != "EOF" and len(t) >= 3 and t[2] != error_line:
                break
            if t[0] == "SEPARATOR_SEMICOLON":
                self.advance()
                break
            if t[0] == "SEPARATOR_RBRACE":
                break
            if t[0] in ("KEYWORD_IF", "KEYWORD_WHILE", "KEYWORD_FOR",
                        "KEYWORD_RETURN", "DATATYPE"):
                break
            # Also stop at keyword-tagged type tokens (KEYWORD_INT_DATATYPE etc.)
            if t[1] in DATA_TYPE_KEYWORDS:
                break
            self.advance()

        if self.current == start_idx:
            self.advance()

    def is_datatype(self):
        t = self.peek()
        return bool(t and (t[0] == "DATATYPE" or t[1] in DATA_TYPE_KEYWORDS))

    # ── symbol table helpers ────────────────────────────────────────────

    def _declare(self, name: str, dtype: str, line: int):
        self.symbol_table.declare(name, dtype, line)

    def _use(self, name: str, line: int):
        self.symbol_table.use(name, line)

    def _register_expr_identifiers(self, node):
        """
        Walk an expression AST node and call _use() for every
        IDENTIFIER leaf found, so that variables referenced in
        expressions always appear in the symbol table.
        """
        if node is None:
            return
        # Leaf token tuple: (token_type, value, line, col)
        if isinstance(node, tuple) and len(node) == 4 and isinstance(node[2], int):
            if node[0] == "IDENTIFIER":
                self._use(node[1], node[2])
            return
        # AST node tuple: ("BinaryOp", op, left, right) etc.
        if isinstance(node, tuple):
            for child in node[1:]:
                self._register_expr_identifiers(child)

    # ── expression parsing ──────────────────────────────────────────────

    def parse_expression(self):
        return self.parse_logical_or()

    def parse_logical_or(self):
        left = self.parse_logical_and()
        while self.match("OPERATOR_OR"):
            op = self.advance(); right = self.parse_logical_and()
            left = ("BinaryOp", op, left, right)
        return left

    def parse_logical_and(self):
        left = self.parse_equality()
        while self.match("OPERATOR_AND"):
            op = self.advance(); right = self.parse_equality()
            left = ("BinaryOp", op, left, right)
        return left

    def parse_equality(self):
        left = self.parse_relational()
        while self.match("OPERATOR_EQ") or self.match("OPERATOR_NEQ"):
            op = self.advance(); right = self.parse_relational()
            left = ("BinaryOp", op, left, right)
        return left

    def parse_relational(self):
        left = self.parse_additive()
        while any(self.match(op) for op in
                  ("OPERATOR_LT","OPERATOR_GT","OPERATOR_LTE","OPERATOR_GTE")):
            op = self.advance(); right = self.parse_additive()
            left = ("BinaryOp", op, left, right)
        return left

    def parse_additive(self):
        left = self.parse_multiplicative()
        while self.match("OPERATOR_PLUS") or self.match("OPERATOR_MINUS"):
            op = self.advance(); right = self.parse_multiplicative()
            if right is None:
                self.add_error(f"Expected expression after '{op[1]}'", op)
                return None
            left = ("BinaryOp", op, left, right)
        return left

    def parse_multiplicative(self):
        left = self.parse_unary()
        while any(self.match(op) for op in
                  ("OPERATOR_MULT","OPERATOR_DIV","OPERATOR_MOD")):
            op = self.advance(); right = self.parse_unary()
            if right is None:
                self.add_error(f"Expected expression after '{op[1]}'", op)
                return None
            left = ("BinaryOp", op, left, right)
        return left

    def parse_unary(self):
        if self.match("OPERATOR_INCREMENT") or self.match("OPERATOR_DECREMENT"):
            op = self.advance(); operand = self.parse_postfix()
            return ("PrefixOp", op, operand)
        if self.match("OPERATOR_MINUS") or self.match("OPERATOR_NOT"):
            op = self.advance(); operand = self.parse_unary()
            return ("UnaryOp", op, operand)
        return self.parse_postfix()

    def parse_postfix(self):
        left = self.parse_primary()
        if self.match("OPERATOR_INCREMENT") or self.match("OPERATOR_DECREMENT"):
            op = self.advance()
            # Register identifier usage for postfix (e.g. counter++)
            self._register_expr_identifiers(left)
            return ("PostfixOp", op, left)
        return left

    def parse_primary(self):
        for ttype in ("INTEGER_LITERAL", "FLOAT_LITERAL",
                      "STRING_LITERAL",  "CHAR_LITERAL",
                      "KEYWORD_TRUE",    "KEYWORD_FALSE"):
            if self.match(ttype):
                return self.advance()

        if self.match("IDENTIFIER"):
            t = self.advance()
            self._use(t[1], t[2])      # register every identifier reference
            return t

        if self.match("SEPARATOR_LPAREN"):
            self.advance()
            expr = self.parse_expression()
            self.expect("SEPARATOR_RPAREN", error_msg="Expected ')' after expression")
            return expr

        token = self.peek()
        if token:
            self.add_error(f"Unexpected token in expression: '{token[1]}'", token)
        else:
            self.add_error("Unexpected end of input in expression")
        return None

    # ── type checking helper ────────────────────────────────────────────

    ALLOWED_LITERALS = {
    "int":    {"INTEGER_LITERAL"},
    "float":  {"INTEGER_LITERAL", "FLOAT_LITERAL"},
    "string": {"STRING_LITERAL"},
    "char":   {"CHAR_LITERAL"},
    "bool":   {"KEYWORD_TRUE", "KEYWORD_FALSE"},
    }

    def _get_literal_type(self, node):
        """
        Given an AST node or token, return its literal token type if it's
        a plain literal — otherwise return None (it's a complex expression
        like a variable reference or binary op, skip type checking).
        """
        if node is None:
            return None
        # A raw token looks like ("INTEGER_LITERAL", "5", 1, 8)
        if isinstance(node, tuple) and len(node) == 4 and isinstance(node[2], int):
            return node[0]   # return the token type
    # Anything else (BinaryOp, identifier, etc.) → can't statically check
        return None
    
    def _check_type_compatibility(self, dtype, value_node, token=None):
        literal_type = self._get_literal_type(value_node)

        if literal_type is None:
            return

        allowed = self.ALLOWED_LITERALS.get(dtype)
        if allowed is None:
            return

        if literal_type not in allowed:
            value_str = value_node[1] if isinstance(value_node, tuple) else str(value_node)

            TYPE_FRIENDLY = {
                "INTEGER_LITERAL": "int",
                "FLOAT_LITERAL":   "float",
                "STRING_LITERAL":  "string",
                "CHAR_LITERAL":    "char",
                "KEYWORD_TRUE":    "bool",
                "KEYWORD_FALSE":   "bool",
            }
            actual_friendly = TYPE_FRIENDLY.get(literal_type, literal_type)

            # ── use value_node's own position, not peek() ──
            if isinstance(value_node, tuple) and len(value_node) >= 4 and isinstance(value_node[2], int):
                err_line   = value_node[2]    # line comes FROM the bad value itself
                err_col    = value_node[3]
                err_token  = value_node[1]
            elif token and len(token) >= 3:   # fallback to passed token
                err_line   = token[2]
                err_col    = token[3] if len(token) >= 4 else 0
                err_token  = token[1]
            else:
                err_line   = "EOF"
                err_col    = 0
                err_token  = None

            self.errors.append({
                "code":    "TYPE_MISMATCH",
                "message": f"Type mismatch: cannot assign {actual_friendly} "f"value '{value_str}' to variable of type '{dtype}'",
                "line":    err_line,
                "column":  err_col,
                "token":   err_token,
            })
    # ── statement parsing ───────────────────────────────────────────────
      
    def parse_variable_declaration(self):
        dtype_token = self.advance()
        dtype       = dtype_token[1]
        declarators = []
        last_token  = dtype_token    # track last known token

        while True:
            ident = self.expect("IDENTIFIER",
                                error_msg="Expected variable name after data type")
            if not ident:
                self.synchronize()
                return None

            last_token = ident       # update
            self._declare(ident[1], dtype, ident[2])

            value = None
            if self.match("OPERATOR_ASSIGN"):
                assign_tok = self.advance()
                last_token = assign_tok   # update

                value = self.parse_expression()
                if value is None:
                    already_reported = (
                        self.errors and
                        self.errors[-1]["line"] == assign_tok[2]
                    )
                    if not already_reported:
                        self.add_error("Expected value after '='", assign_tok)
                    self.synchronize()
                    return None

                self._register_expr_identifiers(value)
                
                # ── TYPE CHECK (was missing here) ──────────────────────────────
                self._check_type_compatibility(dtype, value, ident)
                # ─────────────────────────────────────────────────────────────

                # update last_token from value node if it's a real token
                if isinstance(value, tuple) and len(value) == 4 and isinstance(value[2], int):
                    last_token = value   # the literal/identifier token itself

            declarators.append(("Declarator", ident, value))

            if self.match("SEPARATOR_COMMA"):
                self.advance()
                continue
            break

        # use last_token for the semicolon error, not peek()
        if not self.match("SEPARATOR_SEMICOLON"):
            self.add_error("Expected ';' after variable declaration", last_token)
            self.synchronize()
            return None
        self.advance()   # consume the semicolon

        return ("VariableDeclaration", dtype_token, declarators)

    def parse_assignment(self):
        """
        x = expr;
        The LHS identifier is registered as a use (it's being updated).
        """
        ident = self.advance()
        self._use(ident[1], ident[2])    # LHS counts as usage

        assign_tok = self.expect("OPERATOR_ASSIGN", error_msg="Expected '=' for assignment")
        if not assign_tok:
            self.synchronize()
            return None

        value = self.parse_expression()
        if value is None:
            self.add_error("Expected expression after '='", assign_tok)
            self.synchronize()
            return None
        self._register_expr_identifiers(value)

        # ── TYPE CHECK ──────────────────────────────────────────────────
        # Look up the declared type of this variable from symbol table
        entry = self.symbol_table._table.get(ident[1])
        if entry and entry["type"] != "UNDECLARED":
            self._check_type_compatibility(entry["type"], value)
        # ────────────────────────────────────────────────────────────────

        if not self.expect("SEPARATOR_SEMICOLON",
                           error_msg="Expected ';' after assignment"):
            self.synchronize()
            return None

        return ("Assignment", ident, value)

    def parse_print_statement(self):
        """print expr;"""
        print_token = self.advance()     # consume 'print'
        value = self.parse_expression()
        if value is None:
            self.add_error("Expected expression after 'print'", print_token)
            self.synchronize()
            return None
        self._register_expr_identifiers(value)

        if not self.expect("SEPARATOR_SEMICOLON",
                           error_msg="Expected ';' after print statement"):
            self.synchronize()
            return None
        return ("PrintStatement", value)

    def parse_if_statement(self):
        """if (cond) { ... } [else if (...) { ... }] [else { ... }]"""
        self.advance()   # 'if'
        self.in_if_header = True

        self.expect("SEPARATOR_LPAREN", error_msg="Expected '(' after 'if'")
        condition = self.parse_expression()
        if condition is None:
            self.add_error("Expected condition in if statement")
        else:
            self._register_expr_identifiers(condition)

        self.expect("SEPARATOR_RPAREN", error_msg="Expected ')' after condition")
        self.in_if_header = False

        if not self.match("SEPARATOR_LBRACE"):
            self.expect("SEPARATOR_LBRACE", error_msg="Expected '{' to start if block")
            while self.peek() and self.peek()[0] != "SEPARATOR_LBRACE":
                if self.peek()[0] in ("DATATYPE", "KEYWORD_IF", "KEYWORD_WHILE", "KEYWORD_RETURN"):
                    break
                self.advance()
            if self.match("SEPARATOR_LBRACE"):
                self.advance()
        else:
            self.advance()

        if_body = []
        while not self.match("SEPARATOR_RBRACE") and self.peek():
            stmt = self.parse_statement()
            if stmt: if_body.append(stmt)

        self.expect("SEPARATOR_RBRACE", error_msg="Expected '}' to close if block")

        else_body = None
        if self.match("KEYWORD_ELSE"):
            self.advance()
            if self.match("KEYWORD_IF"):
                else_body = [self.parse_if_statement()]
            else:
                if not self.match("SEPARATOR_LBRACE"):
                    self.expect("SEPARATOR_LBRACE", error_msg="Expected '{' after 'else'")
                    while self.peek() and self.peek()[0] != "SEPARATOR_LBRACE":
                        if self.peek()[0] in ("DATATYPE", "KEYWORD_IF", "KEYWORD_WHILE", "KEYWORD_RETURN"):
                            break
                        self.advance()
                    if self.match("SEPARATOR_LBRACE"):
                        self.advance()
                else:
                    self.advance()

                else_body = []
                while not self.match("SEPARATOR_RBRACE") and self.peek():
                    stmt = self.parse_statement()
                    if stmt: else_body.append(stmt)
                self.expect("SEPARATOR_RBRACE",
                                   error_msg="Expected '}' to close else block")

        return ("IfStatement", condition, if_body, else_body)

    def parse_while_loop(self):
        self.advance()   # 'while'
        self.in_while_header = True

        self.expect("SEPARATOR_LPAREN", error_msg="Expected '(' after 'while'")
        condition = self.parse_expression()
        if condition is None:
            self.add_error("Expected condition in while loop")
        else:
            self._register_expr_identifiers(condition)

        self.expect("SEPARATOR_RPAREN", error_msg="Expected ')' after condition")
        self.in_while_header = False

        if not self.match("SEPARATOR_LBRACE"):
            self.expect("SEPARATOR_LBRACE", error_msg="Expected '{' to start while block")
            while self.peek() and self.peek()[0] != "SEPARATOR_LBRACE":
                if self.peek()[0] in ("DATATYPE", "KEYWORD_IF", "KEYWORD_WHILE", "KEYWORD_RETURN"):
                    break
                self.advance()
            if self.match("SEPARATOR_LBRACE"):
                self.advance()
        else:
            self.advance()

        body = []
        while not self.match("SEPARATOR_RBRACE") and self.peek():
            stmt = self.parse_statement()
            if stmt: body.append(stmt)

        self.expect("SEPARATOR_RBRACE", error_msg="Expected '}' to close while block")

        return ("WhileLoop", condition, body)

    def parse_for_loop(self):
        self.advance()   # 'for'
        self.in_for_header = True

        self.expect("SEPARATOR_LPAREN", error_msg="Expected '(' after 'for'")

        # Init
        init = None
        if self.is_datatype():
            init = self.parse_variable_declaration()
        elif self.match("IDENTIFIER"):
            init = self.parse_assignment()
        elif self.match("SEPARATOR_SEMICOLON"):
            self.advance()
        else:
            self.add_error("Invalid for loop initialization")

        # Condition
        condition = None
        if not self.match("SEPARATOR_SEMICOLON"):
            condition = self.parse_expression()
            if condition:
                self._register_expr_identifiers(condition)
        self.expect("SEPARATOR_SEMICOLON",
                    error_msg="Expected ';' after for loop condition")

        # Update  (assignment  OR  expression)
        update = None
        if not self.match("SEPARATOR_RPAREN"):
            if (self.match("IDENTIFIER") and self.peek(1) and
                    self.peek(1)[0] == "OPERATOR_ASSIGN"):
                ident = self.advance()
                self._use(ident[1], ident[2])
                self.advance()          # '='
                expr  = self.parse_expression()
                self._register_expr_identifiers(expr)
                update = ("Assignment_NoSemi", ident, expr)
            else:
                update = self.parse_expression()
                self._register_expr_identifiers(update)

        self.expect("SEPARATOR_RPAREN",
                           error_msg="Expected ')' after for loop header")

        self.in_for_header = False

        if not self.match("SEPARATOR_LBRACE"):
            self.expect("SEPARATOR_LBRACE", error_msg="Expected '{' to start for loop body")
            while self.peek() and self.peek()[0] != "SEPARATOR_LBRACE":
                if self.peek()[0] in ("DATATYPE", "KEYWORD_IF", "KEYWORD_WHILE", "KEYWORD_RETURN"):
                    break
                self.advance()
            if self.match("SEPARATOR_LBRACE"):
                self.advance()
        else:
            self.advance()

        body = []
        while not self.match("SEPARATOR_RBRACE") and self.peek():
            stmt = self.parse_statement()
            if stmt: body.append(stmt)

        self.expect("SEPARATOR_RBRACE",
                           error_msg="Expected '}' to close for loop")

        return ("ForLoop", init, condition, update, body)

    def parse_return_statement(self):
        self.advance()   # 'return'
        value = None
        if not self.match("SEPARATOR_SEMICOLON"):
            value = self.parse_expression()
            self._register_expr_identifiers(value)
        self.expect("SEPARATOR_SEMICOLON",
                    error_msg="Expected ';' after return statement")
        return ("ReturnStatement", value)

    def parse_main_function(self):
        self.advance()   # datatype (int)
        self.advance()   # main

        self.expect("SEPARATOR_LPAREN", error_msg="Expected '(' after 'main'")
        self.expect("SEPARATOR_RPAREN", error_msg="Expected ')' after 'main('")
        
        if not self.match("SEPARATOR_LBRACE"):
            self.expect("SEPARATOR_LBRACE", error_msg="Expected '{' to start main function")
            while self.peek() and self.peek()[0] != "SEPARATOR_LBRACE":
                if self.peek()[0] in ("DATATYPE", "KEYWORD_IF", "KEYWORD_WHILE", "KEYWORD_RETURN"):
                    break
                self.advance()
            if self.match("SEPARATOR_LBRACE"):
                self.advance()
        else:
            self.advance()

        body = []
        while not self.match("SEPARATOR_RBRACE") and self.peek():
            stmt = self.parse_statement()
            if stmt: body.append(stmt)

        self.expect("SEPARATOR_RBRACE",
                           error_msg="Expected '}' to close main function")

        return ("MainFunction", body)

    def parse_statement(self):
        token = self.peek()
        if not token:
            return None

        # main function
        if self.is_datatype() and self.peek(1) and self.peek(1)[1] == "main":
            return self.parse_main_function()

        # variable declaration
        if self.is_datatype():
            return self.parse_variable_declaration()

        if self.match("KEYWORD_IF"):     return self.parse_if_statement()
        if self.match("KEYWORD_WHILE"):  return self.parse_while_loop()
        if self.match("KEYWORD_FOR"):    return self.parse_for_loop()
        if self.match("KEYWORD_RETURN"): return self.parse_return_statement()
        if self.match("KEYWORD_PRINT"):  return self.parse_print_statement()

        # Assignment or bare expression
        if self.match("IDENTIFIER"):
            next_tok = self.peek(1)

            # Valid continuations after a statement-level identifier:
            #   =        assignment
            #   ++ / --  postfix increment/decrement expression
            #   ;        expression statement (just the identifier, rare but legal)
            #   (        function call (future)
            VALID_AFTER_IDENT = {
                "OPERATOR_ASSIGN",
                "OPERATOR_INCREMENT", "OPERATOR_DECREMENT",
                "SEPARATOR_SEMICOLON",
                "SEPARATOR_LPAREN",
            }
            if next_tok is None or next_tok[0] not in VALID_AFTER_IDENT:
                # Bare identifier not followed by any valid continuation → error
                bad = self.advance()
                self.add_error(
                    f"Identifier '{bad[1]}' used without declaration or "
                    f"valid statement context (missing type keyword or ';')", bad)
                self.synchronize()
                return None

            if self.peek(1) and self.peek(1)[0] == "OPERATOR_ASSIGN":
                return self.parse_assignment()

            expr = self.parse_expression()
            self.expect("SEPARATOR_SEMICOLON",
                        error_msg="Expected ';' after expression")
            return ("ExpressionStatement", expr)

        if token[0] in ("OPERATOR_INCREMENT", "OPERATOR_DECREMENT"):
            expr = self.parse_expression()
            self.expect("SEPARATOR_SEMICOLON",
                        error_msg="Expected ';' after expression")
            return ("ExpressionStatement", expr)

        if token[0] == "INVALID_IDENTIFIER":
            self.add_error(f"Invalid variable name '{token[1]}'", token)
        else:
            self.add_error(f"Unexpected token '{token[1]}'", token)
        self.synchronize()
        return None

    # ── top-level ───────────────────────────────────────────────────────

    def parse_program(self):
        statements = []
        while self.peek():
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
        return {
            "type":     "Program",
            "body":     statements,
            "errors":   self.errors,
            "warnings": self.warnings,
        }

    def print_errors(self):
        if not self.errors:
            print("No syntax errors found!")
            return
        print(f"\n{'='*60}")
        print(f"SYNTAX ERRORS DETECTED: {len(self.errors)} error(s)")
        print(f"{'='*60}\n")
        for i, err in enumerate(self.errors, 1):
            print(f"Error {i}:")
            print(f"  Line: {err['line']}, Column: {err['column']}")
            print(f"  Message: {err['message']}")
            if err['token']:
                print(f"  Near token: '{err['token']}'")
            print()


# ============================================================
#  MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("W++ COMPILER - SCANNER | PARSER | SYMBOL TABLE")
    print("=" * 60)

    # ── Step 1: Scan ────────────────────────────────────────────
    print("\n[STEP 1: SCANNING]")
    scanner = Scanner()
    data    = scanner.load_data("Testfile.txt")

    lines, total_lines                      = scanner.tokenize(data)
    comments, block_comments, cleaned_lines = scanner.line_tokenizer(lines)
    Operators , operators_number , Separators , separators_number = scanner.tokenizing_operators(cleaned_lines)
    Keywords , keywords_number , unrecognized_tokens , unrecognized_tokens_number , identifiers , identifiers_number = scanner.tokenizing_keywords(cleaned_lines)
    literal_interger , literal_interger_number , literal_float , literal_float_number , literal_char , literal_char_number = scanner.tokenizing_literals(cleaned_lines)
    literal_words, literal_words_number = scanner.literal_words(cleaned_lines)
    token_stream                            = scanner.generate_token_stream(cleaned_lines)
    """
    print(f"  Total lines scanned    : {total_lines}")
    print(f"  Single-line comments   : {len(comments)}")
    print(f"  Block comment segments : {len(block_comments)}")
    print(f"  Token lines generated  : {len(token_stream)}")



    print("unrecognized_tokens:", unrecognized_tokens)
    print("unrecognized_tokens count:", unrecognized_tokens_number)
    print("Operators:", Operators)
    print("Operators count:", operators_number)
    print("Separators:", Separators)
    print("Separators count:", separators_number)
    print("Comments:", comments)
    print("Multi-line Comments:", block_comments)
    print("Keywords:", Keywords)
    print("Keywords count:", keywords_number)
    print("identifiers:", identifiers)
    print("identifiers count:", identifiers_number)
    print("Literal words:", literal_words)
    print("Literal words count:", literal_words_number)
    print("Literal integers:", literal_interger)
    print("Literal integers count:", literal_interger_number)
    print("Literal floats:", literal_float)
    print("Literal floats count:", literal_float_number)
    print("Literal characters:", literal_char)
    print("Literal characters count:", literal_char_number) 
    """

    # ── Step 2: Parse ───────────────────────────────────────────
    print("\n[STEP 2: PARSING]")
    parser = Parser(token_stream)
    ast    = parser.parse_program()

    parser.print_errors()

    if not parser.errors:
        print(f"\nProgram parsed successfully!")
        print(f"  Top-level statements: {len(ast['body'])}")

    # ── Step 3: Symbol Table ────────────────────────────────────
    print("\n[STEP 3: SYMBOL TABLE]")
    parser.symbol_table.print_table()


    
def CodeAnalyzer(source_code: str, file_name: str = "snippet.wpp"):
    user = Scanner()
    data = user.load_code(source_code)
    result, total_tokens = user.tokenize(data)
    comments, multi_line_comment, cleaned_lines = user.line_tokenizer(result)
    Operators, operators_number, Separators, separators_number = user.tokenizing_operators(cleaned_lines)
    Keywords, keywords_number, unrecognized_tokens, unrecognized_tokens_number, identifiers, identifiers_number = user.tokenizing_keywords(cleaned_lines)
    literal_interger, literal_interger_number, literal_float, literal_float_number, literal_char, literal_char_number = user.tokenizing_literals(cleaned_lines)
    literal_words_dict, literal_words_number = user.literal_words(cleaned_lines)

    token_stream = user.generate_token_stream(cleaned_lines)
    parser = Parser(token_stream)
    ast = parser.parse_program()
    symbol_table_entries = parser.symbol_table.all_entries()

    return {
        "file_name": file_name,
        "total_lines": total_tokens,
        "lines_with_code": len(cleaned_lines),
        "empty_lines": total_tokens - len(result),
        "total_tokens": sum(operators_number.values()) + sum(separators_number.values()) + sum(keywords_number.values()) + sum(unrecognized_tokens_number.values()) + sum(identifiers_number.values()) + sum(literal_interger_number.values()) + sum(literal_float_number.values()) + sum(literal_char_number.values()) + sum(literal_words_number.values()),
        "operators": {
            "tokens": Operators,
            "counts": operators_number
        },
        "separators": {
            "tokens": Separators,
            "counts": separators_number
        },
        "keywords": {
            "tokens": Keywords,
            "counts": keywords_number
        },
        "identifiers": {
            "tokens": identifiers,
            "counts": identifiers_number
        },
        "literals": {
            "strings": {
                "tokens": literal_words_dict,
                "counts": literal_words_number
            },
            "integers": {
                "tokens": literal_interger,
                "counts": literal_interger_number
            },
            "floats": {
                "tokens": literal_float,
                "counts": literal_float_number
            },
            "chars": {
                "tokens": literal_char,
                "counts": literal_char_number
            }
        },
        "comments": {
            "single_line": [{"text": c, "line": ln} for c, ln in comments],
            "multi_line": [{"text": c, "line": ln} for c, ln in multi_line_comment]
        },
        "unrecognized": {
            "tokens": unrecognized_tokens,
            "counts": unrecognized_tokens_number
        },
        "parser": {
            "ast": ast,
            "symbol_table": symbol_table_entries
        }
    }


def CodeAnalyzerFromFile(file_path: str):
    user = Scanner()
    data = user.load_data(file_path)
    return CodeAnalyzer(data, file_name=file_path)