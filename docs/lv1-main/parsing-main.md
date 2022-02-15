# Lv1.3. 解析 `main` 函数

上一节我们借助词法/语法分析器生成器实现了一个可以解析 `main` 函数的简单程序, 但它离真正的编译器还有一些差距: 这个程序只能~如蜜传如蜜~——把输入的源代码转换成, 呃, 源代码, 而不是 AST.

本节将带大家快速理解 AST 要怎么设计, 以及如何让你的编译器生成 AST.

## 设计 AST

设计 AST 这件事其实很简单, 你首先要知道:

1. AST 保留了程序语法的结构.
2. AST 是为了方便程序的处理而存在的, 不存在什么设计规范.

所以其实你自己用着怎么舒服, 就怎么设计, 这样就好了. 你学会了吗? 现在来写一个编译器吧! (bushi

好吧, 说正经的. 你确实只需要以上这两点, 更重要的是第一点: AST 需要保留一些必要的语法结构. 或者换句话说, EBNF 长什么样, AST 就可以长什么样. 比如本章需要大家处理的 EBNF 如下:

```ebnf
CompUnit  ::= FuncDef;

FuncDef   ::= FuncType IDENT "(" ")" Block;
FuncType  ::= "int";

Block     ::= "{" Stmt "}";
Stmt      ::= "return" Number ";";
Number    ::= INT_CONST;
```

`CompUnit` 由一个 `FuncDef` 组成, `FuncDef` 由 `FuncType`, `IDENT` 和 `Block` 组成 (中间的那对括号暂时没什么实际意义). 所以在 C++ 中, 我们可以这么写:

```cpp
struct CompUnit {
  FuncDef func_def;
};

struct FuncDef {
  FuncType func_type;
  std::string ident;
  Block block;
};
```

当然, 考虑到 Flex/Bison 中返回指针比较方便, 我们可以用一点点 OOP 和智能指针来解决问题:

```cpp
// 所有 AST 的基类
class BaseAST {
 public:
  virtual ~BaseAST() = default;
};

// CompUnit 是 BaseAST
class CompUnitAST : public BaseAST {
 public:
  // 用智能指针管理对象
  std::unique_ptr<BaseAST> func_def;
};

// FuncDef 也是 BaseAST
class FuncDefAST : public BaseAST {
 public:
  std::unique_ptr<BaseAST> func_type;
  std::string ident;
  std::unique_ptr<BaseAST> block;
};

// ...
```

其他 EBNF 对应的 AST 的定义方式与之类似, 不再赘述.

Rust 实现的编译器也可以采用这种方式定义 AST, 不过一方面, lalrpop 可以很方便地给不同的语法规则定义不同的返回类型; 另一方面, 在 Rust 里用指针, 引用或者多态 (trait object) 总会有些别扭, 所以我们不如直接把不同的 AST 定义成不同的类型.

```rust
pub struct CompUnit {
  pub func_def: FuncDef,
}

pub struct FuncDef {
  pub func_type: FuncType,
  pub ident: String,
  pub block: Block,
}

// ...
```

## 生成 AST

C++ 实现中, 我们可以在 `.y` 文件里添加一个新的类型声明:

```bison
%union {
  std::string *str_val;
  int int_val;
  BaseAST *ast_val;
}
```

当然, 在此之前, 所有的 AST 定义应该被放入一个头文件, 同时你应该在 `.y` 文件中正确处理头文件的引用.

此外, 我们还需要修改参数类型的声明 (其他相关声明也应该被一并修改):

```bison
%parse-param { std::unique_ptr<BaseAST> &ast }
```

然后适当调整非终结符和语法规则的定义即可:

```bison
%type <ast_val> FuncDef FuncType Block Stmt
%type <int_val> Number

%%

CompUnit
  : FuncDef {
    auto comp_unit = make_unique<CompUnitAST>();
    comp_unit->func_def = unique_ptr<BaseAST>($1);
    ast = move(comp_unit);
  }
  ;

FuncDef
  : FuncType IDENT '(' ')' Block {
    auto ast = new FuncDefAST();
    ast->func_type = unique_ptr<BaseAST>($1);
    ast->ident = *unique_ptr<string>($2);
    ast->block = unique_ptr<BaseAST>($5);
    $$ = ast;
  }
  ;

// ...
```

这样, 我们就在 Bison 生成的 parser 中完成了 AST 的构建, 并将生成的 AST 返回给了 parser 函数的调用者.

Rust 中, lalrpop 的操作也与之类似 (注意尖括号的用法):

```
pub CompUnit: CompUnit = <func_def: FuncDef> => CompUnit { <> };

FuncDef: FuncDef = {
  <func_type: FuncType> <ident: Ident> "(" ")" <block: Block> => {
    FuncDef { <> }
  }
}

FuncType: FuncType = "int" => FuncType::Int;

Block: Block = "{" <stmt: Stmt> "}" => Block { <> };

Stmt: Stmt = "return" <num: Number> ";" => Stmt { <> };

Number: i32 = <num: IntConst> => <>;
```

## 检查生成结果

目前的编译器已经能够正确生成 AST 了, 不过生成得到的 AST 暂时只能保存在内存里. 如果我们能把 AST 的内容也输出到命令行, 我们就能检查编译器是否按照我们的意愿生成 AST 了.

在 C++ 定义的 AST 中, 我们可以借助虚函数的特性, 给 `BaseAST` 添加一个虚函数 `Dump`, 来输出 AST 的内容:

```cpp
class BaseAST {
 public:
  virtual ~BaseAST() = default;

  virtual void Dump() const = 0;
};
```

?> 当然这里你也可以给 AST 重载流输出运算符 (`operator<<`). C++ 的玩法实在是太多了, 这里只挑相对大众且便于理解的方法介绍.

然后分别为所有其他 AST 实现 `Dump`:

```cpp
class CompUnitAST : public BaseAST {
 public:
  std::unique_ptr<BaseAST> func_def;

  void Dump() const override {
    std::cout << "CompUnitAST { ";
    func_def->Dump();
    std::cout << " }";
  }
};

class FuncDefAST : public BaseAST {
 public:
  std::unique_ptr<BaseAST> func_type;
  std::string ident;
  std::unique_ptr<BaseAST> block;

  void Dump() const override {
    std::cout << "FuncDefAST { ";
    func_type->Dump();
    std::cout << ", " << ident << ", ";
    block->Dump();
    std::cout << " }";
  }
};

// ...
```

在 `main` 函数中, 我们就可以使用 `Dump` 方法来输出 AST 的内容了:

```cpp
// parse input file
unique_ptr<BaseAST> ast;
auto ret = yyparse(ast);
assert(!ret);

// dump AST
ast->Dump();
cout << endl;
```

运行后编译器会输出:

```
CompUnitAST { FuncDefAST { FuncTypeAST { int }, main, BlockAST { StmtAST { 0 } } } }
```

对于 Rust, 事情变得更简单了: 我们只需要给每个 AST 的结构体/枚举 derive `Debug` trait 即可:

```rust
#[derive(Debug)]
pub struct CompUnit {
  pub func_def: FuncDef,
}

#[derive(Debug)]
pub struct FuncDef {
  pub func_type: FuncType,
  pub ident: String,
  pub block: Block,
}

// ...
```

然后稍稍在 `main` 函数的 `println!` 部分加三个字符:

```rust
// parse input file
let ast = sysy::CompUnitParser::new().parse(&input).unwrap();
println!("{:#?}", ast);
```

运行后编译器会输出:

```
CompUnit {
    func_def: FuncDef {
        func_type: Int,
        ident: "main",
        block: Block {
            stmt: Stmt {
                num: 0,
            },
        },
    },
}
```
