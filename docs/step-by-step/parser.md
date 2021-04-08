# 2.3. 语法分析器

在词法分析完成之后, 编译器就会进行语法分析.

语法分析负责处理词法分析器产生的 token 流, 根据其语法含义, 将其转换为一种名为抽象语法树 (Abstract Syntax Tree, AST) 的数据结构. 毕竟在计算机中, 树是一种适用范围较广, 表达能力较强, 且构建和遍历起来都比较方便的数据结构.

其实编译器里的实际处理过程和刚刚我们所描述的, “将 token 流转换为 AST” 的过程, 略有不同. Token 流并不是 “主动” 从 lexer 流向 parser 的, 因为 token 要在 parser 执行语法分析的过程中流动起来, 所以这个 “流动” 过程通常是由 parser 而不是其他什么部分来控制的.

那么综上所述, 在实现语法分析器的过程中, 我们势必会遇到两个问题:

1. 语法分析器怎么实现.
2. AST 如何定义.

优先解决哪一个问题见仁见智. 笔者 (MaxXing) 比较习惯先根据语言的语法定义 AST, 然后根据 EBNF 着手实现 parser, 在实现的过程中再逐步修改和细化 AST 的定义.

## 递归下降语法分析

从编译原理课程中我们得知, parser 根据实现方法可以分为很多类, 比如 LL parser, LR parser, LALR parser 等等... 但这其中最适合手写实现的 parser, 当属使用递归下降分析法构建的 LL(k) parser 了.

递归下降分析法, 顾名思义, 就是借助递归函数实现的, 自顶向下 (top-down) 的语法分析方法. 当我们把某种语言描述为 LL(1) 形式的 EBNF 语法时, 我们就可以很快地利用递归下降分析法写出这种语言的 parser, 比如四则运算表达式的语法可以写成如下的形式:

```ebnf
AddExpr ::= MulExpr {("+" | "-") MulExpr};
MulExpr ::= Value {("*" | "/") Value};
Value   ::= INTEGER | "(" AddExpr ");
```

在 parser 的实现中, 我们可以为每一条语法规则 (每一个非终结符) 都设置一个对应的函数. 在这个函数中, 我们需要实现解析这条语法规则的实际操作, 对应于 EBNF 中 `::=` 右侧的内容. 函数的返回值则为由该条语法规则构建得到的 AST. 具体的实现方式大概如下:

* **对于 `RuleA RuleB RuleC` 的情况**: 直接按顺序调用对应 `RuleA`, `RuleB` 和 `RuleC` 的函数, 把他们的返回值拼起来作为最终的 AST.
* **对于 `RuleA | RuleB` 的情况**: 检查 lexer 返回的当前 token, 如果与 `RuleA` 开头的 token 一致, 则调用函数解析 `RuleA`; 反之同理.
* **对于 `[RuleA]` 的情况**: 检查 lexer 返回的当前 token, 如果与 `RuleA` 开头的 token 一致, 则调用函数解析 `RuleA`; 否则跳过 `RuleA`, 解析之后的内容.
* **对于 `{RuleA}` 的情况**: 检查 lexer 返回的当前 token, 如果与 `RuleA` 开头的 token 一致, 则循环调用 `RuleA` 对应的函数, 直到当前 token 不符合 `RuleA` 的定义; 如果不符合 `RuleA`, 则跳过, 并解析之后的内容.

请自行体会以上的实现方式, 然后忘掉这些条条框框的内容, 因为有的时候你可能会遇到某些例外, 此时你应该结合实际情况, 换用更特定的方式去处理.

根据前文的描述, 我们可以将四则运算的 EBNF 翻译为如下的类 C/C++ **伪代码**:

```clike
AST *ParseAddExpr() {
  auto lhs = ParseMulExpr();
  while (current_token == "+" || current_token == "-") {
    auto token = current_token;
    NextToken();
    auto rhs = ParseMulExpr();
    lhs = MakeBinaryAST(token, lhs, rhs);
  }
  return lhs;
}

AST *ParseMulExpr() {
  auto lhs = ParseValue();
  while (current_token == "*" || current_token == "/") {
    auto token = current_token;
    NextToken();
    auto rhs = ParseValue();
    lhs = MakeBinaryAST(token, lhs, rhs);
  }
  return lhs;
}

AST *ParseValue() {
  if (current_token.IsInteger()) {
    auto integer = current_token;
    NextToken();
    return MakeIntegerAST(integer);
  }
  else if (current_token == "(") {
    NextToken();
    auto expr = ParseAddExpr();
    NextToken();
    return expr;
  }
  else {
    // TODO: handle error
    return nullptr;
  }
}
```

