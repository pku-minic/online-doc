# Lv1. `main` 函数

本章中, 你将实现一个能处理 `main` 函数和 `return` 语句的编译器. 你的编译器会将如下的 SysY 程序:

```c
int main() {
  // 注释也应该被删掉哦
  return 0;
}
```

编译为对应的 Koopa IR:

```koopa
fun @main(): i32 {
%entry:
  ret 0
}
```

## 词法规范

### 标识符

SysY 语言中标识符 `IDENT` (identifier) 的规范如下:

```ebnf
identifier ::= identifier-nondigit
             | identifier identifier-nondigit
             | identifier digit;
```

其中, `identifier-nondigit` 为下划线, 小写英文字母或大写英文字母; `digit` 为数字 0 到 9.

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

### 注释

SysY 语言中注释的规范与 C 语言一致, 如下:

* 单行注释: 以序列 `//` 开始, 直到换行符结束, 不包括换行符.
* 多行注释: 以序列 `/*` 开始, 直到第一次出现 `*/` 时结束, 包括结束处 `*/`.

## 语法规范

开始符号为 `CompUnit`.

```ebnf
CompUnit  ::= FuncDef;

FuncDef   ::= FuncType IDENT "(" ")" Block;
FuncType  ::= "int";

Block     ::= "{" Stmt "}";
Stmt      ::= "return" Number ";";
Number    ::= INT_CONST;
```

## 语义规范

* 在本章中, `IDENT` 的名称一定为 `main`.
* `INT_CONST` 的范围为 $[0, 2^{31} - 1]$, 不包含负号.
