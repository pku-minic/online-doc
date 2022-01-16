# Koopa IR 规范

## 符号名称

### 说明

符号名称可用来表示变量, 函数或标号. 符号分为以下两种:

* **具名符号**: `@name`, `name` 可以是任意可被 `[_A-Za-z][_A-Za-z0-9]*` 匹配的字符串, 也就是类 C 语言的标识符.
* **临时符号**: `%name`, `name` 可以是任意可被 `[0-9]|[1-9][0-9]+|[_A-Za-z][_A-Za-z0-9]*` 匹配的字符串, 也就是类 C 语言的标识符或者任意数字.

这两种符号没有任何区别, 只是我们通常用前一种表示原语言中的变量或函数, 而用后一种类型来表示临时值或标号.

?> 让临时符号也可以包括字母和下划线的目的是, 方便大家调试. 这样你就不需要对着一堆数字来判断到底哪一个标号是 `while` 循环的结束了.

## 类型

### 语法

```ebnf
Type ::= "i32" | ArrayType | PointerType | FunType;
ArrayType ::= "[" Type "," INT "]";
PointerType ::= "*" Type;
FunType ::= "(" [Type {"," Type}] ")" [":" Type];
```

### 说明

Koopa 的函数/表达式/值可具备以下类型:

* **32 位有符号整数**: 默认类型, 可被表示为 `i32`.
* **数组**: 可被表示为 `[BaseType, Length]` 的形式, 如 `[i32, 2]`. `BaseType` 用来描述数组元素的类型, `Length` 用来表示数组长度, 如:
  * `[i32, 2]`: 长度为 2 的数组, 数组元素类型为 32 位有符号整数.
  * `[[i32, 3], 2]`: 长度为 2 的数组, 数组元素类型为一个长度为 3 的 32 位有符号数组, 相当于 C/C++ 中的 `int[2][3]`.
* **指针**: 可被表示为 `*` + `BaseType` 的形式, 如 `*i32`, `**i32`.
* **函数**: 可被表示为 `(BaseType, ...): BaseType` 或 `(BaseType, ...)` 的形式, 如 `(i32, i32): i32`, `()`, 后者表示的函数不具备返回值.

Koopa 是一种强类型 IR, 在书写时只需要为内存分配/函数参数/函数返回值/基本块参数进行类型标注, 其余值的类型将由解析器自动推断. 此外, 在解析 Koopa 时解析器应当检查 IR 的类型, 如发现类型问题, 应报错并退出.

## 值

### 语法

```ebnf
Value ::= SYMBOL | INT | "undef";
Initializer ::= INT | "undef" | Aggregate | "zeroinit";
Aggregate ::= "{" Initializer {"," Initializer} "}";
```

### 说明

* **32 位有符号整数**: 形如 `1`, `233` 等.
* **符号引用**: 形如 `@var`, `%0` 等.
* **数组初始化列表**: 形如 `{1, 2, 3}`, `{{1, 2}, {3, 4}}` 等, 只允许用来初始化数组类型. 初始化列表中不能出现符号引用.
* **零初始化器**: `zeroinit`, 可以初始化任何类型.
* **未定义值**: `undef`, 标记某处的值未定义. 当变量未初始化时, 试图将 IR 提升至 SSA 形式之后可能会出现 `undef`.

## 符号定义

### 语法

```ebnf
SymbolDef ::= SYMBOL "=" (MemoryDeclaration | Load | GetPointer | BinaryExpr | FunCall);
GlobalSymbolDef ::= "global" SYMBOL "=" GlobalMemoryDeclaration;
```

### 说明

`SymbolDef` 只能出现在函数内部, `GlobalSymbolDef` 只能出现在函数外部.

全局的符号不能和其他全局符号同名, 局部的符号 (位于函数内部的符号) 不能和其他全局符号以及局部符号同名. 上述规则对具名符号和临时符号都适用.

?> 简单起见, IR 生成器可以允许用户定义重名的符号, 此时生成器需要自动对重名的符号进行换名, 例如将符号 `%name` 改为 `%name_1`. 这样, 用户就可以将所有的 `while` 出口都标记成 `%while_exit` 而不必担心不同出口之间的名字会冲突了.
<br><br>
当然上述自动换名的约定只在用户使用 IR 生成器生成 IR 时有效, 若用户决定直接生成文本形式的 IR, 则需要自己确保所有符号的名字互不冲突.

## 内存声明

### 语法

```ebnf
MemoryDeclaration ::= "alloc" Type;
GlobalMemoryDeclaration ::= "alloc" Type "," Initializer;
```

### 类型推断规则

使用内存声明时必须标注类型, 该类型指的是申请得到的内存可存储的元素的类型.