当然, 在实际的代码中, 我们还需要处理语法错误, 稍后我们会讨论 parser 的具体实现.

## AST 的表示

上一节我们提到, 递归下降 parser 由若干个函数组成, 每个函数对应 EBNF 里的一条语法规则, 且返回值为 AST. 这就要求我们设计一种统一的 AST 类型作为函数的返回类型, 并且这种类型还能够描述语言中所有语法的结构.

在 C 语言中, 我们可能会选择定义一个结构体, 结构体的某个字段表示这个 AST 所属的类型, 比如表示一个函数定义, 或是一个 `if-else` 语句等. 使用这种方式可以达成上述目标, 但代码写起来未免有些凌乱.

不过还好, 在这个例子中, 我们用的是 C++, 借助面向对象的设计方法, 我们可以将 AST 设计为继承结构:

* 所有的 AST 都有一个公共的基类, 用于为外部提供访问 AST 的统一方法.
* 每个代表不同语法结构的 AST 都继承基类, 实现接口方法, 并且在此基础上扩展自己需要的其他字段.

所以我们先定义一个基类, 然后定义一个智能指针类型, 方便我们在代码中表示 “指向 AST 的指针”, 并且管理动态分配的内存:

```clike
// 所有 AST 的基类
class BaseAST {
 public:
  virtual ~BaseAST() = default;

  // 这里需要写一些接口方法, 方便我们遍历 AST
  // 先空着
};

// AST 的指针, 以及 AST 指针的列表
// 后续可能会有很多地方用到这些类型, 所以先将它们定义出来, 省得敲那么多字
using ASTPtr = std::unique_ptr<BaseAST>;
using ASTPtrList = std::vector<ASTPtr>;
```

这样, 定义一个具体的 AST 时, 我们只需要:

```clike
// 定义一个新的 AST, 并继承 AST 的基类
class SomeAST : public BaseAST {
 public:
  // 构造函数, 包含构造这个 AST 所需的全部数据
  SomeAST(A a, B b, C c, ...) : a_(a), b_(b), c_(c), ... {}

 private:
  // AST 内部的各类数据
  A a_;
  B b_;
  C c_;
  ...
};
```

## AST 的定义

首先我们来回顾一下 `first-step` 的 EBNF:

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

前文我们提到, parser 可以按照 EBNF 右侧的定义, 通过调用对应的函数来解析对应的规则, 然后将这些函数返回的内容按顺序拼成一个 AST. 由这个思路我们大概可以知道, 这其中的一部分 AST 应当如何来定义, 比如:

```ebnf
IfElse ::= "if" Expression Block ["else" (IfElse | Block)];
```

`IfElse` 对应的语法规则中有三个具有实际意义的部分: `if` 的条件 (`Expression`), 满足条件时执行的语句块 (`Block`), 以及不满足条件时执行的内容 (`(IfElse | Block)`). 第三个部分是可选的, 取决于当前这个 `if` 语句究竟有没有 `else` 分支. 我们可以这样定义:

```clike
class IfAST : public BaseAST {
 public:
  IfAST(ASTPtr cond, ASTPtr then, ASTPtr else_then)
      : cond_(std::move(cond)), then_(std::move(then)),
        else_then_(std::move(else_then)) {}

 private:
  // 分别表示 if 的条件, 满足/不满足条件时执行的内容
  ASTPtr cond_, then_, else_then_;
};
```

由于 `ASTPtr` 是个指针, 指针本身就是可空的, 所以当 `if` 不具备 `else` 分支时, 我们将 `else_then_` 字段设为 `nullptr` 即可.

当然, 我们并不需要为所有的语法规则单独设计 AST, 那样就太啰嗦了. 比如:

```ebnf
Expression ::= LOrExpr;
```

`Expression` 相当于 `LOrExpr` 的别名, 所以没必要为 `Expression` 单独定义 AST.

```ebnf
ArgsDef ::= IDENT {"," IDENT};
```

`ArgsDef` 实际上表示的就是 “标识符的列表”, 我们直接用一个 `std::vector` 表示它就可以了, 同样没必要单独定义一个对应的 AST.

```ebnf
LOrExpr   ::= LAndExpr {"||" LAndExpr};
LAndExpr  ::= EqExpr {"&&" EqExpr};
EqExpr    ::= RelExpr {("==" | "!=") RelExpr};
...
```

由于需要表达二元运算的优先级, 所有的二元表达式被我们按照优先级分成了若干个不同的语法规则. 但它们的结构都是一致的, 只需要一个运算符和两个操作数就可以表示. 所以我们只需定义一个统一的 `BinaryAST` 来表示所有二元表达式:

