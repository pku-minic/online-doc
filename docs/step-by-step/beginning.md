# 2.1. 开始

首先我们需要说明 `first-step` 的语法结构.

## 注释

`first-step` 使用 `#` 标记行注释的开头.

## 基本类型和变量

`first-step` 中只支持 32 位有符号整数作为基本类型.

因为 `first-step` 只支持一种基本类型, 所以我们在定义变量时无需书写任何多余的内容, 只需写明变量的初始值即可.

```first-step
# 定义变量 `x`, 初始值为 1
x := 1
# 定义变量 `y`, 初始值为 2
y := 2
# 修改变量 `x`
x = x + 1
```

## 运算符

`first-step` 支持下列运算符:

* 四则运算和模运算: `+`, `-`, `*`, `/`, `%`.
* 比较运算: `<`, `<=`, `==`, `!=`.
* 逻辑运算: `&&`, `||`, `!`.

运算符的优先级和结合性同 C/C++.

```first-step
x := 1
y := 2

# `z` 的值为 0
z := y - x * 2

# `b1` 的值为某个非零值
b1 := y || z

# `b2` 的值为 0
b2 := y && z
```

## 控制流

`first-step` 只支持两种控制流:

* `if cond { stmt1 } else { stmt2 }`: 如果条件 `cond` 成立, 则执行 `stmt1`, 否则执行 `stmt2`. `else` 的部分可以省略.
* `return x`: 从函数中返回, 返回值为 `x`.

```first-step
x := 1
y := 2

if x < y {
  x = x + 1
}
else {
  y = y * 2
}
```

## 函数

`first-step` 可以定义函数, 函数必须具备返回值, 且返回值的类型只能为 32 位有符号整数.

函数定义时, 可以在函数名后的括号内写明形式参数的名称, 形式参数之间使用逗号分隔. 函数不接收参数时, 依然需要在定义中写明括号, 但括号中不包含任何内容.

函数调用的方式和 C/C++ 等语言类似.

约定程序的入口为 `main` 函数, `main` 函数没有参数.

```first-step
# 一个不接收参数的函数
func() {
  return 1
}

# 一个接受两个参数的函数
add(a, b) {
  return a + b
}

# 入口函数
main() {
  return add(108191, 6324) - func()
}
```

## 库函数

为了让写出来的程序更有意义, 我们规定两个函数用来进行输入和输出:

* `input()`: 从标准输入 (`stdin`) 读取一个整数.
* `print(x)`: 向标准输出 (`stdout`) 输出整数 `x`, 并且在之后输出一个换行符.

这两个函数可以直接在程序中使用.

```first-step
main() {
  x := input()
  print(x + 1)
  return 0
}
```

## EBNF 格式的语法定义

以上就是 `first-step` 的全部语法了, 看起来相当简单, 但绝对够用.

我们可以将其书写为 EBNF 格式:

```ebnf
Program       ::= {FunctionDef};
FunctionDef   ::= IDENT "(" [ArgsDef] ")" Block;
ArgsDef       ::= IDENT {"," IDENT};

Block         ::= "{" {Statement} "}";
Statement     ::= IDENT ":=" Expression
                | IDENT "=" Expression
                | FunctionCall
                | IfElse
                | "return" Expression;
IfElse        ::= "if" Expression Block ["else" (IfElse | Block)];

Expression    ::= LOrExpr;
LOrExpr       ::= LAndExpr {"||" LAndExpr};
LAndExpr      ::= EqExpr {"&&" EqExpr};
EqExpr        ::= RelExpr {("==" | "!=") RelExpr};
RelExpr       ::= AddExpr {("<" | "<=") AddExpr};
AddExpr       ::= MulExpr {("+" | "-") MulExpr};
MulExpr       ::= UnaryExpr {("*" | "/" | "%") UnaryExpr};
UnaryExpr     ::= ["-" | "!"] Value;
Value         ::= INTEGER
                | IDENT
                | FunctionCall
                | "(" Expression ")";
FunctionCall  ::= IDENT "(" [Args] ")";
Args          ::= Expression {"," Expression};
```