需要注意的是, 申请得到的内存的类型并不是标注的类型, 而是标注类型的指针, 例如:

```koopa
@a = alloc i32
```

`@a` 对应的内存可存储一个 `i32` 类型的数据, 但 `@a` 本身指的是那块内存, 所以 `@a` 的类型是 `*i32`.

这点和 C/C++ 的逻辑类似, 对应到 C 语言表示的伪代码则为:

```clike
int *a = (int *)malloc(sizeof(int));
```

### 示例

```koopa
@i = alloc i32                                // int i
@arr = alloc [[i32, 3], 2]                    // int arr[2][3]
global @arr2 = alloc [[i32, 5], 2], zeroinit  // int arr2[2][5] = {}
global @arr3 = alloc [i32, 3], {1, 2, 3}      // int arr3[3] = {1, 2, 3}
```

## 内存访问

### 语法

```ebnf
Load ::= "load" SYMBOL;
Store ::= "store" (Value | Initializer) "," SYMBOL;
```

### 类型推断规则

对于一个 `load`, 其 `SYMBOL` 的类型必须是一个指针, 设为 `*t`, 则 `load` 返回的类型为 `t`.

对于一个 `store`, 其 `SYMBOL` 的类型必须是一个指针, 设为 `*t`, 则 `(Value | Initializer)` 的类型必须为 `t`.

### 示例

```koopa
// x = i
%0 = load @i
store %0, @x
```

## 指针运算

### 语法

```ebnf
GetPointer ::= "getptr" SYMBOL "," Value;
GetElementPointer ::= "getelemptr" SYMBOL "," Value;
```

### 说明

`getptr` 用来进行指针运算, 其中 `SYMBOL` 为一个指针, `Value` 为一个偏移量. 其实际执行的操作和 C/C++ 中的指针加偏移量操作的语义一致, 即, 如果指针类型为 `*t`, 则 `getptr` 会返回该指针的内存地址加上 `sizeof(t) * offset` 后的指针.

`getelemptr` 同样用来进行指针运算, 但它进行的是对数组的索引操作. `SYMBOL` 为一个**数组的指针** (并非一个数组), 设为 `*[t, len]`, 则 `getelemptr` 会返回该指针的内存地址加上 `sizeof(t) * offset` 后的指针.

### 类型推断规则

对于一个 `getptr`, 其 `SYMBOL` 的类型必须是一个指针, 设为 `*t`, 则 `getptr` 返回的类型为 `*t`.

对于一个 `getelemptr`, 其 `SYMBOL` 的类型必须是一个数组的指针, 设为 `*[t, len]`, 则 `getelemptr` 返回的类型为 `*t`.

### 示例

普通的数组:

```koopa
@a = alloc [[i32, 9], 10]   // int a[10][9];
%0 = getelemptr @a, 2       // a[2][3] = 5
%1 = getelemptr %0, 3
store 5, %1
```

作为参数, 省略第一维长度的数组:

```koopa
fun @f(@a: *[i32, 9]) ... {   // ... (int a[][9])
  ...

  %0 = getptr @a, 2           // a[2][3] = 5;
  %1 = getelemptr %0, 3
  store 5, %1

  ...
}
```

## 二元运算

### 语法

```ebnf
BinaryExpr ::= BINARY_OP Value "," Value;
```

### 说明

支持的二元操作: `ne`, `eq`, `gt`, `lt`, `ge`, `le`, `add`, `sub`, `mul`, `div`, `mod`, `and`, `or`, `xor`, `shl`, `shr`, `sar`.

不支持一元操作的原因是, 目前已知有意义的一元操作均可用二元操作表示:

* **变补 (取负数)**: 0 减去操作数.
* **按位取反**: 操作数异或全 1 (即 `-1`).
* **逻辑取反**: 操作数和 0 比较相等.

### 类型推断规则

二元运算操作只接受 `i32` 类型的操作数, 同时返回一个 `i32` 类型的结果.

### 示例

```koopa
%2 = add %0, %1
%3 = mul %0, %2
%4 = sub 0, %3
```

## 分支和跳转

### 语法

```ebnf
Branch ::= "br" Value "," SYMBOL "," SYMBOL;
Jump ::= "jump" SYMBOL;
```

### 说明

`Branch` 的第一个参数是分支条件. 条件非 0 时, 将跳转到第二个参数代表的标号处, 否则跳转到第三个参数代表的标号处.

`Jump` 操作会直接将控制流转移到 `SYMBOL` 所代表的标号处.

### 类型推断规则

`br` 操作中的 `Value` (即条件) 必须为 `i32` 类型.

### 示例

```koopa
%while_entry:
  %cond = lt %0, %1                   // while (%0 < %1)
  br %cond, %while_body, %while_end   // {

%while_body:
  ...                                 //   ...
  jump %while_entry

%while_end:                           // }
```

