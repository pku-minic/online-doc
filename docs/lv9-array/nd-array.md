# Lv9.2. 多维数组

本节新增/变更的语法规范如下:

```ebnf
ConstDef      ::= IDENT {"[" ConstExp "]"} "=" ConstInitVal;
ConstInitVal  ::= ConstExp | "{" [ConstInitVal {"," ConstInitVal}] "}";
VarDef        ::= IDENT {"[" ConstExp "]"}
                | IDENT {"[" ConstExp "]"} "=" InitVal;
InitVal       ::= Exp | "{" [InitVal {"," InitVal}] "}";

LVal          ::= IDENT {"[" Exp "]"};
```

## 一个例子

```c
int main() {
  int arr[2][3] = {1, 2};
  return arr[0][2];
}
```

## 词法/语法分析

针对本节发生变化的语法规则, 设计新的 AST, 并更新你的 parser 实现即可.

## 语义分析

上一节的相关注意事项可推广至这一节, 唯一需要注意的是, **多维数组的初始化列表会更复杂.** 比如示例程序中, `int[2][3]` 的数组使用了一个 `{1, 2}` 形式的初始化列表. 我们可以把它写得完整一些:

```c
int arr[2][3] = {{1, 2, 0}, {0, 0, 0}};
```

看起来似乎很好理解: 把这个 2 乘 3 的数组展平, 前两个元素已经给出了, 后续元素填充 0 即可, 对吧? 然而, 实际情况比你想象的还要复杂, 比如以下这个初始化列表:

```c
int arr[2][3][4] = {1, 2, 3, 4, {5}, {6}, {7, 8}};
```

这个就不太好理解了. 如果你遇到这种不好理解的例子, 可以利用我们之前提到的网站——[Compiler Explorer](https://godbolt.org/), 直接查看 C 语言代码对应的汇编. 比如以上这个例子, 如果我们把 `arr` 视作一个全局数组, 那么对应的汇编为:

```
arr:
  .word   1
  .word   2
  .word   3
  .word   4
  .word   5
  .word   0
  .word   0
  .word   0
  .word   6
  .word   0
  .word   0
  .word   0
  .word   7
  .word   8
  .word   0
  .word   0
  .zero   16
  .zero   16
```

之前我们已经介绍过 `.word` 和 `.zero` 的含义, 你不难把上面的汇编代码复原回初始化列表:

```c
int arr[2][3][4] = {
  {{1, 2, 3, 4}, {5, 0, 0, 0}, {6, 0, 0, 0}},
  {{7, 8, 0, 0}, {0, 0, 0, 0}, {0, 0, 0, 0}}
};
```

所以我们建议, 在处理 SysY 的初始化列表前, 你应该先把初始化列表转换为已经填好 0 的形式, 这样处理难度会大幅度下降. 因为用户输入的程序里未必一定会写出一个合法的初始化列表, 比如:

```c
int arr[2][2][2] = {{}, 1, {}};
```

所以这一步应该被放在语义分析阶段, 以便你在转换的同时报告语义错误. 但考虑到由于测试输入一定是合法的, 有的同学不会做语义分析, 所以这一步放到 IR 生成阶段也是可以的.

读到此处, 我觉得你最关心的问题应该是: 到底应该如何理解 SysY 的初始化列表, 然后把它转换成一个填好 0 的形式呢? 其实, 处理 SysY (或 C 语言) 中的初始化列表时, 可以遵循这几个原则:

1. 记录待处理的 $n$ 维数组各维度的总长 $len_1, len_2, \cdots, len_n$. 比如 `int[2][3][4]` 各维度的长度分别为 2, 3 和 4.
2. 依次处理初始化列表内的元素, 元素的形式无非就两种可能: 整数, 或者另一个初始化列表.
3. 遇到整数时, 从当前待处理的维度中的最后一维 (第 $n$ 维) 开始填充数据.
4. 遇到初始化列表时:
    * 当前已经填充完毕的元素的个数必须是 $len_n$ 的整数倍, 否则这个初始化列表没有对齐数组维度的边界, 你可以认为这种情况属于语义错误.
    * 检查当前对齐到了哪一个边界, 然后将当前初始化列表视作这个边界所对应的最长维度的数组的初始化列表, 并递归处理. 比如:
      * 对于 `int[2][3][4]` 和初始化列表 `{1, 2, 3, 4, {5}}`, 内层的初始化列表 `{5}` 对应的数组是 `int[4]`.
      * 对于 `int[2][3][4]` 和初始化列表 `{1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, {5}}`, 内层的初始化列表 `{5}` 对应的数组是 `int[3][4]`.
      * 对于 `int[2][3][4]` 和初始化列表 `{{5}}`, 内层的初始化列表 `{5}` 之前没出现任何整数元素, 这种情况其对应的数组是 `int[3][4]`.

鉴于写文档的人的归纳能力比较捉急, 你可以在 [Compiler Explorer](https://godbolt.org/) 上多写几个初始化列表, 进一步体会上述内容的含义.

!> **注意:** 当你在 Compiler Explorer 查看数组初始化的情况时, 如果你注意到编译器 (比如 GCC) 对你写的初始化列表报告了相关警告 (warning), 那么你可以认为这个初始化列表是不合法的. 你可以通过在编译选项中 (网站右侧面板的文本框) 添加 `-Werror` 来将所有警告转换为编译错误.
<br><br>
例如, 对于代码 `int arr[2][3][4] = {1, 2, {3}};`, GCC 会报告 `{3}` 处出现警告 “braces around scalar initializer”. 也就是说, GCC 认为 `{3}` 实际上代表了标量 (scalar) `3`, 而非聚合类型 (aggregate) `{3}`.
<br><br>
在 SysY 中, 你的编译器不需要像这样聪明到足以纠正用户错误的程度. 在遇到上述 `{3}` 时, 你的编译器只需认为此处出现了一个新的初始化列表, 然后按照规则报错即可.

## IR 生成

与上一节类似, 此处不再赘述.

## 目标代码生成

本节并未用到新的 Koopa IR 指令, 也不涉及 Koopa IR 中的新概念, 所以这部分没有需要改动的内容.