```clike
class BinaryAST : public BaseAST {
 public:
  BinaryAST(Operator op, ASTPtr lhs, ASTPtr rhs)
      : op_(op), lhs_(std::move(lhs)), rhs_(std::move(rhs)) {}

 private:
  // 运算符
  Operator op_;
  // 左操作数和右操作数
  ASTPtr lhs_, rhs_;
};
```

其余 AST 的定义同理, 各位可阅读[源码](https://github.com/pku-minic/first-step/blob/master/src/define/ast.h)并自行体会.

## 实现 parser

说了那么多, 相信你已经基本了解如何使用递归下降法, 实现 `first-step` 的 parser 了.

首先根据 EBNF 定义对应的解析函数. 注意, 有些规则没必要定义单独的解析函数, 比如 `Program`, 因为编译器调用 parser 的过程就是一个循环:

```clike
int main() {
  ...
  while (auto ast = parser.ParseSomething()) {
    // 对 `ast` 做点什么
    ... 
  }
  ...
  return 0;
}
```

直接把 `ParseSomething` 代换为 `ParseFunctionDef` 也是丝毫没有问题的.

然后根据前文描述的情况实现具体的解析过程, 这里我们要注意处理语法错误的情况. 我们可以规定: 如果一个解析语法规则的函数返回了空指针 (`nullptr`), 那说明我们在解析这个规则的过程中遇到了错误, 并且没有产生任何对应的 AST. 依然以解析二元表达式为例子:

```clike
ASTPtr ParseAddExpr() {
  auto lhs = ParseMulExpr();
  // 解析 `MulExpr` 的过程中可能会遇到错误
  // 此时我们没办法继续往下走了, 所以直接返回一个 `nullptr`, 把错误传递下去
  if (!lhs) return nullptr;
  while (IsTokenOp(Operator::Add) || IsTokenOp(Operator::Sub)) {
    // 记下当前的运算符
    auto op = lexer_.op_val();
    NextToken();
    // 解析右表达式, 此时同样可能出错, 处理方式同上
    auto rhs = ParseMulExpr();
    if (!rhs) return nullptr;
    // 更新左表达式
    lhs = std::make_unique<BinaryAST>(op, std::move(lhs), std::move(rhs));
  }
  return lhs;
}
```

而有些情况处理起来并不那么直观, 比如我们注意到 `Statement` 规则中存在左公因子:

```ebnf
Statement ::= IDENT ":=" Expression
            | IDENT "=" Expression
            | FunctionCall (* `FunctionCall` 的开头也是 `IDENT` *)
            | IfElse
            | "return" Expression;
```

这个时候我们可以尝试将 EBNF 修改为提取左公因子后的形式, 但直接按照目前的定义写一个 parser 也是可以的, 比如在 `ParseStatement` 中遇到 `IDENT` 之后:

```clike
ASTPtr ParseStatement() {
  switch (cur_token_) {
    case Token::Id: {
      // 先记下 `IDENT` 的值
      auto name = lexer_.id_val();
      NextToken();
      // 然后根据下一个符号判断目前究竟需要处理哪一条规则
      if (IsTokenOp(Operator::Define)) {
        // 处理变量定义语句, 把 `IDENT` 的值作为参数传入
        return ParseDefine(name);
      }
      else if (IsTokenOp(Operator::Assign)) {
        // 同上
        return ParseAssign(name);
      }
      else if (IsTokenChar('(')) {
        // 同上
        return ParseFunctionCall(name);
      }
      else {
        // 和所有的预期都不符, 处理语法错误
        return LogError("invalid statement");
      }
    }
    case Token::Keyword: ...
    default:;
  }
  ...
}
```

这里的 `LogError` 是我们定义的一个错误处理函数, 调用后, 程序会向 `stderr` 输出指定的错误信息, 并且返回一个 `nullptr`, 来告诉 parser 解析过程中遇到了一个错误.

当然你可能会注意到, 在 `first-step` 的实现中, 我们没有使用上述的方法, 而用了另一套方法. 详情你可以自行查看[源码](https://github.com/pku-minic/first-step/blob/master/src/front/parser.cpp#L58), 此处就不展开叙述了.

## 完整代码

请参考 GitHub 上 [`first-step` repo](https://github.com/pku-minic/first-step) 中的:

* **AST 定义**: [ast.h](https://github.com/pku-minic/first-step/blob/master/src/define/ast.h).
* **parser 实现**: [parser.h](https://github.com/pku-minic/first-step/blob/master/src/front/parser.h) 和 [parser.cpp](https://github.com/pku-minic/first-step/blob/master/src/front/parser.cpp).
