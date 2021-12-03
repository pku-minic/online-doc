# 4.2. Tigger

Tigger (`/'tıgə(r)/`) 是面向 32 位 RISC-V 架构的一种中间表示, 用作寄存器分配阶段的输出格式.

## 语法描述

Tigger 在设计上与 Eeyore 存在诸多相似之处.

### 寄存器

Tigger 共有 28 个可用的寄存器, 这些寄存器的名称与 RISC-V 保持一致 (相比 RISC-V, 删去了一些不需要由编译器管理的寄存器).

* `x0`: 该寄存器恒等于 0, 不可更改
* `s0-s11`: 通用寄存器, 由 “被调用者” (callee) 保存.
* `t0-t6`: 通用寄存器, 由 “调用者” (caller) 保存.
* `a0-a7`: 用来传递函数参数, 同时也可作为通用寄存器, 由 “调用者” 保存. 其中 `a0-a1` 也被用作传递函数返回值, 但因为 SysY 中所有函数的返回值均为 `int` 类型, 所以实际上只有 `a0` 被用作传递返回值.

Tigger 除 `x0` 外所有寄存器的初始值均不确定, 在读取它们之前, 你必须对其进行显式初始化. 同时, `t0-t6` 寄存器的行为严格遵循调用约定, 如需使用这些寄存器, 你必须在调用外部函数 (库函数) 之前保存它们的值, 并在函数返回之后将其恢复, 否则函数返回之后, 这些寄存器的值将被打乱.

从上述定义可以看出, 在 RISC-V 架构中, 我们最多只能通过寄存器传递 8 个函数参数. 简单起见, 在 Tigger 中我们限定所有函数参数个数不超过 8 个.

在所有涉及 Tigger 的评测用例中, 我们会确保这一限制永远成立, 你可以放心对此作出断言.

### 表达式, 标号, 跳转语句

* 所有的表达式计算都需要在寄存器上进行.
* 所有在 Eeyore 中支持的运算符, 在 Tigger 中同样被支持.
* 注意: 因为 SysY 中只有 `int` 和 `int` 数组类型, 所以数组赋值语句中括号内的数应为 4 的整数倍.
* 注意: 由于 RISC-V 某些规则的原因, Tigger 中 `+` 和 `<` 运算符作为 `Reg = Reg BinOp NUM` 语句中的 `BinOp` 时会较为方便. 但不这么做……倒也可以 \_(:з」∠)_.
* 标号与跳转语句和 Eeyore 中的语法相同, 标号是全局的.

### 函数

* 函数定义语句形如 `f_func [2] [3]`, 第一个中括号内是参数个数, 第二个是该函数需要用到的栈空间的大小 (除以 4 之后).
* 函数结束语句与 Eeyore 中一致, 形如 `end f_func`.
* 函数**必须以返回语句返回**. 返回值通过寄存器传递.
* 函数调用语句形如 `call f_func`.

### 栈内存操作

程序运行时, 每个被调用的函数都会维护一个连续的栈空间, 大小为函数定义语句中的第二个参数.

Eeyore 中的局部变量都可以在 Tigger 的栈中找到, 因此 Tigger 中将不再有 "局部变量" 的概念.

* `store Reg NUM` 语句中, `NUM` 是一个小于函数定义语句第二个系数的非负整数. 该语句会把寄存器 `Reg` 的值存入当前函数栈空间第 `NUM` 个位置.
* `load NUM Reg` 语句中, `NUM` 是一个小于函数定义语句第二个系数的非负整数. 该语句会把当前函数栈空间第 `NUM` 个整数存入寄存器 `Reg`.
* `loadaddr NUM Reg` 语句中, `NUM` 是一个小于函数定义语句第二个系数的非负整数. 该语句会把当前函数栈空间第 `NUM` 个位置的内存地址存入寄存器 `Reg`.

举个例子, 假设某个时刻函数调用关系是 `f_main[0][3] -> f_f[0][4]`, 正在执行函数 `f_f`, 则此时的栈如下表所示:

> 注: 如下的例子只适用于 Tigger, 在 RISC-V 程序中, 栈的 layout 和下述情况略有不同.

<table>
<thead>
  <tr>
    <th>地址</th>
    <th>0x00</th>
    <th>0x04</th>
    <th>0x08</th>
    <th>0x0c</th>
    <th>0x10</th>
    <th>0x14</th>
    <th>0x18</th>
  </tr>
</thead>
<tbody>
  <tr>
    <td>栈偏移量<br></td>
    <td>0</td>
    <td>1</td>
    <td>2</td>
    <td>0</td>
    <td>1</td>
    <td>2</td>
    <td>3</td>
  </tr>
  <tr>
    <td>内容<br></td>
    <td>3</td>
    <td>4</td>
    <td>1</td>
    <td>10</td>
    <td>5</td>
    <td>0</td>
    <td>9</td>
  </tr>
  <tr>
    <td>函数<br></td>
    <td colspan="3" style="text-align: center;">f_main</td>
    <td colspan="4" style="text-align: center;">f_f</td>
  </tr>
