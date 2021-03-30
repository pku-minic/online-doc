# 2.2. 词法分析器

词法分析阶段通常是编译的第一个阶段.

为什么要进行词法分析呢? 以人类的阅读来举例子: 假设你在读一部英文小说, 组成小说的最小单位是字符, 包括英文字母, 标点符号, 空白等等. 你显然不会一个字符一个字符地读这部小说, 你会尝试以空白和标点符号为界, 将字符组成一个个单词, 然后通过理解单词的含义, 来理解句子, 段落, 章节, 乃至整部小说的含义.

编译器处理源文件时也是如此: 它会尝试先把读出的字符按照某种规则, 切成一个个便于识别和处理的 token, 然后再由剩下的部分通过匹配 token 来实现后续的处理过程. 这样做会比直接在字符上进行处理要简单, 规整得多.

将输入流切成一个个 token 的过程即为词法分析, 而负责将输入流切成 token 流的工具叫做词法分析器.

本节我们将实现 `first-step` 语言的词法分析器, 即 lexer.

## token 的类型

从上一节的 [EBNF 定义](step-by-step/beginning.md?id=ebnf-格式的语法定义)中, 我们可以发现 lexer 必须能够将输入流切成如下几类 token:

* `IDENT`: 标识符, 在 `first-step` 中, 为任意以字母或下划线开头, 后接零个或多个字母, 下划线或数字的字符串.
* `INTEGER`: 整数, 即 0, 或由非零数字开头, 后接零个或多个数字的字符串.
* 关键字: `if`, `else` 和 `return`.
* 运算符: `+`, `-`, `==` 等符号.
* 其他字符: `{`, `(` 等字符.

此外, lexer 还需要跳过以下的内容:

* 空白符: 包括空格, 缩进, 换行符等符号. lexer 应当具备跳过任意多个连续的上述符号的能力.
* 注释: 以 `#` 开头, 换行符结尾, 中间包含任意多个任意字符的字符串.

当然, 可能你在初次接触编译器的实现时, 并不能立即发现上述规则. 你可以结合 EBNF 以及上一节中 `first-step` 的例程, 略加思考. 当你身经百战, 见得多了之后就会发现, 很多语言的 lexer 其实都长得差不多, token 的分类也无非就那么几种.

## 识别 token

现在我们已经知道了 token 的分类和组成规则, 那我们要如何编写 lexer, 才能让它正确的识别 token 呢?

聪明的你肯定会想到, 老师在课上曾经教过正则式, NFA, DFA, 状态转换表云云, 我们的 lexer 中一定得包含这些东西. 其实这话说得也没错, 从正则表达式匹配字符串的角度来看, 如果你把上述 token 的规则描述为正则式, 而你又期望你的 lexer 能根据这些正则式自动对输入的字符串进行高效匹配, 那你的 lexer 中最好包含这些算法和结构.

不过, 我们目前实现的 lexer 只需要解析 `first-step` 涉及的各类 token, 这些 token 的形式都是固定的, 我们并不需要设计一个通用的程序, 去把这些规则转换为自动机和转换表. 我们完全可以直接根据 token 的描述, 把匹配的逻辑写成一系列循环和条件判断, 硬编码在程序里: 这反而是最省时省力的方案, 虽然听起来这么做程序会变得很乱, 但相信我, 最终的实现一点都不乱.

## 一些准备工作

在 C++ 中, 文件, 标准输入, 乃至一个字符串, 都可以被抽象成流 (stream), 我们可以使用如下的方法从一个流中读取单个字符:

```clike
class Lexer {
 public:
  Lexer(std::istream &in) : in_(in) {}

 private:
  // 从输入流 `in_` 中读取一个字符, 并将其存储到 `last_char_` 中
  void NextChar() {
    in_ >> last_char_;
  }

  std::istream &in_;
  char last_char_;
};
```

由于我们的 lexer 需要通过读取空白符来实现 token 与 token 之间的分隔, 而 C++ 的输入流默认会在读取时跳过空白符, 所以我们需要在 `Lexer` 初始化时来告诉输入流: 不要跳过空白符.

```clike
Lexer() {
  in_ >> std::noskipws;
}
```

### 识别标识符

前文提到, 标识符的开始可以是任意的字母或下划线, 所以我们需要在读取到这些字符时调用处理标识符的函数:

```clike
if (std::isalpha(last_char_) || last_char_ == '_') return HandleId();
```

函数 `HandleId` 负责完成接下来的事情:

```clike
std::string id;
do {
  // 将当前字符放入 `id`, 并继续读取下一个字符
  id += last_char_;
  NextChar();
  // 遇到文件结尾, 或者当前字符不是字母, 数字, 下划线的情况就停下
} while (!in_.eof() && (std::isalnum(last_char_) || last_char_ == '_'));
```

在这种情况下, 变量 `id` 不仅可能读取到标识符, 还可能读取到形如 `if`, `else` 和 `return` 的关键字, 我们必须对这种情况进行处理:

