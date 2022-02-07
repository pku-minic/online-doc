# Lv9. 数组

本章中, 你将在上一章的基础上, 实现一个能够处理数组的编译器. 这也是非可选章节中的最后一部分, 这部分完成后, 你的编译器将可以处理所有合法的 SysY 程序.

你的编译器将可以处理如下的 SysY 程序:

```c
int main() {
  int arr[10], n = getarray(arr);
  int i = 0, sum = 0;
  while (i < n) {
    sum = sum + arr[i];
    i = i + 1;
  }
  putint(sum);
  putch(10);
  return 0;
}
```

## 语法规范

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
                | "if" "(" Exp ")" Stmt ["else" Stmt]
                | "while" "(" Exp ")" Stmt
                | "break" ";"
                | "continue" ";"
                | "return" [Exp] ";";

Exp           ::= LOrExp;
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
ConstExp      ::= Exp;
```

## 语义规范

### 常量定义

* `ConstDef` 用于定义符号常量. `ConstDef` 中的 `IDENT` 为常量的标识符, 在 `IDENT` 后, `=` 之前是可选的数组维度和各维长度的定义部分, 在 `=` 之后是初始值.
* `ConstDef` 的数组维度和各维长度的定义部分不存在时, 表示定义单个常量. 此时 `=` 右边必须是单个初始数值.
* `ConstDef` 的数组维度和各维长度的定义部分存在时, 表示定义数组. 其语义和 C 语言一致, 比如 `[2][8/2][1*3]` 表示三维数组, 第一到第三维长度分别为 2, 4 和 3, 每维的下界从 0 开始编号. `ConstDef` 中表示各维长度的 `ConstExp` 都必须能在编译时被求值到非负整数. SysY 在声明数组时各维长度都需要显式给出, 而不允许是未知的.
* 当 `ConstDef` 定义的是数组时, `=` 右边的 `ConstInitVal` 表示常量初始化器. `ConstInitVal` 中的 `ConstExp` 是能在编译时被求值的 `int` 型表达式, 其中可以引用已定义的符号常量.
* `ConstInitVal` 初始化器必须是以下三种情况之一 (注: `int` 型初始值可以是 `Number`, 或者是 `int` 型常量表达式):
  * 一对花括号 `{}`, 表示所有元素初始为 0.
  * 与多维数组中数组维数和各维长度完全对应的初始值, 如 `{{1,2},{3,4},{5,6}}`, `{1,2,3,4,5,6}`, `{1,2,{3,4},5,6}` 均可作为 `a[3][2]` 的初始值.
  * 如果花括号括起来的列表中的初始值少于数组中对应维的元素个数, 则该维其余部分将被隐式初始化, 需要被隐式初始化的整型元素均初始为 0. 如 `{{1,2},{3},{5}}`, `{1,2,{3},5}`, `{{},{3,4},5,6}` 均可作为 `a[3][2]` 的初始值, 前两个将 `a` 初始化为 `{{1,2},{3,0},{5,0}}`, `{{},{3,4},5,6}` 将 `a` 初始化为 `{{0,0},{3,4},{5,6}}`.

### 变量定义

* `VarDef` 的数组维度和各维长度的定义部分不存在时, 表示定义单个变量; 存在时, 和 `ConstDef` 类似, 表示定义多维数组. (参见 `ConstDef` 的第 2 点)
* 当 `VarDef` 含有 `=` 和初始值时, `=` 右边的 `InitVal` 和 `CostInitVal` 的结构要求相同, 唯一的不同是 `ConstInitVal` 中的表达式是 `ConstExp` 常量表达式, 而 `InitVal` 中的表达式可以是当前上下文合法的任何 `Exp`.
* `VarDef` 中表示各维长度的 `ConstExp` 必须能被求值到非负整数, 但 `InitVal` 中
的初始值为 `Exp` 可以引用变量.
* 对于全局数组变量, 初值表达式必须是常量表达式.

### 初值

常量或变量声明中指定的初值要与该常量或变量的类型一致. 如下形式的 `VarDef`/`ConstDef` 不满足 SysY 语义约束:

```c
a[4] = 4;
a[2] = {{1,2}, 3};
a = {1,2,3};
```

### 函数行参与实参

* `FuncFParam` 定义函数的一个形式参数. 当 `IDENT` 后面的可选部分存在时, 表示定义数组类型的形参.
* 当 `FuncFParam` 为数组时, 其第一维的长度省去 (用方括号 `[]` 表示), 而后面的各维则需要用表达式指明长度, 其长度必须是常量.
* 函数实参的语法是 `Exp`. 对于 `int` 类型的参数, 遵循按值传递的规则; 对于数组类型的参数, 形参接收的是实参数组的地址, 此后可通过地址间接访问实参数组中的元素.
* 对于多维数组, 我们可以传递其中的一部分到形参数组中. 例如, 若存在数组定义 `int a[4][3]`, 则 `a[1]` 是包含三个元素的一维数组, `a[1]` 可以作为实参, 传递给类型为 `int[]` 的形参.

### 左值表达式

* 当 `LVal` 表示数组时, 方括号个数必须和数组变量的维数相同 (即定位到元素). 若 `LVal` 表示的数组作为数组参数参与函数调用, 则数组的方括号个数可以不与维数相同.
* 数组访问时下标越界属于未定义行为.
