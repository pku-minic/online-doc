# Lv1.2. 词法/语法分析初见

上一节介绍了编译器的基本结构, 其中第一部分是词法/语法分析器. 既然我们要做一个编译器, 那么首先就必须完成这一部分.

一个好消息是, 目前已经有很多成熟的词法/语法分析器生成器, 你可以直接使用这些工具来帮助你根据正则表达式和 EBNF 生成词法/语法分析器.

当然, 你也可以使用手写递归下降分析器的方式实现词法/语法分析部分, 但本文档中不会对此方式进行讲解. 如果感兴趣, 你也许可以看看 [Kaleidoscope](https://llvm.org/docs/tutorial/MyFirstLanguageFrontend/LangImpl01.html).

## 一个例子

我们将使用词法/语法分析器生成器生成一个能解析下列程序的词法/语法分析器:

```c
int main() {
  // 忽略我的存在
  return 0;
}
```

这个程序的语法用 EBNF 表示为 (开始符号为 `CompUnit`):

```ebnf
CompUnit  ::= FuncDef;

FuncDef   ::= FuncType IDENT "(" ")" Block;
FuncType  ::= "int";

Block     ::= "{" Stmt "}";
Stmt      ::= "return" Number ";";
Number    ::= INT_CONST;
```

其他规范见[本章开头](/lv1-main/).

## 看懂 EBNF

EBNF, 即 [Extended Backus–Naur Form](https://en.wikipedia.org/wiki/Extended_Backus%E2%80%93Naur_form), 扩展巴科斯范式, 可以用来描述编程语言的语法. 基于 SysY 的 EBNF, 我们可以从开始符号出发, 推导出任何一个符合 SysY 语法定义的 SysY 程序. 那么, 如何从上述的 EBNF 推导出示例的 SysY 程序呢?

我们不难注意到, EBNF 由若干条形如 `A ::= B;` 的规则构成. 这种规则告诉我们, 当我们遇到一个 `A` 时, 我们可以把 `A` 代换成 `B`, 这就完成了一次推导. 这其中, `A` 被称为非终结符, 因为它可以推导出其他的符号.

我们可以先从开始符, 即 `CompUnit` 开始推导:

```ebnf
CompUnit
```

利用规则 `CompUnit ::= FuncDef;`, 我们可以把 `CompUnit` 替换成:

```ebnf
FuncDef
```

进一步应用规则 `FuncDef ::= FuncType IDENT "(" ")" Block;`, 我们得到:

```ebnf
FuncType IDENT "(" ")" Block
```

这里我们遇到了一些看起来和其他符号画风不太一样的符号, 比如 `IDENT`, `"("` 和 `")"`. 在我们使用的 EBNF 记法中, 这种使用大写蛇形命名法的符号, 或者被双引号引起的字符串, 被称为终结符, 它们不能进一步被其他符号所替换, 你也不会在 EBNF 中看到它们出现在规则的左侧. 我们的目标是, 利用 EBNF 中的规则, 把开始符号推导成一系列终结符.

需要注意的是, 在谈论词法/语法分析器的时候, 词法分析器返回的一个 token 通常就代表终结符. 比如这里的 `IDENT`, 对应到词法分析器中, 实际上是词法分析器返回的, 表示标识符 (identifier) 的 token. 示例程序里的 `main` 就是一个 `IDENT`.

持续利用 `FuncType`, `Block`, `Stmt`, `Number` 规则, 我们最终可以得出这样的一串终结符:

```ebnf
"int" IDENT "(" ")" "{" "return" INT_CONST ";" "}"
```

把 `IDENT` 对应为 `main`, `INT_CONST` 对应为 `0`, 这串终结符表示的就是示例程序. 你没在这串终结符中看到空格, 换行符和注释, 是因为我们之前提到, 词法分析器会自动忽略空白符和注释.

除了非终结符, 在我们使用的 EBNF 中还会出现一些别的记法:

* `A | B` 表示可以推导出 `A`, 或者 `B`.
* `[...]` 表示方括号内包含的项可被重复 0 次或 1 次.
* `{...}` 表示花括号内包含的项可被重复 0 次或多次.

例如:

```ebnf
Params ::= Param {"," Param};
Param ::= Type IDENT;
Type ::= "int" | "long";
```

可以表示类似 `int param`, `int x, long y, int z` 这样的参数列表.

## C/C++ 实现

在 C/C++ 中, 你可以使用 Flex 和 Bison 来分别生成词法分析器和语法分析器. 其中:

* Flex 用来描述 EBNF 中的终结符部分, 也就是描述 token 的形式和种类. 你可以使用正则表达式来描述 token.
* Bison 用来描述 EBNF 本身, 其依赖于 Flex 中的终结符描述. 它会生成一个 LALR parser.

关于如何入门 Flex/Bison, 你可以参考 [Calc++](https://www.gnu.org/software/bison/manual/html_node/A-Complete-C_002b_002b-Example.html), 或者自行 STFW/RTFM. 此处我们只介绍与开篇的示例程序相关的基本用法.

首先选择一个项目模板, 此处我们以 [`Makefile` 模板](https://github.com/pku-minic/sysy-make-template)为例. 在模板的 `src` 目录中新建两个文件: `sysy.l` 和 `sysy.y`, 前者将会描述词法规则并被 Flex 读取, 后者将会描述语法规则并被 Bison 读取. 由于 Flex 和 Bison 生成的 lexer 和 parser 会互相调用, 所以这两个文件里的内容也相互依赖.

`.l`/`.y` 文件有一些共同点, 比如它们的结构都是:

```bison
// 这里写一些选项, 可以控制 Flex/Bison 的某些行为

%{

// 这里写一些全局的代码
// 因为最后要生成 C/C++ 文件, 实现主要逻辑的部分都是用 C/C++ 写的
// 难免会用到头文件, 所以通常头文件和一些全局声明/定义写在这里

%}

// 这里写一些 Flex/Bison 相关的定义
// 对于 Flex, 这里可以定义某个符号对应的正则表达式
// 对于 Bison, 这里可以定义终结符/非终结符的类型

%%

// 这里写 Flex/Bison 的规则描述
// 对于 Flex, 这里写的是 lexer 扫描到某个 token 后做的操作
// 对于 Bison, 这里写的是 parser 遇到某种语法规则后做的操作

%%

// 这里写一些用户自定义的代码
// 比如你希望在生成的 C/C++ 文件里定义一个函数, 做一些辅助工作
// 你同时希望在之前的规则描述里调用你定义的函数
// 那么, 你可以把 C/C++ 的函数定义写在这里, 声明写在文件开头

```

其中, 如果某些部分没被使用, 你可以把它们留空.

我们提供的 Make/CMake 模板会采用如下方式处理你的 Flex/Bison 文件:

```shell
# C++ 模式
flex -o 文件名.lex.cpp 文件名.l
bison -d -o 文件名.tab.cpp 文件名.y   # 此时 bison 还会生成 `文件名.tab.hpp`
# C 模式
flex -o 文件名.lex.c 文件名.l
bison -d -o 文件名.tab.c 文件名.y     # 此时 bison 还会生成 `文件名.tab.h`
```

于是, 假设我们使用 C++ 开发, 我们可以在 `sysy.l` 里描述 SysY 里所需的所有 token:

```flex
%option noyywrap
%option nounput
%option noinput

%{

#include <cstdlib>
#include <string>

// 因为 Flex 会用到 Bison 中关于 token 的定义
// 所以需要 include Bison 生成的头文件
#include "sysy.tab.hpp"

using namespace std;

%}

/* 空白符和注释 */
WhiteSpace    [ \t\n\r]*
LineComment   "//".*$

/* 标识符 */
Identifier    [a-zA-Z_][a-zA-Z0-9_]*

/* 整数字面量 */
Decimal       [1-9][0-9]*
Octal         0[0-7]*
Hexadecimal   0[xX][0-9a-fA-F]+

%%

{WhiteSpace}    { /* 忽略, 不做任何操作 */ }
{LineComment}   { /* 忽略, 不做任何操作 */ }

"int"           { return INT; }
"return"        { return RETURN; }

{Identifier}    { yylval.str_val = new string(yytext); return IDENT; }

{Decimal}       { yylval.int_val = strtol(yytext, nullptr, 0); return INT_CONST; }
{Octal}         { yylval.int_val = strtol(yytext, nullptr, 0); return INT_CONST; }
{Hexadecimal}   { yylval.int_val = strtol(yytext, nullptr, 0); return INT_CONST; }

.               { return yytext[0]; }

%%
```

以上内容应该不难理解:

* 文件最开头我们设置了一些选项, 你可以 RTFM 这些选项的含义. 如果不设置这些选项, Flex 就会要求我们在代码里定义一些额外的东西, 但我们实际上用不到这些东西.
* 第二部分声明了必要的头文件, 然后是经典的 `using namespace std`.
* 第三部分定义了一些正则表达式的规则, 比如空白符, 行注释等等. 这些规则其实直接写在第四部分也可以, 但那样太乱了, 还是给它们起个名字比较好理解一些.
* 第四部分定义了 lexer 的行为:
  * 遇到空白符和注释就跳过.
  * 遇到 `int`, `return` 这种关键字就返回对应的 token.
  * 遇到标识符就把标识符存起来, 然后返回对应的 token. `yytext` 代表 lexer 当前匹配到的字符串的内容, 它的类型是 `char *`, 在此处对应读取到的一个标识符. `yylval` 用来向 parser 传递 lexer 读取到的内容, `str_val` 和之后的 `int_val` 是我们在 Bison 文件中定义的字段, 之后再解释.
  * 遇到整数字面量, 先把读取到的字符串转换成整数, 然后存起来, 并返回对应的 token.
  * 遇到单个字符, 就直接返回单个字符作为 token. `.` 这个正则表达式会匹配任意单个字符, 而 `yytext[0]` 实际上读取了目前匹配到的这个字符. 在 Flex/Bison 中, token 实际就是整数, 之前出现的 `INT`, `RETURN`, `IDENT` 等, 其实是 Bison 根据我们的定义生成的枚举 (`enum`). 所以此处相当于, 我们取了当前匹配到的字符, 然后把它转成了整数, 交给 Bison 生成的 parser 处理. 在 Bison 里, 我们可以直接通过写字符 (比如 `'('`), 来表示我们希望匹配 lexer 返回的一个字符转换得到的 token.

!> 此处我们只处理了形如 `// ...` 的行注释, 你需要自行处理形如 `/* ... */` 的块注释. 块注释也可以用正则表达式表达, 但会稍微复杂一些.

之后, 我们可以在 `sysy.y` 中描述语法定义.

你应该还记得之前我们说过, parser 在解析完成后会生成 AST. 但我们现在还没有教大家怎么设计和定义 AST, 所以我们可以让 parser 把它扫描到的东西再保存成文本形式——也就是用字符串作为 AST. 我们的编译器如果读取到一个 `int main()` 程序, 那它就会原样输出一个相同的程序. (听起来是不是太无聊了点?)

```bison
%code requires {
  #include <memory>
  #include <string>
}

%{

#include <iostream>
#include <memory>
#include <string>

// 声明 lexer 函数和错误处理函数
int yylex();
void yyerror(std::unique_ptr<std::string> &ast, const char *s);

using namespace std;

%}

// 定义 parser 函数和错误处理函数的附加参数
// 我们需要返回一个字符串作为 AST, 所以我们把附加参数定义成字符串的智能指针
// 解析完成后, 我们要手动修改这个参数, 把它设置成解析得到的字符串
%parse-param { std::unique_ptr<std::string> &ast }

// yylval 的定义, 我们把它定义成了一个联合体 (union)
// 因为 token 的值有的是字符串指针, 有的是整数
// 之前我们在 lexer 中用到的 str_val 和 int_val 就是在这里被定义的
// 至于为什么要用字符串指针而不直接用 string 或者 unique_ptr<string>?
// 请自行 STFW 在 union 里写一个带析构函数的类会出现什么情况
%union {
  std::string *str_val;
  int int_val;
}

// lexer 返回的所有 token 种类的声明
// 注意 IDENT 和 INT_CONST 会返回 token 的值, 分别对应 str_val 和 int_val
%token INT RETURN
%token <str_val> IDENT
%token <int_val> INT_CONST

// 非终结符的类型定义
%type <str_val> FuncDef FuncType Block Stmt Number

%%

// 开始符, CompUnit ::= FuncDef, 大括号后声明了解析完成后 parser 要做的事情
// 之前我们定义了 FuncDef 会返回一个 str_val, 也就是字符串指针
// 而 parser 一旦解析完 CompUnit, 就说明所有的 token 都被解析了, 即解析结束了
// 此时我们应该把 FuncDef 返回的结果收集起来, 作为 AST 传给调用 parser 的函数
// $1 指代规则里第一个符号的返回值, 也就是 FuncDef 的返回值
CompUnit
  : FuncDef {
    ast = unique_ptr<string>($1);
  }
  ;

// FuncDef ::= FuncType IDENT '(' ')' Block;
// 我们这里可以直接写 '(' 和 ')', 因为之前在 lexer 里已经处理了单个字符的情况
// 解析完成后, 把这些符号的结果收集起来, 然后拼成一个新的字符串, 作为结果返回
// $$ 表示非终结符的返回值, 我们可以通过给这个符号赋值的方法来返回结果
// 你可能会问, FuncType, IDENT 之类的结果已经是字符串指针了
// 为什么还要用 unique_ptr 接住它们, 然后再解引用, 把它们拼成另一个字符串指针呢
// 因为所有的字符串指针都是我们 new 出来的, new 出来的内存一定要 delete
// 否则会发生内存泄漏, 而 unique_ptr 这种智能指针可以自动帮我们 delete
// 虽然此处你看不出用 unique_ptr 和手动 delete 的区别, 但当我们定义了 AST 之后
// 这种写法会省下很多内存管理的负担
FuncDef
  : FuncType IDENT '(' ')' Block {
    auto type = unique_ptr<string>($1);
    auto ident = unique_ptr<string>($2);
    auto block = unique_ptr<string>($5);
    $$ = new string(*type + " " + *ident + "() " + *block);
  }
  ;

// 同上, 不再解释
FuncType
  : INT {
    $$ = new string("int");
  }
  ;

Block
  : '{' Stmt '}' {
    auto stmt = unique_ptr<string>($2);
    $$ = new string("{ " + *stmt + " }");
  }
  ;

Stmt
  : RETURN Number ';' {
    auto number = unique_ptr<string>($2);
    $$ = new string("return " + *number + ";");
  }
  ;

Number
  : INT_CONST {
    $$ = new string(to_string($1));
  }
  ;

%%

// 定义错误处理函数, 其中第二个参数是错误信息
// parser 如果发生错误 (例如输入的程序出现了语法错误), 就会调用这个函数
void yyerror(unique_ptr<string> &ast, const char *s) {
  cerr << "error: " << s << endl;
}
```

在文件里我们做了几件事:

* 设置一些必要的选项, 比如 `%code requires`.
* 引用头文件, 声明 lexer 函数和错误处理函数. 如果不声明这些函数的话, parser 会找不到 Flex 中定义的 lexer, 也没办法正常报错.
* 定义 parser 函数的参数. Bison 生成的 parser 函数返回类型一定是 `int`, 所以我们没办法通过返回值返回 AST, 所以只能通过参数来返回 AST 了. 当然你也可以通过全局变量来返回 AST, 但, 那样做很 dirty (如果你接触过函数式编程或了解软件工程技术的话).
* 定义了 `yylval`, token 和非终结符的类型.
* 定义了语法规则, 同时定义了 parser 解析完语法规则之后执行的操作.
* 定义了错误处理函数.

接下来我们解释一下为什么要在开头写 `%code requires`: 这个玩意做的事情和 `%{ ... %}` 是类似的, 前者会把大括号里的内容塞到 Bison 生成的头文件里, 后者会把 `...` 对应的内容塞到 Bison 生成的源文件里.

生成的头文件会包括什么内容呢? 主要是 parser 函数的定义, 和 `yylval` 的定义. 前者是给用户用的, 比如我们想在编译器里调用 Bison 生成的 parser 帮我们解析 SysY 文件, 就需要引用这个头文件. 后者前文已经介绍过, 用来在 lexer 和 parser 之间传递信息, 我们已经在 Flex 文件中引用了这个头文件.

那么, 你一定注意到, 在 Bison 文件中, 我们指定了 parser 函数的参数类型是 `unique_ptr<string> &`, `yylval.str_val` 的类型是 `string *`, 他们都依赖于标准库里对应类的定义. 如果不在头文件里引用对应的头文件, 那么我们的编译器在引用 parser 函数的时候就可能会报错, Flex 生成的 lexer 在编译的时候也一定会报错.

以上就是 Flex 和 Bison 的基本用法了, 我们只需要写不太复杂的内容 ~(真的吗?)~, 就可以得到一个 lexer 和一个 parser. 最后的最后, 我们需要新建一个 `.cpp` 文件, 比如叫做 `main.cpp`, 来写一下程序的主函数:

```cpp
#include <cassert>
#include <cstdio>
#include <iostream>
#include <memory>
#include <string>

using namespace std;

// 声明 lexer 的输入, 以及 parser 函数
// 为什么不引用 sysy.tab.hpp 呢? 因为首先里面没有 yyin 的定义
// 其次, 因为这个文件不是我们自己写的, 而是被 Bison 生成出来的
// 你的代码编辑器/IDE 很可能找不到这个文件, 然后会给你报错 (虽然编译不会出错)
// 看起来会很烦人, 于是干脆采用这种看起来 dirty 但实际很有效的手段
extern FILE *yyin;
extern int yyparse(unique_ptr<string> &ast);

int main(int argc, const char *argv[]) {
  // 解析命令行参数. 测试脚本/评测平台要求你的编译器能接收如下参数:
  // compiler 模式 输入文件 -o 输出文件
  assert(argc == 5);
  auto mode = argv[1];
  auto input = argv[2];
  auto output = argv[4];

  // 打开输入文件, 并且指定 lexer 在解析的时候读取这个文件
  yyin = fopen(input, "r");
  assert(yyin);

  // 调用 parser 函数, parser 函数会进一步调用 lexer 解析输入文件的
  unique_ptr<string> ast;
  auto ret = yyparse(ast);
  assert(!ret);

  // 输出解析得到的 AST, 其实就是个字符串
  cout << *ast << endl;
  return 0;
}
```

完成上述内容后, 项目的目录/文件结构是这样的:

* 项目目录.
  * `src` 目录.
    * `sysy.l` 文件, 用来描述 lexer.
    * `sysy.y` 文件, 用来描述 parser.
    * `main.cpp` 文件, 定义 `main` 函数, 调用 lexer 和 parser, 并输出结果.
  * `Makefile` 文件.
  * 其他文件.

在 Docker 的实验环境中, 我们可以在项目的目录里执行:

```
make
build/compiler -koopa hello.c -o hello.koopa
```

当然, 你需要把本节开头的示例程序先放到 `hello.c` 中. 然后你会看到输出:

```
int main() { return 0; }
```

成功了! 你可以尝试修改 `main` 函数的返回值, 或者把 `main` 改成其他什么内容, 观察输出的变化.

!> **请不要在 `src` 目录中放置其他文件!** Make/CMake 模板会处理 `src` 目录中所有的 C/C++/Flex/Bison 源文件, 并试图将它们编译和链接成一个最终的可执行文件.
<br><br>
如果你在 `src` 目录中放置了其他的相关文件, 比如你把你要喂给你的编译器的, 用来测试的 SysY 源程序保存在了 `src/hello.c` 中, 此时链接就会出错——因为 `hello.c` 和 `main.cpp` 中都会出现 `main` 函数, 链接器会报告出现了多个同名符号.
<br><br>
我们建议你在项目目录中新建一个用来存放临时文件的目录, 比如一个名字叫 `debug` 的目录. 你可以把所有和你的编译器的实现无关的文件都放在这个目录中. 记得在 `.gitignore` 文件中添加这个目录, 以防你不小心把这些临时文件提交到 Git 中, 详见[如何使用 Git](/preface/prerequisites?id=如何使用-git).

!> 如果你遇到了其他更奇怪的问题, 请仔细检查你是否按照文档中描述的方式使用了实验环境的 Docker 镜像. 详见[免责声明](/lv0-env-config/docker?id=免责声明).

## Rust 实现

在 Rust 中, 你可以使用 [lalrpop](https://github.com/lalrpop/lalrpop) 来帮你生成词法/语法分析器. 和前文提到的 Flex/Bison 类似, lalrpop 也是一个 LR/LALR 分析器生成器 (从名字就能看出来), 不过它同时接管了词法部分和语法部分, 用起来更简单.

关于如何入门 lalrpop, 你可以参考 lalrpop 的[文档](https://lalrpop.github.io/lalrpop/), 里面有详细的教程可供学习.

如需在你的 Rust 项目中使用 lalrpop, 你首先需要在 `Cargo.toml` 中添加对应依赖:

```
[build-dependencies]
lalrpop = "0.19.7"

[dependencies]
lalrpop-util = { version = "0.19.7", features = ["lexer"] }
```

?> 写这篇文档时 lalrpop 的最新版本是 `0.19.7`, 你也许需要检查一下目前的最新版本.

然后在项目根目录 (即 `Cargo.toml` 所在目录) 新建 `build.rs`:

```rust
fn main() {
  lalrpop::process_root().unwrap();
}
```

之后就完成了. Cargo 在编译你的项目时, 会自动根据 `build.rs` 的配置, 扫描项目中的 `.lalrpop` 文件, 然后使用 lalrpop 生成 lexer 和 parser.

lalrpop 的具体用法和 Flex/Bison 大同小异, 建议选用 Rust 开发编译器的同学先简单看一下前文对 Flex/Bison 的描述. 之后, 我们可以在 `src` 目录中新建 `sysy.lalrpop`, 并写入如下内容:

```
// lalrpop 里的约定
grammar;

// 约束 lexer 的行为
match {
  // 跳过空白符和注释
  r"\s*" => {},
  r"//[^\n\r]*[\n\r]*" => {},
  // 剩下的情况采用默认方式处理
  _
}

// 定义 CompUnit, 其返回值类型为 String
// parser 在解析完成后的行为是返回 FuncDef 的值
pub CompUnit: String = <func_def: FuncDef> => func_def;

// 同上, 不解释
FuncDef: String = {
  <func_type: FuncType> <id: Ident> "(" ")" <block: Block> => {
    format!("{} {}() {}", func_type, id, block)
  }
}

FuncType: String = "int" => "int".to_string();

Block: String = "{" <stmt: Stmt> "}" => format!("{{ {} }}", stmt);

Stmt: String = "return" <num: Number> ";" => format!("return {};", num);

Number: String = <num: IntConst> => num.to_string();

// 如果匹配到标识符, 就返回这个字符串
// 一对尖括号在此处指代的是正则表达式匹配到的字符串 (&str)
// 关于尖括号到底代表什么, 请 RTFM
Ident: String = r"[_a-zA-Z][_a-zA-Z0-9]*" => <>.to_string();

// 对整数字面量的处理方式: 把匹配到的字符串按对应进制转换成数字
IntConst: i32 = {
  r"[1-9][0-9]*" => i32::from_str_radix(<>, 10).unwrap(),
  r"0[0-7]*" => i32::from_str_radix(<>, 8).unwrap(),
  r"0[xX][0-9a-fA-F]+" => i32::from_str_radix(&<>[2..], 16).unwrap(),
}
```

!> 此处我们只处理了形如 `// ...` 的行注释, 你需要自行处理形如 `/* ... */` 的块注释. 块注释也可以用正则表达式表达, 但会稍微复杂一些.

在 `main.rs` 里我们可以这么写:

```rust
use lalrpop_util::lalrpop_mod;
use std::env::args;
use std::fs::read_to_string;
use std::io::Result;

// 引用 lalrpop 生成的解析器
// 因为我们刚刚创建了 sysy.lalrpop, 所以模块名是 sysy
lalrpop_mod!(sysy);

fn main() -> Result<()> {
  // 解析命令行参数
  let mut args = args();
  args.next();
  let mode = args.next().unwrap();
  let input = args.next().unwrap();
  args.next();
  let output = args.next().unwrap();

  // 读取输入文件
  let input = read_to_string(input)?;

  // 调用 lalrpop 生成的 parser 解析输入文件
  let ast = sysy::CompUnitParser::new().parse(&input).unwrap();

  // 输出解析得到的 AST
  println!("{}", ast);
  Ok(())
}
```

完成上述内容后, 项目的目录/文件结构是这样的:

* 项目目录.
  * `src` 目录.
    * `sysy.lalrpop` 文件, 描述了 lexer 和 parser.
    * `main.rs` 文件, 定义 `main` 函数, 调用 lexer 和 parser, 并输出结果.
  * `build.rs` 文件, 描述 lalrpop 生成 lexer 和 parser 的操作.
  * `Cargo.toml` 文件.
  * 其他文件.

如果需要运行这个简单的编译器, 你只需要在项目目录执行:

```
cargo run -- -koopa hello.c -o hello.koopa
```

然后你可以在命令行中看到输出:

```
int main() { return 0; }
```

很简单吧!
