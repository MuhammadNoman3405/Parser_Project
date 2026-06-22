const WPP_KEYWORDS = ["int", "float", "double", "char", "string", "bool", "void", "long", "if", "else", "while", "for", "do", "return", "print", "read", "true", "false", "main"];
const KW_REGEX = new RegExp(`\\b(${WPP_KEYWORDS.join('|')})\\b`, 'g');
let str = "int main() {";
console.log(str.replace(KW_REGEX, '<b>$1</b>'));