```clike
// 检查 `id` 中的字符串是否是一个关键字
auto it = kKeywords.find(id);
if (it == kKeywords.end()) {
  // 不是关键字, 将读取到的标识符存起来, 并返回代表标识符的 token
  id_val_ = std::move(id);
  return Token::Id;
}
else {
  // 是一个关键字
  key_val_ = it->second;
  return Token::Keyword;
}
```

### 识别整数

整数可能由数字 0 到 9 开头:

```clike
if (std::isdigit(last_char_)) return HandleInteger();
```

当然也由数字 0 到 9 组成:

```clike
std::string num;
do {
  num += last_char_;
  NextChar();
} while (!in_.eof() && std::isdigit(last_char_));
```

标准库 (`cstdlib`) 中已经给我们提供了检查字符串是否为合法数字, 并将其转换为整数的函数, 我们直接调用即可:

```clike
// 尝试将字符串中的内容转换为数字, 并将结果存起来
char *end_pos;
int_val_ = std::strtol(num.c_str(), &end_pos, 10);
// 如果存在转换失败的情况, 或者数字开头为 0 但又不是单个的 0, 则发生词法错误
return *end_pos || (num[0] == '0' && num.size() > 1)
           ? LogError("invalid number") : Token::Integer;
```

### 识别运算符

运算符的识别也并不复杂, 我们可以先实现一个函数, 判断某个字符 `c` 是否是一个可能出现在运算符中的字符:

```clike
bool IsOperatorChar(char c) {
  const char op_chars[] = "+-*/%<=!&|:";
  for (const auto &i : op_chars) {
    if (i == c) return true;
  }
  return false;
}
```

然后用和识别数字类似的方法即可. 运算符开头的字符肯定要符合 `IsOperatorChar` 定义的特征:

```clike
if (IsOperatorChar(last_char_)) return HandleOperator();
```

同时运算符也由符合这些特征的字符组成:

```clike
std::string op;
do {
  op += last_char_;
  NextChar();
} while (!in_.eof() && IsOperatorChar(last_char_));
```

最后我们会得到一个看起来像是运算符的字符串, 至于它到底是不是一个合法的运算符, 还需要进一步判断:

```clike
// 检查运算符是否合法
auto it = kOperators.find(op);
if (it == kOperators.end()) return LogError("invalid operator");
// 记录运算符的内容, 并返回代表运算符的 token
op_val_ = it->second;
return Token::Operator;
```

### 跳过空白符和注释

我们可以在处理标识符, 整数, 运算符等内容之前, 先跳过所有的空白符.

```clike
// 跳过空白符
while (std::isspace(last_char_)) NextChar();
```

这么写会有一些问题, 比如某个文件的结尾处有一些空白符, 这时 lexer 会试图一直读取下一个字符, 然而这么做会导致程序陷入死循环. 因为 `NextChar` 函数是这么写的:

```clike
void NextChar() {
  in_ >> last_char_;
}
```

输入流 `in_` 在遇到文件结尾 (EOF) 时, 并不会更新 `last_char_` 的值, 这就导致 `last_char_` 始终保留着上一次的值, 也就是空白符. 而判断循环退出的条件是 “`last_char_` 不是空白符”, 所以循环永远不会退出.

我们可以添加对 EOF 的判断, 并且在出现 EOF 时返回一个对应的 token:

```clike
// 跳过空白符
while (!in_.eof() && std::isspace(last_char_)) NextChar();
// 处理 EOF, 以防陷入死循环
if (in_.eof()) return Token::End;
```

处理注释的方法和之前类似, `first-step` 中所有以 `#` 开头的内容都属于行注释.

```clike
if (last_char_ == '#') return HandleComment();
```

行注释的结尾是换行符, 所以在遇到换行符之后要停下来. 此外, 由于行注释本身并没有任何含义, 所以我们并不需要提供一个代表行注释的 token, 在解析完行注释之后, 返回它的下一个 token 即可.

```clike
// 跳过当前行
while (!in_.eof() && last_char_ != '\n' && last_char_ != '\r') {
  NextChar();
}
// 返回下一个 token
return NextToken();
```

### 组合

在 lexer 中, `NextToken` 函数借助上述我们提到的所有处理方式, 实现了将输入流变为 token 流的过程:

```clike
Token NextToken()) {
  // 跳过空白符
  while (!in_.eof() && std::isspace(last_char_)) NextChar();
  // 处理文件结尾
  if (in_.eof()) return Token::End;
  // 跳过注释
  if (last_char_ == '#') return HandleComment();
  // 识别标识符或关键字
  if (std::isalpha(last_char_) || last_char_ == '_') return HandleId();
  // 识别整数
  if (std::isdigit(last_char_)) return HandleInteger();
  // 识别运算符
  if (IsOperatorChar(last_char_)) return HandleOperator();
  // 处理其他字符
  other_val_ = last_char_;
  NextChar();
  return Token::Other;
}
```

## 完整代码

请参考 GitHub 上 [`first-step` repo](https://github.com/pku-minic/first-step) 中的 [lexer.h](https://github.com/pku-minic/first-step/blob/master/src/front/lexer.h) 和 [lexer.cpp](https://github.com/pku-minic/first-step/blob/master/src/front/lexer.cpp).
