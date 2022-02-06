# Lv8. 函数和全局变量

本章中, 你将在上一章的基础上, 实现一个能够处理函数 (包括 SysY 库函数) 和全局变量的编译器.

你的编译器将可以处理如下的 SysY 程序:

```c
int var;

int func(int x) {
  var = var + x;
  return var;
}

int main() {
  // putint 和 putch 都是 SysY 库函数
  // SysY 要求库函数不声明就可以使用
  putint(func(1));
  var = var * 10;
  putint(func(2));
  putch(10);
  return var;
}
```

## 语法规范

```ebnf
CompUnit      ::= [CompUnit] FuncDef;

Decl          ::= ConstDecl | VarDecl;
ConstDecl     ::= "const" BType ConstDef {"," ConstDef} ";";
BType         ::= "int";
ConstDef      ::= IDENT "=" ConstInitVal;
ConstInitVal  ::= ConstExp;
VarDecl       ::= BType VarDef {"," VarDef} ";";
VarDef        ::= IDENT | IDENT "=" InitVal;
InitVal       ::= Exp;

FuncDef       ::= FuncType IDENT "(" [FuncFParams] ")" Block;
FuncType      ::= "void" | "int";
FuncFParams   ::= FuncFParam {"," FuncFParam};
FuncFParam    ::= BType IDENT;

Block         ::= "{" {BlockItem} "}";
BlockItem     ::= Decl | Stmt;
Stmt          ::= LVal "=" Exp ";"
                | [Exp] ";"
                | Block
                | "if" "(" Exp ")" Stmt ["else" Stmt]
                | "while" "(" Exp ")" Stmt
                | "break" ";"
                | "continue" ";"
                | "return" [Exp] ";";

Exp           ::= LOrExp;
LVal          ::= IDENT;
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
ConstExp      ::= Exp;
```

## 语义规范

### 编译单元

* 一个 SysY 程序由单个文件组成, 文件内容对应 EBNF 表示中的 `CompUnit`. 在该 `CompUnit` 中, 必须存在且仅存在一个标识为 `main`, 无参数, 返回类型为 `int` 的 `FuncDef` (函数定义). `main` 函数是程序的入口点.
* `CompUnit` 的顶层变量/常量声明语句 (对应 `Decl`), 函数定义 (对应 `FuncDef`) 都不可以重复定义同名标识符 (`IDENT`), 即便标识符的类型不同也不允许.
* `CompUnit` 的变量/常量/函数声明的作用域从该声明处开始, 直到文件结尾.

### 全局变量/作用域

* 全局变量和局部变量的作用域可以重叠, 局部变量会覆盖同名全局变量.
* SysY 程序声明的函数名不能和 SysY 库函数名相同.
* 变量名可以和函数名相同.
* 全局变量声明中指定的初值表达式必须是常量表达式.
* 未显式初始化的全局变量, 其 (元素) 值均被初始化为 0.

### 函数

* `FuncDef` 表示函数定义. 其中的 `FuncType` 指明了函数的返回类型.
  * 当返回类型为 `int` 时, 函数内的所有分支都应当含有带有 `Exp` 的 `return` 语句. 不含有 `return` 语句的分支的返回值未定义.
  * 当返回值类型为 `void` 时, 函数内只能出现不带返回值的 `return` 语句.
* `FuncFParam` 定义函数的一个形式参数.
* SysY 标准中未指定函数形式参数应该被放入何种作用域. 为保持和 C 语言一致, 你可以将其放入函数体的作用域; 为实现方便, 你可以将其放入一个单独的作用域.
* 函数调用形式是 `IDENT "(" FuncRParams ")"`, 其中的 `FuncRParams` 表示实际参数. 实际参数的类型和个数必须与 `IDENT` 对应的函数定义的形参完全匹配.
* 函数实参的语法是 `Exp`. 对于 `int` 类型的参数, 遵循按值传递的规则.
* 试图使用返回类型为 `void` 的函数的返回值是未定义行为.