## 函数调用和返回

### 语法

```ebnf
FunCall ::= "call" SYMBOL "(" [Value {"," Value}] ")";
Return ::= "ret" [Value];
```

### 说明

`call` 中 `SYMBOL` 为函数名称, 括号内的内容为函数调用时传递的参数.

`ret` 中 `Value` 为返回值. 当然, 如果一个函数没有返回值, `ret` 也可以不带 `Value`.

### 类型推断规则

`call` 中的 `SYMBOL` 具备函数类型, 之后括号中 `Value` 的数量和类型应当和函数参数的数量和类型一致.

`ret` 中 `Value` 的类型应当和当前函数的返回类型一致.

### 示例

```koopa
%0 = call @getint ()
call @putint (%0)
ret %0
```

## 函数和参数

### 语法

```ebnf
FunDef ::= "fun" SYMBOL "(" [FunParams] ")" [":" Type] "{" FunBody "}";
FunParams ::= SYMBOL ":" Type {"," SYMBOL ":" Type};
FunBody ::= {Block};
Block ::= SYMBOL ":" {Statement} EndStatement;
Statement ::= SymbolDef | Store | FunCall;
EndStatement ::= Branch | Jump | Return;
```

### 说明

`FunDef` 用来定义一个函数, 其中的 `FunParams` 用来声明参数的名称和类型.

`Block` 表示基本块. 所有的基本块必须具备一个标号, 并且由 `Branch`, `Jump` 或者 `Return` 结尾.

函数的函数体 (`FunBody`) 由一个或多个基本块组成, 其中第一个出现的基本块为入口基本块 (entry basic block), 入口基本块不能具备任何前驱 (predecessor).

### 示例

```koopa
global @arr = alloc [i32, 10], zeroinit   // int arr[10] = {};

fun @func(@a: i32, @b: i32): i32 {        // int func(int a, int b) {
%entry:
  %ret = alloc i32
  jump %2

%2:
  %0 = getelemptr @arr, @a                //   return arr[a] + b;
  %1 = load %0
  %2 = add %1, @b
  store %2, %ret
  jump %end

%end:
  %3 = load %ret
  ret %3
}                                         // }
```

## 函数声明

### 语法

```ebnf
FunDecl ::= "decl" SYMBOL "(" [FunDeclParams] ")" [":" Type];
FunDeclParams ::= Type {"," Type};
```

### 说明

`FunDecl` 可以声明一个函数. 此处的 “声明” 与 C/C++ 里的 `extern` 声明含义类似, 指这个函数的定义并不在当前文件内, 而在另外的文件中. 如果当前文件表示的程序需要调用另一个文件中定义的函数, 则必须在 Koopa IR 中显式的写明这个函数的声明.

SysY 的库函数, 如 `getint`/`putint`, 就是一类典型的需要被声明的函数.

### 示例

```koopa
decl @getint(): i32
decl @putint(i32)

fun @main(): i32 {
%entry:
  %0 = call @getint()
  call @putint(%0)
  ret 0
}
```

## Koopa IR 的 SSA 扩展

### 语法

该形式需要扩展之前定义的 `Branch`, `Jump` 以及 `Block` 语法:

```ebnf
Branch ::= "br" Value "," SYMBOL [BlockArgList] "," SYMBOL [BlockArgList];
Jump ::= "jump" SYMBOL [BlockArgList];
BlockArgList ::= "(" Value {"," Value} ")";

Block ::= SYMBOL [BlockParamList] ":" {Statement} EndStatement;
BlockParamList ::= "(" SYMBOL ":" Type {"," SYMBOL ":" Type} ")";
```

### 说明

基础形式的 Koopa 已经足够作为一个编译器的 IR 使用了, 但为了让 Koopa 兼容 SSA 形式, 我们推出了 SSA 扩展.

Koopa 支持 SSA 形式, 但这并非是必选内容. 为了实现更多更强大的优化, 你可以选择将 Koopa 转换到 SSA 形式. 但我觉得这部分内容不应该放在本科编译原理的课程实践中, 也许可以针对本科生再开一门和编译优化相关的课程.

