# 4.1. Eeyore

Eeyore (`/'ı:juə(r)/`) 是一种三地址码, 用作 SysY 语法分析后的输出格式. Eeyore 的设计遵循简洁的原则, 其设计目标是使代码易读易调试.

## 语法描述

Eeyore 要求**每条语句单独占一行**.

### 变量

* Eeyore 中的变量有三种: 原生变量, 临时变量, 函数参数. 这三种变量分别以 `T`, `t`, `p` 开头, 后接一个整数编号, 编号从 0 开始, 每个变量单独编号. 如 `p0`, `p1`, `t0`, `T0`.
* Eeyore 的变量声明形如 `var t0` 和 `var 8 T0`, 前者声明了一个 `int` 型临时变量, 后者声明了有 2 个元素的原生 `int` 数组.
* 函数参数 (即以 `p` 开头的变量) 不需要声明.
* 函数内声明的变量 (含函数参数变量) 作用域为变量声明语句到函数结束语句, 函数外声明的变量作用域为变量声明语句到程序最后.
* 变量在其作用域范围内不允许重名.
* 函数内所有的变量声明语句**必须出现在函数开头**.

所谓原生变量, 是指 SysY 中使用的变量转到 Eeyore 中对应的变量. 相应地, 临时变量是指在 SysY 中没有显式对应的变量.

其实这上述两种变量在语义上没必要做如此区分, Eeyore 区分二者是为了方便用户调试. 用一个例子来说明, 把左边的 SysY 语句翻译到 Eeyore:

<!-- TODO: 下面这段太暴力了, 不利于人类阅读, 是否有其他合理的书写方式? -->
| SysY  | Eeyore  |
| ---   | ---     |
| <pre data-lang="clike"><code class="lang-clike">int a;<br>int b;<br>int c;<br>a = b + 2 * c;</code></pre> | <pre data-lang="eeyore"><code class="lang-eeyore">var T0<br>var T1<br>var T2<br>var t0<br>var t1<br>t0 = 2 * T2<br>t1 = T1 + t0<br>T0 = t1</code></pre> |

上面 `T0`, `T1`, `T2` 是原生变量, 分别对应 SysY 中的 `a`, `b`, `c`. `t0`, `t1` 是临时变量, 分别对应中间运算结果 `2 * c`, `b + 2 * c`.

### 表达式

Eeyore 表达式有以下特点:

* 允许直接把整数作为操作数 (如 `t0 = 2 * T2`).
* Eeyore 表达式支持的单目运算符有 `!`, `-`.
* 支持的双目运算符有 `!=`, `==`, `>`, `<`, `>=`, `<=`, `&&`, `||`, `+`, `-`, `*`, `/`, `%`, 其中前 6 个是逻辑运算符.
* 数组操作语句形如 `T0[t0] = t1` 和 `t0 = T0[t1]`.
* 注意: 由于 SysY 的表达式只支持 32 位 `int` 和 `int` 数组类型, 数组操作语句中括号内的数应当是 4 的整数倍.

### 函数

* Eeyore 中的函数以 `f_` 开头, 后接函数名, 如 `f_main`, `f_getint`.
* 函数定义语句形如 `f_putint [1]`, 中括号内的整数表示该函数的参数个数, 函数结束处应有函数结束语句, 形如 `end f_xxx`.
* 函数外的变量声明语句被视为全局变量声明, 函数内的声明被视为局部变量声明.
* 函数调用语句形如: `t0 = call f_xxx` (有返回值) 或 `call f_xxx` (没有返回值).
* 传参数指令形如: `param t1`, 所有传参都是传值, 多个参数需依照从左往右的先后次序传入.
* 作为参数的变量, 在 `param Variable` 语句之后, 到函数调用前, **不应被修改**. 这样限制的目的是避免寄存器分配时繁琐的分类讨论.
* 函数返回语句形如 `return t0` (有返回值) 或 `return` (无返回值). 函数退出前**必须执行返回语句**, 即使这个函数是一个返回类型为 `void` 的函数.

### 标号和跳转

* Eeyore 中的标号以小写字母 `l` 开头, 后接整数编号, 编号从 0 开始, 如 `l0`, `l1`. 标号用来指明跳转语句的跳转目标, 标号声明语句形如 `l0:`.
* 跳转语句分两种: 无条件跳转, 如 `goto l1`; 和条件跳转, 如 `if t0 < 1 goto l0`.

### 缩进

Eeyore 在语法和语义上没有缩进要求, 同时允许使用缩进. 为了之后代码调试的便利, 我们建议你在生成 Eeyore 时正确使用缩进.

### 注释

Eeyore 允许单行注释, 与 C/C++ 语言的行注释类似, 使用 `//` 标记.

### 运行时库函数支持

Eeyore 虚拟机 (MiniVM) 提供对各类 SysY 运行时库函数的支持.

关于相关的运行时库函数, 请参考 [3.3 节](sysy/runtime.md).

## Eeyore 语法的 EBNF 定义

开始符号为 `Program`.

```ebnf
Program         ::= {Declaration | Initialization | FunctionDef};

Declaration     ::= "var" [NUM] SYMBOL;
Initialization  ::= SYMBOL "=" NUM
                  | SYMBOL "[" NUM "]" "=" NUM;
FunctionDef     ::= FunctionHeader Statements FunctionEnd;
FunctionHeader  ::= FUNCTION "[" NUM "]";
Statements      ::= {Statement};
FunctionEnd     ::= "end" FUNCTION;

Statement       ::= Expression | Declaration;
Expression      ::= SYMBOL "=" RightValue BinOp RightValue
                  | SYMBOL "=" OP RightValue
                  | SYMBOL "=" RightValue
                  | SYMBOL "[" RightValue "]" "=" RightValue
                  | SYMBOL "=" SYMBOL "[" RightValue "]"
                  | "if" RightValue LOGICOP RightValue "goto" LABEL
                  | "goto" LABEL
                  | LABEL ":"
                  | "param" RightValue
                  | "call" FUNCTION
                  | SYMBOL "=" "call" FUNCTION
                  | "return" RightValue
                  | "return";
RightValue      ::= SYMBOL | NUM;
BinOp           ::= OP | LOGICOP;
```

## 示例

SysY 语言源程序:

```clike
int n, a[10];

int main() {
  n = getint();
  if (n > 10) return 1;
  int i = 0, s = i;
  while (i < n) {
    a[i] = getint();
    s = s + a[i];
    i = i + 1;
  }
  putint(s);
  return 0;
}
```

采用某种方式翻译得到的 Eeyore 程序 (当然, 这种翻译方式并不唯一):

```eeyore
var T0                    // int n;
var 40 T1                 // int a[10];

f_main [0]                // int main() {
  var T2                  //   int i;
  var T3                  //   int s;
  var t0
  var t1
  var t2

  T0 = call f_getint      //   n = getint();
  if T0 <= 10 goto l0     //   if (n > 10) return 1;
  return 1
l0:
  T2 = 0                  //   i = 0;
  T3 = T2                 //   s = i;
l1:
  if T2 >= T0 goto l2     //   while (i < n) {
  t0 = call f_getint      //     a[i] = getint();
  t1 = T2 * 4
  T1[t1] = t0
  t2 = T1[t1]             //     s = s + a[i];
  T3 = T3 + t2
  T2 = T2 + 1             //     i = i + 1;
  goto l1                 //   }
l2:
  param T3                //   putint(s);
  call f_putint
  return 0                //   return 0;
end f_main                // }
```