</tbody>
</table>

此时语句 `load 2 s0`, 会将 `s0` 的值更新为 0; 语句 `loadaddr 2 s0`, 会将 `s0` 的值更新为 `0x14`; 语句 `store s0 2` 会将栈中地址 `0x14` 处内存的值更新为 `s0` 寄存器的值.

### 全局变量

* 全局变量名称以 `v` 开头, 后接一个整数编号, 编号从 0 开始, 比如 `v0`, `v1`.
* `VARIABLE = NUM` 用来声明一个初始值为 `NUM` 的全局变量 `VARIABLE`, 即 `VARIABLE` 这个名称表示的 4 字节内存中存储的内容为 `NUM`.
* `VARIABLE = malloc NUM` 用来声明数组, `VARIABLE` 这个名称表示的, 长度为 `NUM` 字节的内存的内容为一个数组. 注意 `NUM` **应为 4 的整数倍**.
* `load VARIABLE Reg` 表示把 `VARIABLE` 这个全局变量对应的 4 字节**内存中的内容**加载到寄存器 `Reg`.
* `loadaddr VARIABLE Reg` 表示把 `VARIABLE` 这个全局变量对应**内存地址**加载到寄存器 `Reg`.
* 注意: 由于 RISC-V 汇编的原因, Tigger 中没有设计 `store Reg VARIABLE` 操作. 该操作可以通过结合 `loadaddr` 语句与数组访问语句来实现.

### 缩进

Tigger 在语法和语义上没有缩进要求, 同时允许使用缩进. 为了之后代码调试的便利, 我们建议你在生成 Tigger 时正确使用缩进.

### 注释

Tigger 允许单行注释, 与 C/C++ 语言的行注释类似, 使用 `//` 标记.

### 运行时库函数支持

Tigger 虚拟机 (MiniVM) 提供对各类 SysY 运行时库函数的支持.

关于相关的运行时库函数, 请参考 [3.3 节](sysy/runtime.md).

## Tigger 语法的 EBNF 定义

开始符号为 `Program`.

```ebnf
Program         ::= {GlobalVarDecl | FunctionDef};

GlobalVarDecl   ::= VARIABLE "=" NUM
                  | VARIABLE "=" "malloc" NUM;
FunctionDef     ::= FunctionHeader Expressions FunctionEnd;
FunctionHeader  ::= FUNCTION "[" NUM "]" "[" NUM "]";
Expressions     ::= {Expression};
FunctionEnd     ::= "end" FUNCTION;

Expression      ::= Reg "=" Reg BinOp Reg
                  | Reg "=" Reg BinOp NUM
                  | Reg "=" OP Reg
                  | Reg "=" Reg
                  | Reg "=" NUM
                  | Reg "[" NUM "]" "=" Reg
                  | Reg "=" Reg "[" NUM "]"
                  | "if" Reg LOGICOP Reg "goto" LABEL
                  | "goto" LABEL
                  | LABEL ":"
                  | "call" FUNCTION
                  | "return"
                  | "store" Reg NUM
                  | "load" NUM Reg
                  | "load" VARIABLE Reg
                  | "loadaddr" NUM Reg
                  | "loadaddr" VARIABLE Reg;
BinOp           ::= OP | LOGICOP;
Reg             ::= "x0"
                  | "s0" | "s1" | "s2" | "s3" | "s4" | "s5" | "s6" | "s7" | "s8" | "s9" | "s10" | "s11"
                  | "t0" | "t1" | "t2" | "t3" | "t4" | "t5" | "t6"
                  | "a0" | "a1" | "a2" | "a3" | "a4" | "a5" | "a6" | "a7";
```

## 示例

Eeyore 程序:

```eeyore
var T0
var 40 T1

f_main [0]
  var T2
  var T3
  var t0
  var t1
  var t2

  T0 = call f_getint
  if T0 <= 10 goto l0
  return 1
l0:
  T2 = 0
  T3 = T2
l1:
  if T2 >= T0 goto l2
  t0 = call f_getint
  t1 = T2 * 4
  T1[t1] = t0
  t2 = T1[t1]
  T3 = T3 + t2
  T2 = T2 + 1
  goto l1
l2:
  param T3
  call f_putint
  return 0
end f_main
```

采用某种方式翻译得到的 Tigger 程序 (当然, 这种翻译方式并不唯一):

```tigger
v0 = 0
v1 = malloc 40

f_main [0] [0]
  call f_getint
  loadaddr v0 t0
  t0[0] = a0
  load v0 t0
  t1 = 10
  if t0 <= t1 goto l0
  a0 = 1
  return
l0:
  s0 = 0
  s1 = s0
l1:
  load v0 t0
  if s0 >= t0 goto l2
  call f_getint
  t0 = a0
  t1 = 4
  t2 = s0 * t1
  loadaddr v1 t3
  t3 = t3 + t2
  t3[0] = t0
  t4 = t3[0]
  s1 = s1 + t4
  s0 = s0 + 1
  goto l1
l2:
  a0 = s1
  call f_putint
  a0 = 0
  return
end f_main
```
