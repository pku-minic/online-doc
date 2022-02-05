# Lv7.2. `break` 和 `continue`

本节新增/变更的语法规范如下:

```ebnf
Stmt ::= ...
       | ...
       | ...
       | ...
       | ...
       | "break" ";"
       | "continue" ";"
       | ...;
```

## 一个例子

```c
int main() {
  while (1) break;
  return 0;
}
```

## 词法/语法分析

本节新增了关键字 `break` 和 `continue`, 你需要修改你的 lexer 来支持它们. 同时, 你需要针对这两种语句设计 AST, 并更新你的 parser 实现.

## 语义分析

注意 `break` 和 `continue` 只能出现在循环内. 例如, 以下的程序存在语义错误:

```c
int main() {
  break;
  return 0;
}
```

?> 其实在写编译器的时候你会发现, 在进行 IR 生成时, 你很容易判断 `break`/`continue` 是否出现在了循环内.

## IR 生成

`break` 和 `continue` 本质上执行的都是跳转操作, 只不过一个会跳转到循环结尾, 一个会跳转到循环开头. 所以, 为了正确获取跳转的目标, 你的编译器在生成循环时必须记录循环开头和结尾的相关信息.

此外需要注意的是, `while` 循环是可以嵌套的, 所以, 你应该选择合适的数据结构来存储 `break`/`continue` 所需的信息.

示例程序生成的 Koopa IR **可能**为:

```koopa
fun @main(): i32 {
%entry:
  jump %while_entry

%while_entry:
  br 1, %while_body, %end

%while_body:
  jump %end

%while_body1:
  jump %while_entry

%end:
  ret 0
}
```

!> 上面的 Koopa IR 程序是文档作者根据经验, 模仿一个编译器生成出来的 (事实上文档里所有的 Koopa IR 示例都是这么写的) (人形编译器 MaxXing 实锤), 仅代表一种可能的 IR 生成方式.
<br><br>
你会看到, 程序中出现了一个不可达的基本块 `%while_body1`. 这件事情在人类看来比较费解: 为什么会这样呢? ~~怎么会事呢?~~ 但对于编译器的 IR 生成部分而言, 这么做是最省事的. 你也许可以思考一下背后的原因.

## 目标代码生成

本节并未用到新的 Koopa IR 指令, 也不涉及 Koopa IR 中的新概念, 所以这部分没有需要改动的内容.
