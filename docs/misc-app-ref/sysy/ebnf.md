# 3.1. 文法定义

SysY 语言的文法采用扩展的 Backus 范式 (EBNF, Extended Backus-Naur Form) 表示, 其中:

* 符号 `[...]` 表示方括号内包含的项可选.
* 符号 `{...} `表示花括号内包含的项可被重复 0 次或多次.
* 终结符是由双引号括起的串, 或者是 `IDENT`, `INT_CONST` 这样的大写记号.

SysY 语言的文法表示如下，其中 `CompUnit` 为开始符号:

```ebnf
CompUnit      ::= [CompUnit] (Decl | FuncDef);

Decl          ::= ConstDecl | VarDecl;
ConstDecl     ::= "const" BType ConstDef {"," ConstDef} ";";
BType         ::= "int";
ConstDef      ::= IDENT {"[" ConstExp "]"} "=" ConstInitVal;
ConstInitVal  ::= ConstExp | "{" [ConstInitVal {"," ConstInitVal}] "}";
VarDecl       ::= BType VarDef {"," VarDef} ";";
VarDef        ::= IDENT {"[" ConstExp "]"}
                | IDENT {"[" ConstExp "]"} "=" InitVal;
InitVal       ::= Exp | "{" [InitVal {"," InitVal}] "}";

FuncDef       ::= FuncType IDENT "(" [FuncFParams] ")" Block;
FuncType      ::= "void" | "int";
FuncFParams   ::= FuncFParam {"," FuncFParam};
FuncFParam    ::= BType IDENT ["[" "]" {"[" ConstExp "]"}];

Block         ::= "{" {BlockItem} "}";
BlockItem     ::= Decl | Stmt;
Stmt          ::= LVal "=" Exp ";"
                | [Exp] ";"
                | Block
                | "if" "(" Cond ")" Stmt ["else" Stmt]
                | "while" "(" Cond ")" Stmt
                | "break" ";"
                | "continue" ";"
                | "return" [Exp] ";";

Exp           ::= AddExp;
Cond          ::= LOrExp;
LVal          ::= IDENT {"[" Exp "]"};
PrimaryExp    ::= "(" Exp ")" | LVal | Number;
Number        ::= INT_CONST;
UnaryExp      ::= PrimaryExp | IDENT "(" [FuncRParams] ")" | UnaryOp UnaryExp;
UnaryOp       ::= "+" | "-" | "!";
FuncRParams   ::= Exp {"," Exp};
MulExp        ::= UnaryExp | MulExp ("*" | "/" | "%") UnaryExp;
AddExp        ::= MulExp | AddExp ("+" | "-") MulExp;
RelExp        ::= AddExp | RelExp ("<" | ">" | "<=" | ">=") AddExp;
EqExp         ::= RelExp | EqExp ("==" | "!=") RelExp;
LAndExp       ::= EqExp | LAndExp "&&" EqExp;
LOrExp        ::= LAndExp | LOrExp "||" LAndExp;
ConstExp      ::= AddExp;
```

其中, 各符号的含义如下:

| 符号         | 含义         | 符号           | 含义        |
| ---         | ---          | ---           | ---        |
| CompUnit    | 编译单元      | Decl          | 声明        |
| ConstDecl   | 常量声明      | BType         | 基本类型     |
| ConstDef    | 常数定义      | ConstInitVal  | 常量初值     |
| VarDecl     | 变量声明      | VarDef        | 变量定义     |
| InitVal     | 变量初值      | FuncDef       | 函数定义     |
| FuncType    | 函数类型      | FuncFParams   | 函数形参表   |
| FuncFParam  | 函数形参      | Block         | 语句块      |
| BlockItem   | 语句块项      | Stmt          | 语句        |
| Exp         | 表达式       | Cond           | 条件表达式   |
| LVal        | 左值表达式    | PrimaryExp     | 基本表达式   |
| Number      | 数值         | UnaryExp       | 一元表达式   |
| UnaryOp     | 单目运算符    | FuncRParams    | 函数实参表   |
| MulExp      | 乘除模表达式  | AddExp         | 加减表达式   |
| RelExp      | 关系表达式    | EqExp          | 相等性表达式 |
| LAndExp     | 逻辑与表达式  | LOrExp         | 逻辑或表达式 |
| ConstExp    | 常量表达式    |

需要注意的是:

* `Exp`: SysY 中表达式的类型均为 `int` 型.
* `UnaryOp`: 运算符 `!` 仅会出现在条件表达式中.
* `ConstExp`: 其中使用的 `IDENT` 必须是常量.

## SysY 语言的终结符特征

### 标识符

SysY 语言中标识符 `IDENT` (identifier) 的规范如下:

```ebnf
identifier  ::= identifier-nondigit
              | identifier identifier-nondigit
              | identifier digit;
```

其中, `identifier-nondigit` 为下划线, 小写英文字母或大写英文字母; `digit` 为数字 0 到 9.

关于其他信息, 请参考 [ISO/IEC 9899](http://www.open-std.org/jtc1/sc22/wg14/www/docs/n1124.pdf) 第 51 页关于标识符的定义.

对于同名**标识符**, SysY 中有以下约定:

* 全局变量和局部变量的作用域可以重叠, 重叠部分局部变量优先.
* 同名局部变量的作用域不能重叠.
* 变量名可以和函数名相同.

### 数值常量

SysY 语言中数值常量可以是整型数 `INT_CONST` (integer-const), 其规范如下:

```ebnf
integer-const       ::= decimal-const
                      | octal-const
                      | hexadecimal-const;
decimal-const       ::= nonzero-digit
                      | decimal-const digit;
octal-const         ::= "0"
                      | octal-const octal-digit;
hexadecimal-const   ::= hexadecimal-prefix hexadecimal-digit
                      | hexadecimal-const hexadecimal-digit;
hexadecimal-prefix  ::= "0x" | "0X";
```

其中, `nonzero-digit` 为数字 1 到 9; `octal-digit` 为数字 0 到 7; `hexadecimal-digit` 为数字 0 到 9, 或大写/小写字母 a 到 f.

关于其他信息, 请参考 [ISO/IEC 9899](http://www.open-std.org/jtc1/sc22/wg14/www/docs/n1124.pdf) 第 54 页关于整数型常量的定义, 在此基础上忽略所有后缀.

### 注释

SysY 语言中注释的规范与 C 语言一致, 如下:

* 单行注释: 以序列 `//` 开始, 直到换行符结束, 不包括换行符.
* 多行注释: 以序列 `/*` 开始, 直到第一次出现 `*/` 时结束, 包括结束处 `*/`.

关于其他信息, 请参考 [ISO/IEC 9899](http://www.open-std.org/jtc1/sc22/wg14/www/docs/n1124.pdf) 第 66 页关于注释的定义.