我们并没有选择让 SSA 的 Koopa 采用 Phi 函数的形式, 虽然我们之前确实这么做了, 但权衡之下, 我们决定采用另一种等价的形式: 基本块参数 (basic block arguments). 相比传统的 Phi 函数, 这种形式在实现上要简单得多, 且在不削弱表达能力的情况下, 可以更好的分离数据流和控制流. 关于 SSA 形式设计的讨论, 请参考 MaxXing 的[这篇博文](http://blog.maxxsoft.net/index.php/archives/143/).

在该形式下, 原先的 Phi 语义使用基本块参数进行表示. 在进入带参数基本块时, 前驱的基本块的最后一条转移指令中必须传递基本块的实际参数. 基本块中的指令可以通过使用形式参数的方式来使用这些传入的值.

### 类型推断规则

传入基本块的实际参数的数量和类型, 应当和基本块定义时指定的形式参数的数量和类型一致.

### 示例

```koopa
// return a > 10 ? a + 5 : a - 7
%if_begin:
  %cond = gt %a_0, 10
  br %cond, %if_then, %if_else

%if_then:
  %a_1 = add %a_0, 5
  jump %if_end(%a_1)

%if_else:
  %a_2 = sub %a_0, 7
  jump %if_end(%a_2)

%if_end(%a_3: i32):
  ret %a_3
```

## 注释和注解

### 说明

Koopa 支持类似 C++ 语言的单行和多行注释.

用户可以使用 `//!` 或 `/*! */` 对 IR 进行注解, 以在 IR 中插入更多的信息. 后者为行内注解, 对符号的行内注解应当写在某个符号之后.

注解的形式如下:

```ebnf
Annotation ::= AnnoPair {";" AnnoPair} [";"];
AnnoPair ::= AnnoName [":" AnnoValue];
```

注解由若干个 `AnnoPair` 构成, 中间以分号分隔, 也可以以分号结尾. `AnnoPair` 包含注解的名称和注解的值, 有些注解只有名称而没有值.

`AnnoName` 实际上是一个字符串, 其中不允许出现任何空白符或其他控制字符. `AnnoName` 的命名格式并无特殊规定, 你愿意的话甚至可以用中文或其他 unicode 字符来表示, 但建议使用 [kebab-case](https://en.wikipedia.org/wiki/Letter_case#Special_case_styles).

`AnnoValue` 实际上也是一个字符串. 默认情况下, 字符串从 `AnnoName` 后的冒号处开始, 到分号处或注解结束处结束, 首尾空白符会被忽略.

考虑到用户可能会在 `AnnoValue` 中写各种稀奇古怪的东西, `AnnoValue` 还支持双引号形式的字符串, 形式同 C/C++ 的字符串. 该形式下, `AnnoValue` 可包含如下转义字符:

* **换行**: `\n`
* **回车**: `\r`
* **tab**: `\t`
* **反斜杠**: `\\`
* **双引号**: `\"`
* **任意字节**: `\x00` - `\xff`

支持的标准注解:

| 名称    | 值                        | 含义                              |
| --      | --                        | --                                |
| pred    | 基本块标号列表, 逗号分隔  | 标记基本块的前驱                  |
| succ    | 基本块标号, 逗号分隔      | 标记基本块的后继                  |
| type    | 类型声明                  | 标记 IR 表达式的类型              |
| src     | 文件名                    | 标记 IR 文件对应的源代码文件      |
| line    | 行号                      | 标记 IR 对应的源代码文件的行数    |
| version | 版本号                    | 标记 IR 文件对应的 IR 标准的版本  |

此外, 用户可自定义非标准注解, Koopa 的标准解析器将不负责解析这些注解.

### 设计意图

为了保持 IR 的简洁性, 我们势必削弱 IR 的表达能力.

但有没有一种方式, 让只需要解析 IR 内容的解析器要考虑的事情不那么多, 同时让需要分析 IR 的静态分析器能在 IR 的基础上表达更多信息呢? 以注释的形式添加注解信息是一种不错的思路.

早在 Eeyore 和 Tigger 的时代, 就有很多同学使用注释在 IR 的代码中插入了很多元数据 (metadata), 方便调试. 例如标注翻译后的代码和源代码的对应关系, 或者标记寄存器分配的结果. 但这些行为并没有被标准化, 导致这些元数据的格式完全不同, 信息无法共享, 反而都被浪费了.

注解存在的意义就是为元数据提供一种标准化的定义, 在维持 IR 简洁性的同时提升表达能力.

### 示例

```koopa
//! version: 0.0.1
//! src: example.c

//! type: *[i32, 10]; line: 1
global @arr = alloc [i32, 10], zeroinit

//! type: (i32, i32): i32; line: 2
fun @func (@a: i32, @b: i32): i32 {
%entry:
  %ret /*! type: *i32 */ = alloc i32
  jump %2

//! pred: %entry
%2:
  //! line: 3
  %0 /*! type: *i32 */ = getelemptr @arr, @a
  %1 /*! type: i32 */ = load %0
  %2 /*! type: i32 */ = add %1, @b
  store %2, %ret
  jump %end

//! pred: %2
%end:
  //! line: 4
  %3 /*! type: i32 */ = load %ret
  ret %3
}

/*!
  user-defined-annotation: "  complicated strings\n\nhello?";
*/
```
